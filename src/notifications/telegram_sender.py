import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import aiohttp

from ..config import settings
from ..models.schemas import Alert

logger = logging.getLogger(__name__)

class TelegramSender:
    """Handles Telegram notifications for fiscal alerts"""
    
    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    async def send_weekly_digest(self, alerts: List[Alert]) -> bool:
        """Send weekly digest via Telegram"""
        try:
            message = self._generate_weekly_digest_message(alerts)
            
            return await self._send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending weekly digest to Telegram: {str(e)}")
            return False
            
    async def send_alert_notification(self, alert: Alert) -> bool:
        """Send immediate notification for high-priority alerts"""
        try:
            message = self._generate_alert_message(alert)
            
            return await self._send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending alert notification to Telegram: {str(e)}")
            return False
            
    async def send_system_notification(self, message: str) -> bool:
        """Send system notification via Telegram"""
        try:
            formatted_message = f"🤖 *Sistema IA Fiscal Capivari*\n\n{message}\n\n_{datetime.now().strftime('%d/%m/%Y às %H:%M')}_"
            
            return await self._send_message(formatted_message)
            
        except Exception as e:
            logger.error(f"Error sending system notification to Telegram: {str(e)}")
            return False
            
    async def _send_message(self, message: str) -> bool:
        """Send message to Telegram"""
        try:
            url = f"{self.api_url}/sendMessage"
            
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info("Message sent successfully to Telegram")
                            return True
                        else:
                            logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                            return False
                    else:
                        logger.error(f"HTTP error sending to Telegram: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {str(e)}")
            return False
            
    def _generate_weekly_digest_message(self, alerts: List[Alert]) -> str:
        """Generate weekly digest message for Telegram"""
        # Group alerts by type
        alerts_by_type = {}
        for alert in alerts:
            if alert.rule_type not in alerts_by_type:
                alerts_by_type[alert.rule_type] = []
            alerts_by_type[alert.rule_type].append(alert)
            
        # Calculate statistics
        total_alerts = len(alerts)
        critical_alerts = len([a for a in alerts if a.risk_score >= 8])
        medium_alerts = len([a for a in alerts if 5 <= a.risk_score < 8])
        low_alerts = len([a for a in alerts if a.risk_score < 5])
        
        # Build message
        message = f"""🏛️ *IA Fiscal Capivari*
📊 *Resumo Semanal de Alertas*

📅 *Período:* {(datetime.now() - datetime.timedelta(days=7)).strftime('%d/%m/%Y')} - {datetime.now().strftime('%d/%m/%Y')}

📈 *Estatísticas:*
• Total de alertas: {total_alerts}
• Alertas críticos: {critical_alerts} (risco ≥ 8)
• Alertas médios: {medium_alerts} (risco 5-7)
• Alertas baixos: {low_alerts} (risco < 5)

"""
        
        if total_alerts == 0:
            message += "✅ *Nenhum alerta foi gerado nesta semana.*\n"
        else:
            message += "🚨 *Alertas por Categoria:*\n"
            
            for rule_type, type_alerts in alerts_by_type.items():
                emoji = self._get_rule_emoji(rule_type)
                message += f"{emoji} *{rule_type.replace('_', ' ').title()}:* {len(type_alerts)} alertas\n"
                
                # Show top 2 alerts for each type
                for alert in sorted(type_alerts, key=lambda x: x.risk_score, reverse=True)[:2]:
                    risk_emoji = self._get_risk_emoji(alert.risk_score)
                    message += f"  {risk_emoji} Risco {alert.risk_score}/10: {alert.description[:80]}...\n"
                    
                if len(type_alerts) > 2:
                    message += f"  ... e mais {len(type_alerts) - 2} alertas\n"
                    
                message += "\n"
        
        message += f"📱 *Acesse o dashboard para mais detalhes*\n"
        message += f"🕐 _Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}_"
        
        return message
        
    def _generate_alert_message(self, alert: Alert) -> str:
        """Generate alert message for Telegram"""
        risk_emoji = self._get_risk_emoji(alert.risk_score)
        rule_emoji = self._get_rule_emoji(alert.rule_type)
        
        message = f"""🚨 *ALERTA FISCAL CRÍTICO*

{rule_emoji} *Tipo:* {alert.rule_type.replace('_', ' ').title()}
{risk_emoji} *Risco:* {alert.risk_score}/10
🆔 *ID:* `{alert.id}`
📊 *Registros Afetados:* {len(alert.affected_records)}
🕐 *Data:* {alert.created_at.strftime('%d/%m/%Y às %H:%M')}

📝 *Descrição:*
{alert.description}

⚠️ *Ação Necessária:*
Este alerta requer investigação imediata. Acesse o sistema para mais detalhes.

📱 *Acesse o dashboard para investigar*
"""
        
        return message
        
    def _get_risk_emoji(self, risk_score: int) -> str:
        """Get emoji based on risk score"""
        if risk_score >= 8:
            return "🔴"
        elif risk_score >= 5:
            return "🟡"
        else:
            return "🟢"
            
    def _get_rule_emoji(self, rule_type: str) -> str:
        """Get emoji based on rule type"""
        emojis = {
            "overpricing": "💰",
            "split_orders": "✂️",
            "supplier_concentration": "🎯",
            "recurring_emergency": "🚨",
            "payroll_anomaly": "👥",
            "unusual_timing": "⏰",
            "duplicate_payments": "🔄"
        }
        return emojis.get(rule_type, "⚠️")
        
    async def send_file(self, file_path: str, caption: str = "") -> bool:
        """Send file to Telegram"""
        try:
            url = f"{self.api_url}/sendDocument"
            
            data = aiohttp.FormData()
            data.add_field('chat_id', self.chat_id)
            data.add_field('caption', caption)
            data.add_field('parse_mode', 'Markdown')
            
            with open(file_path, 'rb') as file:
                data.add_field('document', file, filename=file_path.split('/')[-1])
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get("ok"):
                                logger.info(f"File sent successfully to Telegram: {file_path}")
                                return True
                            else:
                                logger.error(f"Telegram API error sending file: {result.get('description', 'Unknown error')}")
                                return False
                        else:
                            logger.error(f"HTTP error sending file to Telegram: {response.status}")
                            return False
                            
        except Exception as e:
            logger.error(f"Error sending file to Telegram: {str(e)}")
            return False
            
    async def send_chart(self, chart_data: bytes, caption: str = "") -> bool:
        """Send chart as image to Telegram"""
        try:
            url = f"{self.api_url}/sendPhoto"
            
            data = aiohttp.FormData()
            data.add_field('chat_id', self.chat_id)
            data.add_field('caption', caption)
            data.add_field('parse_mode', 'Markdown')
            data.add_field('photo', chart_data, filename='chart.png')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info("Chart sent successfully to Telegram")
                            return True
                        else:
                            logger.error(f"Telegram API error sending chart: {result.get('description', 'Unknown error')}")
                            return False
                    else:
                        logger.error(f"HTTP error sending chart to Telegram: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending chart to Telegram: {str(e)}")
            return False
            
    async def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            url = f"{self.api_url}/getMe"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            bot_info = result.get("result", {})
                            logger.info(f"Telegram bot connected: {bot_info.get('username', 'Unknown')}")
                            return True
                        else:
                            logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                            return False
                    else:
                        logger.error(f"HTTP error testing Telegram connection: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error testing Telegram connection: {str(e)}")
            return False
            
    async def send_test_message(self) -> bool:
        """Send test message to verify configuration"""
        try:
            message = f"""🤖 *Teste de Configuração*

Sistema IA Fiscal Capivari conectado com sucesso!

🕐 _Teste realizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}_"""
            
            return await self._send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending test message: {str(e)}")
            return False
            
    async def get_chat_info(self) -> Optional[Dict[str, Any]]:
        """Get chat information"""
        try:
            url = f"{self.api_url}/getChat"
            
            params = {"chat_id": self.chat_id}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            return result.get("result")
                        else:
                            logger.error(f"Telegram API error getting chat info: {result.get('description', 'Unknown error')}")
                            return None
                    else:
                        logger.error(f"HTTP error getting chat info: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting chat info: {str(e)}")
            return None
            
    def get_telegram_statistics(self) -> Dict[str, Any]:
        """Get Telegram sending statistics"""
        # In a real implementation, this would query a database
        return {
            "messages_sent_today": 0,
            "messages_sent_week": 0,
            "failed_messages": 0,
            "last_message_sent": None
        }
        
    async def send_interactive_keyboard(self, message: str, buttons: List[Dict[str, str]]) -> bool:
        """Send message with interactive keyboard"""
        try:
            url = f"{self.api_url}/sendMessage"
            
            # Create inline keyboard
            keyboard = []
            for button in buttons:
                keyboard.append([{
                    "text": button["text"],
                    "callback_data": button["callback_data"]
                }])
            
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "reply_markup": {
                    "inline_keyboard": keyboard
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("ok"):
                            logger.info("Interactive message sent successfully to Telegram")
                            return True
                        else:
                            logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                            return False
                    else:
                        logger.error(f"HTTP error sending interactive message: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending interactive message: {str(e)}")
            return False