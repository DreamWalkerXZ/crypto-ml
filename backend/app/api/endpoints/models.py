from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from app.core.model_wrappers import (
    CatBoostModelWrapper,
    XGBoostModelWrapper,
    LogisticRegressionModelWrapper,
    RandomForestModelWrapper,
    PyTorchMLPWrapper,
    PyTorchLSTMWrapper,
    PyTorchGRUWrapper
)
from app.schemas.models import ModelInfo
from app.schemas.common import ResponseModel

# Create router for model-related endpoints
router = APIRouter()

# Model information mapping
MODEL_INFO_MAP = {
    "CatBoost": ModelInfo(
        name="CatBoost",
        description="Gradient boosting decision tree model, particularly suitable for categorical features",
        default_params=CatBoostModelWrapper.DEFAULT_MODEL_PARAMS,
        requires_input_size=False
    ),
    "XGBoost": ModelInfo(
        name="XGBoost",
        description="Efficient gradient boosting decision tree implementation with parallel computing support",
        default_params=XGBoostModelWrapper.DEFAULT_MODEL_PARAMS,
        requires_input_size=False
    ),
    "LogisticRegression": ModelInfo(
        name="LogisticRegression",
        description="Linear classification model suitable for linearly separable data",
        default_params=LogisticRegressionModelWrapper.DEFAULT_MODEL_PARAMS,
        requires_input_size=False
    ),
    "RandomForest": ModelInfo(
        name="RandomForest",
        description="Ensemble learning model based on decision trees with good generalization ability",
        default_params=RandomForestModelWrapper.DEFAULT_MODEL_PARAMS,
        requires_input_size=False
    ),
    "PyTorchMLP": ModelInfo(
        name="PyTorchMLP",
        description="Multi-layer perceptron neural network suitable for non-linear relationships",
        default_params=PyTorchMLPWrapper.DEFAULT_MODEL_PARAMS,
        requires_input_size=True
    ),
    "PyTorchLSTM": ModelInfo(
        name="PyTorchLSTM",
        description="Long Short-Term Memory network suitable for time series data",
        default_params=PyTorchLSTMWrapper.DEFAULT_MODEL_PARAMS,
        requires_input_size=True
    ),
    "PyTorchGRU": ModelInfo(
        name="PyTorchGRU",
        description="Gated Recurrent Unit network, a simplified version of LSTM",
        default_params=PyTorchGRUWrapper.DEFAULT_MODEL_PARAMS,
        requires_input_size=True
    )
}

@router.get("", response_model=ResponseModel[List[ModelInfo]])
async def get_available_models():
    """Get information about all available models"""
    return ResponseModel(success=True, data=list(MODEL_INFO_MAP.values()))

@router.get("/{model_name}", response_model=ResponseModel[ModelInfo])
async def get_model_info(model_name: str):
    """Get detailed information about a specific model"""
    if model_name not in MODEL_INFO_MAP:
        raise HTTPException(status_code=404, detail=f"Model {model_name} does not exist")
    return ResponseModel(success=True, data=MODEL_INFO_MAP[model_name]) 