
#!/usr/bin/env python3
"""
Run only the Streamlit dashboard
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run dashboard only"""
    print("🌐 Starting IA Fiscal Capivari Dashboard...")
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    dashboard_path = Path(__file__).parent / "src" / "dashboard" / "main.py"
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        'STREAMLIT_SERVER_PORT': '8501',
        'STREAMLIT_SERVER_ADDRESS': '0.0.0.0',
        'STREAMLIT_SERVER_HEADLESS': 'true',
        'STREAMLIT_BROWSER_GATHER_USAGE_STATS': 'false'
    })
    
    cmd = [
        "streamlit", "run", str(dashboard_path),
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.enableCORS=true",
        "--server.enableXsrfProtection=false",
        "--logger.level=info"
    ]
    
    print(f"📂 Dashboard path: {dashboard_path}")
    print(f"🚀 Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

if __name__ == "__main__":
    main()
