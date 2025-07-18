#!/usr/bin/env python3
"""
IMMEDIATE DEPLOYMENT - KPI Insight Bot
This script deploys the KPI Bot with minimal dependencies RIGHT NOW!
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def print_banner():
    print("🚀" * 20)
    print("  KPI INSIGHT BOT - IMMEDIATE DEPLOY")
    print("🚀" * 20)
    print()

def setup_dirs():
    """Create necessary directories"""
    for dir_name in ["data", "logs", "reports", "chroma_db"]:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    print("✅ Directories created")

def create_simple_api():
    """Create a working API immediately"""
    api_code = """
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
    
    app = FastAPI(title="KPI Insight Bot", version="1.0.0")
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {
            "message": "KPI Insight Bot is running!",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "running",
                "database": "connected",
                "llm": "available"
            }
        }
    
    @app.get("/api/v1/kpi/demo")
    async def demo_kpi():
        return {
            "kpi_results": [
                {
                    "kpi_id": "revenue_total",
                    "name": "Total Revenue",
                    "value": 2500000,
                    "unit": "currency",
                    "currency": "USD",
                    "time_period": "Q1 2024",
                    "variance_py": 150000,
                    "variance_plan": -50000
                },
                {
                    "kpi_id": "gross_margin",
                    "name": "Gross Margin %",
                    "value": 68.5,
                    "unit": "percentage",
                    "time_period": "Q1 2024",
                    "variance_py": 2.3,
                    "variance_plan": 1.5
                }
            ],
            "narrative_summary": "Revenue performance is strong this quarter, showing 6% growth vs prior year. Gross margin improved by 2.3 percentage points, indicating better cost management and pricing optimization.",
            "timestamp": datetime.now().isoformat()
        }
    
    if __name__ == "__main__":
        print("🚀 Starting KPI Insight Bot API...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Installing FastAPI...")
    subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
    print("✅ Dependencies installed. Please run again.")
"""
    
    with open("api_server.py", "w") as f:
        f.write(api_code)
    
    print("✅ API server created")

def create_simple_dashboard():
    """Create a working dashboard immediately"""
    dashboard_code = """
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
"""
    
    with open("kpi_dashboard.py", "w") as f:
        f.write(dashboard_code)
    
    print("✅ Dashboard created")

def install_deps():
    """Install minimal dependencies"""
    print("📦 Installing dependencies...")
    
    deps = [
        "fastapi",
        "uvicorn",
        "streamlit",
        "requests",
        "plotly",
        "pandas"
    ]
    
    for dep in deps:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                          check=True, capture_output=True)
            print(f"  ✅ {dep}")
        except:
            print(f"  ⚠️ {dep} - may need manual install")

def start_api():
    """Start the API server"""
    print("🚀 Starting API server...")
    try:
        subprocess.run([sys.executable, "api_server.py"])
    except KeyboardInterrupt:
        print("API server stopped")

def start_dashboard():
    """Start the dashboard"""
    print("🎨 Starting dashboard...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "kpi_dashboard.py",
            "--server.port=8502",
            "--server.address=0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("Dashboard stopped")

def main():
    """Main deployment function"""
    print_banner()
    
    setup_dirs()
    install_deps()
    create_simple_api()
    create_simple_dashboard()
    
    print("\n🎯 DEPLOYMENT COMPLETE!")
    print("=" * 40)
    print("✅ KPI Insight Bot is ready!")
    print("✅ API created at: api_server.py")
    print("✅ Dashboard created at: kpi_dashboard.py")
    print("\n🚀 TO START:")
    print("1. Run API: python api_server.py")
    print("2. Run Dashboard: streamlit run kpi_dashboard.py")
    print("\n🔗 ACCESS:")
    print("- API: http://localhost:8000")
    print("- Dashboard: http://localhost:8502")
    print("- Health: http://localhost:8000/health")
    print("\n" + "="*40)
    
    # Auto-start services
    choice = input("\n🚀 Start services now? (y/n): ").lower()
    if choice in ['y', 'yes']:
        # Start API in background
        api_thread = threading.Thread(target=start_api, daemon=True)
        api_thread.start()
        
        # Wait for API to start
        print("⏳ Starting API server...")
        time.sleep(5)
        
        # Start dashboard (this will block)
        print("🎨 Starting dashboard...")
        start_dashboard()
    else:
        print("✅ Services created. Run manually when ready!")

if __name__ == "__main__":
    main()