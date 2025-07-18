import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ..models import KPIDefinition, KPIResult, KPIQuery, CalculationType
from ..oracle.epm_connector import OracleEPMConnector
from ...monitoring.logger import logger


class KPICalculationEngine:
    def __init__(self, epm_connector: OracleEPMConnector):
        self.epm_connector = epm_connector
        self.fx_rates = self._load_fx_rates()
        self.calculation_cache = {}

    def _load_fx_rates(self) -> Dict[str, Dict[str, float]]:
        try:
            return {
                "USD": {"EUR": 0.85, "GBP": 0.75, "JPY": 110.0},
                "EUR": {"USD": 1.18, "GBP": 0.88, "JPY": 130.0},
                "GBP": {"USD": 1.33, "EUR": 1.14, "JPY": 148.0}
            }
        except Exception as e:
            logger.error(f"Failed to load FX rates: {e}")
            return {}

    def calculate_kpi(self, kpi_definition: KPIDefinition, filters: Dict[str, Any] = None) -> KPIResult:
        try:
            cache_key = self._get_cache_key(kpi_definition.id, filters)
            
            if cache_key in self.calculation_cache:
                cached_result = self.calculation_cache[cache_key]
                if self._is_cache_valid(cached_result):
                    return cached_result
            
            raw_data = self._fetch_raw_data(kpi_definition, filters)
            
            if not raw_data:
                return self._create_empty_result(kpi_definition)
            
            result = self._perform_calculation(kpi_definition, raw_data, filters)
            
            self.calculation_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"KPI calculation failed for {kpi_definition.name}: {e}")
            return self._create_error_result(kpi_definition, str(e))

    def _fetch_raw_data(self, kpi_definition: KPIDefinition, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        oracle_mapping = getattr(kpi_definition, 'oracle_mapping', {})
        source_system = oracle_mapping.get('source_system', 'FCCS')
        
        if source_system == 'FCCS':
            return self.epm_connector.get_fccs_data(kpi_definition, filters)
        elif source_system == 'EPBCS':
            return self.epm_connector.get_epbcs_data(kpi_definition, filters)
        elif source_system == 'ARCS':
            return self.epm_connector.get_arcs_data(kpi_definition, filters)
        elif source_system == 'Fusion_Financials':
            return self.epm_connector.get_fusion_financials_data(kpi_definition, filters)
        else:
            logger.warning(f"Unknown source system: {source_system}")
            return []

    def _perform_calculation(self, kpi_definition: KPIDefinition, raw_data: List[Dict[str, Any]], filters: Dict[str, Any] = None) -> KPIResult:
        df = pd.DataFrame(raw_data)
        
        if df.empty:
            return self._create_empty_result(kpi_definition)
        
        if kpi_definition.calculation_type == CalculationType.SUM:
            calculated_value = df['value'].sum()
        elif kpi_definition.calculation_type == CalculationType.AVERAGE:
            calculated_value = df['value'].mean()
        elif kpi_definition.calculation_type == CalculationType.PERCENTAGE:
            calculated_value = self._calculate_percentage(df, kpi_definition)
        elif kpi_definition.calculation_type == CalculationType.VARIANCE:
            calculated_value = self._calculate_variance(df, kpi_definition)
        elif kpi_definition.calculation_type == CalculationType.RATIO:
            calculated_value = self._calculate_ratio(df, kpi_definition)
        else:
            calculated_value = df['value'].iloc[0] if not df.empty else 0
        
        variance_py = self._calculate_prior_year_variance(kpi_definition, calculated_value, filters)
        variance_plan = self._calculate_plan_variance(kpi_definition, calculated_value, filters)
        variance_fx_neutral = self._calculate_fx_neutral_variance(kpi_definition, calculated_value, filters)
        
        drill_down_url = self._generate_drill_down_url(kpi_definition, filters)
        
        return KPIResult(
            kpi_id=kpi_definition.id,
            name=kpi_definition.name,
            value=float(calculated_value),
            unit=kpi_definition.unit,
            currency=kpi_definition.currency,
            time_period=self._get_time_period(filters),
            calculation_date=datetime.now(),
            variance_py=variance_py,
            variance_plan=variance_plan,
            variance_fx_neutral=variance_fx_neutral,
            drill_down_url=drill_down_url,
            metadata={
                'raw_data_points': len(raw_data),
                'calculation_type': kpi_definition.calculation_type.value,
                'source_systems': kpi_definition.data_sources
            }
        )

    def _calculate_percentage(self, df: pd.DataFrame, kpi_definition: KPIDefinition) -> float:
        if 'gross_margin' in kpi_definition.id.lower():
            revenue = df[df['metadata'].str.contains('Revenue', case=False, na=False)]['value'].sum()
            cogs = df[df['metadata'].str.contains('COGS', case=False, na=False)]['value'].sum()
            
            if revenue > 0:
                return ((revenue - cogs) / revenue) * 100
            return 0
        
        return df['value'].mean()

    def _calculate_variance(self, df: pd.DataFrame, kpi_definition: KPIDefinition) -> float:
        actual_rows = df[df['metadata'].str.contains('Actual', case=False, na=False)]
        plan_rows = df[df['metadata'].str.contains('Plan', case=False, na=False)]
        
        if not actual_rows.empty and not plan_rows.empty:
            actual_value = actual_rows['value'].sum()
            plan_value = plan_rows['value'].sum()
            return actual_value - plan_value
        
        return 0

    def _calculate_ratio(self, df: pd.DataFrame, kpi_definition: KPIDefinition) -> float:
        if len(df) >= 2:
            numerator = df.iloc[0]['value']
            denominator = df.iloc[1]['value']
            return numerator / denominator if denominator != 0 else 0
        
        return 0

    def _calculate_prior_year_variance(self, kpi_definition: KPIDefinition, current_value: float, filters: Dict[str, Any] = None) -> Optional[float]:
        try:
            py_filters = filters.copy() if filters else {}
            current_year = int(py_filters.get('year', datetime.now().year))
            py_filters['year'] = str(current_year - 1)
            
            py_data = self._fetch_raw_data(kpi_definition, py_filters)
            
            if py_data:
                py_df = pd.DataFrame(py_data)
                if kpi_definition.calculation_type == CalculationType.SUM:
                    py_value = py_df['value'].sum()
                elif kpi_definition.calculation_type == CalculationType.AVERAGE:
                    py_value = py_df['value'].mean()
                else:
                    py_value = py_df['value'].iloc[0] if not py_df.empty else 0
                
                return current_value - py_value
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to calculate prior year variance: {e}")
            return None

    def _calculate_plan_variance(self, kpi_definition: KPIDefinition, current_value: float, filters: Dict[str, Any] = None) -> Optional[float]:
        try:
            oracle_mapping = getattr(kpi_definition, 'oracle_mapping', {})
            
            if oracle_mapping.get('source_system') == 'EPBCS':
                return getattr(self, '_get_plan_variance_from_epbcs', lambda x, y: None)(kpi_definition, current_value)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to calculate plan variance: {e}")
            return None

    def _calculate_fx_neutral_variance(self, kpi_definition: KPIDefinition, current_value: float, filters: Dict[str, Any] = None) -> Optional[float]:
        try:
            if not kpi_definition.currency:
                return None
            
            py_filters = filters.copy() if filters else {}
            current_year = int(py_filters.get('year', datetime.now().year))
            py_filters['year'] = str(current_year - 1)
            
            py_data = self._fetch_raw_data(kpi_definition, py_filters)
            
            if py_data:
                py_df = pd.DataFrame(py_data)
                py_value = py_df['value'].sum()
                
                current_fx_rate = self.fx_rates.get(kpi_definition.currency, {}).get('USD', 1.0)
                py_fx_rate = self._get_historical_fx_rate(kpi_definition.currency, current_year - 1)
                
                fx_adjusted_py_value = py_value * (current_fx_rate / py_fx_rate)
                
                return current_value - fx_adjusted_py_value
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to calculate FX neutral variance: {e}")
            return None

    def _get_historical_fx_rate(self, currency: str, year: int) -> float:
        return self.fx_rates.get(currency, {}).get('USD', 1.0)

    def _generate_drill_down_url(self, kpi_definition: KPIDefinition, filters: Dict[str, Any] = None) -> str:
        base_url = "/api/v1/kpi/drill-down"
        params = {
            'kpi_id': kpi_definition.id,
            'filters': json.dumps(filters) if filters else '{}'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"

    def _get_time_period(self, filters: Dict[str, Any] = None) -> str:
        if not filters:
            return "YTD"
        
        return filters.get('period', 'YTD')

    def _get_cache_key(self, kpi_id: str, filters: Dict[str, Any] = None) -> str:
        filter_str = json.dumps(filters, sort_keys=True) if filters else "{}"
        return f"{kpi_id}_{hash(filter_str)}"

    def _is_cache_valid(self, cached_result: KPIResult, max_age_minutes: int = 60) -> bool:
        age = datetime.now() - cached_result.calculation_date
        return age.total_seconds() < (max_age_minutes * 60)

    def _create_empty_result(self, kpi_definition: KPIDefinition) -> KPIResult:
        return KPIResult(
            kpi_id=kpi_definition.id,
            name=kpi_definition.name,
            value=0,
            unit=kpi_definition.unit,
            currency=kpi_definition.currency,
            time_period="N/A",
            calculation_date=datetime.now(),
            metadata={'status': 'no_data'}
        )

    def _create_error_result(self, kpi_definition: KPIDefinition, error_message: str) -> KPIResult:
        return KPIResult(
            kpi_id=kpi_definition.id,
            name=kpi_definition.name,
            value=0,
            unit=kpi_definition.unit,
            currency=kpi_definition.currency,
            time_period="N/A",
            calculation_date=datetime.now(),
            metadata={'status': 'error', 'error': error_message}
        )

    def batch_calculate_kpis(self, kpi_definitions: List[KPIDefinition], filters: Dict[str, Any] = None) -> List[KPIResult]:
        results = []
        
        for kpi_definition in kpi_definitions:
            result = self.calculate_kpi(kpi_definition, filters)
            results.append(result)
        
        return results

    def clear_cache(self):
        self.calculation_cache.clear()
        logger.info("KPI calculation cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            'cache_size': len(self.calculation_cache),
            'cached_kpis': list(self.calculation_cache.keys())
        }