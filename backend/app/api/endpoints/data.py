from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_crypto_db
from app.core.data_service import DataService
from app.schemas.data import DataFetchRequest, AvailableDataResponse
from app.schemas.common import ResponseModel

# Create router for data-related endpoints
router = APIRouter()

@router.post("/fetch", response_model=ResponseModel[dict])
async def fetch_data(request: DataFetchRequest, db: Session = Depends(get_crypto_db)):
    """Fetch market data from exchange and store in database"""
    data_service = DataService(db)
    return data_service.fetch_and_store_data(request)

@router.get("/available", response_model=ResponseModel[list[AvailableDataResponse]])
async def get_available_data(db: Session = Depends(get_crypto_db)):
    """Get available data ranges from database"""
    data_service = DataService(db)
    return data_service.get_available_data()

@router.get("/ohlcv")
async def get_ohlcv_data(
    symbol: str,
    timeframe: str,
    start_timestamp: str,
    end_timestamp: str,
    db: Session = Depends(get_crypto_db)
):
    """Get OHLCV data for specified time range"""
    from datetime import datetime
    start = datetime.fromisoformat(start_timestamp)
    end = datetime.fromisoformat(end_timestamp)
    data_service = DataService(db)
    return data_service.get_ohlcv_data(symbol, timeframe, start, end) 