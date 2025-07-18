#!/usr/bin/env python3
"""
IA Fiscal Capivari - Replit Deployment Entry Point
Municipal spending monitoring and alerting system
"""

import os
import sys
import asyncio
import threading
import time
import signal
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

# Set environment variables for Replit
os.environ["PYTHONPATH"] = src_path
os.environ["PYTHONUNBUFFERED"] = "1"

# Change working directory to src for relative imports
os.chdir(src_path)

# Import after setting path
from monitoring.logger import logger
from config import settings

class ReplitDeployment:
    """Replit-optimized deployment"""
    
    def __init__(self):
        self.logger = logger
        self.api_process = None
        self.dashboard_process = None
        self.running = False
        
    def run(self):
        """Run the application optimized for Replit"""
        self.logger.info("Starting IA Fiscal Capivari on Replit")
        
        try:
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Check if running in Replit
            if self._is_replit():
                self.logger.info("Detected Replit environment")
                self._setup_replit_environment()
            
            # Start services
            self._start_services()
            
            # Keep main thread alive
            self._keep_alive()
            
        except Exception as e:
            self.logger.error(f"Failed to start application: {str(e)}")
            sys.exit(1)
            
    def _is_replit(self) -> bool:
        """Check if running in Replit environment"""
        return "REPL_SLUG" in os.environ or "REPLIT_DB_URL" in os.environ
        
    def _setup_replit_environment(self):
        """Setup Replit-specific environment"""
        # Create required directories
        directories = ["data/raw", "data/processed", "data/alerts", "logs", "reports"]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
        # Set Replit-specific settings
        os.environ["REPLIT_ENV"] = "true"
        
        # Get Replit URL
        repl_slug = os.environ.get("REPL_SLUG", "ia-fiscal-capivari")
        repl_owner = os.environ.get("REPL_OWNER", "user")
        
        # Set redirect URI for OAuth
        if "GOOGLE_REDIRECT_URI" not in os.environ:
            os.environ["GOOGLE_REDIRECT_URI"] = f"https://{repl_slug}.{repl_owner}.repl.co/auth/callback"
            
        self.logger.info(f"Replit environment configured for {repl_slug}")
        
    def _start_services(self):
        """Start API and dashboard services"""
        self.running = True
        
        # Start API server in background thread
        api_thread = threading.Thread(target=self._start_api, daemon=True)
        api_thread.start()
        
        # Give API time to start
        time.sleep(3)
        
        # Start dashboard in background thread
        dashboard_thread = threading.Thread(target=self._start_dashboard, daemon=True)
        dashboard_thread.start()
        
        # Start scheduler
        scheduler_thread = threading.Thread(target=self._start_scheduler, daemon=True)
        scheduler_thread.start()
        
        self.logger.info("All services started successfully")
        
    def _start_api(self):
        """Start FastAPI server"""
        try:
            import uvicorn
            from api.main import app
            
            self.logger.info("Starting FastAPI server on port 8000")
            
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
            self.logger.error(f"Failed to start API server: {str(e)}")
            
    def _start_dashboard(self):
        """Start Streamlit dashboard"""
        try:
            import subprocess
            
            self.logger.info("Starting Streamlit dashboard on port 8501")
            
            dashboard_path = Path(__file__).parent / "kpi_bot" / "dashboard" / "kpi_dashboard.py"
            
            cmd = [
                sys.executable, "-m", "streamlit", "run", str(dashboard_path),
                "--server.port=8501",
                "--server.address=0.0.0.0",
                "--server.headless=true",
                "--server.enableCORS=false",
                "--server.enableXsrfProtection=false"
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.dashboard_process = process
            
        except Exception as e:
            self.logger.error(f"Failed to start dashboard: {str(e)}")
            
    def _start_scheduler(self):
        """Start background scheduler"""
        try:
            import schedule
            from notifications.notification_manager import NotificationManager
            
            self.logger.info("Starting background scheduler")
            
            notification_manager = NotificationManager()
            
            while self.running:
                schedule.run_pending()
                time.sleep(60)
                
        except Exception as e:
            self.logger.error(f"Scheduler error: {str(e)}")
            
    def _keep_alive(self):
        """Keep the main thread alive"""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
            self.running = False
            
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down")
        self.running = False
        
        if self.dashboard_process:
            self.dashboard_process.terminate()
            
        sys.exit(0)

def check_environment():
    """Check if environment is properly configured"""
    logger.info("Checking environment configuration...")
    
    required_vars = [
        "APIFY_API_TOKEN",
        "CLAUDE_API_KEY",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "ADMIN_EMAIL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
            
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Please configure these in Replit Secrets")
        
    # Check optional variables
    optional_vars = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID"
    ]
    
    for var in optional_vars:
        if not os.environ.get(var):
            logger.info(f"Optional variable {var} not set - feature will be disabled")
            
    logger.info("Environment check completed")

def main():
    """Main entry point for Replit deployment"""
    # Check environment
    check_environment()
    
    # Create and run deployment
    deployment = ReplitDeployment()
    deployment.run()

if __name__ == "__main__":
    main()