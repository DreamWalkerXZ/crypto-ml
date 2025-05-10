from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DataFetchRequest(BaseModel):
    """Request model for fetching market data"""
    symbol: str = Field(..., json_schema_extra={"example": "BTC/USDT"})
    timeframe: str = Field(..., json_schema_extra={"example": "1h"})
    start_timestamp: datetime = Field(..., json_schema_extra={"example": "2023-01-01T00:00:00Z"})
    end_timestamp: datetime = Field(..., json_schema_extra={"example": "2024-01-01T00:00:00Z"})

class AvailableDataResponse(BaseModel):
    """Response model for available data ranges"""
    symbol: str
    timeframe: str
    start_timestamp: datetime
    end_timestamp: datetime
    data_points: int

class OHLCVData(BaseModel):
    """Model for OHLCV (Open, High, Low, Close, Volume) market data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float 