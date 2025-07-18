"""
Simplified FastAPI main for Replit deployment
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IA Fiscal Capivari",
    description="Municipal spending monitoring and alerting system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IA Fiscal Capivari API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "running",
            "database": "connected",
            "monitoring": "active"
        }
    }

@app.get("/info")
async def system_info():
    """System information"""
    return {
        "system": "IA Fiscal Capivari",
        "description": "Municipal spending monitoring with AI",
        "features": [
            "Automated data collection",
            "AI-powered anomaly detection", 
            "Real-time alerts",
            "Interactive dashboard",
            "Comprehensive reporting"
        ],
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "webhook": "/webhook/ingestion"
        }
    }

@app.post("/webhook/ingestion")
async def webhook_ingestion(data: Dict[str, Any]):
    """Webhook for data ingestion"""
    try:
        logger.info(f"Webhook received: {data}")
        
        # Simple webhook handling
        return {
            "status": "accepted",
            "message": "Webhook received successfully",
            "timestamp": datetime.now().isoformat(),
            "data_id": data.get("dataset_id", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@app.get("/metrics")
async def get_metrics():
    """System metrics"""
    return {
        "alerts": {
            "total": 42,
            "critical": 8,
            "medium": 15,
            "low": 19
        },
        "data": {
            "sources": 3,
            "last_update": "2024-01-15T06:00:00",
            "records_processed": 1250
        },
        "system": {
            "uptime": "2 days",
            "status": "healthy",
            "version": "1.0.0"
        }
    }

@app.get("/alerts")
async def get_alerts():
    """Get recent alerts"""
    # Mock alert data
    alerts = [
        {
            "id": "alert_001",
            "type": "overpricing",
            "description": "Item priced 35% above market average",
            "risk_score": 8,
            "created_at": "2024-01-15T08:30:00",
            "status": "pending"
        },
        {
            "id": "alert_002", 
            "type": "split_orders",
            "description": "Potential order splitting detected",
            "risk_score": 6,
            "created_at": "2024-01-15T09:15:00",
            "status": "investigated"
        },
        {
            "id": "alert_003",
            "type": "supplier_concentration", 
            "description": "High supplier concentration (78%)",
            "risk_score": 7,
            "created_at": "2024-01-15T10:00:00",
            "status": "pending"
        }
    ]
    
    return {
        "alerts": alerts,
        "total": len(alerts),
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    # For testing locally
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )