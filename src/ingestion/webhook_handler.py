import logging
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import json
import os

from ..config import settings, config
from ..models.schemas import IngestionStatus, DatasetType

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Handles webhook processing and data ingestion"""
    
    def __init__(self):
        self.raw_data_path = Path(config["data_storage"]["raw_data_path"])
        self.processed_data_path = Path(config["data_storage"]["processed_data_path"])
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        self.processed_data_path.mkdir(parents=True, exist_ok=True)
        
        # Status tracking
        self.ingestion_status = {}
        
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> None:
        """Process incoming webhook data"""
        dataset_id = webhook_data["dataset_id"]
        dataset_type = webhook_data["dataset_type"]
        
        logger.info(f"Processing webhook for dataset {dataset_id} of type {dataset_type}")
        
        # Update status
        self.ingestion_status[dataset_id] = IngestionStatus(
            dataset_id=dataset_id,
            status="processing",
            started_at=datetime.now(),
            records_processed=0,
            file_size=0
        )
        
        try:
            # Download dataset
            csv_data = await self._download_dataset(webhook_data["download_url"])
            
            # Save raw data
            raw_file_path = await self._save_raw_data(dataset_id, dataset_type, csv_data)
            
            # Save as parquet with partitioning
            parquet_file_path = await self._save_parquet_data(dataset_id, dataset_type, csv_data)
            
            # Update status
            self.ingestion_status[dataset_id].status = "completed"
            self.ingestion_status[dataset_id].completed_at = datetime.now()
            self.ingestion_status[dataset_id].file_size = len(csv_data)
            
            logger.info(f"Successfully processed dataset {dataset_id}")
            
        except Exception as e:
            logger.error(f"Error processing webhook for dataset {dataset_id}: {str(e)}")
            self.ingestion_status[dataset_id].status = "failed"
            self.ingestion_status[dataset_id].error_message = str(e)
            self.ingestion_status[dataset_id].completed_at = datetime.now()
            
    async def _download_dataset(self, download_url: str) -> bytes:
        """Download dataset from Apify"""
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Failed to download dataset: {response.status}")
                    
    async def _save_raw_data(self, dataset_id: str, dataset_type: str, csv_data: bytes) -> Path:
        """Save raw CSV data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{dataset_type}_{dataset_id}_{timestamp}.csv"
        file_path = self.raw_data_path / filename
        
        with open(file_path, 'wb') as f:
            f.write(csv_data)
            
        logger.info(f"Raw data saved to {file_path}")
        return file_path
        
    async def _save_parquet_data(self, dataset_id: str, dataset_type: str, csv_data: bytes) -> Path:
        """Save data as partitioned parquet"""
        try:
            # Read CSV data
            df = pd.read_csv(io.BytesIO(csv_data))
            
            # Add metadata
            df['dataset_id'] = dataset_id
            df['dataset_type'] = dataset_type
            df['ingestion_timestamp'] = datetime.now()
            
            # Create date-based partitions
            now = datetime.now()
            year = now.year
            month = now.month
            
            # Create partition directory
            partition_dir = self.processed_data_path / f"year={year}" / f"month={month:02d}" / dataset_type
            partition_dir.mkdir(parents=True, exist_ok=True)
            
            # Save as parquet
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            filename = f"{dataset_type}_{dataset_id}_{timestamp}.parquet"
            file_path = partition_dir / filename
            
            df.to_parquet(file_path, index=False)
            
            # Update record count
            self.ingestion_status[dataset_id].records_processed = len(df)
            
            logger.info(f"Parquet data saved to {file_path} with {len(df)} records")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving parquet data: {str(e)}")
            raise
            
    async def get_ingestion_status(self, dataset_id: str) -> Dict[str, Any]:
        """Get ingestion status for a dataset"""
        if dataset_id in self.ingestion_status:
            return self.ingestion_status[dataset_id].dict()
        else:
            return {"error": "Dataset not found"}
            
    async def get_ingestion_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get ingestion history"""
        history = list(self.ingestion_status.values())
        history.sort(key=lambda x: x.started_at, reverse=True)
        return [status.dict() for status in history[:limit]]
        
    def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """Clean up old data files"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for file_path in self.raw_data_path.glob("*.csv"):
            if file_path.stat().st_mtime < cutoff_date.timestamp():
                file_path.unlink()
                logger.info(f"Deleted old file: {file_path}")
                
import io
from datetime import timedelta