import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

from ..config import settings, config
from ..models.schemas import Alert, NotificationRequest

logger = logging.getLogger(__name__)

class EmailSender:
    """Handles email notifications for fiscal alerts"""
    
    def __init__(self):
        self.smtp_server = config["notification_settings"]["email"]["smtp_server"]
        self.smtp_port = config["notification_settings"]["email"]["smtp_port"]
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.admin_email = settings.admin_email
        
    def send_weekly_digest(self, alerts: List[Alert], recipients: List[str]) -> bool:
        """Send weekly digest of alerts"""
        try:
            subject = f"Resumo Semanal - IA Fiscal Capivari ({datetime.now().strftime('%d/%m/%Y')})"
            
            # Generate digest content
            html_content = self._generate_weekly_digest_html(alerts)
            text_content = self._generate_weekly_digest_text(alerts)
            
            # Send to all recipients
            success = True
            for recipient in recipients:
                if not self._send_email(recipient, subject, html_content, text_content):
                    success = False
                    logger.error(f"Failed to send weekly digest to {recipient}")
                    
            return success
            
        except Exception as e:
            logger.error(f"Error sending weekly digest: {str(e)}")
            return False
            
    def send_alert_notification(self, alert: Alert, recipients: List[str]) -> bool:
        """Send immediate notification for high-priority alerts"""
        try:
            subject = f"🚨 Alerta Fiscal Crítico - {alert.rule_type.replace('_', ' ').title()}"
            
            # Generate alert content
            html_content = self._generate_alert_html(alert)
            text_content = self._generate_alert_text(alert)
            
            # Send to all recipients
            success = True
            for recipient in recipients:
                if not self._send_email(recipient, subject, html_content, text_content):
                    success = False
                    logger.error(f"Failed to send alert notification to {recipient}")
                    
            return success
            
        except Exception as e:
            logger.error(f"Error sending alert notification: {str(e)}")
            return False
            
    def send_system_notification(self, message: str, subject: str, recipients: List[str]) -> bool:
        """Send system notification"""
        try:
            html_content = f"""
            <html>
                <body>
                    <h2>IA Fiscal Capivari - Notificação do Sistema</h2>
                    <p>{message}</p>
                    <hr>
                    <p><small>Enviado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</small></p>
                </body>
            </html>
            """
            
            text_content = f"""
            IA Fiscal Capivari - Notificação do Sistema
            
            {message}
            
            Enviado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
            """
            
            success = True
            for recipient in recipients:
                if not self._send_email(recipient, subject, html_content, text_content):
                    success = False
                    
            return success
            
        except Exception as e:
            logger.error(f"Error sending system notification: {str(e)}")
            return False
            
    def _send_email(self, recipient: str, subject: str, html_content: str, text_content: str, 
                   attachments: Optional[List[str]] = None) -> bool:
        """Send email to recipient"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.username
            message["To"] = recipient
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(attachment_path)}'
                        )
                        message.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.username, recipient, message.as_string())
                
            logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient}: {str(e)}")
            return False
            
    def _generate_weekly_digest_html(self, alerts: List[Alert]) -> str:
        """Generate HTML content for weekly digest"""
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
        
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ background-color: #2a5298; color: white; padding: 20px; text-align: center; }}
                    .summary {{ padding: 20px; background-color: #f8f9fa; }}
                    .alert-section {{ margin: 20px 0; }}
                    .alert-item {{ padding: 10px; margin: 5px 0; border-left: 4px solid #2a5298; background-color: #f8f9fa; }}
                    .risk-high {{ border-left-color: #dc3545; }}
                    .risk-medium {{ border-left-color: #ffc107; }}
                    .risk-low {{ border-left-color: #28a745; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🏛️ IA Fiscal Capivari</h1>
                    <h2>Resumo Semanal de Alertas</h2>
                    <p>Período: {(datetime.now() - datetime.timedelta(days=7)).strftime('%d/%m/%Y')} - {datetime.now().strftime('%d/%m/%Y')}</p>
                </div>
                
                <div class="summary">
                    <h3>📊 Resumo Executivo</h3>
                    <p><strong>Total de alertas:</strong> {total_alerts}</p>
                    <p><strong>Alertas críticos:</strong> {critical_alerts} (risco ≥ 8)</p>
                    <p><strong>Alertas médios:</strong> {medium_alerts} (risco 5-7)</p>
                    <p><strong>Alertas baixos:</strong> {low_alerts} (risco < 5)</p>
                </div>
        """
        
        if total_alerts == 0:
            html_content += """
                <div class="alert-section">
                    <h3>✅ Nenhum alerta gerado</h3>
                    <p>Não foram detectadas anomalias significativas nesta semana.</p>
                </div>
            """
        else:
            for rule_type, type_alerts in alerts_by_type.items():
                html_content += f"""
                <div class="alert-section">
                    <h3>🚨 {rule_type.replace('_', ' ').title()} ({len(type_alerts)} alertas)</h3>
                """
                
                for alert in type_alerts[:5]:  # Show top 5 alerts per type
                    risk_class = "risk-high" if alert.risk_score >= 8 else "risk-medium" if alert.risk_score >= 5 else "risk-low"
                    html_content += f"""
                    <div class="alert-item {risk_class}">
                        <strong>Risco: {alert.risk_score}/10</strong><br>
                        {alert.description}<br>
                        <small>Criado em: {alert.created_at.strftime('%d/%m/%Y às %H:%M')}</small>
                    </div>
                    """
                    
                if len(type_alerts) > 5:
                    html_content += f"<p><em>... e mais {len(type_alerts) - 5} alertas</em></p>"
                    
                html_content += "</div>"
        
        html_content += f"""
                <div class="footer">
                    <p>Este é um resumo automático gerado pelo sistema IA Fiscal Capivari.</p>
                    <p>Para mais detalhes, acesse o dashboard: <a href="{settings.google_redirect_uri}">Sistema IA Fiscal</a></p>
                    <p>Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                </div>
            </body>
        </html>
        """
        
        return html_content
        
    def _generate_weekly_digest_text(self, alerts: List[Alert]) -> str:
        """Generate text content for weekly digest"""
        content = f"""
IA FISCAL CAPIVARI - RESUMO SEMANAL

Período: {(datetime.now() - datetime.timedelta(days=7)).strftime('%d/%m/%Y')} - {datetime.now().strftime('%d/%m/%Y')}

RESUMO EXECUTIVO:
- Total de alertas: {len(alerts)}
- Alertas críticos: {len([a for a in alerts if a.risk_score >= 8])}
- Alertas médios: {len([a for a in alerts if 5 <= a.risk_score < 8])}
- Alertas baixos: {len([a for a in alerts if a.risk_score < 5])}

"""
        
        if len(alerts) == 0:
            content += "✅ Nenhum alerta foi gerado nesta semana.\n"
        else:
            # Group by type
            alerts_by_type = {}
            for alert in alerts:
                if alert.rule_type not in alerts_by_type:
                    alerts_by_type[alert.rule_type] = []
                alerts_by_type[alert.rule_type].append(alert)
            
            for rule_type, type_alerts in alerts_by_type.items():
                content += f"\n🚨 {rule_type.replace('_', ' ').title().upper()} ({len(type_alerts)} alertas):\n"
                
                for alert in type_alerts[:3]:  # Show top 3 in text format
                    content += f"  - Risco {alert.risk_score}/10: {alert.description}\n"
                    
                if len(type_alerts) > 3:
                    content += f"  ... e mais {len(type_alerts) - 3} alertas\n"
        
        content += f"\nGerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        
        return content
        
    def _generate_alert_html(self, alert: Alert) -> str:
        """Generate HTML content for individual alert"""
        risk_color = "#dc3545" if alert.risk_score >= 8 else "#ffc107" if alert.risk_score >= 5 else "#28a745"
        
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ background-color: {risk_color}; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .alert-info {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🚨 Alerta Fiscal Crítico</h1>
                    <h2>{alert.rule_type.replace('_', ' ').title()}</h2>
                </div>
                
                <div class="content">
                    <div class="alert-info">
                        <h3>📋 Informações do Alerta</h3>
                        <p><strong>ID:</strong> {alert.id}</p>
                        <p><strong>Nível de Risco:</strong> {alert.risk_score}/10</p>
                        <p><strong>Descrição:</strong> {alert.description}</p>
                        <p><strong>Registros Afetados:</strong> {len(alert.affected_records)}</p>
                        <p><strong>Data de Criação:</strong> {alert.created_at.strftime('%d/%m/%Y às %H:%M')}</p>
                    </div>
                    
                    <div class="alert-info">
                        <h3>⚠️ Ação Necessária</h3>
                        <p>Este alerta requer investigação imediata. Acesse o sistema para mais detalhes e para marcar como investigado.</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Para mais informações, acesse: <a href="{settings.google_redirect_uri}">Sistema IA Fiscal</a></p>
                    <p>Gerado automaticamente em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                </div>
            </body>
        </html>
        """
        
        return html_content
        
    def _generate_alert_text(self, alert: Alert) -> str:
        """Generate text content for individual alert"""
        content = f"""
IA FISCAL CAPIVARI - ALERTA CRÍTICO

TIPO: {alert.rule_type.replace('_', ' ').title()}
ID: {alert.id}
RISCO: {alert.risk_score}/10
DESCRIÇÃO: {alert.description}
REGISTROS AFETADOS: {len(alert.affected_records)}
DATA: {alert.created_at.strftime('%d/%m/%Y às %H:%M')}

⚠️ AÇÃO NECESSÁRIA:
Este alerta requer investigação imediata. Acesse o sistema IA Fiscal para mais detalhes.

Gerado automaticamente em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
        """
        
        return content
        
    def send_test_email(self, recipient: str) -> bool:
        """Send test email to verify configuration"""
        try:
            subject = "Teste - IA Fiscal Capivari"
            html_content = """
            <html>
                <body>
                    <h2>Teste de Configuração</h2>
                    <p>Se você está recebendo este email, a configuração está funcionando corretamente.</p>
                    <p>Sistema IA Fiscal Capivari</p>
                </body>
            </html>
            """
            text_content = "Teste de configuração - Sistema IA Fiscal Capivari"
            
            return self._send_email(recipient, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            return False
            
    def get_email_statistics(self) -> Dict[str, Any]:
        """Get email sending statistics"""
        # In a real implementation, this would query a database
        return {
            "emails_sent_today": 0,
            "emails_sent_week": 0,
            "failed_emails": 0,
            "last_email_sent": None
        }