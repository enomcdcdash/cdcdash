import streamlit as st

def show_sidebar():
    with st.sidebar:
        # Sidebar header
        st.markdown("""
            <div style='text-align: center; font-size: 26px; font-weight: bold; margin-bottom: 10px;'>
                📊 CDC Project Dashboard
            </div>
        """, unsafe_allow_html=True)

        # Separator line
        st.markdown("<hr style='margin-top: 0; margin-bottom: 10px;'>", unsafe_allow_html=True)

        # Navigation section title
        # st.markdown("### 🧭 Navigation")

        # Persistent page selection
        if "page" not in st.session_state:
            st.session_state.page = "⛽ Tracker Pengisian BBM"

        # Navigation buttons
        if st.button("⛽ Tracker Pengisian BBM", use_container_width=True):
            st.session_state.page = "⛽ Tracker Pengisian BBM"

        if st.button("📅 CDC Availability", use_container_width=True):
            st.session_state.page = "📅 CDC Availability"

        if st.button("🏗️ Dapot Asset CDC", use_container_width=True):
            st.session_state.page = "🏗️ Dapot Asset CDC"

    return st.session_state.page
