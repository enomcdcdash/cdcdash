import streamlit as st
from sidebar import show_sidebar
from my_pages import availability, tracker_bbm, dapot

# Set page config
st.set_page_config(page_title="Dashboard CDC", layout="wide")

# Title
st.title("📊 Dashboard CDC")

# Show sidebar and get selected page
selected_page = show_sidebar()

# Load selected page
if selected_page == "📅 CDC Availability":
    availability.show()
elif selected_page == "⛽ Tracker Pengisian BBM":
    tracker_bbm.show()
elif selected_page == "🏗️ Dapot Asset CDC":
    dapot.show()