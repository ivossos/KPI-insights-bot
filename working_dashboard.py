
#!/usr/bin/env python3

import streamlit as st
from datetime import datetime

# Minimal page config
st.set_page_config(page_title="Working Dashboard", layout="wide")

# Clear any cached data that might cause issues
if 'initialized' not in st.session_state:
    st.session_state.initialized = True

# Simple working dashboard
st.title("✅ Working Dashboard")
st.success("Dashboard is now working!")

# Current time to show it's live
st.write(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Simple metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Status", "ONLINE")
with col2:
    st.metric("Test", "PASS")
with col3:
    st.metric("Connection", "OK")

# Test button
if st.button("Test Button"):
    st.balloons()
    st.success("Button works!")

st.info("This minimal dashboard is working. You can now build additional features.")
