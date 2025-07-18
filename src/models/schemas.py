from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class DatasetType(str, Enum):
    FOLHA = "folha"
    DESPESAS = "despesas"
    CONTRATOS = "contratos"

class WebhookData(BaseModel):
    """Schema for incoming webhook data from Apify"""
    dataset_id: str = Field(..., description="Dataset ID from Apify")
    dataset_type: DatasetType = Field(..., description="Type of dataset")
    run_id: str = Field(..., description="Apify run ID")
    status: str = Field(..., description="Run status")
    items_count: int = Field(..., description="Number of items in dataset")
    download_url: str = Field(..., description="URL to download the dataset")
    timestamp: datetime = Field(default_factory=datetime.now)

class IngestionResponse(BaseModel):
    """Response schema for ingestion endpoint"""
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    dataset_id: str = Field(..., description="Dataset ID")
    timestamp: datetime = Field(..., description="Response timestamp")

class IngestionStatus(BaseModel):
    """Schema for ingestion status"""
    dataset_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    records_processed: int = 0
    file_size: int = 0

class ExpenseRecord(BaseModel):
    """Schema for expense records"""
    id: str
    date: datetime
    supplier: str
    description: str
    amount: float
    category: str
    subcategory: Optional[str] = None
    catmat_code: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    department: str
    process_number: Optional[str] = None
    contract_number: Optional[str] = None
    is_emergency: bool = False
    
class PayrollRecord(BaseModel):
    """Schema for payroll records"""
    id: str
    employee_id: str
    name: str
    position: str
    department: str
    salary: float
    benefits: float
    total_payment: float
    date: datetime
    
class ContractRecord(BaseModel):
    """Schema for contract records"""
    id: str
    contract_number: str
    supplier: str
    description: str
    amount: float
    start_date: datetime
    end_date: Optional[datetime] = None
    category: str
    is_emergency: bool = False
    
class Alert(BaseModel):
    """Schema for generated alerts"""
    id: str
    rule_type: str
    title: str
    description: str
    risk_score: int = Field(..., ge=1, le=10)
    affected_records: List[str]
    created_at: datetime
    is_investigated: bool = False
    investigated_at: Optional[datetime] = None
    investigator: Optional[str] = None
    notes: Optional[str] = None
    
class AlertSummary(BaseModel):
    """Schema for alert summary with AI explanation"""
    alert_id: str
    summary: str
    citizen_explanation: str
    risk_assessment: str
    recommended_actions: List[str]
    
class NotificationRequest(BaseModel):
    """Schema for notification requests"""
    type: str = Field(..., description="Type of notification (email/telegram)")
    recipient: str = Field(..., description="Recipient identifier")
    subject: str = Field(..., description="Notification subject")
    message: str = Field(..., description="Notification message")
    attachments: Optional[List[str]] = None