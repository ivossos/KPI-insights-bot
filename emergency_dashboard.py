
#!/usr/bin/env python3
"""
Emergency Dashboard - Minimal working version
"""

import streamlit as st
import time
from datetime import datetime

# Basic page config
st.set_page_config(
    page_title="IA Fiscal Emergency",
    page_icon="🚨",
    layout="wide"
)

# Force clear any cached states
st.cache_data.clear()
st.cache_resource.clear()

# Simple header
st.title("🚨 IA Fiscal Capivari - Emergency Dashboard")
st.success("✅ Dashboard is working!")

# Current time
st.write(f"**Current Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Simple metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Status", "ONLINE", "Emergency Mode")

with col2:
    st.metric("Alerts", "12", "+3")

with col3:
    st.metric("System", "OK", "Running")

# Simple content
st.subheader("📊 Basic Info")
st.write("This is an emergency working dashboard.")

# Test button
if st.button("🔄 Refresh"):
    st.balloons()
    st.success("Refresh successful!")

# Footer
st.markdown("---")
st.info("Emergency dashboard is working. You can now build from here.")
