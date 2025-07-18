#!/usr/bin/env python3
"""
Quick Deploy Script for KPI Insight Bot
Simplified version for immediate deployment
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def setup_environment():
    """Setup basic environment"""
    print("🔧 Setting up environment...")
    
    # Create directories
    for directory in ["data", "logs", "reports", "chroma_db"]:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Set environment variables
    os.environ["PYTHONPATH"] = str(Path.cwd() / "src")
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    print("✅ Environment ready!")

def install_minimal_deps():
    """Install minimal dependencies"""
    print("📦 Installing minimal dependencies...")
    
    minimal_deps = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0", 
        "streamlit==1.28.1",
        "requests==2.31.0",
        "anthropic==0.3.11",
        "openai==1.3.5",
        "pydantic==2.5.0",
        "python-dotenv==1.0.0",
        "plotly==5.17.0"
    ]
    
    for dep in minimal_deps:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                          check=True, capture_output=True)
            print(f"  ✅ {dep}")
        except subprocess.CalledProcessError:
            print(f"  ⚠️ {dep} - skipping")

def create_minimal_api():
    """Create a minimal API for testing"""
    api_code = '''
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
from datetime import datetime

app = FastAPI(title="KPI Insight Bot API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "KPI Insight Bot API", "status": "running", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/v1/kpi/test")
async def test_kpi():
    return {
        "kpi_id": "test_revenue",
        "name": "Test Revenue",
        "value": 1000000,
        "unit": "currency",
        "currency": "USD",
        "message": "KPI Insight Bot is working!"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
    
    with open("minimal_api.py", "w") as f:
        f.write(api_code)
    
    print("✅ Minimal API created!")

def create_minimal_dashboard():
    """Create a minimal dashboard for testing"""
    dashboard_code = '''
import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(
    page_title="KPI Insight Bot",
    page_icon="📊",
    layout="wide"
)

st.title("📊 KPI Insight Bot - Quick Deploy")
st.markdown("---")

# Test API connection
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        st.success("✅ API is running!")
        health_data = response.json()
        st.json(health_data)
    else:
        st.error("❌ API not responding")
except:
    st.error("❌ Cannot connect to API")

# Test KPI endpoint
st.subheader("🧪 Test KPI")
if st.button("Test KPI Query"):
    try:
        response = requests.get("http://localhost:8000/api/v1/kpi/test", timeout=5)
        if response.status_code == 200:
            kpi_data = response.json()
            st.success("✅ KPI endpoint working!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("KPI Name", kpi_data["name"])
            with col2:
                st.metric("Value", f"${kpi_data['value']:,}")
            with col3:
                st.metric("Currency", kpi_data["currency"])
                
            st.json(kpi_data)
        else:
            st.error("❌ KPI endpoint not working")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Environment info
st.subheader("🔧 Environment")
st.write(f"Timestamp: {datetime.now()}")
st.write(f"Status: Deployment successful!")

# Next steps
st.subheader("🚀 Next Steps")
st.markdown("""
1. **API is running** at http://localhost:8000
2. **Dashboard is running** at http://localhost:8502
3. **Ready for full deployment** with complete features
4. **Add Oracle EPM connections** for real data
5. **Configure LLM keys** for natural language queries
""")
'''
    
    with open("minimal_dashboard.py", "w") as f:
        f.write(dashboard_code)
    
    print("✅ Minimal dashboard created!")

def start_services():
    """Start API and dashboard services"""
    print("🚀 Starting services...")
    
    # Start API in background
    import threading
    
    def run_api():
        subprocess.run([sys.executable, "minimal_api.py"])
    
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # Wait for API to start
    time.sleep(3)
    
    # Start dashboard
    print("🎨 Starting dashboard...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "minimal_dashboard.py",
        "--server.port=8502",
        "--server.address=0.0.0.0"
    ])

def main():
    """Main deployment function"""
    print("🚀 KPI INSIGHT BOT - QUICK DEPLOY")
    print("=" * 40)
    
    setup_environment()
    install_minimal_deps()
    create_minimal_api()
    create_minimal_dashboard()
    start_services()

if __name__ == "__main__":
    main()