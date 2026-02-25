import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('ultrasound_tracker.db')
    c = conn.cursor()
    # Create table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS movements 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  device_name TEXT,
                  location TEXT, 
                  user_identity TEXT, 
                  timestamp DATETIME)''')
    
    # --- SAFETY MIGRATION ---
    c.execute("PRAGMA table_info(movements)")
    columns = [column[1] for column in c.fetchall()]
    if 'device_name' not in columns:
        c.execute("ALTER TABLE movements ADD COLUMN device_name TEXT DEFAULT 'Black Ultrasound'")
    
    conn.commit()
    conn.close()

def add_entry(device, location, user):
    conn = sqlite3.connect('ultrasound_tracker.db')
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO movements (device_name, location, user_identity, timestamp) VALUES (?, ?, ?, ?)", 
              (device, location, user, now))
    conn.commit()
    conn.close()

def get_latest_status(device):
    conn = sqlite3.connect('ultrasound_tracker.db')
    query = "SELECT location, user_identity, timestamp FROM movements WHERE device_name = ? ORDER BY id DESC LIMIT 1"
    try:
        df = pd.read_sql_query(query, conn, params=(device,))
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def get_full_history():
    conn = sqlite3.connect('ultrasound_tracker.db')
    try:
        df = pd.read_sql_query("SELECT device_name, timestamp, location, user_identity FROM movements ORDER BY id DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# Initialize DB on startup
init_db()

# --- STREAMLIT UI ---
st.set_page_config(page_title="AMU Ultrasound Tracker", page_icon="🩺", layout="wide")

# --- HIDE STREAMLIT MENU & FOOTER ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            stDecoration {display:none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Header
st.title("🩺 AMU Ultrasound Locator")
st.markdown("Track the **Black** and **White** ultrasound units across the hospital.")
st.markdown("---")

# 1. CURRENT STATUS SECTION (Side-by-Side)
col_black, col_white = st.columns(2)

# --- BLACK ULTRASOUND STATUS ---
with col_black:
    st.subheader("⬛ Black Ultrasound")
    status_black = get_latest_status("Black Ultrasound")
    if not status_black.empty:
        curr = status_black.iloc[0]
        st.metric("Current Location", curr['location'])
        time_display = curr['timestamp'].split()[1][:5] if " " in curr['timestamp'] else curr['timestamp']
        st.caption(f"Last moved: {time_display} by {curr['user_identity']}")
    else:
        st.info("No data for Black Ultrasound")

# --- WHITE ULTRASOUND STATUS ---
with col_white:
    st.subheader("⬜ White Ultrasound")
    status_white = get_latest_status("White Ultrasound")
    if not status_white.empty:
        curr = status_white.iloc[0]
        st.metric("Current Location", curr['location'])
        time_display = curr['timestamp'].split()[1][:5] if " " in curr['timestamp'] else curr['timestamp']
        st.caption(f"Last moved: {time_display} by {curr['user_identity']}")
    else:
        st.info("No data for White Ultrasound")

st.markdown("---")

# 2. UPDATE LOCATION FORM
st.subheader("📍 Update Device Location")
with st.form("location_form", clear_on_submit=True):
    # Radio buttons to choose which machine is being moved
    device_to_move = st.radio("Which device are you moving?", ["Black Ultrasound", "White Ultrasound"], horizontal=True)
    
    new_loc = st.text_input("Destination (e.g., Coleridge, RSU, Side Room 2)")
    staff_name = st.text_input("Your Name / Bleep (Required for Check-Out)")
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        submit = st.form_submit_button("Check-Out to New Location")
    with f_col2:
        return_to_base = st.form_submit_button("Return to AMU")

    if submit:
        # Check-out requires details
        if new_loc and staff_name:
            add_entry(device_to_move, new_loc, staff_name)
            st.success(f"{device_to_move} updated to {new_loc}")
            st.rerun()
        else:
            st.error("Please provide both a Destination and your Name/Bleep for Check-Out.")

    if return_to_base:
        # Destination is now set to AMU Doctor's Office as requested
        caller = staff_name if staff_name else "System (Return)"
        add_entry(device_to_move, "AMU Doctor's Office", caller)
        st.success(f"{device_to_move} returned to Doctor's Office!")
        st.rerun()

# 3. AUDIT TRAIL (Combined History)
st.markdown("---")
st.subheader("📜 Movement History (Audit Trail)")
history_df = get_full_history()
if not history_df.empty:
    st.dataframe(history_df, use_container_width=True, hide_index=True)
else:
    st.write("No history available.")
