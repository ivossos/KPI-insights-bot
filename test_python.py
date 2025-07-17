
#!/usr/bin/env python3
"""
Test script to verify Python environment
"""

import sys
import os
from pathlib import Path

def test_python_environment():
    """Test Python environment setup"""
    print("🐍 Python Environment Test")
    print("=" * 30)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[0]}")
    
    # Test imports
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
    
    try:
        import streamlit
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
    
    # Check directories
    src_dir = Path("src")
    if src_dir.exists():
        print("✅ src directory found")
    else:
        print("❌ src directory not found")
    
    print("\n🚀 Environment test completed!")

if __name__ == "__main__":
    test_python_environment()
