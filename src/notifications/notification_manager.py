import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import schedule

from ..config import settings, config
from ..models.schemas import Alert, NotificationRequest
from .email_sender import EmailSender
from .telegram_sender import TelegramSender

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manages all notification channels and scheduling"""
    
    def __init__(self):
        self.email_sender = EmailSender()
        self.telegram_sender = TelegramSender()
        
        # Load notification recipients
        self.email_recipients = self._load_email_recipients()
        self.telegram_enabled = config["notification_settings"]["telegram"]["enabled"]
        self.email_enabled = config["notification_settings"]["email"]["enabled"]
        
        # Schedule jobs
        self._schedule_notifications()
        
    def _load_email_recipients(self) -> List[str]:
        """Load email recipients from configuration"""
        # In production, this would load from database
        return [
            settings.admin_email,
            "auditoria@capivari.sp.gov.br",
            "fiscal@capivari.sp.gov.br"
        ]
        
    def _schedule_notifications(self):
        """Schedule notification jobs"""
        # Weekly digest
        weekly_time = config["schedule"]["weekly_digest_time"]
        weekly_day = config["schedule"]["weekly_digest_day"]
        
        schedule.every().monday.at(weekly_time).do(self._send_weekly_digest)
        
        # Daily summary (optional)
        schedule.every().day.at("18:00").do(self._send_daily_summary)
        
        logger.info("Notification schedule configured")
        
    async def send_immediate_alert(self, alert: Alert) -> Dict[str, bool]:
        """Send immediate notification for high-priority alerts"""
        results = {"email": False, "telegram": False}
        
        # Only send immediate notifications for critical alerts
        if alert.risk_score >= 8:
            try:
                # Send email notification
                if self.email_enabled:
                    results["email"] = self.email_sender.send_alert_notification(
                        alert, self.email_recipients
                    )
                
                # Send Telegram notification
                if self.telegram_enabled:
                    results["telegram"] = await self.telegram_sender.send_alert_notification(alert)
                
                # Log results
                if any(results.values()):
                    logger.info(f"Immediate alert sent for {alert.id}: {results}")
                else:
                    logger.warning(f"Failed to send immediate alert for {alert.id}")
                    
            except Exception as e:
                logger.error(f"Error sending immediate alert: {str(e)}")
                
        return results
        
    async def send_batch_alerts(self, alerts: List[Alert]) -> Dict[str, bool]:
        """Send batch notification for multiple alerts"""
        results = {"email": False, "telegram": False}
        
        if not alerts:
            return results
            
        try:
            # Filter critical alerts for immediate notification
            critical_alerts = [a for a in alerts if a.risk_score >= 8]
            
            if critical_alerts:
                # Send email batch
                if self.email_enabled:
                    results["email"] = self.email_sender.send_weekly_digest(
                        critical_alerts, self.email_recipients
                    )
                
                # Send Telegram batch
                if self.telegram_enabled:
                    results["telegram"] = await self.telegram_sender.send_weekly_digest(critical_alerts)
                
                logger.info(f"Batch alerts sent for {len(critical_alerts)} alerts: {results}")
                
        except Exception as e:
            logger.error(f"Error sending batch alerts: {str(e)}")
            
        return results
        
    def _send_weekly_digest(self):
        """Send weekly digest (called by scheduler)"""
        try:
            # Get alerts from last week
            from ..database.queries import DatabaseQueries
            db = DatabaseQueries()
            
            alerts = db.get_recent_alerts(7)  # Last 7 days
            
            # Send digest
            asyncio.create_task(self._send_weekly_digest_async(alerts))
            
        except Exception as e:
            logger.error(f"Error in weekly digest job: {str(e)}")
            
    async def _send_weekly_digest_async(self, alerts: List[Alert]):
        """Send weekly digest asynchronously"""
        try:
            results = {"email": False, "telegram": False}
            
            # Send email digest
            if self.email_enabled:
                results["email"] = self.email_sender.send_weekly_digest(
                    alerts, self.email_recipients
                )
            
            # Send Telegram digest
            if self.telegram_enabled:
                results["telegram"] = await self.telegram_sender.send_weekly_digest(alerts)
            
            logger.info(f"Weekly digest sent: {results}")
            
        except Exception as e:
            logger.error(f"Error sending weekly digest: {str(e)}")
            
    def _send_daily_summary(self):
        """Send daily summary (called by scheduler)"""
        try:
            # Get alerts from last day
            from ..database.queries import DatabaseQueries
            db = DatabaseQueries()
            
            alerts = db.get_recent_alerts(1)  # Last 24 hours
            
            if alerts:
                asyncio.create_task(self._send_daily_summary_async(alerts))
                
        except Exception as e:
            logger.error(f"Error in daily summary job: {str(e)}")
            
    async def _send_daily_summary_async(self, alerts: List[Alert]):
        """Send daily summary asynchronously"""
        try:
            # Create summary message
            summary_message = f"""📊 *Resumo Diário - IA Fiscal Capivari*

🗓️ {datetime.now().strftime('%d/%m/%Y')}

📈 *Alertas de Hoje:*
• Total: {len(alerts)}
• Críticos: {len([a for a in alerts if a.risk_score >= 8])}
• Médios: {len([a for a in alerts if 5 <= a.risk_score < 8])}
• Baixos: {len([a for a in alerts if a.risk_score < 5])}

📱 Acesse o dashboard para mais detalhes"""
            
            # Send only via Telegram for daily summary
            if self.telegram_enabled:
                await self.telegram_sender.send_system_notification(summary_message)
                
        except Exception as e:
            logger.error(f"Error sending daily summary: {str(e)}")
            
    async def send_system_notification(self, message: str, subject: str = "Sistema IA Fiscal") -> Dict[str, bool]:
        """Send system notification via all channels"""
        results = {"email": False, "telegram": False}
        
        try:
            # Send email
            if self.email_enabled:
                results["email"] = self.email_sender.send_system_notification(
                    message, subject, self.email_recipients
                )
            
            # Send Telegram
            if self.telegram_enabled:
                results["telegram"] = await self.telegram_sender.send_system_notification(message)
            
            logger.info(f"System notification sent: {results}")
            
        except Exception as e:
            logger.error(f"Error sending system notification: {str(e)}")
            
        return results
        
    async def send_data_quality_alert(self, quality_metrics: Dict[str, Any]) -> Dict[str, bool]:
        """Send alert about data quality issues"""
        results = {"email": False, "telegram": False}
        
        try:
            # Check if quality is below threshold
            completeness = quality_metrics.get("completeness", 100)
            consistency = quality_metrics.get("consistency", 100)
            
            if completeness < 80 or consistency < 80:
                message = f"""⚠️ *Alerta de Qualidade de Dados*

📊 *Métricas Atuais:*
• Completude: {completeness:.1f}%
• Consistência: {consistency:.1f}%

🔍 *Problemas Identificados:*
{quality_metrics.get('issues', 'Verificar dashboard para detalhes')}

📱 Acesse o sistema para mais informações"""
                
                results = await self.send_system_notification(message, "Alerta de Qualidade de Dados")
                
        except Exception as e:
            logger.error(f"Error sending data quality alert: {str(e)}")
            
        return results
        
    async def send_processing_error_alert(self, error_details: Dict[str, Any]) -> Dict[str, bool]:
        """Send alert about processing errors"""
        results = {"email": False, "telegram": False}
        
        try:
            message = f"""🚨 *Erro no Processamento*

⏰ *Horário:* {datetime.now().strftime('%d/%m/%Y às %H:%M')}
🔧 *Módulo:* {error_details.get('module', 'Unknown')}
❌ *Erro:* {error_details.get('error', 'Unknown error')}

🔍 *Detalhes:*
{error_details.get('details', 'Verificar logs para mais informações')}

⚠️ *Ação Necessária:* Verificar sistema e logs"""
            
            results = await self.send_system_notification(message, "Erro no Sistema")
            
        except Exception as e:
            logger.error(f"Error sending processing error alert: {str(e)}")
            
        return results
        
    async def test_all_channels(self) -> Dict[str, bool]:
        """Test all notification channels"""
        results = {"email": False, "telegram": False}
        
        try:
            # Test email
            if self.email_enabled:
                results["email"] = self.email_sender.send_test_email(settings.admin_email)
            
            # Test Telegram
            if self.telegram_enabled:
                results["telegram"] = await self.telegram_sender.send_test_message()
            
            logger.info(f"Notification channels tested: {results}")
            
        except Exception as e:
            logger.error(f"Error testing notification channels: {str(e)}")
            
        return results
        
    def get_notification_statistics(self) -> Dict[str, Any]:
        """Get notification statistics"""
        stats = {
            "email": self.email_sender.get_email_statistics(),
            "telegram": self.telegram_sender.get_telegram_statistics(),
            "enabled_channels": {
                "email": self.email_enabled,
                "telegram": self.telegram_enabled
            },
            "recipients": {
                "email_count": len(self.email_recipients),
                "telegram_configured": bool(settings.telegram_chat_id)
            }
        }
        
        return stats
        
    async def send_custom_notification(self, request: NotificationRequest) -> bool:
        """Send custom notification"""
        try:
            if request.type == "email" and self.email_enabled:
                return self.email_sender.send_system_notification(
                    request.message, request.subject, [request.recipient]
                )
            elif request.type == "telegram" and self.telegram_enabled:
                return await self.telegram_sender.send_system_notification(request.message)
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending custom notification: {str(e)}")
            return False
            
    def run_scheduler(self):
        """Run the notification scheduler"""
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Error running scheduler: {str(e)}")
            
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of scheduled jobs"""
        jobs = []
        
        for job in schedule.jobs:
            jobs.append({
                "function": job.job_func.__name__,
                "interval": str(job.interval),
                "unit": job.unit,
                "at_time": str(job.at_time) if job.at_time else None,
                "next_run": job.next_run.strftime('%d/%m/%Y %H:%M:%S') if job.next_run else None
            })
            
        return jobs
        
    def update_recipients(self, email_recipients: List[str]):
        """Update email recipients"""
        self.email_recipients = email_recipients
        logger.info(f"Email recipients updated: {len(email_recipients)} recipients")
        
    def toggle_channel(self, channel: str, enabled: bool):
        """Enable/disable notification channel"""
        if channel == "email":
            self.email_enabled = enabled
        elif channel == "telegram":
            self.telegram_enabled = enabled
            
        logger.info(f"Notification channel {channel} {'enabled' if enabled else 'disabled'}")
        
    async def send_urgent_alert(self, alert: Alert, override_settings: bool = False) -> Dict[str, bool]:
        """Send urgent alert bypassing normal filters"""
        results = {"email": False, "telegram": False}
        
        try:
            # Send via all channels for urgent alerts
            if self.email_enabled or override_settings:
                results["email"] = self.email_sender.send_alert_notification(
                    alert, self.email_recipients
                )
            
            if self.telegram_enabled or override_settings:
                results["telegram"] = await self.telegram_sender.send_alert_notification(alert)
            
            logger.info(f"Urgent alert sent for {alert.id}: {results}")
            
        except Exception as e:
            logger.error(f"Error sending urgent alert: {str(e)}")
            
        return results