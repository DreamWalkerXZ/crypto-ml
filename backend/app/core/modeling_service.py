from typing import Any, Dict, Optional, Protocol, runtime_checkable
from abc import abstractmethod
import numpy as np
import pandas as pd

@runtime_checkable
class BaseClassifierModel(Protocol):
    """Base classifier model protocol defining required methods"""
    
    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train the model"""
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class labels"""
        pass
    
    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict class probabilities"""
        pass

from .model_wrappers.catboost_model import CatBoostModelWrapper
from .model_wrappers.xgboost_model import XGBoostModelWrapper
from .model_wrappers.logistic_regression_model import LogisticRegressionModelWrapper
from .model_wrappers.random_forest_model import RandomForestModelWrapper
from .model_wrappers.pytorch_mlp import PyTorchMLPWrapper
from .model_wrappers.pytorch_lstm import PyTorchLSTMWrapper
from .model_wrappers.pytorch_gru import PyTorchGRUWrapper

def get_model(model_name: str, input_size: Optional[int] = None, **params: Dict[str, Any]) -> BaseClassifierModel:
    """
    Create a model instance based on model name and parameters
    
    Args:
        model_name: Model name, supported values: "CatBoost", "XGBoost", "LogisticRegression", 
                   "RandomForest", "PyTorchMLP", "PyTorchLSTM", "PyTorchGRU"
        input_size: Input feature dimension, required only for PyTorch models
        **params: Model-specific parameters
    
    Returns:
        BaseClassifierModel instance
    """
    model_map = {
        "CatBoost": CatBoostModelWrapper,
        "XGBoost": XGBoostModelWrapper,
        "LogisticRegression": LogisticRegressionModelWrapper,
        "RandomForest": RandomForestModelWrapper,
        "PyTorchMLP": lambda **p: PyTorchMLPWrapper(input_size, **p),
        "PyTorchLSTM": lambda **p: PyTorchLSTMWrapper(input_size, **p),
        "PyTorchGRU": lambda **p: PyTorchGRUWrapper(input_size, **p)
    }
    
    if model_name not in model_map:
        raise ValueError(f"Unsupported model type: {model_name}")
    
    if model_name.startswith("PyTorch") and input_size is None:
        raise ValueError(f"{model_name} requires input_size parameter")
    
    return model_map[model_name](**params) 