#!/usr/bin/env python3
"""
Run just the Streamlit dashboard for Replit
"""

import os
import sys
import subprocess
from pathlib import Path

# Set up paths
workspace_dir = Path("/home/runner/workspace")
src_dir = workspace_dir / "src"

# Change to src directory
os.chdir(str(src_dir))

# Add to Python path
sys.path.insert(0, str(src_dir))
os.environ["PYTHONPATH"] = str(src_dir)

print("🚀 Starting IA Fiscal Capivari Dashboard...")
print(f"📁 Working directory: {os.getcwd()}")

# Run Streamlit
dashboard_path = src_dir / "dashboard" / "main.py"

cmd = [
    sys.executable, "-m", "streamlit", "run", str(dashboard_path),
    "--server.port=8501",
    "--server.address=0.0.0.0",
    "--server.headless=true",
    "--server.enableCORS=false",
    "--server.enableXsrfProtection=false"
]

try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\n👋 Dashboard stopped")
except Exception as e:
    print(f"❌ Error: {e}")