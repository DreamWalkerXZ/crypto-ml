from sqlalchemy import Column, Integer, String, Float, DateTime, Index, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from .database import CryptoBase, BacktestBase

class OHLCVData(CryptoBase):
    """
    Model for storing OHLCV (Open, High, Low, Close, Volume) market data.
    
    This class represents the database table for storing cryptocurrency market data
    with timestamps and trading information.
    """
    __tablename__ = "ohlcv_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timeframe = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Create composite index and unique constraint
    __table_args__ = (
        Index('idx_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp', unique=True),
    )

    def __repr__(self):
        return f"<OHLCVData(symbol={self.symbol}, timeframe={self.timeframe}, timestamp={self.timestamp})>"

class BacktestParams(BacktestBase):
    """
    Model for storing backtesting parameters.
    
    This class represents the database table for storing configuration parameters
    used in backtesting strategies, including model settings and trading rules.
    """
    __tablename__ = "backtest_params"

    id = Column(String, primary_key=True, index=True)  # UUID as primary key
    symbol = Column(String, index=True)
    timeframe = Column(String)
    start_timestamp = Column(DateTime)
    end_timestamp = Column(DateTime)
    ta_indicators = Column(JSON)  # List of technical indicators
    look_back = Column(Integer)
    prediction_horizon = Column(Integer)
    price_change_threshold = Column(Float)
    model_name = Column(String)
    model_params = Column(JSON)  # Model configuration parameters
    retrain_interval = Column(Integer)
    window_size = Column(Integer)  # Training window size
    buy_threshold = Column(Float)
    sell_threshold = Column(Float)
    stop_loss_pct = Column(Float)
    initial_balance = Column(Float)
    transaction_fee = Column(Float)
    slippage = Column(Float)
    risk_free_rate = Column(Float)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<BacktestParams(id={self.id}, symbol={self.symbol}, model={self.model_name})>"

class BacktestResult(BacktestBase):
    """
    Model for storing backtesting results.
    
    This class represents the database table for storing comprehensive backtesting
    results, including performance metrics, trading statistics, and equity curves.
    """
    __tablename__ = "backtest_results"

    id = Column(String, primary_key=True, index=True)  # UUID as primary key
    params_id = Column(String, ForeignKey('backtest_params.id'), index=True)
    
    # Basic information
    timeframe = Column(String)
    annual_periods = Column(Integer)
    initial_balance = Column(Float)
    final_balance = Column(Float)
    
    # Return metrics
    total_return_pct = Column(Float)
    annualized_return_pct = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    calmar_ratio = Column(Float)
    
    # Risk metrics
    max_drawdown_pct = Column(Float)
    max_drawdown_duration = Column(Integer)
    volatility_pct = Column(Float)
    
    # Trading metrics
    total_trades = Column(Integer)
    win_rate_pct = Column(Float)
    profit_factor = Column(Float)
    avg_trade_return_pct = Column(Float)
    avg_winning_trade_pct = Column(Float)
    avg_losing_trade_pct = Column(Float)
    
    # Position metrics
    avg_holding_period = Column(Integer)
    max_holding_period = Column(Integer)
    min_holding_period = Column(Integer)
    
    # Additional metrics
    fee_rate = Column(Float)
    total_fees = Column(Float)
    consecutive_losses = Column(Integer)
    
    # Trading records and equity curve
    trade_logs = Column(JSON)  # Trading records
    equity_curve = Column(JSON)  # Equity curve data
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<BacktestResult(id={self.id}, params_id={self.params_id})>" 