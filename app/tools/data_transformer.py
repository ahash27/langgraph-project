"""Data transformation tool"""

from typing import Any, Dict
from app.tools.base_tool import BaseTool


class DataTransformer(BaseTool):
    """
    Tool for transforming data between formats.
    
    Can be used by agents to convert, format, or restructure data.
    """
    
    def __init__(self):
        super().__init__(
            name="data_transformer",
            description="Transforms data between different formats and structures"
        )
    
    def execute(self, data: Any, transform_type: str = "normalize") -> Any:
        """
        Transform data according to specified type.
        
        Args:
            data: Input data to transform
            transform_type: Type of transformation (normalize, format, convert)
            
        Returns:
            Transformed data
        """
        if transform_type == "normalize":
            return self._normalize(data)
        elif transform_type == "format":
            return self._format(data)
        elif transform_type == "convert":
            return self._convert(data)
        else:
            return data
    
    def _normalize(self, data: Any) -> Any:
        """Normalize data structure"""
        if isinstance(data, str):
            return data.strip().lower()
        return data
    
    def _format(self, data: Any) -> str:
        """Format data as string"""
        return str(data)
    
    def _convert(self, data: Any) -> Dict:
        """Convert data to dictionary"""
        if isinstance(data, dict):
            return data
        return {"value": data}
