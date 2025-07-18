#!/usr/bin/env python3
"""
IA Fiscal Capivari - Main Application Entry Point
Municipal spending monitoring and alerting system
"""

import asyncio
import uvicorn
import streamlit
import schedule
import time
import threading
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.main import app as fastapi_app
from src.config import settings, config
from src.monitoring.logger import logger, performance_monitor
from src.monitoring.metrics import metrics_collector, app_metrics, health_checker
from src.notifications.notification_manager import NotificationManager
from src.ingestion.data_processor import DataProcessor
from src.rules.engine import BusinessRulesEngine
from src.ai.claude_explainer import ClaudeExplainer

class IAFiscalCapivariApp:
    """Main application coordinator"""
    
    def __init__(self):
        self.logger = logger
        self.notification_manager = NotificationManager()
        self.data_processor = DataProcessor()
        self.rules_engine = BusinessRulesEngine()
        self.ai_explainer = ClaudeExplainer()
        self.running = False
        
    def run(self):
        """Run the complete application"""
        self.logger.info("Starting IA Fiscal Capivari application")
        
        try:
            # Start background services
            self._start_background_services()
            
            # Start API server
            self._start_api_server()
            
        except Exception as e:
            self.logger.error(f"Failed to start application: {str(e)}")
            sys.exit(1)
            
    def _start_background_services(self):
        """Start background services"""
        self.logger.info("Starting background services")
        
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Start health monitoring
        health_thread = threading.Thread(target=self._run_health_monitor, daemon=True)
        health_thread.start()
        
        self.running = True
        
    def _run_scheduler(self):
        """Run the job scheduler"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Scheduler error: {str(e)}")
                time.sleep(60)
                
    def _run_health_monitor(self):
        """Run health monitoring"""
        while self.running:
            try:
                health_results = health_checker.run_health_checks()
                
                if health_results["overall_status"] == "critical":
                    self.logger.critical("System health critical", **health_results)
                elif health_results["overall_status"] == "degraded":
                    self.logger.warning("System health degraded", **health_results)
                    
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Health monitor error: {str(e)}")
                time.sleep(300)
                
    def _start_api_server(self):
        """Start the FastAPI server"""
        self.logger.info("Starting FastAPI server")
        
        # Configure uvicorn
        config = uvicorn.Config(
            app=fastapi_app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        server.run()
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully")
        self.running = False
        sys.exit(0)

def run_streamlit_dashboard():
    """Run the Streamlit dashboard"""
    import subprocess
    
    dashboard_path = Path(__file__).parent / "src" / "dashboard" / "main.py"
    
    cmd = [
        "streamlit", "run", str(dashboard_path),
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ]
    
    subprocess.run(cmd)

def run_api_only():
    """Run only the API server"""
    app = IAFiscalCapivariApp()
    app.run()

def run_dashboard_only():
    """Run only the dashboard"""
    run_streamlit_dashboard()

def run_scheduler_only():
    """Run only the scheduler"""
    notification_manager = NotificationManager()
    
    logger.info("Starting scheduler-only mode")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")

def main():
    """Main entry point with command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description="IA Fiscal Capivari - Municipal Spending Monitor")
    parser.add_argument("--mode", choices=["full", "api", "dashboard", "scheduler"], 
                       default="full", help="Application mode")
    parser.add_argument("--port", type=int, default=8000, help="API server port")
    parser.add_argument("--dashboard-port", type=int, default=8501, help="Dashboard port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logger.logger.setLevel("DEBUG")
        
    # Set ports
    if args.port != 8000:
        # Update uvicorn config - would need to modify the server startup
        pass
        
    # Setup signal handlers only in main thread
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run based on mode
    if args.mode == "full":
        # Run both API and dashboard
        api_thread = threading.Thread(target=run_api_only, daemon=True)
        api_thread.start()
        
        # Give API time to start
        time.sleep(2)
        
        # Run dashboard in main thread
        run_streamlit_dashboard()
        
    elif args.mode == "api":
        run_api_only()
        
    elif args.mode == "dashboard":
        run_dashboard_only()
        
    elif args.mode == "scheduler":
        run_scheduler_only()

if __name__ == "__main__":
    main()