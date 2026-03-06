# Crypto ML Backend

FastAPI-based backend service for cryptocurrency trading strategy backtesting with machine learning prediction capabilities.

## Features

- **Market Data Service**: Fetch OHLCV data from Binance via CCXT
- **ML Model Support**: 7 built-in models (CatBoost, XGBoost, Random Forest, Logistic Regression, PyTorch MLP/LSTM/GRU)
- **Backtesting Engine**: Rolling window backtesting with periodic model retraining
- **Task Management**: Async task execution for long-running backtests
- **SQLite Storage**: Persistent data storage for market data and backtest results

## Requirements

- Python 3.12+
- uv (Python package manager)

## Installation

```bash
# Install dependencies
uv sync
```

## Running

```bash
# Development server with auto-reload
uv run python run.py
```

The API will be available at `http://0.0.0.0:8000`

## API Documentation

Interactive API documentation available at:

- Swagger UI: `http://0.0.0.0:8000/docs`
- ReDoc: `http://0.0.0.0:8000/redoc`

## Project Structure

```text
app/
├── main.py                    # FastAPI application entry point
├── api/endpoints/             # API route handlers
│   ├── data.py               # Data fetching endpoints
│   ├── backtest.py           # Backtest execution endpoints
│   └── models.py             # Model information endpoints
├── core/                      # Business logic services
│   ├── data_service.py       # Market data fetching
│   ├── modeling_service.py   # Model factory
│   ├── backtesting_service.py # Backtest execution
│   ├── preprocessing_service.py # Feature engineering
│   ├── task_service.py       # Async task management
│   └── model_wrappers/       # ML model implementations
├── db/                        # Database layer
│   ├── database.py           # Database engines
│   └── models.py             # ORM models
└── schemas/                   # Pydantic schemas
    ├── backtest.py
    ├── data.py
    ├── models.py
    └── common.py
```

## Database

Two SQLite databases are created in the `data/` directory:

- **crypto_data.db**: Stores OHLCV market data
  - `ohlcv_data`: Market data with (symbol, timeframe, timestamp) index

- **backtest_results.db**: Stores backtest parameters and results
  - `backtest_params`: Configuration parameters (UUID primary key)
  - `backtest_results`: Performance metrics, trade logs, equity curves

## Environment Variables

| Variable  | Default  | Description             |
| --------- | -------- | ----------------------- |
| `DB_PATH` | `./data` | Database directory path |

## API Endpoints

### Data

| Method | Endpoint              | Description                 |
| ------ | --------------------- | --------------------------- |
| GET    | `/api/data/available` | List available data ranges  |
| POST   | `/api/data/fetch`     | Fetch and store market data |
| GET    | `/api/data/ohlcv`     | Get OHLCV data for a range  |

### Models

| Method | Endpoint             | Description              |
| ------ | -------------------- | ------------------------ |
| GET    | `/api/models`        | List available ML models |
| GET    | `/api/models/{name}` | Get model information    |

### Backtest

| Method | Endpoint                     | Description                      |
| ------ | ---------------------------- | -------------------------------- |
| POST   | `/api/backtest/run`          | Run a backtest (returns task_id) |
| GET    | `/api/backtest/tasks`        | List all tasks                   |
| GET    | `/api/backtest/tasks/{id}`   | Get task status                  |
| GET    | `/api/backtest/results`      | List all backtest results        |
| GET    | `/api/backtest/results/{id}` | Get specific backtest result     |

## Adding New Models

1. Create a wrapper in `app/core/model_wrappers/` implementing `BaseClassifierModel`:

```python
from app.core.modeling_service import BaseClassifierModel
import pandas as pd
import numpy as np

class MyModelWrapper:
    def __init__(self, **params):
        self.model = MyModel(**params)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self.model.fit(X, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(X)
```

1. Register in `app/core/modeling_service.py`:

```python
from .model_wrappers.my_model import MyModelWrapper

def get_model(model_name: str, input_size: Optional[int] = None, **params):
    model_map = {
        # ... existing models
        "MyModel": MyModelWrapper,
    }
    # ...
```

1. Add model info in `app/api/endpoints/models.py` if needed

## License

This project is licensed under the GNU General Public License v3.0 - see the [COPYING](../COPYING) file for details.
