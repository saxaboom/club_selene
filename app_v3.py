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
st.title("Welcome to Club-Selene!")
st.subheader("   ... a hub for messages and play-dates.  ; )")

# --- Chat Section ---
st.header("Leave a Message")
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
    try:
        dt = datetime.fromisoformat(msg['timestamp'])
        human_time = dt.strftime('%A, %B %d, %Y at %I:%M %p')
    except:
        human_time = msg['timestamp']
    st.write(f"**{msg['name']}**")
    st.write(f"{msg['message']}")
    st.write(f"{human_time}")

    toggle_key = f"delete_toggle_{i}"
    if toggle_key not in st.session_state:
        st.session_state[toggle_key] = False
    if st.button("🗑️", key=f"toggle_delete_{i}"):
        st.session_state[toggle_key] = not st.session_state[toggle_key]
    if st.session_state[toggle_key]:
        pin_value = st.text_input(
            f"Enter PIN to delete message {i}",
            key=f"pin_input_{i}",
            placeholder="PIN",
            label_visibility='collapsed',
            type='password'
        )
        if st.button("Confirm Delete", key=f"confirm_del_{i}"):
            entered_pin = st.session_state.get(f"pin_input_{i}", "")
            if entered_pin == pin_code:
                try:
                    messages.pop(i)
                    save_data(messages, CHAT_FILE)
                    st.success("Message deleted.")
                    st.session_state[toggle_key] = False
                except:
                    st.error("Failed to delete message.")
            else:
                st.error("Incorrect PIN.")

# --- Schedule Play Dates ---
st.header("Schedule Play Dates")
today = datetime.today()
selected_month = st.slider("Select Month", 1, 12, today.month)
selected_year = st.slider("Select Year", today.year - 1, today.year + 1, today.year)

cal_matrix = calendar.monthcalendar(selected_year, selected_month)
st.subheader(f"{calendar.month_name[selected_month]} {selected_year}")

# Initialize session states
if 'selected_date' not in st.session_state:
    st.session_state['selected_date'] = None
if 'view_bookings_for_date' not in st.session_state:
    st.session_state['view_bookings_for_date'] = None

# Placeholder for blocked, pending, confirmed dates (populate as needed)
blocked_dates = set()   # e.g., {'2024-05-15'}
pending_dates = set()
confirmed_dates = set()

# Populate date statuses based on bookings
for b in bookings:
    date_str = b['date']
    status = b.get('status', 'Pending')
    if status == 'Blocked':
        blocked_dates.add(date_str)
    elif status == 'Pending':
        pending_dates.add(date_str)
    elif status == 'Confirmed':
        confirmed_dates.add(date_str)

def get_date_icon(date_str):
    if date_str in blocked_dates:
        return '🔴'  # Red
    elif date_str in pending_dates:
        return '🔵'  # Blue
    elif date_str in confirmed_dates:
        return '🟢'  # Green
    else:
        return ''  # No icon

# Display calendar grid with icons
for week in cal_matrix:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write(" ")
        else:
            date_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
            icon = get_date_icon(date_str)
            btn_label = f"{day} {icon}"
            if cols[i].button(btn_label, key=f"date_{date_str}"):
                # When clicked, set selected date & show bookings
                st.session_state['selected_date'] = date_str
                st.session_state['view_bookings_for_date'] = date_str

# --- Show bookings for selected date ---
if st.session_state.get('view_bookings_for_date'):
    selected_date = st.session_state['view_bookings_for_date']
    st.subheader(f"Bookings for {selected_date}")
    date_bookings = [b for b in bookings if b['date'] == selected_date]
    if date_bookings:
        for idx, b in enumerate(date_bookings):
            status = b.get('status', 'Pending')
            st.write(f"**Child:** {b['child']} | **Parent:** {b['parent']} | **Time:** {b['time']} | **Status:** {status}")
            if status == 'Pending':
                if st.button(f"Confirm Booking {idx+1}", key=f"confirm_{selected_date}_{idx}"):
                    # Mark as Confirmed
                    for orig_b in bookings:
                        if orig_b == b:
                            orig_b['status'] = 'Confirmed'
                            break
                    save_data(bookings, BOOKINGS_FILE)
                    st.success("Booking confirmed.")
    else:
        st.write("No bookings for this date.")

# --- Booking request form when clicking a date ---
if st.session_state.get('selected_date'):
    booking_date = st.session_state['selected_date']
    st.subheader(f"Book Play Date on {booking_date}")
    with st.form("booking_form"):
        parent_name = st.text_input("Parent's Name")
        child_name = st.text_input("Child's Name")
        time_slot = st.time_input("Preferred Time")
        if st.form_submit_button("Confirm Booking"):
            # Add new booking with 'Pending' status
            bookings.append({
                "parent": parent_name,
                "child": child_name,
                "date": booking_date,
                "time": str(time_slot),
                "status": "Pending"
            })
            save_data(bookings, BOOKINGS_FILE)
            st.success("Play date booked! Await confirmation.")
            # Clear selected date
            st.session_state['selected_date'] = None
            st.session_state['view_bookings_for_date'] = None

