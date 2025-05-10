from typing import Any, Dict
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from ..modeling_service import BaseClassifierModel

class RandomForestModelWrapper(BaseClassifierModel):
    """
    Wrapper for Random Forest classifier model.
    
    This class provides a standardized interface for the Random Forest classifier,
    implementing the BaseClassifierModel interface.
    """
    
    # Default model parameters
    DEFAULT_MODEL_PARAMS = {
        "n_estimators": 1000,
        "n_jobs": -1,
        "random_state": 7
    }
    
    def __init__(self, **params: Dict[str, Any]):
        """
        Initialize the Random Forest model wrapper.
        
        Args:
            **params: Additional parameters to override default model parameters
        """
        model_params = {**self.DEFAULT_MODEL_PARAMS, **params}
        self.model = RandomForestClassifier(**model_params)
    
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