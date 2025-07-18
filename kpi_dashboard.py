
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

# Page config
st.set_page_config(
    page_title="KPI Insight Bot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown('''
<style>
    .main {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    .stButton > button {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #ffd700;
    }
    .stButton > button:hover {
        background-color: #ffd700;
        color: #000000;
    }
    .metric-card {
        background-color: #2d2d2d;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ffd700;
        margin: 10px 0;
    }
</style>
''', unsafe_allow_html=True)

# Title
st.title("📊 KPI Insight Bot")
st.markdown("**Conversational Analytics for Finance Teams**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("🎛️ Controls")
    st.info("Demo Mode - Full features available after deployment")
    
    # Test API connection
    st.subheader("🔗 API Status")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Not Connected")
    except:
        st.warning("⚠️ API Starting...")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Natural Language Query")
    
    # Demo queries
    demo_queries = [
        "What's our revenue this quarter?",
        "Show me gross margin performance",
        "How are we doing vs plan?",
        "What's the cash position?"
    ]
    
    query = st.selectbox("Try a demo query:", demo_queries)
    
    if st.button("Ask KPI Bot", type="primary"):
        with st.spinner("Processing your query..."):
            try:
                response = requests.get("http://localhost:8000/api/v1/kpi/demo", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Show narrative
                    st.subheader("📝 Analysis")
                    st.write(data["narrative_summary"])
                    
                    # Show KPIs
                    st.subheader("📊 KPI Results")
                    
                    for kpi in data["kpi_results"]:
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.metric(
                                kpi["name"],
                                f"{kpi['value']:,.0f}" if kpi["unit"] == "currency" else f"{kpi['value']:.1f}%",
                                delta=kpi.get("variance_py", 0)
                            )
                        
                        with col_b:
                            st.metric(
                                "vs Plan",
                                f"{kpi.get('variance_plan', 0):+,.0f}" if kpi["unit"] == "currency" else f"{kpi.get('variance_plan', 0):+.1f}%"
                            )
                        
                        with col_c:
                            st.metric(
                                "Period",
                                kpi["time_period"]
                            )
                    
                    # Demo chart
                    st.subheader("📈 Visualization")
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=["Revenue", "Gross Margin"],
                        y=[2500000, 68.5],
                        marker_color=['#ffd700', '#00cc88']
                    ))
                    fig.update_layout(
                        title="KPI Performance",
                        paper_bgcolor='#2d2d2d',
                        plot_bgcolor='#1a1a1a',
                        font=dict(color='white')
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.error("❌ Failed to fetch KPI data")
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.info("Make sure the API server is running!")

with col2:
    st.header("📈 KPI Overview")
    
    # Demo metrics
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Total Revenue", "$2.5M", "6%")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Gross Margin", "68.5%", "2.3%")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Cash Position", "$850K", "-5%")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Status
    st.subheader("🚦 System Status")
    st.success("✅ KPI Bot Deployed")
    st.info("🔄 Demo Mode Active")
    st.warning("⚙️ Configure Oracle EPM for live data")

# Footer
st.markdown("---")
st.markdown("**KPI Insight Bot** - Deployed successfully! 🎉")
st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
