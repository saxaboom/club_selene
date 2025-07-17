import streamlit as st
import json
from datetime import datetime
import calendar

# Load secrets
pin_code = st.secrets["pin_key"]

# Data files
CHAT_FILE = 'chat_messages.json'
BOOKINGS_FILE = 'bookings.json'

# Load data
def load_data(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except:
        return []

def save_data(data, file):
    with open(file, 'w') as f:
        json.dump(data, f)

messages = load_data(CHAT_FILE)
bookings = load_data(BOOKINGS_FILE)

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

# Display chat messages
st.subheader("Messages")
for i, msg in enumerate(messages):
    st.write(f"**{msg['name']}** ({msg['timestamp']}): {msg['message']}")
    # Provide delete option
    pin = st.text_input(f"Enter PIN to delete message {i}", key=f"pin_{i}")
    if st.button(f"Delete message {i}", key=f"del_{i}"):
        # Check PIN against secret
        entered_pin = st.session_state.get(f"pin_{i}")
        if entered_pin == pin_code:
            messages.pop(i)
            save_data(messages, CHAT_FILE)
            st.success("Message deleted.")
        else:
            st.error("Incorrect PIN.")

# --- Schedule Calendar ---
st.header("Schedule Play Dates")
today = datetime.today()
month = st.slider("Select Month", 1, 12, today.month)
year = st.slider("Select Year", today.year-1, today.year+1, today.year)

# Generate calendar
cal = calendar.monthcalendar(year, month)
st.write(calendar.month_name[month], year)

for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write(" ")
        else:
            date_str = f"{year}-{month:02d}-{day:02d}"
            # Show existing bookings
            day_bookings = [b for b in bookings if b['date'] == date_str]
            if day_bookings:
                for b in day_bookings:
                    cols[i].write(f"{day}\n- {b['child']} (Parent: {b['parent']}) at {b['time']}")
            # Book button
            with cols[i]:
                if st.button(f"Book {day}", key=f"book_{date_str}"):
                    st.session_state['booking_date'] = date_str
                    st.session_state['show_booking_form'] = True

# --- Booking Form ---
if 'show_booking_form' not in st.session_state:
    st.session_state['show_booking_form'] = False

if st.session_state['show_booking_form']:
    st.subheader(f"Book Play Date on {st.session_state['booking_date']}")
    with st.form("booking_form"):
        parent_name = st.text_input("Parent's Name")
        child_name = st.text_input("Child's Name")
        time_slot = st.time_input("Preferred Time")
        submitted_booking = st.form_submit_button("Confirm Booking")
        if submitted_booking:
            bookings.append({
                "parent": parent_name,
                "child": child_name,
                "date": st.session_state['booking_date'],
                "time": str(time_slot)
            })
            save_data(bookings, BOOKINGS_FILE)
            st.success("Play date booked!")
            st.session_state['show_booking_form'] = False
