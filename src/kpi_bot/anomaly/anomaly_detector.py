import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

from ..models import KPIResult, AlertRule, AlertInstance, AlertType
from ...monitoring.logger import logger


class AnomalyDetector:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.thresholds = {}
        self.seasonal_patterns = {}
        
    def detect_anomalies(self, kpi_results: List[KPIResult], historical_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            anomalies = []
            
            for kpi_result in kpi_results:
                kpi_historical = [d for d in historical_data if d.get('kpi_id') == kpi_result.kpi_id]
                
                if len(kpi_historical) < 10:  # Need minimum data points
                    continue
                
                # Statistical anomaly detection
                stat_anomaly = self._detect_statistical_anomaly(kpi_result, kpi_historical)
                if stat_anomaly:
                    anomalies.append(stat_anomaly)
                
                # Machine learning anomaly detection
                ml_anomaly = self._detect_ml_anomaly(kpi_result, kpi_historical)
                if ml_anomaly:
                    anomalies.append(ml_anomaly)
                
                # Seasonal anomaly detection
                seasonal_anomaly = self._detect_seasonal_anomaly(kpi_result, kpi_historical)
                if seasonal_anomaly:
                    anomalies.append(seasonal_anomaly)
                
                # Variance anomaly detection
                variance_anomaly = self._detect_variance_anomaly(kpi_result)
                if variance_anomaly:
                    anomalies.append(variance_anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return []

    def _detect_statistical_anomaly(self, kpi_result: KPIResult, historical_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        try:
            values = [d['value'] for d in historical_data]
            current_value = kpi_result.value
            
            # Calculate statistical measures
            mean = np.mean(values)
            std = np.std(values)
            z_score = abs(current_value - mean) / std if std > 0 else 0
            
            # Check for outliers using Z-score
            if z_score > 3:  # 3 standard deviations
                return {
                    'type': 'statistical',
                    'kpi_id': kpi_result.kpi_id,
                    'kpi_name': kpi_result.name,
                    'current_value': current_value,
                    'mean': mean,
                    'std': std,
                    'z_score': z_score,
                    'severity': 'high' if z_score > 4 else 'medium',
                    'message': f"{kpi_result.name} is {z_score:.2f} standard deviations from the mean",
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Statistical anomaly detection failed: {e}")
            return None

    def _detect_ml_anomaly(self, kpi_result: KPIResult, historical_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        try:
            if len(historical_data) < 20:  # Need more data for ML
                return None
            
            # Prepare features
            df = pd.DataFrame(historical_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Create features
            features = self._create_features(df)
            
            if features.empty:
                return None
            
            # Train or use existing model
            model_key = kpi_result.kpi_id
            
            if model_key not in self.models:
                self.models[model_key] = IsolationForest(contamination=0.1, random_state=42)
                self.scalers[model_key] = StandardScaler()
                
                # Fit the model
                scaled_features = self.scalers[model_key].fit_transform(features)
                self.models[model_key].fit(scaled_features)
            
            # Predict anomaly for current value
            current_features = self._create_current_features(kpi_result, historical_data[-10:])
            
            if current_features is None:
                return None
            
            scaled_current = self.scalers[model_key].transform([current_features])
            anomaly_score = self.models[model_key].decision_function(scaled_current)[0]
            is_anomaly = self.models[model_key].predict(scaled_current)[0] == -1
            
            if is_anomaly:
                return {
                    'type': 'ml',
                    'kpi_id': kpi_result.kpi_id,
                    'kpi_name': kpi_result.name,
                    'current_value': kpi_result.value,
                    'anomaly_score': anomaly_score,
                    'severity': 'high' if anomaly_score < -0.5 else 'medium',
                    'message': f"{kpi_result.name} shows anomalous behavior (score: {anomaly_score:.3f})",
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"ML anomaly detection failed: {e}")
            return None

    def _detect_seasonal_anomaly(self, kpi_result: KPIResult, historical_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        try:
            if len(historical_data) < 24:  # Need at least 2 years of monthly data
                return None
            
            df = pd.DataFrame(historical_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Extract seasonal patterns
            df['month'] = df['timestamp'].dt.month
            df['quarter'] = df['timestamp'].dt.quarter
            
            # Calculate seasonal averages
            monthly_avg = df.groupby('month')['value'].mean()
            quarterly_avg = df.groupby('quarter')['value'].mean()
            
            # Get current period
            current_time = kpi_result.calculation_date
            current_month = current_time.month
            current_quarter = (current_month - 1) // 3 + 1
            
            # Check against seasonal patterns
            monthly_expected = monthly_avg.get(current_month, df['value'].mean())
            quarterly_expected = quarterly_avg.get(current_quarter, df['value'].mean())
            
            # Calculate seasonal deviation
            monthly_deviation = abs(kpi_result.value - monthly_expected) / monthly_expected if monthly_expected > 0 else 0
            quarterly_deviation = abs(kpi_result.value - quarterly_expected) / quarterly_expected if quarterly_expected > 0 else 0
            
            # Check for significant seasonal anomaly
            if monthly_deviation > 0.3 or quarterly_deviation > 0.25:  # 30% or 25% deviation
                return {
                    'type': 'seasonal',
                    'kpi_id': kpi_result.kpi_id,
                    'kpi_name': kpi_result.name,
                    'current_value': kpi_result.value,
                    'monthly_expected': monthly_expected,
                    'quarterly_expected': quarterly_expected,
                    'monthly_deviation': monthly_deviation,
                    'quarterly_deviation': quarterly_deviation,
                    'severity': 'high' if max(monthly_deviation, quarterly_deviation) > 0.5 else 'medium',
                    'message': f"{kpi_result.name} deviates significantly from seasonal pattern",
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Seasonal anomaly detection failed: {e}")
            return None

    def _detect_variance_anomaly(self, kpi_result: KPIResult) -> Optional[Dict[str, Any]]:
        try:
            anomalies = []
            
            # Check prior year variance
            if kpi_result.variance_py is not None:
                py_deviation = abs(kpi_result.variance_py) / kpi_result.value if kpi_result.value > 0 else 0
                if py_deviation > 0.2:  # 20% variance threshold
                    anomalies.append({
                        'type': 'variance_py',
                        'kpi_id': kpi_result.kpi_id,
                        'kpi_name': kpi_result.name,
                        'current_value': kpi_result.value,
                        'variance': kpi_result.variance_py,
                        'deviation': py_deviation,
                        'severity': 'high' if py_deviation > 0.4 else 'medium',
                        'message': f"{kpi_result.name} has significant variance vs prior year ({py_deviation:.1%})",
                        'timestamp': datetime.now()
                    })
            
            # Check plan variance
            if kpi_result.variance_plan is not None:
                plan_deviation = abs(kpi_result.variance_plan) / kpi_result.value if kpi_result.value > 0 else 0
                if plan_deviation > 0.15:  # 15% variance threshold
                    anomalies.append({
                        'type': 'variance_plan',
                        'kpi_id': kpi_result.kpi_id,
                        'kpi_name': kpi_result.name,
                        'current_value': kpi_result.value,
                        'variance': kpi_result.variance_plan,
                        'deviation': plan_deviation,
                        'severity': 'high' if plan_deviation > 0.3 else 'medium',
                        'message': f"{kpi_result.name} has significant variance vs plan ({plan_deviation:.1%})",
                        'timestamp': datetime.now()
                    })
            
            return anomalies[0] if anomalies else None
            
        except Exception as e:
            logger.error(f"Variance anomaly detection failed: {e}")
            return None

    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            features = pd.DataFrame()
            
            # Basic value features
            features['value'] = df['value']
            features['value_lag1'] = df['value'].shift(1)
            features['value_lag2'] = df['value'].shift(2)
            
            # Rolling statistics
            features['rolling_mean_3'] = df['value'].rolling(window=3).mean()
            features['rolling_std_3'] = df['value'].rolling(window=3).std()
            features['rolling_mean_6'] = df['value'].rolling(window=6).mean()
            features['rolling_std_6'] = df['value'].rolling(window=6).std()
            
            # Trend features
            features['trend'] = df['value'].pct_change()
            features['trend_lag1'] = features['trend'].shift(1)
            
            # Time-based features
            features['month'] = df['timestamp'].dt.month
            features['quarter'] = df['timestamp'].dt.quarter
            features['day_of_month'] = df['timestamp'].dt.day
            features['day_of_week'] = df['timestamp'].dt.dayofweek
            
            # Remove NaN values
            features = features.dropna()
            
            return features
            
        except Exception as e:
            logger.error(f"Feature creation failed: {e}")
            return pd.DataFrame()

    def _create_current_features(self, kpi_result: KPIResult, recent_data: List[Dict[str, Any]]) -> Optional[List[float]]:
        try:
            if len(recent_data) < 3:
                return None
            
            values = [d['value'] for d in recent_data]
            current_value = kpi_result.value
            
            # Calculate features similar to training data
            features = [
                current_value,
                values[-1] if len(values) > 0 else current_value,
                values[-2] if len(values) > 1 else current_value,
                np.mean(values[-3:]) if len(values) >= 3 else current_value,
                np.std(values[-3:]) if len(values) >= 3 else 0,
                np.mean(values[-6:]) if len(values) >= 6 else current_value,
                np.std(values[-6:]) if len(values) >= 6 else 0,
                (current_value - values[-1]) / values[-1] if len(values) > 0 and values[-1] > 0 else 0,
                (values[-1] - values[-2]) / values[-2] if len(values) > 1 and values[-2] > 0 else 0,
                kpi_result.calculation_date.month,
                (kpi_result.calculation_date.month - 1) // 3 + 1,
                kpi_result.calculation_date.day,
                kpi_result.calculation_date.weekday()
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"Current feature creation failed: {e}")
            return None

    def create_alert_rules(self, kpi_results: List[KPIResult]) -> List[AlertRule]:
        try:
            alert_rules = []
            
            for kpi_result in kpi_results:
                # Statistical threshold rule
                if kpi_result.value > 0:
                    alert_rules.append(AlertRule(
                        id=f"stat_threshold_{kpi_result.kpi_id}",
                        name=f"Statistical Threshold - {kpi_result.name}",
                        kpi_id=kpi_result.kpi_id,
                        alert_type=AlertType.THRESHOLD,
                        threshold_value=kpi_result.value * 1.3,  # 30% above current
                        comparison_operator="greater_than",
                        notification_channels=["email", "slack"],
                        is_active=True,
                        created_by="system",
                        created_at=datetime.now()
                    ))
                
                # Anomaly detection rule
                alert_rules.append(AlertRule(
                    id=f"anomaly_{kpi_result.kpi_id}",
                    name=f"Anomaly Detection - {kpi_result.name}",
                    kpi_id=kpi_result.kpi_id,
                    alert_type=AlertType.ANOMALY,
                    notification_channels=["email", "slack"],
                    is_active=True,
                    created_by="system",
                    created_at=datetime.now()
                ))
            
            return alert_rules
            
        except Exception as e:
            logger.error(f"Alert rule creation failed: {e}")
            return []

    def process_alerts(self, anomalies: List[Dict[str, Any]], alert_rules: List[AlertRule]) -> List[AlertInstance]:
        try:
            alert_instances = []
            
            for anomaly in anomalies:
                # Find matching alert rule
                matching_rule = None
                for rule in alert_rules:
                    if rule.kpi_id == anomaly['kpi_id'] and rule.alert_type == AlertType.ANOMALY:
                        matching_rule = rule
                        break
                
                if matching_rule:
                    alert_instance = AlertInstance(
                        id=f"alert_{anomaly['kpi_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        rule_id=matching_rule.id,
                        kpi_id=anomaly['kpi_id'],
                        triggered_at=datetime.now(),
                        value=anomaly['current_value'],
                        severity=anomaly['severity'],
                        message=anomaly['message'],
                        acknowledged=False
                    )
                    alert_instances.append(alert_instance)
            
            return alert_instances
            
        except Exception as e:
            logger.error(f"Alert processing failed: {e}")
            return []

    def get_anomaly_summary(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            if not anomalies:
                return {'total': 0, 'by_severity': {}, 'by_type': {}}
            
            summary = {
                'total': len(anomalies),
                'by_severity': {},
                'by_type': {},
                'most_critical': None,
                'timestamp': datetime.now().isoformat()
            }
            
            # Count by severity
            for anomaly in anomalies:
                severity = anomaly.get('severity', 'unknown')
                summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            # Count by type
            for anomaly in anomalies:
                anomaly_type = anomaly.get('type', 'unknown')
                summary['by_type'][anomaly_type] = summary['by_type'].get(anomaly_type, 0) + 1
            
            # Find most critical
            critical_anomalies = [a for a in anomalies if a.get('severity') == 'high']
            if critical_anomalies:
                summary['most_critical'] = critical_anomalies[0]
            
            return summary
            
        except Exception as e:
            logger.error(f"Anomaly summary generation failed: {e}")
            return {'total': 0, 'by_severity': {}, 'by_type': {}}