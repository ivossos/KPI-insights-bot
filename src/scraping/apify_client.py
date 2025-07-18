import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from apify_client import ApifyClient
from ..config import settings, config

logger = logging.getLogger(__name__)

class ApifyClientManager:
    """Manages Apify client and actor runs"""
    
    def __init__(self):
        self.client = ApifyClient(settings.apify_api_token)
        self.actor_id = "your_username/betha-portals-scraper"  # Replace with your actual actor ID from Apify Console
        self.default_input = {
            "portals": ["folha", "despesas", "contratos"],
            "maxRetries": 3
        }
        
    async def run_scraper(self, portals: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run the scraper actor"""
        try:
            # Prepare input
            run_input = self.default_input.copy()
            if portals:
                run_input["portals"] = portals
                
            logger.info(f"Starting scraper run for portals: {run_input['portals']}")
            
            # Run the actor
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            
            # Get run details
            run_info = {
                "id": run["id"],
                "status": run["status"],
                "started_at": run["startedAt"],
                "finished_at": run.get("finishedAt"),
                "stats": run.get("stats", {}),
                "meta": run.get("meta", {})
            }
            
            logger.info(f"Scraper run completed: {run_info['status']}")
            
            # Get results if successful
            if run["status"] == "SUCCEEDED":
                results = await self._get_run_results(run["id"])
                run_info["results"] = results
                
            return run_info
            
        except Exception as e:
            logger.error(f"Error running scraper: {str(e)}")
            raise
            
    async def _get_run_results(self, run_id: str) -> List[Dict[str, Any]]:
        """Get results from a completed run"""
        try:
            # Get default dataset
            dataset_client = self.client.dataset(run_id)
            
            # Download items
            items = dataset_client.list_items()
            
            return items.items
            
        except Exception as e:
            logger.error(f"Error getting run results: {str(e)}")
            return []
            
    async def schedule_daily_run(self) -> str:
        """Schedule daily scraper run"""
        try:
            # Create schedule
            schedule_input = {
                "name": "Daily Betha Portals Scraper",
                "cronExpression": f"0 {config['schedule']['scraping_time'].split(':')[0]} * * *",
                "isEnabled": True,
                "actions": [
                    {
                        "type": "RUN_ACTOR",
                        "actorId": self.actor_id,
                        "input": self.default_input
                    }
                ]
            }
            
            schedule = self.client.schedules().create(schedule_input)
            
            logger.info(f"Daily schedule created: {schedule['id']}")
            
            return schedule["id"]
            
        except Exception as e:
            logger.error(f"Error creating schedule: {str(e)}")
            raise
            
    async def get_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent actor runs"""
        try:
            runs = self.client.actor(self.actor_id).runs().list(limit=limit)
            
            return [
                {
                    "id": run["id"],
                    "status": run["status"],
                    "started_at": run["startedAt"],
                    "finished_at": run.get("finishedAt"),
                    "runtime_millis": run.get("stats", {}).get("runtimeMillis", 0),
                    "success": run["status"] == "SUCCEEDED"
                }
                for run in runs.items
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent runs: {str(e)}")
            return []
            
    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get status of a specific run"""
        try:
            run = self.client.actor(self.actor_id).runs().get(run_id)
            
            return {
                "id": run["id"],
                "status": run["status"],
                "started_at": run["startedAt"],
                "finished_at": run.get("finishedAt"),
                "stats": run.get("stats", {}),
                "meta": run.get("meta", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting run status: {str(e)}")
            return {}
            
    async def download_dataset(self, dataset_id: str, format: str = "csv") -> bytes:
        """Download dataset in specified format"""
        try:
            dataset_client = self.client.dataset(dataset_id)
            
            # Get download URL
            download_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format={format}"
            
            # Download data
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        raise Exception(f"Download failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error downloading dataset: {str(e)}")
            raise
            
    async def cleanup_old_runs(self, keep_last_n: int = 50) -> int:
        """Clean up old actor runs"""
        try:
            runs = self.client.actor(self.actor_id).runs().list(limit=1000)
            
            # Sort by date (newest first)
            sorted_runs = sorted(runs.items, key=lambda x: x["startedAt"], reverse=True)
            
            # Delete old runs
            deleted_count = 0
            for run in sorted_runs[keep_last_n:]:
                try:
                    self.client.actor(self.actor_id).runs().delete(run["id"])
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Could not delete run {run['id']}: {str(e)}")
                    
            logger.info(f"Cleaned up {deleted_count} old runs")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old runs: {str(e)}")
            return 0
            
    async def get_actor_info(self) -> Dict[str, Any]:
        """Get actor information"""
        try:
            actor = self.client.actor(self.actor_id).get()
            
            return {
                "id": actor["id"],
                "name": actor["name"],
                "username": actor["username"],
                "description": actor.get("description", ""),
                "stats": actor.get("stats", {}),
                "created_at": actor["createdAt"],
                "modified_at": actor["modifiedAt"]
            }
            
        except Exception as e:
            logger.error(f"Error getting actor info: {str(e)}")
            return {}
            
    async def update_actor_input(self, new_input: Dict[str, Any]) -> bool:
        """Update default actor input"""
        try:
            self.default_input.update(new_input)
            
            # Update actor's input schema if needed
            actor_input = {
                "name": "Betha Portals Scraper",
                "input": self.default_input
            }
            
            self.client.actor(self.actor_id).update(actor_input)
            
            logger.info("Actor input updated successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating actor input: {str(e)}")
            return False
            
    async def test_actor(self) -> Dict[str, Any]:
        """Test actor with minimal input"""
        try:
            test_input = {
                "portals": ["folha"],  # Test with one portal
                "maxRetries": 1
            }
            
            logger.info("Starting actor test run")
            
            run = self.client.actor(self.actor_id).call(run_input=test_input)
            
            result = {
                "success": run["status"] == "SUCCEEDED",
                "run_id": run["id"],
                "status": run["status"],
                "duration_ms": run.get("stats", {}).get("runtimeMillis", 0),
                "error": run.get("statusMessage") if run["status"] != "SUCCEEDED" else None
            }
            
            logger.info(f"Actor test completed: {result['success']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing actor: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        try:
            # Get account info
            user = self.client.user().get()
            
            return {
                "usage_credits": user.get("usageCredits", 0),
                "monthly_usage": user.get("monthlyUsage", {}),
                "limits": user.get("limits", {}),
                "plan": user.get("plan", "Unknown")
            }
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {str(e)}")
            return {}
            
    async def handle_webhook_data(self, webhook_data: Dict[str, Any]) -> bool:
        """Handle incoming webhook data from actor"""
        try:
            dataset_id = webhook_data.get("dataset_id")
            dataset_type = webhook_data.get("dataset_type")
            
            if not dataset_id or not dataset_type:
                logger.error("Invalid webhook data: missing dataset_id or dataset_type")
                return False
                
            # Download the dataset
            csv_data = await self.download_dataset(dataset_id, "csv")
            
            # Process the data through the ingestion pipeline
            from ..ingestion.webhook_handler import WebhookHandler
            webhook_handler = WebhookHandler()
            
            # Create webhook data object
            processed_webhook_data = {
                "dataset_id": dataset_id,
                "dataset_type": dataset_type,
                "run_id": webhook_data.get("run_id"),
                "status": webhook_data.get("status"),
                "items_count": webhook_data.get("items_count", 0),
                "download_url": webhook_data.get("download_url"),
                "timestamp": webhook_data.get("timestamp")
            }
            
            # Process webhook
            await webhook_handler.process_webhook(processed_webhook_data)
            
            logger.info(f"Webhook data processed successfully: {dataset_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling webhook data: {str(e)}")
            return False
            
    async def monitor_runs(self) -> List[Dict[str, Any]]:
        """Monitor running actors"""
        try:
            runs = self.client.actor(self.actor_id).runs().list(limit=10)
            
            active_runs = []
            for run in runs.items:
                if run["status"] in ["RUNNING", "READY"]:
                    active_runs.append({
                        "id": run["id"],
                        "status": run["status"],
                        "started_at": run["startedAt"],
                        "runtime_millis": run.get("stats", {}).get("runtimeMillis", 0)
                    })
                    
            return active_runs
            
        except Exception as e:
            logger.error(f"Error monitoring runs: {str(e)}")
            return []
            
    async def get_run_logs(self, run_id: str) -> List[str]:
        """Get logs for a specific run"""
        try:
            log_client = self.client.log(run_id)
            logs = log_client.get()
            
            return logs.split('\n') if logs else []
            
        except Exception as e:
            logger.error(f"Error getting run logs: {str(e)}")
            return []
            
    def get_client_info(self) -> Dict[str, Any]:
        """Get client configuration info"""
        return {
            "actor_id": self.actor_id,
            "default_input": self.default_input,
            "has_token": bool(settings.apify_api_token),
            "base_url": "https://api.apify.com/v2"
        }