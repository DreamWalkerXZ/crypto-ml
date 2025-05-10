from fastapi import APIRouter
from . import data, backtest, models

# Create main API router
api_router = APIRouter()

# Register sub-routers with their respective prefixes and tags
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
