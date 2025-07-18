#!/usr/bin/env python3
"""
Quick fix script for Replit deployment issues
"""

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("🔧 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-replit.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = [
        "data/raw",
        "data/processed", 
        "data/alerts",
        "logs",
        "reports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")

def check_environment():
    """Check environment variables"""
    print("🔍 Checking environment...")
    
    required_vars = [
        "APIFY_API_TOKEN",
        "CLAUDE_API_KEY",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "ADMIN_EMAIL"
    ]
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        print(f"⚠️  Missing environment variables: {', '.join(missing)}")
        print("Please add these in Replit Secrets (Tools → Secrets)")
        return False
    
    print("✅ All required environment variables found!")
    return True

def fix_imports():
    """Fix import issues"""
    print("🔧 Fixing import issues...")
    
    # Set Python path
    src_path = str(Path(__file__).parent / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Set environment variable
    os.environ["PYTHONPATH"] = src_path
    
    print("✅ Python path configured!")

def main():
    """Main fix function"""
    print("🚀 IA Fiscal Capivari - Replit Fix Script")
    print("=" * 50)
    
    # Fix imports
    fix_imports()
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Check environment
    if not check_environment():
        print("⚠️  Environment configuration needed")
        print("\nNext steps:")
        print("1. Go to Tools → Secrets in Replit")
        print("2. Add all required environment variables")
        print("3. Run this script again")
        return False
    
    print("\n🎉 Fix completed successfully!")
    print("You can now run: python main_replit.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)