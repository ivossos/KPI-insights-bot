#!/usr/bin/env python3
"""
Minimal Complete IA Fiscal Capivari App
Uses only basic Python libraries - works everywhere
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path

def main():
    """Main entry point"""
    print("=" * 60)
    print("🏛️  IA FISCAL CAPIVARI - MINIMAL COMPLETE SYSTEM")
    print("    Municipal Spending Monitoring with AI")
    print("=" * 60)
    
    current_dir = Path(__file__).parent.absolute()
    
    print(f"📁 Working directory: {current_dir}")
    print("🚀 Starting services...")
    
    # Create data directories
    directories = ["data/raw", "data/processed", "data/alerts", "logs", "reports"]
    for directory in directories:
        dir_path = current_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
    print("📁 Directories created")
    
    # Start API server in background
    api_thread = threading.Thread(target=start_api, args=(current_dir,), daemon=True)
    api_thread.start()
    
    # Wait for API to start
    time.sleep(2)
    
    # Start dashboard in background
    dashboard_thread = threading.Thread(target=start_dashboard, args=(current_dir,), daemon=True)
    dashboard_thread.start()
    
    # Wait for dashboard to start
    time.sleep(3)
    
    print("\n✅ All services started!")
    print("🌐 API Server: http://localhost:8000")
    print("📊 Dashboard: http://localhost:8501")
    print("\n📋 Available API endpoints:")
    print("   GET  /         - API info")
    print("   GET  /health   - Health check")
    print("   GET  /info     - System info")
    print("   GET  /alerts   - Get alerts")
    print("   POST /webhook/ingestion - Data webhook")
    print("\nPress Ctrl+C to stop all services")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down all services...")

def start_api(base_dir):
    """Start the simple API server"""
    try:
        print("🔧 Starting API server on port 8000...")
        
        api_file = base_dir / "simple_api.py"
        subprocess.run([sys.executable, str(api_file)])
        
    except Exception as e:
        print(f"❌ API server error: {e}")

def start_dashboard(base_dir):
    """Start the simple dashboard"""
    try:
        print("🔧 Starting dashboard on port 8501...")
        
        dashboard_file = base_dir / "simple_dashboard.py"
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", str(dashboard_file),
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false"
        ]
        
        subprocess.run(cmd)
        
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

if __name__ == "__main__":
    main()