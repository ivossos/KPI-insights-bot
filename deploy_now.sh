#!/bin/bash

# 🚀 KPI Insight Bot - IMMEDIATE DEPLOYMENT SCRIPT
# This script will deploy the KPI Bot right now!

set -e

echo "🚀 DEPLOYING KPI INSIGHT BOT NOW!"
echo "================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "main_replit.py" ]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

# Create necessary directories
log_info "Creating directories..."
mkdir -p data/{raw,processed,alerts}
mkdir -p logs
mkdir -p reports
mkdir -p chroma_db

# Set permissions
chmod 755 data logs reports chroma_db

# Check Python version
log_info "Checking Python version..."
python3 --version

# Install dependencies
log_info "Installing dependencies..."
python3 -m pip install -r requirements.txt

# Check if environment variables are set
log_info "Checking environment variables..."
if [ -z "$OPENAI_API_KEY" ]; then
    log_warning "OPENAI_API_KEY not set - using .env file"
fi

if [ -z "$CLAUDE_API_KEY" ]; then
    log_warning "CLAUDE_API_KEY not set - using .env file"
fi

# Run the application
log_info "Starting KPI Insight Bot..."
log_info "API will be available at: http://localhost:8000"
log_info "Dashboard will be available at: http://localhost:8502"

# Start the application
python3 main_replit.py