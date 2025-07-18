from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import uuid

from ..models import (
    KPIQuery, KPIResponse, KPIResult, KPIDefinition, 
    User, UserRole, SubscriptionTier
)
from ..auth.auth_manager import AuthManager
from ..chat.intent_detector import IntentDetector
from ..catalog.metric_catalog import MetricCatalog
from ..oracle.epm_connector import OracleEPMConnector
from ..calculations.kpi_engine import KPICalculationEngine
from ..chat.narrative_generator import NarrativeGenerator
from ..visualizations.chart_generator import ChartGenerator
from ...monitoring.logger import logger

router = APIRouter(prefix="/api/v1/kpi", tags=["KPI"])

auth_manager = AuthManager(secret_key="your-secret-key")
intent_detector = IntentDetector(openai_api_key="your-openai-key")
metric_catalog = MetricCatalog()
narrative_generator = NarrativeGenerator(openai_api_key="your-openai-key")


@router.post("/query", response_model=KPIResponse)
async def query_kpi(
    query: KPIQuery,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    try:
        start_time = datetime.now()
        
        user_role = UserRole(current_user["role"])
        available_kpis = metric_catalog.get_all_kpis(user_role)
        
        intent_analysis = intent_detector.detect_intent(query.query_text, available_kpis)
        
        if not intent_analysis["detected_kpis"]:
            return KPIResponse(
                query_id=str(uuid.uuid4()),
                user_id=current_user["user_id"],
                kpi_results=[],
                narrative_summary="I couldn't find any matching KPIs for your query. Please try rephrasing or check available KPIs.",
                processing_time=0.1,
                suggestions=["Show available KPIs", "Try a different query", "Contact support"]
            )
        
        kpi_results = []
        for detected_kpi in intent_analysis["detected_kpis"][:3]:  # Limit to top 3
            kpi_definition = metric_catalog.get_kpi_by_id(detected_kpi["kpi_id"])
            if kpi_definition:
                try:
                    oracle_connection = _get_oracle_connection()
                    epm_connector = OracleEPMConnector(oracle_connection)
                    kpi_engine = KPICalculationEngine(epm_connector)
                    
                    result = kpi_engine.calculate_kpi(kpi_definition, query.filters)
                    kpi_results.append(result)
                    
                except Exception as e:
                    logger.error(f"Failed to calculate KPI {kpi_definition.name}: {e}")
                    continue
        
        narrative_summary = narrative_generator.generate_narrative(kpi_results, query)
        suggestions = narrative_generator.generate_suggestions(kpi_results, query)
        
        chart_generator = ChartGenerator()
        chart_data = chart_generator.generate_chart_data(kpi_results)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = KPIResponse(
            query_id=str(uuid.uuid4()),
            user_id=current_user["user_id"],
            kpi_results=kpi_results,
            narrative_summary=narrative_summary,
            chart_data=chart_data,
            processing_time=processing_time,
            suggestions=suggestions
        )
        
        _log_query(query, response, current_user)
        
        return response
        
    except Exception as e:
        logger.error(f"KPI query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )


@router.get("/definitions", response_model=List[KPIDefinition])
async def get_kpi_definitions(
    category: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    try:
        user_role = UserRole(current_user["role"])
        
        if category:
            from ..models import KPICategory
            kpi_category = KPICategory(category)
            kpis = metric_catalog.get_kpis_by_category(kpi_category, user_role)
        else:
            kpis = metric_catalog.get_all_kpis(user_role)
        
        return kpis
        
    except Exception as e:
        logger.error(f"Failed to get KPI definitions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KPI definitions"
        )


@router.get("/definitions/{kpi_id}", response_model=KPIDefinition)
async def get_kpi_definition(
    kpi_id: str,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    try:
        kpi_definition = metric_catalog.get_kpi_by_id(kpi_id)
        
        if not kpi_definition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KPI not found"
            )
        
        user_role = UserRole(current_user["role"])
        if user_role not in kpi_definition.access_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this KPI"
            )
        
        return kpi_definition
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get KPI definition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KPI definition"
        )


@router.post("/definitions", response_model=KPIDefinition)
@auth_manager.require_role(UserRole.ADMIN)
async def create_kpi_definition(
    kpi_definition: KPIDefinition,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    try:
        kpi_definition.id = str(uuid.uuid4())
        kpi_definition.created_at = datetime.now()
        kpi_definition.updated_at = datetime.now()
        kpi_definition.owner = current_user["user_id"]
        
        success = metric_catalog.add_kpi(kpi_definition)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create KPI definition"
            )
        
        return kpi_definition
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create KPI definition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create KPI definition"
        )


@router.put("/definitions/{kpi_id}", response_model=KPIDefinition)
@auth_manager.require_role(UserRole.ADMIN)
async def update_kpi_definition(
    kpi_id: str,
    kpi_definition: KPIDefinition,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    try:
        existing_kpi = metric_catalog.get_kpi_by_id(kpi_id)
        
        if not existing_kpi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KPI not found"
            )
        
        kpi_definition.id = kpi_id
        kpi_definition.updated_at = datetime.now()
        
        success = metric_catalog.update_kpi(kpi_definition)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update KPI definition"
            )
        
        return kpi_definition
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update KPI definition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update KPI definition"
        )


@router.delete("/definitions/{kpi_id}")
@auth_manager.require_role(UserRole.ADMIN)
async def delete_kpi_definition(
    kpi_id: str,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    try:
        existing_kpi = metric_catalog.get_kpi_by_id(kpi_id)
        
        if not existing_kpi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KPI not found"
            )
        
        success = metric_catalog.delete_kpi(kpi_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete KPI definition"
            )
        
        return {"message": "KPI definition deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete KPI definition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete KPI definition"
        )


@router.get("/drill-down")
async def get_drill_down_data(
    kpi_id: str,
    filters: str = "{}",
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    try:
        import json
        filter_dict = json.loads(filters)
        
        kpi_definition = metric_catalog.get_kpi_by_id(kpi_id)
        if not kpi_definition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="KPI not found"
            )
        
        user_role = UserRole(current_user["role"])
        if user_role not in kpi_definition.access_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this KPI"
            )
        
        oracle_connection = _get_oracle_connection()
        epm_connector = OracleEPMConnector(oracle_connection)
        
        drill_down_data = epm_connector.get_drill_down_data(kpi_id, filter_dict)
        
        return {"drill_down_data": drill_down_data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get drill-down data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve drill-down data"
        )


@router.get("/suggestions")
async def get_kpi_suggestions(
    q: str,
    current_user: Dict[str, Any] = Depends(auth_manager.get_current_user)
):
    try:
        user_role = UserRole(current_user["role"])
        suggestions = metric_catalog.get_kpi_suggestions(q, user_role)
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Failed to get KPI suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve suggestions"
        )


def _get_oracle_connection():
    from ..models import OracleConnection
    
    return OracleConnection(
        id="default",
        name="Default Oracle Connection",
        connection_type="EPM",
        host="your-epm-host.com",
        port=443,
        service_name="FCCS",
        username="your-username",
        password="your-password"
    )


def _log_query(query: KPIQuery, response: KPIResponse, user: Dict[str, Any]):
    from ..models import AuditLog
    
    audit_log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user["user_id"],
        action="kpi_query",
        resource_type="kpi",
        resource_id=response.query_id,
        details={
            "query_text": query.query_text,
            "kpi_count": len(response.kpi_results),
            "processing_time": response.processing_time,
            "filters": query.filters
        }
    )
    
    logger.info(f"KPI query logged: {audit_log.id}")