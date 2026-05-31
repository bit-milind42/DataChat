from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class DatasetResponse(BaseModel):
    id: str
    name: str
    filename: str
    rowCount: int
    columns: List[str]
    uploadedAt: str


class QueryResultResponse(BaseModel):
    id: str
    query: str
    rows: List[dict]
    columns: List[str]
    executionTime: int


class MessageResponse(BaseModel):
    id: str
    content: str
    sender: str  # 'user' or 'assistant'
    timestamp: str


class ChatHistoryResponse(BaseModel):
    messages: List[MessageResponse]
    datasetId: str
    createdAt: str
    updatedAt: str


class QueryRequest(BaseModel):
    datasetId: str
    question: str


class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    message: Optional[str] = None


# ========== DASHBOARD SCHEMAS ==========

class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dataset_ids: Optional[List[str]] = None
    is_public: Optional[bool] = False


class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dataset_ids: Optional[List[str]] = None
    layout: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class WidgetCreate(BaseModel):
    title: str
    widget_type: str  # chart, table, kpi, metric
    position_x: Optional[int] = 0
    position_y: Optional[int] = 0
    width: Optional[int] = 4
    height: Optional[int] = 3
    config: Optional[Dict[str, Any]] = None
    query_id: Optional[str] = None


class WidgetUpdate(BaseModel):
    title: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


# ========== SCHEDULED REPORT SCHEMAS ==========

class ScheduledReportCreate(BaseModel):
    name: str
    description: Optional[str] = None
    schedule: str  # cron expression
    frequency: str  # daily, weekly, monthly
    recipients: Optional[List[str]] = None
    format: Optional[str] = "pdf"  # pdf, excel, html
    include_insights: Optional[bool] = True
    is_active: Optional[bool] = True


class ScheduledReportUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schedule: Optional[str] = None
    recipients: Optional[List[str]] = None
    is_active: Optional[bool] = None


# ========== USER & TEAM SCHEMAS ==========

class UserCreate(BaseModel):
    email: str
    password: str  # Required for signup/login
    name: Optional[str] = None
    role: Optional[str] = "user"


class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None


# ========== SAVED QUERY SCHEMAS ==========

class SavedQueryCreate(BaseModel):
    name: str
    dataset_id: str
    question: str
    query_result_id: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = False
