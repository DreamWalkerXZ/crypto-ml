from pydantic import BaseModel, Field, validator, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime

class TradeLog(BaseModel):
    """Trade log entry"""
    timestamp: datetime
    type: str  # 'buy', 'sell', 'sell_forced'
    price: float  # Price
    shares: float  # Quantity
    fee_cash: float  # Transaction fee (in cash)
    cash_before: float  # Cash balance before transaction
    cash_after: float  # Cash balance after transaction
    reason: Optional[str] = None  # Transaction reason, e.g., 'signal', 'stop_loss'

class EquityPoint(BaseModel):
    """Equity curve data point"""
    time: datetime
    value: float  # Equity value
    position: int  # 0: no position, 1: long position
    shares: float  # Position size
    cash: float  # Cash balance

class BacktestMetrics(BaseModel):
    """Backtest performance metrics"""
    # Basic information
    timeframe: str
    annual_periods: int
    initial_balance: float
    final_balance: float
    
    # Return metrics
    total_return_pct: float
    annualized_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Risk metrics
    max_drawdown_pct: float
    max_drawdown_duration: int  # Maximum drawdown duration (in periods)
    volatility_pct: float  # Volatility
    
    # Trading metrics
    total_trades: int
    win_rate_pct: float
    profit_factor: float  # Profit factor
    avg_trade_return_pct: float  # Average return per trade
    avg_winning_trade_pct: float  # Average winning trade return
    avg_losing_trade_pct: float  # Average losing trade return
    
    # Position metrics
    avg_holding_period: int  # Average holding period (in periods)
    max_holding_period: int  # Maximum holding period
    min_holding_period: int  # Minimum holding period
    
    # Other metrics
    fee_rate: float
    total_fees: float
    consecutive_losses: int  # Maximum consecutive losses

class BacktestResult(BaseModel):
    """Backtest results"""
    metrics: BacktestMetrics
    trade_logs: List[TradeLog]
    equity_curve: List[EquityPoint]

class BacktestParams(BaseModel):
    """Backtest parameters"""
    symbol: str = Field(..., description="Trading pair, e.g., 'BTC/USDT'")
    timeframe: str = Field(..., description="Timeframe, e.g., '1h', '4h', '15m'")
    start_timestamp: str = Field(..., description="Start date in ISO 8601 format")
    end_timestamp: str = Field(..., description="End date in ISO 8601 format")
    ta_indicators: List[str] = Field(..., description="List of technical indicators")
    look_back: int = Field(..., gt=0, description="Number of past periods to use as input")
    prediction_horizon: int = Field(..., gt=0, description="Number of future periods to predict")
    price_change_threshold: float = Field(..., ge=0, description="Price change threshold for target variable")
    model_name: str = Field(..., description="Model name")
    model_params: Optional[Dict[str, Any]] = Field(None, description="Model parameters")
    retrain_interval: int = Field(..., gt=0, description="Model retraining interval")
    window_size: int = Field(..., gt=0, description="Rolling training window size")
    buy_threshold: float = Field(..., ge=0, le=1.0, description="Buy signal threshold")
    sell_threshold: float = Field(..., ge=0, le=1.0, description="Sell signal threshold")
    stop_loss_pct: float = Field(..., ge=0, le=1, description="Stop loss percentage")
    initial_balance: float = Field(..., gt=0, description="Initial capital")
    transaction_fee: float = Field(..., ge=0, le=1, description="Transaction fee rate")
    max_position_size: Optional[float] = Field(None, gt=0, description="Maximum position size")
    min_position_size: Optional[float] = Field(None, gt=0, description="Minimum position size")
    risk_free_rate: float = Field(0.0, ge=0, le=1, description="Risk-free rate")
    slippage: float = Field(0.0, ge=0, le=1, description="Slippage rate")

    @field_validator('timeframe')
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        """Validate timeframe format"""
        valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        if v not in valid_timeframes:
            raise ValueError(f"Invalid timeframe. Must be one of: {valid_timeframes}")
        return v

class AvailableModelsResponse(BaseModel):
    """Available models list"""
    models: List[str]

class AvailableIndicatorsResponse(BaseModel):
    """Available indicators list"""
    indicators: List[str] 