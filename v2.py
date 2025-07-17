import streamlit as st
import json
from datetime import datetime
import calendar

# Load secrets (set in secrets.toml)
pin_code = st.secrets["pin_key"]

# Data files
CHAT_FILE = 'chat_messages.json'
BOOKINGS_FILE = 'bookings.json'

# Functions to load and save data
def load_data(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except:
        return []

def save_data(data, file):
    with open(file, 'w') as f:
        json.dump(data, f)

# Load existing data
messages = load_data(CHAT_FILE)
bookings = load_data(BOOKINGS_FILE)

# --- App Title ---
st.title("Club-Selene: Children's Play Date Organizer & Chat")

# --- Chat Section ---
st.header("Public Chat")
with st.form("chat_form", clear_on_submit=True):
    user_name = st.text_input("Your Name")
    message = st.text_area("Message")
    submitted = st.form_submit_button("Send")
    if submitted and user_name and message:
        messages.append({
            "name": user_name,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        save_data(messages, CHAT_FILE)
        st.success("Message sent!")

# Display chat messages
st.subheader("Messages")
for i, msg in enumerate(messages):
    col1, col2, col3 = st.columns([4, 2, 2])
    with col1:
        st.write(f"**{msg['name']}** ({msg['timestamp']}): {msg['message']}")
    with col2:
        # Input for PIN to delete
        pin_input = st.text_input(f"PIN to delete message {i}", key=f"pin_{i}")
    with col3:
        if st.button(f"Delete", key=f"del_{i}"):
            entered_pin = st.session_state.get(f"pin_{i}")
            if entered_pin == pin_code:
                try:
                    messages.pop(i)
                    save_data(messages, CHAT_FILE)
                    st.success("Message deleted.")
                except IndexError:
                    st.error("Failed to delete message.")
            else:
                st.error("Incorrect PIN.")

# --- Calendar View ---
st.header("Schedule Play Dates")
today = datetime.today()
selected_month = st.slider("Select Month", 1, 12, today.month)
selected_year = st.slider("Select Year", today.year - 1, today.year + 1, today.year)

# Generate calendar matrix
cal_matrix = calendar.monthcalendar(selected_year, selected_month)

st.subheader(f"{calendar.month_name[selected_month]} {selected_year}")

for week in cal_matrix:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write(" ")
        else:
            date_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
            # Find bookings for the day
            day_bks = [b for b in bookings if b['date'] == date_str]
            with cols[i]:
                if st.button(f"{day}", key=f"day_{date_str}"):
                    st.session_state['booking_date'] = date_str
                    st.session_state['show_booking_form'] = True
                # Show existing bookings
                if day_bks:
                    for b in day_bks:
                        st.write(f"- {b['child']} (Parent: {b['parent']}) at {b['time']}")

# --- Booking Form ---
if 'show_booking_form' not in st.session_state:
    st.session_state['show_booking_form'] = False

if st.session_state.get('show_booking_form'):
    booking_date = st.session_state.get('booking_date')
    st.subheader(f"Book Play Date on {booking_date}")
    with st.form("booking_form"):
        parent_name = st.text_input("Parent's Name")
        child_name = st.text_input("Child's Name")
        time_slot = st.time_input("Preferred Time")
        submit_bk = st.form_submit_button("Confirm Booking")
        if submit_bk:
            # Save booking
            bookings.append({
                "parent": parent_name,
                "child": child_name,
                "date": booking_date,
                "time": str(time_slot)
            })
            save_data(bookings, BOOKINGS_FILE)
            st.success("Play date booked!")
            st.session_state['show_booking_form'] = False
