import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from enum import Enum

from ..config import config
from ..models.schemas import Alert

logger = logging.getLogger(__name__)

class RuleType(Enum):
    OVERPRICING = "overpricing"
    SPLIT_ORDERS = "split_orders"
    SUPPLIER_CONCENTRATION = "supplier_concentration"
    RECURRING_EMERGENCY = "recurring_emergency"
    PAYROLL_ANOMALY = "payroll_anomaly"
    UNUSUAL_TIMING = "unusual_timing"
    DUPLICATE_PAYMENTS = "duplicate_payments"

@dataclass
class RuleResult:
    rule_type: RuleType
    passed: bool
    score: int
    message: str
    affected_records: List[str]
    evidence: Dict[str, Any]

class BusinessRulesEngine:
    """Engine for detecting financial anomalies using business rules"""
    
    def __init__(self):
        self.thresholds = config["thresholds"]
        self.rules = {
            RuleType.OVERPRICING: self._check_overpricing,
            RuleType.SPLIT_ORDERS: self._check_split_orders,
            RuleType.SUPPLIER_CONCENTRATION: self._check_supplier_concentration,
            RuleType.RECURRING_EMERGENCY: self._check_recurring_emergency,
            RuleType.PAYROLL_ANOMALY: self._check_payroll_anomaly,
            RuleType.UNUSUAL_TIMING: self._check_unusual_timing,
            RuleType.DUPLICATE_PAYMENTS: self._check_duplicate_payments,
        }
        
    def run_all_rules(self, df: pd.DataFrame, dataset_type: str) -> List[RuleResult]:
        """Run all applicable rules on the dataset"""
        results = []
        
        for rule_type, rule_func in self.rules.items():
            try:
                # Check if rule is applicable to this dataset type
                if self._is_rule_applicable(rule_type, dataset_type):
                    result = rule_func(df)
                    if result and not result.passed:
                        results.append(result)
                        logger.info(f"Rule {rule_type.value} triggered: {result.message}")
                        
            except Exception as e:
                logger.error(f"Error running rule {rule_type.value}: {str(e)}")
                
        return results
        
    def _is_rule_applicable(self, rule_type: RuleType, dataset_type: str) -> bool:
        """Check if a rule is applicable to the dataset type"""
        applicability = {
            RuleType.OVERPRICING: ["despesas", "contratos"],
            RuleType.SPLIT_ORDERS: ["despesas"],
            RuleType.SUPPLIER_CONCENTRATION: ["despesas", "contratos"],
            RuleType.RECURRING_EMERGENCY: ["despesas", "contratos"],
            RuleType.PAYROLL_ANOMALY: ["folha"],
            RuleType.UNUSUAL_TIMING: ["despesas", "contratos"],
            RuleType.DUPLICATE_PAYMENTS: ["despesas", "folha"]
        }
        
        return dataset_type in applicability.get(rule_type, [])
        
    def _check_overpricing(self, df: pd.DataFrame) -> Optional[RuleResult]:
        """Check for overpricing anomalies"""
        if 'unit_price' not in df.columns or 'price_mean' not in df.columns:
            return None
            
        threshold = self.thresholds["overpricing_percentage"] / 100
        
        # Find items with unit price significantly above market mean
        overpriced_mask = (
            (df['unit_price'] > df['price_mean'] * (1 + threshold)) &
            (df['price_mean'] > 0) &
            (df['unit_price'] > 0)
        )
        
        overpriced_items = df[overpriced_mask]
        
        if len(overpriced_items) > 0:
            # Calculate average overpricing percentage
            avg_overpricing = (
                (overpriced_items['unit_price'] / overpriced_items['price_mean'] - 1) * 100
            ).mean()
            
            # Calculate risk score based on number of items and severity
            risk_score = min(10, int(len(overpriced_items) / 10) + int(avg_overpricing / 50))
            
            return RuleResult(
                rule_type=RuleType.OVERPRICING,
                passed=False,
                score=risk_score,
                message=f"Found {len(overpriced_items)} items with prices {avg_overpricing:.1f}% above market average",
                affected_records=overpriced_items.index.tolist(),
                evidence={
                    "overpriced_count": len(overpriced_items),
                    "average_overpricing": avg_overpricing,
                    "threshold_used": threshold * 100,
                    "most_overpriced": overpriced_items.nlargest(5, 'unit_price')[['description', 'unit_price', 'price_mean']].to_dict('records')
                }
            )
            
        return RuleResult(
            rule_type=RuleType.OVERPRICING,
            passed=True,
            score=0,
            message="No overpricing detected",
            affected_records=[],
            evidence={}
        )
        
    def _check_split_orders(self, df: pd.DataFrame) -> Optional[RuleResult]:
        """Check for order splitting to avoid procurement limits"""
        if 'supplier' not in df.columns or 'amount' not in df.columns:
            return None
            
        threshold = self.thresholds["split_order_threshold"]
        
        # Group by supplier and date to find potential splits
        df['date_only'] = pd.to_datetime(df['date']).dt.date
        
        suspicious_groups = []
        
        for (supplier, date), group in df.groupby(['supplier', 'date_only']):
            if len(group) > 1:  # Multiple orders from same supplier on same date
                total_amount = group['amount'].sum()
                
                # Check if individual orders are just below threshold but total exceeds
                below_threshold = group[group['amount'] < threshold]
                if len(below_threshold) > 1 and total_amount > threshold:
                    suspicious_groups.append({
                        'supplier': supplier,
                        'date': date,
                        'orders_count': len(group),
                        'total_amount': total_amount,
                        'individual_amounts': group['amount'].tolist(),
                        'record_ids': group.index.tolist()
                    })
                    
        if suspicious_groups:
            total_suspicious_records = sum(len(g['record_ids']) for g in suspicious_groups)
            
            # Calculate risk score
            risk_score = min(10, len(suspicious_groups) + int(total_suspicious_records / 5))
            
            return RuleResult(
                rule_type=RuleType.SPLIT_ORDERS,
                passed=False,
                score=risk_score,
                message=f"Found {len(suspicious_groups)} potential order splitting cases involving {total_suspicious_records} records",
                affected_records=[rid for g in suspicious_groups for rid in g['record_ids']],
                evidence={
                    "suspicious_groups": suspicious_groups,
                    "threshold_used": threshold,
                    "total_cases": len(suspicious_groups)
                }
            )
            
        return RuleResult(
            rule_type=RuleType.SPLIT_ORDERS,
            passed=True,
            score=0,
            message="No order splitting detected",
            affected_records=[],
            evidence={}
        )
        
    def _check_supplier_concentration(self, df: pd.DataFrame) -> Optional[RuleResult]:
        """Check for excessive supplier concentration"""
        if 'supplier' not in df.columns or 'amount' not in df.columns:
            return None
            
        threshold = self.thresholds["supplier_concentration_threshold"]
        
        # Calculate supplier concentration
        supplier_totals = df.groupby('supplier')['amount'].sum().sort_values(ascending=False)
        total_spending = supplier_totals.sum()
        
        if total_spending == 0:
            return None
            
        # Check concentration of top suppliers
        top_supplier_pct = supplier_totals.iloc[0] / total_spending
        top_3_suppliers_pct = supplier_totals.head(3).sum() / total_spending
        
        concentrated_suppliers = []
        
        if top_supplier_pct > threshold:
            concentrated_suppliers.append({
                'supplier': supplier_totals.index[0],
                'percentage': top_supplier_pct * 100,
                'amount': supplier_totals.iloc[0]
            })
            
        if top_3_suppliers_pct > 0.8:  # 80% threshold for top 3
            concentrated_suppliers.extend([
                {
                    'supplier': supplier,
                    'percentage': (amount / total_spending) * 100,
                    'amount': amount
                }
                for supplier, amount in supplier_totals.head(3).items()
                if supplier not in [s['supplier'] for s in concentrated_suppliers]
            ])
            
        if concentrated_suppliers:
            # Get affected records
            affected_suppliers = [s['supplier'] for s in concentrated_suppliers]
            affected_records = df[df['supplier'].isin(affected_suppliers)].index.tolist()
            
            risk_score = min(10, int(top_supplier_pct * 10) + len(concentrated_suppliers))
            
            return RuleResult(
                rule_type=RuleType.SUPPLIER_CONCENTRATION,
                passed=False,
                score=risk_score,
                message=f"High supplier concentration detected: top supplier has {top_supplier_pct*100:.1f}% of total spending",
                affected_records=affected_records,
                evidence={
                    "concentrated_suppliers": concentrated_suppliers,
                    "top_supplier_percentage": top_supplier_pct * 100,
                    "top_3_percentage": top_3_suppliers_pct * 100,
                    "threshold_used": threshold * 100,
                    "total_spending": total_spending
                }
            )
            
        return RuleResult(
            rule_type=RuleType.SUPPLIER_CONCENTRATION,
            passed=True,
            score=0,
            message="No excessive supplier concentration detected",
            affected_records=[],
            evidence={}
        )
        
    def _check_recurring_emergency(self, df: pd.DataFrame) -> Optional[RuleResult]:
        """Check for recurring emergency purchases"""
        if 'is_emergency' not in df.columns or 'supplier' not in df.columns:
            return None
            
        emergency_df = df[df['is_emergency'] == True]
        
        if len(emergency_df) == 0:
            return None
            
        days_threshold = self.thresholds["emergency_recurrence_days"]
        
        # Check for suppliers with multiple emergency purchases
        emergency_suppliers = emergency_df.groupby('supplier').agg({
            'date': ['count', 'min', 'max'],
            'amount': 'sum'
        }).reset_index()
        
        emergency_suppliers.columns = ['supplier', 'emergency_count', 'first_emergency', 'last_emergency', 'total_amount']
        
        # Find suppliers with frequent emergencies
        frequent_emergency = emergency_suppliers[emergency_suppliers['emergency_count'] > 1]
        
        suspicious_suppliers = []
        
        for _, row in frequent_emergency.iterrows():
            days_between = (pd.to_datetime(row['last_emergency']) - pd.to_datetime(row['first_emergency'])).days
            
            if days_between <= days_threshold:
                supplier_records = emergency_df[emergency_df['supplier'] == row['supplier']]
                suspicious_suppliers.append({
                    'supplier': row['supplier'],
                    'emergency_count': row['emergency_count'],
                    'days_between': days_between,
                    'total_amount': row['total_amount'],
                    'record_ids': supplier_records.index.tolist()
                })
                
        if suspicious_suppliers:
            total_suspicious_records = sum(len(s['record_ids']) for s in suspicious_suppliers)
            
            risk_score = min(10, len(suspicious_suppliers) * 2 + int(total_suspicious_records / 5))
            
            return RuleResult(
                rule_type=RuleType.RECURRING_EMERGENCY,
                passed=False,
                score=risk_score,
                message=f"Found {len(suspicious_suppliers)} suppliers with recurring emergency purchases within {days_threshold} days",
                affected_records=[rid for s in suspicious_suppliers for rid in s['record_ids']],
                evidence={
                    "suspicious_suppliers": suspicious_suppliers,
                    "days_threshold": days_threshold,
                    "total_emergency_purchases": len(emergency_df)
                }
            )
            
        return RuleResult(
            rule_type=RuleType.RECURRING_EMERGENCY,
            passed=True,
            score=0,
            message="No recurring emergency purchases detected",
            affected_records=[],
            evidence={}
        )
        
    def _check_payroll_anomaly(self, df: pd.DataFrame) -> Optional[RuleResult]:
        """Check for payroll anomalies"""
        if 'total_payment' not in df.columns or 'position' not in df.columns:
            return None
            
        threshold = self.thresholds["payroll_variation_threshold"]
        
        anomalies = []
        
        # Check for outliers within position groups
        for position, group in df.groupby('position'):
            if len(group) > 2:  # Need at least 3 employees for statistical analysis
                mean_payment = group['total_payment'].mean()
                std_payment = group['total_payment'].std()
                
                if std_payment > 0:
                    # Find outliers (payments more than 2 standard deviations from mean)
                    outliers = group[
                        abs(group['total_payment'] - mean_payment) > 2 * std_payment
                    ]
                    
                    if len(outliers) > 0:
                        for _, outlier in outliers.iterrows():
                            deviation = abs(outlier['total_payment'] - mean_payment) / mean_payment
                            if deviation > threshold:
                                anomalies.append({
                                    'employee_id': outlier['employee_id'],
                                    'name': outlier['name'],
                                    'position': position,
                                    'payment': outlier['total_payment'],
                                    'position_mean': mean_payment,
                                    'deviation_percentage': deviation * 100,
                                    'record_id': outlier.name
                                })
                                
        if anomalies:
            risk_score = min(10, len(anomalies))
            
            return RuleResult(
                rule_type=RuleType.PAYROLL_ANOMALY,
                passed=False,
                score=risk_score,
                message=f"Found {len(anomalies)} payroll anomalies with significant deviations from position averages",
                affected_records=[a['record_id'] for a in anomalies],
                evidence={
                    "anomalies": anomalies,
                    "threshold_used": threshold * 100,
                    "total_employees": len(df)
                }
            )
            
        return RuleResult(
            rule_type=RuleType.PAYROLL_ANOMALY,
            passed=True,
            score=0,
            message="No payroll anomalies detected",
            affected_records=[],
            evidence={}
        )
        
    def _check_unusual_timing(self, df: pd.DataFrame) -> Optional[RuleResult]:
        """Check for transactions at unusual times"""
        if 'date' not in df.columns:
            return None
            
        df['hour'] = pd.to_datetime(df['date']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
        
        # Define unusual times (late night, early morning, weekends)
        unusual_hours = df['hour'].isin([0, 1, 2, 3, 4, 5, 22, 23])
        weekend_days = df['day_of_week'].isin([5, 6])  # Saturday, Sunday
        
        unusual_timing = df[unusual_hours | weekend_days]
        
        if len(unusual_timing) > 0:
            risk_score = min(10, int(len(unusual_timing) / 10))
            
            return RuleResult(
                rule_type=RuleType.UNUSUAL_TIMING,
                passed=False,
                score=risk_score,
                message=f"Found {len(unusual_timing)} transactions at unusual times (late night, early morning, or weekends)",
                affected_records=unusual_timing.index.tolist(),
                evidence={
                    "unusual_count": len(unusual_timing),
                    "total_transactions": len(df),
                    "unusual_percentage": (len(unusual_timing) / len(df)) * 100,
                    "time_breakdown": {
                        "late_night": len(df[unusual_hours]),
                        "weekends": len(df[weekend_days])
                    }
                }
            )
            
        return RuleResult(
            rule_type=RuleType.UNUSUAL_TIMING,
            passed=True,
            score=0,
            message="No unusual timing detected",
            affected_records=[],
            evidence={}
        )
        
    def _check_duplicate_payments(self, df: pd.DataFrame) -> Optional[RuleResult]:
        """Check for duplicate payments"""
        if 'amount' not in df.columns or 'supplier' not in df.columns:
            return None
            
        # Find potential duplicates based on supplier, amount, and date
        duplicate_cols = ['supplier', 'amount', 'date']
        
        # Only check columns that exist
        available_cols = [col for col in duplicate_cols if col in df.columns]
        
        if len(available_cols) < 2:
            return None
            
        duplicates = df[df.duplicated(subset=available_cols, keep=False)]
        
        if len(duplicates) > 0:
            # Group duplicates to show sets
            duplicate_groups = []
            for values, group in duplicates.groupby(available_cols):
                if len(group) > 1:
                    duplicate_groups.append({
                        'criteria': dict(zip(available_cols, values)),
                        'count': len(group),
                        'record_ids': group.index.tolist(),
                        'total_amount': group['amount'].sum()
                    })
                    
            risk_score = min(10, len(duplicate_groups))
            
            return RuleResult(
                rule_type=RuleType.DUPLICATE_PAYMENTS,
                passed=False,
                score=risk_score,
                message=f"Found {len(duplicate_groups)} sets of potential duplicate payments involving {len(duplicates)} records",
                affected_records=duplicates.index.tolist(),
                evidence={
                    "duplicate_groups": duplicate_groups,
                    "total_duplicates": len(duplicates),
                    "criteria_used": available_cols
                }
            )
            
        return RuleResult(
            rule_type=RuleType.DUPLICATE_PAYMENTS,
            passed=True,
            score=0,
            message="No duplicate payments detected",
            affected_records=[],
            evidence={}
        )
        
    def create_alerts_from_results(self, results: List[RuleResult]) -> List[Alert]:
        """Convert rule results to Alert objects"""
        alerts = []
        
        for result in results:
            if not result.passed:
                alert = Alert(
                    id=f"{result.rule_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    rule_type=result.rule_type.value,
                    title=f"Anomalia Detectada: {result.rule_type.value.replace('_', ' ').title()}",
                    description=result.message,
                    risk_score=result.score,
                    affected_records=result.affected_records,
                    created_at=datetime.now(),
                    is_investigated=False
                )
                alerts.append(alert)
                
        return alerts