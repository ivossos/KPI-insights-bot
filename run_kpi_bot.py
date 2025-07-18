#!/usr/bin/env python3
"""
KPI Insight Bot - Complete Application Runner
Integrates KPI Bot with existing IA Fiscal Capivari system
"""

import asyncio
import uvicorn
import streamlit
import threading
import time
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.main import app as fastapi_app
from src.config import settings
from src.monitoring.logger import logger
from src.kpi_bot.catalog.metric_catalog import MetricCatalog
from src.kpi_bot.auth.auth_manager import AuthManager

def run_kpi_dashboard():
    """Run the KPI Bot Streamlit dashboard"""
    import subprocess
    
    dashboard_path = Path(__file__).parent / "src" / "kpi_bot" / "dashboard" / "kpi_dashboard.py"
    
    cmd = [
        "streamlit", "run", str(dashboard_path),
        "--server.port=8502",
        "--server.address=0.0.0.0",
        "--theme.base=dark",
        "--theme.primaryColor=#ffd700",
        "--theme.backgroundColor=#1a1a1a",
        "--theme.secondaryBackgroundColor=#2d2d2d",
        "--theme.textColor=#ffffff"
    ]
    
    subprocess.run(cmd)

def run_api_server():
    """Run the FastAPI server with KPI Bot endpoints"""
    config = uvicorn.Config(
        app=fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
    
    server = uvicorn.Server(config)
    server.run()

def initialize_kpi_system():
    """Initialize the KPI Bot system"""
    logger.info("Initializing KPI Insight Bot system...")
    
    try:
        # Initialize metric catalog
        metric_catalog = MetricCatalog()
        logger.info("Metric catalog initialized")
        
        # Initialize auth manager
        auth_manager = AuthManager(secret_key=settings.secret_key)
        logger.info("Authentication system initialized")
        
        logger.info("KPI Insight Bot system initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize KPI system: {e}")
        return False

def run_complete_system():
    """Run both API server and KPI dashboard"""
    logger.info("Starting complete KPI Insight Bot system")
    
    # Initialize system
    if not initialize_kpi_system():
        logger.error("System initialization failed")
        return
    
    # Start API server in background thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Give API time to start
    time.sleep(3)
    
    # Run KPI dashboard in main thread
    run_kpi_dashboard()

def run_api_only():
    """Run only the API server"""
    logger.info("Starting KPI Bot API server only")
    
    if not initialize_kpi_system():
        logger.error("System initialization failed")
        return
    
    run_api_server()

def run_dashboard_only():
    """Run only the KPI dashboard"""
    logger.info("Starting KPI Bot dashboard only")
    run_kpi_dashboard()

def setup_environment():
    """Set up the environment for KPI Bot"""
    logger.info("Setting up KPI Bot environment")
    
    # Create necessary directories
    directories = [
        "chroma_db",
        "logs/kpi_bot",
        "data/kpi_cache",
        "reports/kpi"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    logger.info("Environment setup complete")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="KPI Insight Bot - Complete System")
    parser.add_argument(
        "--mode", 
        choices=["complete", "api", "dashboard", "setup"], 
        default="complete",
        help="Application mode"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--setup-only", action="store_true", help="Only setup environment")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logger.setLevel("DEBUG")
    
    # Setup environment
    setup_environment()
    
    if args.setup_only:
        logger.info("Environment setup completed")
        return
    
    # Run based on mode
    if args.mode == "complete":
        run_complete_system()
    elif args.mode == "api":
        run_api_only()
    elif args.mode == "dashboard":
        run_dashboard_only()
    elif args.mode == "setup":
        logger.info("Setup mode - environment configured")

if __name__ == "__main__":
    main()