from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
import logging
from datetime import datetime
from typing import Dict, Any
import hashlib
import hmac

from ..config import settings, config
from ..ingestion.webhook_handler import WebhookHandler
from ..ingestion.data_processor import DataProcessor
from ..models.schemas import WebhookData, IngestionResponse
from ..kpi_bot.api.kpi_api import router as kpi_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

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

# Security
security = HTTPBearer()

# Initialize handlers
webhook_handler = WebhookHandler()
data_processor = DataProcessor()

# Include KPI Bot routes
app.include_router(kpi_router)

def verify_webhook_signature(request: Request, body: bytes) -> bool:
    """Verify webhook signature for security"""
    signature = request.headers.get("X-Webhook-Signature")
    if not signature:
        return False
    
    expected_signature = hmac.new(
        settings.webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

@app.get("/")
async def root():
    return {"message": "IA Fiscal Capivari API", "status": "running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.post("/webhook/ingestion", response_model=IngestionResponse)
async def handle_ingestion_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    webhook_data: WebhookData
):
    """Handle ingestion webhook from Apify"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify webhook signature
        if not verify_webhook_signature(request, body):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Log incoming webhook
        logger.info(f"Received webhook for dataset: {webhook_data.dataset_id}")
        
        # Process webhook in background
        background_tasks.add_task(
            webhook_handler.process_webhook,
            webhook_data.dict()
        )
        
        return IngestionResponse(
            status="accepted",
            message="Webhook received and processing started",
            dataset_id=webhook_data.dataset_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/webhook/test")
async def test_webhook(data: Dict[str, Any]):
    """Test endpoint for webhook functionality"""
    logger.info(f"Test webhook received: {data}")
    return {"status": "received", "data": data}

@app.get("/ingestion/status/{dataset_id}")
async def get_ingestion_status(dataset_id: str):
    """Get ingestion status for a specific dataset"""
    try:
        status = await webhook_handler.get_ingestion_status(dataset_id)
        return status
    except Exception as e:
        logger.error(f"Error getting ingestion status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/ingestion/history")
async def get_ingestion_history(limit: int = 50):
    """Get ingestion history"""
    try:
        history = await webhook_handler.get_ingestion_history(limit)
        return history
    except Exception as e:
        logger.error(f"Error getting ingestion history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/process/manual")
async def manual_processing(
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Manual trigger for data processing"""
    # Here you would verify the JWT token
    # For now, just start processing
    try:
        background_tasks.add_task(data_processor.process_all_data)
        return {"status": "processing started"}
    except Exception as e:
        logger.error(f"Error starting manual processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )