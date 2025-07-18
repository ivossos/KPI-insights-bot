#!/usr/bin/env python3
"""
Complete IA Fiscal Capivari App for Replit
Runs both API and Dashboard together
"""

import os
import sys
import subprocess
import threading
import time
import signal
from pathlib import Path
import asyncio
import uvicorn

# Setup paths - work in both local and Replit environments
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"

# For Replit, try the workspace path
if not src_dir.exists():
    workspace_dir = Path("/home/runner/workspace")
    src_dir = workspace_dir / "src"

# Fix Python paths
os.chdir(str(src_dir))
sys.path.insert(0, str(src_dir))
os.environ["PYTHONPATH"] = str(src_dir)
os.environ["PYTHONUNBUFFERED"] = "1"

print("🚀 Starting IA Fiscal Capivari - Complete System")
print(f"📁 Working directory: {os.getcwd()}")
print(f"🐍 Python path: {sys.path[0]}")

# Import after path setup
try:
    from monitoring.logger import logger
    from config import settings
    logger.info("✅ Imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    print("Creating minimal config...")
    
    # Create minimal config if imports fail
    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
    
    logger = MockLogger()

class CompleteApp:
    """Complete IA Fiscal Capivari Application"""
    
    def __init__(self):
        self.running = False
        self.api_thread = None
        self.dashboard_process = None
        
    def run(self):
        """Run complete application"""
        logger.info("🚀 Starting complete IA Fiscal Capivari system")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.running = True
        
        # Create required directories
        self._create_directories()
        
        # Start API server in background
        self.api_thread = threading.Thread(target=self._start_api, daemon=True)
        self.api_thread.start()
        
        # Give API time to start
        time.sleep(3)
        
        # Start dashboard in background
        dashboard_thread = threading.Thread(target=self._start_dashboard, daemon=True)
        dashboard_thread.start()
        
        # Start scheduler
        scheduler_thread = threading.Thread(target=self._start_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("✅ All services started!")
        logger.info("🌐 API: https://workspace.your-username.repl.co")
        logger.info("📊 Dashboard: https://workspace.your-username.repl.co:3000")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("👋 Shutting down...")
            self.running = False
            
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            "data/raw",
            "data/processed", 
            "data/alerts",
            "logs",
            "reports"
        ]
        
        for directory in directories:
            dir_path = current_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
        logger.info("📁 Directories created")
        
    def _start_api(self):
        """Start FastAPI server"""
        try:
            logger.info("🔧 Starting API server on port 8000...")
            
            # Try to import full API app first
            try:
                from api.main import app
                logger.info("✅ Using full API")
            except Exception as import_error:
                logger.warning(f"⚠️ Full API import failed: {import_error}")
                logger.info("🔄 Falling back to simplified API...")
                from api.main_simple import app
            
            # Configure uvicorn
            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=8000,
                log_level="info",
                access_log=True
            )
            
            server = uvicorn.Server(config)
            asyncio.run(server.serve())
            
        except Exception as e:
            logger.error(f"❌ API server error: {e}")
            
    def _start_dashboard(self):
        """Start Streamlit dashboard"""
        try:
            logger.info("🔧 Starting dashboard on port 8501...")
            
            dashboard_path = src_dir / "dashboard" / "main.py"
            
            cmd = [
                sys.executable, "-m", "streamlit", "run", str(dashboard_path),
                "--server.port=8501",
                "--server.address=0.0.0.0",
                "--server.headless=true",
                "--server.enableCORS=false",
                "--server.enableXsrfProtection=false"
            ]
            
            self.dashboard_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            logger.info("✅ Dashboard started")
            
        except Exception as e:
            logger.error(f"❌ Dashboard error: {e}")
            
    def _start_scheduler(self):
        """Start background scheduler"""
        try:
            logger.info("🔧 Starting scheduler...")
            
            import schedule
            
            # Simple scheduler without complex imports
            def dummy_job():
                logger.info("⏰ Scheduler heartbeat")
                
            schedule.every(5).minutes.do(dummy_job)
            
            while self.running:
                schedule.run_pending()
                time.sleep(60)
                
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}")
        self.running = False
        
        if self.dashboard_process:
            self.dashboard_process.terminate()
            
        sys.exit(0)

def check_environment():
    """Check environment setup"""
    logger.info("🔍 Checking environment...")
    
    # Check required directories
    required_dirs = ["data", "logs", "src"]
    for dir_name in required_dirs:
        dir_path = current_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Created {dir_name}")
    
    # Check Python packages
    required_packages = ["fastapi", "streamlit", "uvicorn"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning(f"⚠️ Missing packages: {missing_packages}")
        logger.info("📦 Installing missing packages...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "fastapi", "streamlit", "uvicorn[standard]", "python-multipart"
            ])
            logger.info("✅ Packages installed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Package installation failed: {e}")
            return False
    
    return True

def main():
    """Main entry point"""
    print("=" * 60)
    print("🏛️  IA FISCAL CAPIVARI - COMPLETE SYSTEM")
    print("    Municipal Spending Monitoring with AI")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed")
        return False
    
    # Create and run app
    app = CompleteApp()
    app.run()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)