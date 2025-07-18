from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class KPICategory(str, Enum):
    REVENUE = "revenue"
    EXPENSES = "expenses"
    CASH = "cash"
    MARGIN = "margin"
    VARIANCE = "variance"


class CalculationType(str, Enum):
    SUM = "sum"
    AVERAGE = "average"
    PERCENTAGE = "percentage"
    VARIANCE = "variance"
    RATIO = "ratio"


class AlertType(str, Enum):
    THRESHOLD = "threshold"
    ANOMALY = "anomaly"
    TREND = "trend"


class SubscriptionTier(str, Enum):
    BASIC = "basic"
    ADVANCED = "advanced"
    ENTERPRISE = "enterprise"


class User(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    subscription_tier: SubscriptionTier
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


class KPIDefinition(BaseModel):
    id: str
    name: str
    description: str
    category: KPICategory
    calculation_type: CalculationType
    formula: str
    unit: str
    currency: Optional[str] = None
    data_sources: List[str]
    refresh_frequency: str
    owner: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    access_roles: List[UserRole]
    tags: List[str] = []


class KPIQuery(BaseModel):
    user_id: str
    query_text: str
    intent: Optional[str] = None
    kpi_id: Optional[str] = None
    filters: Dict[str, Any] = {}
    time_range: Optional[Dict[str, str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class KPIResult(BaseModel):
    kpi_id: str
    name: str
    value: Union[float, int, str]
    unit: str
    currency: Optional[str] = None
    time_period: str
    calculation_date: datetime
    variance_py: Optional[float] = None
    variance_plan: Optional[float] = None
    variance_fx_neutral: Optional[float] = None
    drill_down_url: Optional[str] = None
    metadata: Dict[str, Any] = {}


class KPIResponse(BaseModel):
    query_id: str
    user_id: str
    kpi_results: List[KPIResult]
    narrative_summary: str
    chart_data: Optional[Dict[str, Any]] = None
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)
    suggestions: List[str] = []


class AlertRule(BaseModel):
    id: str
    name: str
    kpi_id: str
    alert_type: AlertType
    threshold_value: Optional[float] = None
    comparison_operator: Optional[str] = None
    notification_channels: List[str]
    is_active: bool = True
    created_by: str
    created_at: datetime
    last_triggered: Optional[datetime] = None


class AlertInstance(BaseModel):
    id: str
    rule_id: str
    kpi_id: str
    triggered_at: datetime
    value: float
    threshold: Optional[float] = None
    severity: str
    message: str
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class AuditLog(BaseModel):
    id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ChatSession(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    is_active: bool = True
    queries: List[KPIQuery] = []


class OracleConnection(BaseModel):
    id: str
    name: str
    connection_type: str
    host: str
    port: int
    service_name: str
    username: str
    password: str
    is_active: bool = True
    last_tested: Optional[datetime] = None
    test_status: Optional[str] = None