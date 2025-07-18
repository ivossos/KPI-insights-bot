#!/usr/bin/env python3
"""
Replit Deployment Script for KPI Insight Bot
Simplified deployment for Replit environment
"""

import os
import subprocess
import sys
import time
import threading
from pathlib import Path

def setup_replit_environment():
    """Setup Replit environment"""
    print("🔧 Setting up Replit environment...")
    
    # Create necessary directories
    directories = [
        "data/raw",
        "data/processed", 
        "data/alerts",
        "logs",
        "reports",
        "chroma_db"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Set environment variables for Replit
    os.environ["PYTHONPATH"] = "/home/runner/ia-fiscal-capivari/src"
    os.environ["ENVIRONMENT"] = "replit"
    
    print("✅ Environment setup complete!")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting API server...")
    
    try:
        # Import and run the API
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        import uvicorn
        from src.api.main import app
        
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
        
        server = uvicorn.Server(config)
        server.run()
        
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        sys.exit(1)

def start_dashboard():
    """Start the Streamlit dashboard"""
    print("🎨 Starting dashboard...")
    
    try:
        dashboard_path = Path(__file__).parent / "src" / "kpi_bot" / "dashboard" / "kpi_dashboard.py"
        
        cmd = [
            "streamlit", "run", str(dashboard_path),
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--server.runOnSave=false",
            "--theme.base=dark",
            "--theme.primaryColor=#ffd700",
            "--theme.backgroundColor=#1a1a1a",
            "--theme.secondaryBackgroundColor=#2d2d2d",
            "--theme.textColor=#ffffff"
        ]
        
        subprocess.run(cmd, check=True)
        
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        sys.exit(1)

def run_replit_deployment():
    """Run the complete deployment for Replit"""
    print("🚀 Starting KPI Insight Bot deployment for Replit...")
    
    # Setup environment
    setup_replit_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Start API server in background thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Give API time to start
    time.sleep(5)
    
    # Start dashboard (this will block)
    start_dashboard()

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "api":
            setup_replit_environment()
            install_dependencies()
            start_api_server()
        elif sys.argv[1] == "dashboard":
            setup_replit_environment()
            start_dashboard()
        else:
            print("Usage: python deploy_replit.py [api|dashboard]")
            sys.exit(1)
    else:
        run_replit_deployment()

if __name__ == "__main__":
    main()