import chromadb
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
from sentence_transformers import SentenceTransformer

from ..models import KPIDefinition, KPICategory, CalculationType, UserRole
from ...monitoring.logger import logger


class MetricCatalog:
    def __init__(self, chroma_db_path: str = "./chroma_db"):
        self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="kpi_definitions",
            metadata={"description": "KPI definitions and metadata"}
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._init_default_kpis()

    def _init_default_kpis(self):
        default_kpis = [
            {
                "id": "revenue_total",
                "name": "Total Revenue",
                "description": "Total revenue including all income streams",
                "category": KPICategory.REVENUE,
                "calculation_type": CalculationType.SUM,
                "formula": "SUM(revenue_accounts)",
                "unit": "currency",
                "currency": "USD",
                "data_sources": ["oracle_fusion_financials", "fccs"],
                "refresh_frequency": "daily",
                "owner": "finance_team",
                "tags": ["revenue", "income", "sales", "total"],
                "access_roles": [UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN],
                "oracle_mapping": {
                    "source_system": "FCCS",
                    "cube": "FCCS_Revenue",
                    "account_filter": "Revenue_Total",
                    "scenario": "Actual"
                }
            },
            {
                "id": "gross_margin_pct",
                "name": "Gross Margin %",
                "description": "Gross margin as percentage of revenue",
                "category": KPICategory.MARGIN,
                "calculation_type": CalculationType.PERCENTAGE,
                "formula": "(Total_Revenue - COGS) / Total_Revenue * 100",
                "unit": "percentage",
                "data_sources": ["oracle_fusion_financials", "fccs"],
                "refresh_frequency": "daily",
                "owner": "finance_team",
                "tags": ["margin", "profitability", "gross", "percentage"],
                "access_roles": [UserRole.VIEWER, UserRole.ANALYST, UserRole.ADMIN],
                "oracle_mapping": {
                    "source_system": "FCCS",
                    "cube": "FCCS_Profitability",
                    "formula": "calc_gross_margin_pct"
                }
            },
            {
                "id": "opex_variance",
                "name": "OPEX Variance",
                "description": "Operating expenses variance vs plan",
                "category": KPICategory.VARIANCE,
                "calculation_type": CalculationType.VARIANCE,
                "formula": "Actual_OPEX - Plan_OPEX",
                "unit": "currency",
                "currency": "USD",
                "data_sources": ["epbcs", "fccs"],
                "refresh_frequency": "daily",
                "owner": "finance_team",
                "tags": ["opex", "variance", "expenses", "operational"],
                "access_roles": [UserRole.ANALYST, UserRole.ADMIN],
                "oracle_mapping": {
                    "source_system": "EPBCS",
                    "cube": "EPBCS_Expenses",
                    "account_filter": "OPEX_Total",
                    "scenario_actual": "Actual",
                    "scenario_plan": "Plan"
                }
            },
            {
                "id": "cash_position",
                "name": "Cash Position",
                "description": "Current cash and cash equivalents",
                "category": KPICategory.CASH,
                "calculation_type": CalculationType.SUM,
                "formula": "SUM(cash_accounts)",
                "unit": "currency",
                "currency": "USD",
                "data_sources": ["oracle_fusion_financials", "arcs"],
                "refresh_frequency": "daily",
                "owner": "treasury_team",
                "tags": ["cash", "liquidity", "position", "treasury"],
                "access_roles": [UserRole.ANALYST, UserRole.ADMIN],
                "oracle_mapping": {
                    "source_system": "ARCS",
                    "cube": "ARCS_Cash",
                    "account_filter": "Cash_Total"
                }
            }
        ]
        
        for kpi_data in default_kpis:
            if not self.get_kpi_by_id(kpi_data["id"]):
                kpi = KPIDefinition(
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    is_active=True,
                    **kpi_data
                )
                self.add_kpi(kpi)

    def add_kpi(self, kpi: KPIDefinition) -> bool:
        try:
            kpi_text = f"{kpi.name} {kpi.description} {' '.join(kpi.tags)}"
            embedding = self.model.encode([kpi_text])[0].tolist()
            
            self.collection.add(
                ids=[kpi.id],
                embeddings=[embedding],
                documents=[kpi_text],
                metadatas=[{
                    "name": kpi.name,
                    "description": kpi.description,
                    "category": kpi.category.value,
                    "calculation_type": kpi.calculation_type.value,
                    "formula": kpi.formula,
                    "unit": kpi.unit,
                    "currency": kpi.currency,
                    "data_sources": json.dumps(kpi.data_sources),
                    "refresh_frequency": kpi.refresh_frequency,
                    "owner": kpi.owner,
                    "tags": json.dumps(kpi.tags),
                    "access_roles": json.dumps([role.value for role in kpi.access_roles]),
                    "oracle_mapping": json.dumps(getattr(kpi, 'oracle_mapping', {})),
                    "created_at": kpi.created_at.isoformat(),
                    "updated_at": kpi.updated_at.isoformat(),
                    "is_active": str(kpi.is_active)
                }]
            )
            
            logger.info(f"Added KPI to catalog: {kpi.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add KPI to catalog: {e}")
            return False

    def search_kpis(self, query: str, user_role: UserRole, limit: int = 10) -> List[KPIDefinition]:
        try:
            query_embedding = self.model.encode([query])[0].tolist()
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where={"is_active": "True"}
            )
            
            kpis = []
            for i, metadata in enumerate(results['metadatas'][0]):
                access_roles = json.loads(metadata['access_roles'])
                if user_role.value in access_roles:
                    kpi = self._metadata_to_kpi(metadata, results['ids'][0][i])
                    kpis.append(kpi)
            
            return kpis
            
        except Exception as e:
            logger.error(f"Failed to search KPIs: {e}")
            return []

    def get_kpi_by_id(self, kpi_id: str) -> Optional[KPIDefinition]:
        try:
            results = self.collection.get(ids=[kpi_id])
            if results['ids']:
                metadata = results['metadatas'][0]
                return self._metadata_to_kpi(metadata, kpi_id)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get KPI by ID: {e}")
            return None

    def get_kpis_by_category(self, category: KPICategory, user_role: UserRole) -> List[KPIDefinition]:
        try:
            results = self.collection.get(
                where={
                    "category": category.value,
                    "is_active": "True"
                }
            )
            
            kpis = []
            for i, metadata in enumerate(results['metadatas']):
                access_roles = json.loads(metadata['access_roles'])
                if user_role.value in access_roles:
                    kpi = self._metadata_to_kpi(metadata, results['ids'][i])
                    kpis.append(kpi)
            
            return kpis
            
        except Exception as e:
            logger.error(f"Failed to get KPIs by category: {e}")
            return []

    def update_kpi(self, kpi: KPIDefinition) -> bool:
        try:
            kpi.updated_at = datetime.now()
            
            kpi_text = f"{kpi.name} {kpi.description} {' '.join(kpi.tags)}"
            embedding = self.model.encode([kpi_text])[0].tolist()
            
            self.collection.update(
                ids=[kpi.id],
                embeddings=[embedding],
                documents=[kpi_text],
                metadatas=[{
                    "name": kpi.name,
                    "description": kpi.description,
                    "category": kpi.category.value,
                    "calculation_type": kpi.calculation_type.value,
                    "formula": kpi.formula,
                    "unit": kpi.unit,
                    "currency": kpi.currency,
                    "data_sources": json.dumps(kpi.data_sources),
                    "refresh_frequency": kpi.refresh_frequency,
                    "owner": kpi.owner,
                    "tags": json.dumps(kpi.tags),
                    "access_roles": json.dumps([role.value for role in kpi.access_roles]),
                    "oracle_mapping": json.dumps(getattr(kpi, 'oracle_mapping', {})),
                    "created_at": kpi.created_at.isoformat(),
                    "updated_at": kpi.updated_at.isoformat(),
                    "is_active": str(kpi.is_active)
                }]
            )
            
            logger.info(f"Updated KPI in catalog: {kpi.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update KPI: {e}")
            return False

    def delete_kpi(self, kpi_id: str) -> bool:
        try:
            self.collection.delete(ids=[kpi_id])
            logger.info(f"Deleted KPI from catalog: {kpi_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete KPI: {e}")
            return False

    def get_all_kpis(self, user_role: UserRole) -> List[KPIDefinition]:
        try:
            results = self.collection.get(where={"is_active": "True"})
            
            kpis = []
            for i, metadata in enumerate(results['metadatas']):
                access_roles = json.loads(metadata['access_roles'])
                if user_role.value in access_roles:
                    kpi = self._metadata_to_kpi(metadata, results['ids'][i])
                    kpis.append(kpi)
            
            return kpis
            
        except Exception as e:
            logger.error(f"Failed to get all KPIs: {e}")
            return []

    def _metadata_to_kpi(self, metadata: Dict[str, Any], kpi_id: str) -> KPIDefinition:
        return KPIDefinition(
            id=kpi_id,
            name=metadata['name'],
            description=metadata['description'],
            category=KPICategory(metadata['category']),
            calculation_type=CalculationType(metadata['calculation_type']),
            formula=metadata['formula'],
            unit=metadata['unit'],
            currency=metadata.get('currency'),
            data_sources=json.loads(metadata['data_sources']),
            refresh_frequency=metadata['refresh_frequency'],
            owner=metadata['owner'],
            tags=json.loads(metadata['tags']),
            access_roles=[UserRole(role) for role in json.loads(metadata['access_roles'])],
            created_at=datetime.fromisoformat(metadata['created_at']),
            updated_at=datetime.fromisoformat(metadata['updated_at']),
            is_active=metadata['is_active'] == 'True'
        )

    def get_kpi_suggestions(self, partial_query: str, user_role: UserRole, limit: int = 5) -> List[str]:
        try:
            kpis = self.search_kpis(partial_query, user_role, limit)
            return [kpi.name for kpi in kpis]
            
        except Exception as e:
            logger.error(f"Failed to get KPI suggestions: {e}")
            return []