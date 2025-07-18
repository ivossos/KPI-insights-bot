import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import logging
from pathlib import Path

from ..models.schemas import Alert, AlertSummary, IngestionStatus
from ..config import settings

logger = logging.getLogger(__name__)

class DatabaseQueries:
    """Database query interface for IA Fiscal Capivari"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "data/ia_fiscal.db"
        self.ensure_database_exists()
        
    def ensure_database_exists(self):
        """Ensure database and tables exist"""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        rule_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        risk_score INTEGER NOT NULL,
                        affected_records TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        is_investigated BOOLEAN DEFAULT FALSE,
                        investigated_at TIMESTAMP,
                        investigator TEXT,
                        notes TEXT
                    )
                """)
                
                # Create alert explanations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alert_explanations (
                        alert_id TEXT PRIMARY KEY,
                        summary TEXT NOT NULL,
                        citizen_explanation TEXT NOT NULL,
                        risk_assessment TEXT NOT NULL,
                        recommended_actions TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (alert_id) REFERENCES alerts (id)
                    )
                """)
                
                # Create ingestion status table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ingestion_status (
                        dataset_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        started_at TIMESTAMP NOT NULL,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        records_processed INTEGER DEFAULT 0,
                        file_size INTEGER DEFAULT 0
                    )
                """)
                
                # Create data sources table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS data_sources (
                        name TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        last_update TIMESTAMP,
                        records_count INTEGER DEFAULT 0,
                        size_mb REAL DEFAULT 0,
                        error_message TEXT
                    )
                """)
                
                # Create user actions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_actions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_email TEXT NOT NULL,
                        action TEXT NOT NULL,
                        details TEXT,
                        timestamp TIMESTAMP NOT NULL
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
            
    def get_dashboard_metrics(self, days_back: int = 30) -> Dict[str, Any]:
        """Get dashboard metrics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total alerts
                cursor.execute("""
                    SELECT COUNT(*) FROM alerts 
                    WHERE created_at >= ?
                """, (cutoff_date,))
                total_alerts = cursor.fetchone()[0]
                
                # Critical alerts
                cursor.execute("""
                    SELECT COUNT(*) FROM alerts 
                    WHERE created_at >= ? AND risk_score >= 8
                """, (cutoff_date,))
                critical_alerts = cursor.fetchone()[0]
                
                # Investigated alerts
                cursor.execute("""
                    SELECT COUNT(*) FROM alerts 
                    WHERE created_at >= ? AND is_investigated = TRUE
                """, (cutoff_date,))
                investigated_alerts = cursor.fetchone()[0]
                
                # Investigation rate
                investigation_rate = (investigated_alerts / total_alerts * 100) if total_alerts > 0 else 0
                
                # Investigated amount (mock data)
                investigated_amount = investigated_alerts * 50000  # R$ 50k average per alert
                
                return {
                    "total_alerts": total_alerts,
                    "critical_alerts": critical_alerts,
                    "investigated_alerts": investigated_alerts,
                    "investigation_rate": investigation_rate,
                    "investigated_amount": investigated_amount
                }
                
        except Exception as e:
            logger.error(f"Error getting dashboard metrics: {str(e)}")
            return {}
            
    def get_recent_alerts(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM alerts 
                    WHERE created_at >= ?
                    ORDER BY created_at DESC
                    LIMIT 100
                """, (cutoff_date,))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    alert_dict = dict(zip(columns, row))
                    # Parse JSON fields
                    alert_dict['affected_records'] = json.loads(alert_dict['affected_records'])
                    results.append(alert_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting recent alerts: {str(e)}")
            return []
            
    def get_filtered_alerts(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get filtered alerts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM alerts WHERE 1=1"
                params = []
                
                # Rule types filter
                if filters.get('rule_types'):
                    placeholders = ','.join(['?' for _ in filters['rule_types']])
                    query += f" AND rule_type IN ({placeholders})"
                    params.extend(filters['rule_types'])
                
                # Risk range filter
                if filters.get('risk_range'):
                    min_risk, max_risk = filters['risk_range']
                    query += " AND risk_score >= ? AND risk_score <= ?"
                    params.extend([min_risk, max_risk])
                
                # Date range filter
                if filters.get('date_range'):
                    start_date, end_date = filters['date_range']
                    query += " AND created_at >= ? AND created_at <= ?"
                    params.extend([start_date, end_date])
                
                # Status filter
                if filters.get('status') and filters['status'] != 'Todos':
                    if filters['status'] == 'Não Investigado':
                        query += " AND is_investigated = FALSE"
                    elif filters['status'] == 'Investigado':
                        query += " AND is_investigated = TRUE"
                
                query += " ORDER BY created_at DESC LIMIT 1000"
                
                cursor.execute(query, params)
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    alert_dict = dict(zip(columns, row))
                    alert_dict['affected_records'] = json.loads(alert_dict['affected_records'])
                    results.append(alert_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting filtered alerts: {str(e)}")
            return []
            
    def get_alert_explanation(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get alert explanation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM alert_explanations 
                    WHERE alert_id = ?
                """, (alert_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    result = dict(zip(columns, row))
                    result['recommended_actions'] = json.loads(result['recommended_actions'])
                    return result
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting alert explanation: {str(e)}")
            return None
            
    def mark_alert_investigated(self, alert_id: str, investigator: str = None, notes: str = None):
        """Mark alert as investigated"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE alerts 
                    SET is_investigated = TRUE, 
                        investigated_at = ?, 
                        investigator = ?, 
                        notes = ?
                    WHERE id = ?
                """, (datetime.now(), investigator, notes, alert_id))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error marking alert as investigated: {str(e)}")
            raise
            
    def add_alert_notes(self, alert_id: str, notes: str):
        """Add notes to alert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE alerts 
                    SET notes = ?
                    WHERE id = ?
                """, (notes, alert_id))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error adding alert notes: {str(e)}")
            raise
            
    def save_alert(self, alert: Alert):
        """Save alert to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO alerts 
                    (id, rule_type, title, description, risk_score, affected_records, created_at, is_investigated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.id,
                    alert.rule_type,
                    alert.title,
                    alert.description,
                    alert.risk_score,
                    json.dumps(alert.affected_records),
                    alert.created_at,
                    alert.is_investigated
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving alert: {str(e)}")
            raise
            
    def save_alert_explanation(self, explanation: AlertSummary):
        """Save alert explanation to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO alert_explanations 
                    (alert_id, summary, citizen_explanation, risk_assessment, recommended_actions, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    explanation.alert_id,
                    explanation.summary,
                    explanation.citizen_explanation,
                    explanation.risk_assessment,
                    json.dumps(explanation.recommended_actions),
                    datetime.now()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving alert explanation: {str(e)}")
            raise
            
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Get data quality metrics"""
        try:
            # Mock data quality metrics
            return {
                "completeness": 95.5,
                "consistency": 92.1,
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "issues": "3 registros com valores nulos em 'fornecedor'"
            }
            
        except Exception as e:
            logger.error(f"Error getting data quality metrics: {str(e)}")
            return {}
            
    def get_data_sources_status(self) -> List[Dict[str, Any]]:
        """Get data sources status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM data_sources ORDER BY name")
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                # Add mock data if empty
                if not results:
                    results = [
                        {
                            "name": "Folha de Pagamento",
                            "status": "ok",
                            "last_update": "2024-01-15 06:00:00",
                            "records_count": 1250,
                            "size_mb": 15.2,
                            "error_message": None
                        },
                        {
                            "name": "Despesas",
                            "status": "ok",
                            "last_update": "2024-01-15 06:00:00",
                            "records_count": 856,
                            "size_mb": 12.8,
                            "error_message": None
                        },
                        {
                            "name": "Contratos",
                            "status": "warning",
                            "last_update": "2024-01-14 06:00:00",
                            "records_count": 234,
                            "size_mb": 5.4,
                            "error_message": "Alguns registros com datas inconsistentes"
                        }
                    ]
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting data sources status: {str(e)}")
            return []
            
    def get_report_data(self, report_type: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get data for report generation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get alerts in date range
                cursor.execute("""
                    SELECT * FROM alerts 
                    WHERE created_at >= ? AND created_at <= ?
                    ORDER BY created_at DESC
                """, (start_date, end_date))
                
                columns = [desc[0] for desc in cursor.description]
                alerts = []
                
                for row in cursor.fetchall():
                    alert_dict = dict(zip(columns, row))
                    alert_dict['affected_records'] = json.loads(alert_dict['affected_records'])
                    alerts.append(alert_dict)
                
                # Calculate statistics
                total_alerts = len(alerts)
                critical_alerts = len([a for a in alerts if a['risk_score'] >= 8])
                medium_alerts = len([a for a in alerts if 5 <= a['risk_score'] < 8])
                low_alerts = len([a for a in alerts if a['risk_score'] < 5])
                
                # Group by type
                alerts_by_type = {}
                for alert in alerts:
                    rule_type = alert['rule_type']
                    if rule_type not in alerts_by_type:
                        alerts_by_type[rule_type] = []
                    alerts_by_type[rule_type].append(alert)
                
                # Mock additional data for specific report types
                data = {
                    "period": f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
                    "total_records": total_alerts,
                    "alerts": alerts,
                    "total_alerts": total_alerts,
                    "critical_alerts": critical_alerts,
                    "medium_alerts": medium_alerts,
                    "low_alerts": low_alerts,
                    "alerts_by_type": alerts_by_type,
                    "investigation_rate": (len([a for a in alerts if a['is_investigated']]) / total_alerts * 100) if total_alerts > 0 else 0
                }
                
                # Add specific data based on report type
                if report_type == "Análise de Fornecedores":
                    data["top_suppliers"] = [
                        {"name": "Fornecedor A", "total_amount": 150000, "percentage": 25.5},
                        {"name": "Fornecedor B", "total_amount": 120000, "percentage": 20.3},
                        {"name": "Fornecedor C", "total_amount": 95000, "percentage": 16.1}
                    ]
                    data["concentration_analysis"] = {
                        "hhi": 0.15,
                        "top3_share": 61.9,
                        "level": "Moderada"
                    }
                    
                elif report_type == "Evolução Temporal":
                    data["monthly_trends"] = [
                        {"month": "Jan/2024", "alerts_count": 12, "total_amount": 250000},
                        {"month": "Fev/2024", "alerts_count": 18, "total_amount": 340000},
                        {"month": "Mar/2024", "alerts_count": 15, "total_amount": 290000}
                    ]
                    data["seasonal_patterns"] = [
                        "Maior incidência de alertas no final do mês",
                        "Picos de emergências em dezembro",
                        "Concentração de fornecedores aumenta no 4º trimestre"
                    ]
                
                return data
                
        except Exception as e:
            logger.error(f"Error getting report data: {str(e)}")
            return {}
            
    def log_user_action(self, user_email: str, action: str, details: Dict[str, Any] = None):
        """Log user action"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO user_actions 
                    (user_email, action, details, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (user_email, action, json.dumps(details or {}), datetime.now()))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error logging user action: {str(e)}")
            
    def get_user_actions(self, user_email: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user actions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if user_email:
                    cursor.execute("""
                        SELECT * FROM user_actions 
                        WHERE user_email = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (user_email, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM user_actions 
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    action_dict = dict(zip(columns, row))
                    action_dict['details'] = json.loads(action_dict['details'])
                    results.append(action_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting user actions: {str(e)}")
            return []