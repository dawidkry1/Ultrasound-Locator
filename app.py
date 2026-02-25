import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('ultrasound_tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS movements 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  location TEXT, 
                  user_identity TEXT, 
                  timestamp DATETIME)''')
    conn.commit()
    conn.close()

def add_entry(location, user):
    conn = sqlite3.connect('ultrasound_tracker.db')
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO movements (location, user_identity, timestamp) VALUES (?, ?, ?)", 
              (location, user, now))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect('ultrasound_tracker.db')
    df = pd.read_sql_query("SELECT timestamp, location, user_identity FROM movements ORDER BY id DESC", conn)
    conn.close()
    return df

# Initialize DB on startup
init_db()

# --- STREAMLIT UI ---
st.set_page_config(page_title="AMU Ultrasound Tracker", page_icon="🩺")

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
st.markdown("---")

# 1. Current Status Section
history_df = get_history()

if not history_df.empty:
    current = history_df.iloc[0]
    st.subheader("Current Status")
    col1, col2 = st.columns(2)
    col1.metric("Current Location", current['location'])
    col2.metric("Last Seen", current['timestamp'].split()[1][:5]) # Shows just HH:MM
    st.caption(f"Logged by: {current['user_identity']}")
else:
    st.info("No data logged yet. Please check in the device.")

st.markdown("---")

# 2. Update Location Form
st.subheader("📍 Update Location")
with st.form("location_form", clear_on_submit=True):
    new_loc = st.text_input("Destination (e.g., Coleridge, RSU, Side Room 2)")
    staff_name = st.text_input("Your Name / Bleep")
    
    # Primary action first: Check-Out
    submit = st.form_submit_button("Check-Out to New Location")
    # Secondary action second: Return to Base
    return_to_base = st.form_submit_button("Return to AMU Reception")

    if submit:
        if new_loc and staff_name:
            add_entry(new_loc, staff_name)
            st.success(f"Location updated to {new_loc}")
            st.rerun()
        else:
            st.error("Please fill in both fields.")

    if return_to_base:
        add_entry("AMU Reception (Base)", staff_name if staff_name else "System/Return")
        st.success("Device returned to base!")
        st.rerun()

# 3. Audit Trail (History)
st.markdown("---")
st.subheader("📜 Movement History (Audit Trail)")
if not history_df.empty:
    st.dataframe(history_df, use_container_width=True, hide_index=True)
else:
    st.write("No history available.")
