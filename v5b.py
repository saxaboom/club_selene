import streamlit as st
import json
from datetime import datetime
import calendar
import uuid  # For unique IDs

# Load secrets
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

# Load data
messages = load_data(CHAT_FILE)
bookings = load_data(BOOKINGS_FILE)

# --- Messaging ---
st.title("Welcome to Club-Selene!")
st.subheader("... a hub for messages and play-dates.  ; )")

# Message form
with st.form("chat_form", clear_on_submit=True):
    user_name = st.text_input("Your Name")
    message = st.text_area("Message")
    if st.form_submit_button("Send") and user_name and message:
        message_id = str(uuid.uuid4())
        messages.append({
            "id": message_id,
            "name": user_name,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        save_data(messages, CHAT_FILE)
        st.success("Message sent!")

# Display messages with delete option
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

    toggle_key = f"delete_toggle_{msg['id']}"
    if toggle_key not in st.session_state:
        st.session_state[toggle_key] = False
    if st.button("🗑️", key=f"toggle_delete_{msg['id']}"):
        st.session_state[toggle_key] = not st.session_state[toggle_key]
    if st.session_state[toggle_key]:
        entered_pin = st.text_input(
            f"Enter PIN to delete this message",
            key=f"pin_input_{msg['id']}",
            placeholder="PIN",
            label_visibility='collapsed',
            type='password'
        )
        if st.button("Confirm Delete", key=f"confirm_del_{msg['id']}"):
            if entered_pin == pin_code:
                try:
                    messages = [m for m in messages if m['id'] != msg['id']]
                    save_data(messages, CHAT_FILE)
                    st.success("Message deleted.")
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

# Define date status sets
blocked_dates = set()
pending_dates = set()
confirmed_dates = set()

# Populate date statuses
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
        return '🔴'
    elif date_str in pending_dates:
        return '🔵'
    elif date_str in confirmed_dates:
        return '🟢'
    else:
        return ''

# Calendar display
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
                st.session_state['selected_date'] = date_str
                st.session_state['view_bookings_for_date'] = date_str

# Show bookings for selected date
if st.session_state.get('view_bookings_for_date'):
    selected_date = st.session_state['view_bookings_for_date']
    date_bookings = [b for b in bookings if b['date'] == selected_date]
    st.subheader(f"Bookings for {selected_date}")
    if date_bookings:
        for idx, b in enumerate(date_bookings):
            status = b.get('status', 'Pending')
            st.write(f"**Child:** {b['child']} | **Parent:** {b['parent']} | **Time:** {b['time']} | **Status:** {status}")
            if status == 'Pending':
                if st.button(f"Confirm Booking {idx+1}", key=f"confirm_{selected_date}_{idx}"):
                    for orig_b in bookings:
                        if orig_b['id'] == b['id']:
                            orig_b['status'] = 'Confirmed'
                            break
                    save_data(bookings, BOOKINGS_FILE)
                    st.success("Booking confirmed.")
    else:
        st.write("No bookings for this date.")

# Booking form
if st.session_state.get('selected_date'):
    booking_date = st.session_state['selected_date']
    st.subheader(f"Book Play Date on {booking_date}")
    with st.form("booking_form"):
        parent_name = st.text_input("Parent's Name")
        child_name = st.text_input("Child's Name")
        time_slot = st.time_input("Preferred Time")
        if st.form_submit_button("Confirm Booking"):
            new_booking = {
                "id": str(uuid.uuid4()),
                "parent": parent_name,
                "child": child_name,
                "date": booking_date,
                "time": str(time_slot),
                "status": "Pending"
            }
            bookings.append(new_booking)
            save_data(bookings, BOOKINGS_FILE)
            st.success("Play date booked! Await confirmation.")
            st.session_state['selected_date'] = None
            st.session_state['view_bookings_for_date'] = None

