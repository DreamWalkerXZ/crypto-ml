from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import os

# Get database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
os.makedirs(DB_PATH, exist_ok=True)

# Database URLs
CRYPTO_DB_URL = f"sqlite:///{os.path.join(DB_PATH, 'crypto_data.db')}"
BACKTEST_DB_URL = f"sqlite:///{os.path.join(DB_PATH, 'backtest_results.db')}"

# Create database engine for cryptocurrency data
crypto_engine = create_engine(
    CRYPTO_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

# Create database engine for backtest results
backtest_engine = create_engine(
    BACKTEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

# Create session factories
CryptoSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=crypto_engine)
BacktestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=backtest_engine)

# Create base model classes
CryptoBase = declarative_base()
BacktestBase = declarative_base()

def get_crypto_db():
    """Get a database session for cryptocurrency data"""
    db = CryptoSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_backtest_db():
    """Get a database session for backtest results"""
    db = BacktestSessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_crypto_db():
    """Initialize the cryptocurrency database"""
    try:
        CryptoBase.metadata.create_all(bind=crypto_engine)
    except Exception as e:
        raise Exception(f"Failed to initialize cryptocurrency database: {str(e)}")

def init_backtest_db():
    """Initialize the backtest results database"""
    try:
        BacktestBase.metadata.create_all(bind=backtest_engine)
    except Exception as e:
        raise Exception(f"Failed to initialize backtest results database: {str(e)}") 