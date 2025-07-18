#!/usr/bin/env python3
"""
Fix imports for Replit deployment
"""

import os
import sys
from pathlib import Path

def main():
    """Fix import paths for Replit"""
    
    # Get the current working directory
    workspace_dir = Path("/home/runner/workspace")
    src_dir = workspace_dir / "src"
    
    # Change to the src directory
    os.chdir(str(src_dir))
    
    # Add src to Python path
    sys.path.insert(0, str(src_dir))
    
    # Set environment variables
    os.environ["PYTHONPATH"] = str(src_dir)
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    print("🔧 Import paths fixed!")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path[0]}")
    
    # Now run the dashboard
    try:
        print("🚀 Starting dashboard...")
        import subprocess
        
        dashboard_path = src_dir / "dashboard" / "main.py"
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", str(dashboard_path),
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false"
        ]
        
        subprocess.run(cmd)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()