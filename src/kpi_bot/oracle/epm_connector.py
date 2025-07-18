import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from urllib.parse import urljoin
import base64
import xml.etree.ElementTree as ET

from ..models import OracleConnection, KPIDefinition, KPIResult
from ...monitoring.logger import logger


class OracleEPMConnector:
    def __init__(self, connection: OracleConnection):
        self.connection = connection
        self.session = requests.Session()
        self.base_url = f"https://{connection.host}:{connection.port}"
        self.auth_token = None
        self._authenticate()

    def _authenticate(self):
        try:
            auth_url = urljoin(self.base_url, "/HyperionPlanning/rest/v3/applications")
            
            credentials = base64.b64encode(
                f"{self.connection.username}:{self.connection.password}".encode()
            ).decode()
            
            headers = {
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(auth_url, headers=headers)
            
            if response.status_code == 200:
                self.auth_token = credentials
                logger.info("Successfully authenticated with Oracle EPM")
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                raise Exception("Authentication failed")
                
        except Exception as e:
            logger.error(f"Failed to authenticate with Oracle EPM: {e}")
            raise

    def get_fccs_data(self, kpi_definition: KPIDefinition, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            oracle_mapping = getattr(kpi_definition, 'oracle_mapping', {})
            
            if oracle_mapping.get('source_system') != 'FCCS':
                raise ValueError("KPI not configured for FCCS")
            
            url = urljoin(self.base_url, "/HyperionPlanning/rest/v3/applications/FCCS/planTypes/FCCS/cubes/data")
            
            headers = {
                "Authorization": f"Basic {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            cube_query = {
                "cube": oracle_mapping.get('cube', 'FCCS_Revenue'),
                "dimensions": {
                    "Account": oracle_mapping.get('account_filter', 'Revenue_Total'),
                    "Scenario": oracle_mapping.get('scenario', 'Actual'),
                    "Year": filters.get('year', '2024') if filters else '2024',
                    "Period": filters.get('period', 'YTD') if filters else 'YTD'
                }
            }
            
            response = self.session.post(url, headers=headers, json=cube_query)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_fccs_response(data, kpi_definition)
            else:
                logger.error(f"FCCS data retrieval failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get FCCS data: {e}")
            return []

    def get_epbcs_data(self, kpi_definition: KPIDefinition, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            oracle_mapping = getattr(kpi_definition, 'oracle_mapping', {})
            
            if oracle_mapping.get('source_system') != 'EPBCS':
                raise ValueError("KPI not configured for EPBCS")
            
            url = urljoin(self.base_url, "/HyperionPlanning/rest/v3/applications/EPBCS/planTypes/EPBCS/cubes/data")
            
            headers = {
                "Authorization": f"Basic {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            cube_query = {
                "cube": oracle_mapping.get('cube', 'EPBCS_Expenses'),
                "dimensions": {
                    "Account": oracle_mapping.get('account_filter', 'OPEX_Total'),
                    "Scenario": [
                        oracle_mapping.get('scenario_actual', 'Actual'),
                        oracle_mapping.get('scenario_plan', 'Plan')
                    ],
                    "Year": filters.get('year', '2024') if filters else '2024',
                    "Period": filters.get('period', 'YTD') if filters else 'YTD'
                }
            }
            
            response = self.session.post(url, headers=headers, json=cube_query)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_epbcs_response(data, kpi_definition)
            else:
                logger.error(f"EPBCS data retrieval failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get EPBCS data: {e}")
            return []

    def get_arcs_data(self, kpi_definition: KPIDefinition, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            oracle_mapping = getattr(kpi_definition, 'oracle_mapping', {})
            
            if oracle_mapping.get('source_system') != 'ARCS':
                raise ValueError("KPI not configured for ARCS")
            
            url = urljoin(self.base_url, "/HyperionPlanning/rest/v3/applications/ARCS/data")
            
            headers = {
                "Authorization": f"Basic {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            query = {
                "cube": oracle_mapping.get('cube', 'ARCS_Cash'),
                "dimensions": {
                    "Account": oracle_mapping.get('account_filter', 'Cash_Total'),
                    "Period": filters.get('period', 'Current') if filters else 'Current'
                }
            }
            
            response = self.session.post(url, headers=headers, json=query)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_arcs_response(data, kpi_definition)
            else:
                logger.error(f"ARCS data retrieval failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get ARCS data: {e}")
            return []

    def get_fusion_financials_data(self, kpi_definition: KPIDefinition, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        try:
            url = urljoin(self.base_url, "/fscmRestApi/resources/11.13.18.05/gl/generalLedger/ledgers/balances")
            
            headers = {
                "Authorization": f"Basic {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            query_params = {
                "q": f"LedgerName='{filters.get('ledger', 'Primary_Ledger')}'" if filters else "LedgerName='Primary_Ledger'",
                "fields": "Amount,AccountCombination,PeriodName,CurrencyCode"
            }
            
            response = self.session.get(url, headers=headers, params=query_params)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_fusion_response(data, kpi_definition)
            else:
                logger.error(f"Fusion Financials data retrieval failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get Fusion Financials data: {e}")
            return []

    def _parse_fccs_response(self, data: Dict[str, Any], kpi_definition: KPIDefinition) -> List[Dict[str, Any]]:
        results = []
        
        for row in data.get('rows', []):
            result = {
                'kpi_id': kpi_definition.id,
                'name': kpi_definition.name,
                'value': row.get('value', 0),
                'unit': kpi_definition.unit,
                'currency': kpi_definition.currency,
                'time_period': row.get('period', 'YTD'),
                'metadata': {
                    'source': 'FCCS',
                    'account': row.get('account'),
                    'scenario': row.get('scenario'),
                    'entity': row.get('entity')
                }
            }
            results.append(result)
        
        return results

    def _parse_epbcs_response(self, data: Dict[str, Any], kpi_definition: KPIDefinition) -> List[Dict[str, Any]]:
        results = []
        actual_value = None
        plan_value = None
        
        for row in data.get('rows', []):
            if row.get('scenario') == 'Actual':
                actual_value = row.get('value', 0)
            elif row.get('scenario') == 'Plan':
                plan_value = row.get('value', 0)
        
        if actual_value is not None and plan_value is not None:
            variance = actual_value - plan_value
            result = {
                'kpi_id': kpi_definition.id,
                'name': kpi_definition.name,
                'value': variance,
                'unit': kpi_definition.unit,
                'currency': kpi_definition.currency,
                'time_period': data.get('period', 'YTD'),
                'variance_plan': variance,
                'metadata': {
                    'source': 'EPBCS',
                    'actual_value': actual_value,
                    'plan_value': plan_value
                }
            }
            results.append(result)
        
        return results

    def _parse_arcs_response(self, data: Dict[str, Any], kpi_definition: KPIDefinition) -> List[Dict[str, Any]]:
        results = []
        
        for row in data.get('rows', []):
            result = {
                'kpi_id': kpi_definition.id,
                'name': kpi_definition.name,
                'value': row.get('value', 0),
                'unit': kpi_definition.unit,
                'currency': kpi_definition.currency,
                'time_period': row.get('period', 'Current'),
                'metadata': {
                    'source': 'ARCS',
                    'account': row.get('account'),
                    'entity': row.get('entity')
                }
            }
            results.append(result)
        
        return results

    def _parse_fusion_response(self, data: Dict[str, Any], kpi_definition: KPIDefinition) -> List[Dict[str, Any]]:
        results = []
        
        for item in data.get('items', []):
            result = {
                'kpi_id': kpi_definition.id,
                'name': kpi_definition.name,
                'value': item.get('Amount', 0),
                'unit': kpi_definition.unit,
                'currency': item.get('CurrencyCode', 'USD'),
                'time_period': item.get('PeriodName', 'Current'),
                'metadata': {
                    'source': 'Fusion_Financials',
                    'account_combination': item.get('AccountCombination'),
                    'ledger': item.get('LedgerName')
                }
            }
            results.append(result)
        
        return results

    def test_connection(self) -> Dict[str, Any]:
        try:
            test_url = urljoin(self.base_url, "/HyperionPlanning/rest/v3/applications")
            
            headers = {
                "Authorization": f"Basic {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(test_url, headers=headers)
            
            return {
                "status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_drill_down_data(self, kpi_id: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            url = urljoin(self.base_url, f"/HyperionPlanning/rest/v3/applications/drilldown/{kpi_id}")
            
            headers = {
                "Authorization": f"Basic {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.post(url, headers=headers, json=filters)
            
            if response.status_code == 200:
                return response.json().get('detail_data', [])
            else:
                logger.error(f"Drill-down data retrieval failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get drill-down data: {e}")
            return []