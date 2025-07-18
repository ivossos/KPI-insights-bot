#!/bin/bash

# KPI Insight Bot Deployment Script
# This script deploys the KPI Insight Bot system using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="kpi-insight-bot"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env file not found. Please create it from .env.example"
        exit 1
    fi
    
    log_info "Prerequisites check passed!"
}

setup_directories() {
    log_info "Setting up directories..."
    
    # Create necessary directories
    mkdir -p data/{raw,processed,alerts}
    mkdir -p logs
    mkdir -p reports
    mkdir -p chroma_db
    mkdir -p ssl
    
    # Set permissions
    chmod 755 data logs reports chroma_db
    
    log_info "Directories created successfully!"
}

generate_ssl_cert() {
    log_info "Generating SSL certificate..."
    
    if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
        openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=kpi-bot.local"
        log_info "SSL certificate generated!"
    else
        log_info "SSL certificate already exists."
    fi
}

build_and_start() {
    log_info "Building and starting services..."
    
    # Build images
    docker-compose build
    
    # Start services
    docker-compose up -d
    
    log_info "Services started successfully!"
}

wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for API to be ready
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
            log_info "API service is ready!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "API service failed to start within timeout"
            exit 1
        fi
        
        log_info "Attempt $attempt/$max_attempts - waiting for API..."
        sleep 10
        ((attempt++))
    done
    
    # Wait for dashboard to be ready
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:8502 > /dev/null 2>&1; then
            log_info "Dashboard service is ready!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Dashboard service failed to start within timeout"
            exit 1
        fi
        
        log_info "Attempt $attempt/$max_attempts - waiting for dashboard..."
        sleep 10
        ((attempt++))
    done
}

show_status() {
    log_info "Deployment status:"
    docker-compose ps
    
    echo ""
    log_info "Services are available at:"
    echo "  - API: http://localhost:8000"
    echo "  - Dashboard: http://localhost:8502"
    echo "  - Health Check: http://localhost:8000/health"
    echo ""
    
    log_info "To view logs: docker-compose logs -f"
    log_info "To stop services: docker-compose down"
}

cleanup() {
    log_info "Cleaning up..."
    docker-compose down --remove-orphans
    docker system prune -f
    log_info "Cleanup completed!"
}

# Main deployment function
deploy() {
    log_info "Starting KPI Insight Bot deployment..."
    
    check_prerequisites
    setup_directories
    generate_ssl_cert
    build_and_start
    wait_for_services
    show_status
    
    log_info "Deployment completed successfully!"
}

# Script options
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "start")
        log_info "Starting services..."
        docker-compose up -d
        show_status
        ;;
    "stop")
        log_info "Stopping services..."
        docker-compose down
        ;;
    "restart")
        log_info "Restarting services..."
        docker-compose restart
        show_status
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "update")
        log_info "Updating services..."
        docker-compose pull
        docker-compose up -d --force-recreate
        show_status
        ;;
    *)
        echo "Usage: $0 {deploy|start|stop|restart|logs|status|cleanup|update}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment (default)"
        echo "  start   - Start services"
        echo "  stop    - Stop services"
        echo "  restart - Restart services"
        echo "  logs    - Show logs"
        echo "  status  - Show service status"
        echo "  cleanup - Clean up containers and images"
        echo "  update  - Update and restart services"
        exit 1
        ;;
esac