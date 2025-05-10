from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import api_router, data, backtest
from app.db.database import init_crypto_db, init_backtest_db

# Initialize FastAPI application
app = FastAPI(
    title="Crypto ML Backend",
    description="Backend API for cryptocurrency price direction prediction and backtesting platform",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize databases
init_crypto_db()
init_backtest_db()

# Register API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to Crypto ML Backend API"} 