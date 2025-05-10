from typing import Any, Dict
import numpy as np
from catboost import CatBoostClassifier

from ..modeling_service import BaseClassifierModel

class CatBoostModelWrapper(BaseClassifierModel):
    """
    Wrapper for CatBoost classifier model.
    
    This class provides a standardized interface for the CatBoost classifier,
    implementing the BaseClassifierModel interface.
    """
    
    # Default model parameters
    DEFAULT_MODEL_PARAMS = {
        "n_estimators": 1000,
        "allow_writing_files": False,
        "verbose": False,
        "random_state": 7
    }
    
    def __init__(self, **params: Dict[str, Any]):
        """
        Initialize the CatBoost model wrapper.
        
        Args:
            **params: Additional parameters to override default model parameters
        """
        model_params = {**self.DEFAULT_MODEL_PARAMS, **params}
        self.model = CatBoostClassifier(**model_params)
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Train the model on the given data.
        
        Args:
            X: Training data features
            y: Training data labels
        """
        self.model.fit(X, y)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions for the given data.
        
        Args:
            X: Input data features
            
        Returns:
            Predicted class labels
        """
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities for the given data.
        
        Args:
            X: Input data features
            
        Returns:
            Probability estimates for each class
        """
        return self.model.predict_proba(X) 