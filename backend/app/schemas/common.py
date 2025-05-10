from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime

class ErrorResponse(BaseModel):
    """Generic error response model"""
    error: str
    detail: Optional[str] = None

class TimeRange(BaseModel):
    """Generic time range model"""
    start: datetime
    end: datetime

class PaginationParams(BaseModel):
    """Generic pagination parameters"""
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)

class PaginatedResponse(BaseModel):
    """Generic paginated response model"""
    total: int
    page: int
    page_size: int
    items: List[Any]

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    """Unified API response model"""
    success: bool
    data: Optional[T] = None
    message: str = "" 