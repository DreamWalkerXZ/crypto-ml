from typing import Dict, Any
from pydantic import BaseModel

class ModelInfo(BaseModel):
    """Model information schema"""
    name: str
    description: str
    default_params: Dict[str, Any]
    requires_input_size: bool 