from typing import Any, Dict
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
import copy
import logging

from ..modeling_service import BaseClassifierModel

logger = logging.getLogger(__name__)

# Set seed for reproducibility
torch.manual_seed(7)
np.random.seed(7)

class GRU(nn.Module):
    """
    Gated Recurrent Unit (GRU) model implemented in PyTorch.
    
    This class implements a bidirectional GRU network for sequence classification,
    with configurable number of layers and dropout for regularization.
    """
    
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, dropout: float, bidirectional: bool):
        """
        Initialize the GRU model.
        
        Args:
            input_size: Size of the input features
            hidden_size: Size of the hidden state
            num_layers: Number of GRU layers
            dropout: Dropout probability for regularization
            bidirectional: Whether to use bidirectional GRU
        """
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            bidirectional=bidirectional,
            batch_first=True
        )
        self.fc = nn.Linear(hidden_size * (2 if bidirectional else 1), 2)  # Binary classification output
    
    def forward(self, x):
        """
        Forward pass through the network.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, input_size)
            
        Returns:
            Network output tensor
        """
        gru_out, _ = self.gru(x)
        return self.fc(gru_out[:, -1, :])  # Use only the last time step output

class PyTorchGRUWrapper(BaseClassifierModel):
    """
    Wrapper for PyTorch GRU model.
    
    This class provides a standardized interface for the PyTorch GRU model,
    implementing the BaseClassifierModel interface with GPU support.
    """
    
    # Default model parameters
    DEFAULT_MODEL_PARAMS = {
        "hidden_size": 64,
        "num_layers": 2,
        "dropout": 0.2,
        "bidirectional": True,
        "epochs": 100,               # Increased epochs
        "batch_size": 32,
        "learning_rate": 1e-3,       # Added learning rate
        "validation_split_ratio": 0.2, # Added validation split ratio
        "early_stopping_patience": 10  # Added patience for early stopping
    }
    
    def __init__(self, input_size: int, **params: Dict[str, Any]):
        """
        Initialize the PyTorch GRU wrapper.
        
        Args:
            input_size: Size of the input features
            **params: Additional parameters to override default model parameters
        """
        model_params = {**self.DEFAULT_MODEL_PARAMS, **params}
        
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")

        self.device = device
        logger.info(f"Using device: {self.device}")
        
        self.model = GRU(
            input_size=input_size,
            hidden_size=model_params['hidden_size'],
            num_layers=model_params['num_layers'],
            dropout=model_params['dropout'],
            bidirectional=model_params['bidirectional']
        ).to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=model_params['learning_rate'])
        self.criterion = nn.CrossEntropyLoss()
        self.batch_size = model_params['batch_size']
        self.epochs = model_params['epochs']
        self.validation_split_ratio = model_params['validation_split_ratio']
        self.early_stopping_patience = model_params['early_stopping_patience']
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Train the model on the given data with early stopping.
        
        Args:
            X: Training data features
            y: Training data labels
        """
        if self.validation_split_ratio <= 0 or self.validation_split_ratio >= 1:
            raise ValueError("validation_split_ratio must be between 0 and 1.")

        # Split data into training and validation sets
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=self.validation_split_ratio, random_state=42, stratify=y
        )

        # Convert to PyTorch tensors and reshape
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        X_train_tensor = X_train_tensor.unsqueeze(1)
        y_train_tensor = torch.LongTensor(y_train).to(self.device)
        
        X_val_tensor = torch.FloatTensor(X_val).to(self.device)
        X_val_tensor = X_val_tensor.unsqueeze(1)
        y_val_tensor = torch.LongTensor(y_val).to(self.device)

        # Create data loaders
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_dataloader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)

        val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
        val_dataloader = DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)

        best_val_loss = float('inf')
        patience_counter = 0
        best_model_state = None

        logger.info(f"Starting training for {self.epochs} epochs...")
        # Training loop
        for epoch in range(self.epochs):
            self.model.train()
            train_loss = 0.0
            for batch_X, batch_y in train_dataloader:
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()
                train_loss += loss.item() * batch_X.size(0)

            train_loss /= len(train_dataloader.dataset)

            # Validation loop
            self.model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch_X_val, batch_y_val in val_dataloader:
                    outputs = self.model(batch_X_val)
                    loss = self.criterion(outputs, batch_y_val)
                    val_loss += loss.item() * batch_X_val.size(0)

            val_loss /= len(val_dataloader.dataset)
            logger.info(f"Epoch {epoch+1}/{self.epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

            # Early stopping check
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save the best model state
                best_model_state = copy.deepcopy(self.model.state_dict())
                logger.debug(f"Validation loss improved to {best_val_loss:.4f}. Saving model.")
            else:
                patience_counter += 1
                logger.debug(f"Validation loss did not improve. Patience: {patience_counter}/{self.early_stopping_patience}")

            if patience_counter >= self.early_stopping_patience:
                logger.info(f"Early stopping triggered after epoch {epoch+1}.")
                break

        # Load the best model state found during training
        if best_model_state:
            logger.info(f"Loading best model state with validation loss: {best_val_loss:.4f}")
            self.model.load_state_dict(best_model_state)
        else:
            logger.warning("No best model state saved; either validation split is 0 or training stopped before improvement.")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions for the given data.
        
        Args:
            X: Input data features
            
        Returns:
            Predicted class labels
        """
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            X_tensor = X_tensor.unsqueeze(1)
            outputs = self.model(X_tensor)
            _, predicted = torch.max(outputs.data, 1)
            return predicted.cpu().numpy()
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities for the given data.
        
        Args:
            X: Input data features
            
        Returns:
            Probability estimates for each class
        """
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            X_tensor = X_tensor.unsqueeze(1)
            outputs = self.model(X_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            return probabilities.cpu().numpy() 