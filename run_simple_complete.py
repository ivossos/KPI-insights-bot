#!/usr/bin/env python3
"""
Simple Complete IA Fiscal Capivari App
Works without complex dependencies
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path

# Setup paths
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"

# For Replit, try workspace path
if not src_dir.exists():
    workspace_dir = Path("/home/runner/workspace")
    src_dir = workspace_dir / "src"

# Change to src directory
os.chdir(str(src_dir))
sys.path.insert(0, str(src_dir))
os.environ["PYTHONPATH"] = str(src_dir)

print("🚀 Starting IA Fiscal Capivari - Simple Complete System")
print(f"📁 Working directory: {os.getcwd()}")

class SimpleCompleteApp:
    """Simple complete application without complex dependencies"""
    
    def __init__(self):
        self.running = False
        self.processes = []
        
    def run(self):
        """Run the complete application"""
        print("✅ Starting services...")
        
        self.running = True
        
        # Create data directories
        self._create_directories()
        
        # Start API server
        api_thread = threading.Thread(target=self._start_api, daemon=True)
        api_thread.start()
        
        # Wait for API to start
        time.sleep(3)
        
        # Start dashboard
        dashboard_thread = threading.Thread(target=self._start_dashboard, daemon=True)
        dashboard_thread.start()
        
        print("🌐 API Server: http://localhost:8000")
        print("📊 Dashboard: http://localhost:8501")
        print("✅ All services running!")
        print("Press Ctrl+C to stop")
        
        # Keep alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            self.running = False
            
    def _create_directories(self):
        """Create necessary directories"""
        directories = ["data/raw", "data/processed", "data/alerts", "logs", "reports"]
        
        for directory in directories:
            dir_path = current_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
        print("📁 Directories created")
        
    def _start_api(self):
        """Start API server"""
        try:
            print("🔧 Starting API server...")
            
            # Try uvicorn command first
            api_file = src_dir / "api" / "main_simple.py"
            if not api_file.exists():
                api_file = src_dir / "api" / "main.py"
                
            cmd = [
                sys.executable, "-m", "uvicorn", 
                f"api.{api_file.stem}:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ]
            
            process = subprocess.Popen(cmd)
            self.processes.append(process)
            
        except Exception as e:
            print(f"❌ API error: {e}")
            
    def _start_dashboard(self):
        """Start dashboard"""
        try:
            print("🔧 Starting dashboard...")
            
            dashboard_file = src_dir / "dashboard" / "main.py"
            
            cmd = [
                sys.executable, "-m", "streamlit", "run", str(dashboard_file),
                "--server.port=8501",
                "--server.address=0.0.0.0",
                "--server.headless=true"
            ]
            
            process = subprocess.Popen(cmd)
            self.processes.append(process)
            
        except Exception as e:
            print(f"❌ Dashboard error: {e}")

def main():
    """Main entry point"""
    print("=" * 60)
    print("🏛️  IA FISCAL CAPIVARI - SIMPLE COMPLETE SYSTEM")
    print("    Municipal Spending Monitoring with AI")
    print("=" * 60)
    
    app = SimpleCompleteApp()
    app.run()

if __name__ == "__main__":
    main()