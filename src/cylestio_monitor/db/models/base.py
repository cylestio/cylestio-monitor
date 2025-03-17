"""Base model class with common functionality for all models.

This module provides the Base model class that all other models will inherit from,
along with utility functions and mixins for common functionality across models.
"""
from __future__ import annotations

import datetime
import json
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

from sqlalchemy import DateTime, func, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

T = TypeVar('T', bound='Base')


class Base(DeclarativeBase):
    """Base model class that all other models inherit from.
    
    Provides common functionality like serialization, deserialization,
    and string representation.
    """
    
    # Common fields that might be useful across models
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),
        onupdate=func.now()
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate the table name automatically from the class name.
        
        Returns:
            str: The table name in snake_case.
        """
        return cls.__name__.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model instance to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model.
        """
        return {
            c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs
        }
    
    def to_json(self) -> str:
        """Convert the model instance to a JSON string.
        
        Returns:
            str: JSON string representation of the model.
        """
        return json.dumps(self.to_dict(), default=self._json_serializer)
    
    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """Serialize objects that aren't natively serializable by json.dumps.
        
        Args:
            obj (Any): The object to serialize.
            
        Returns:
            Any: Serialized representation of the object.
        """
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create a model instance from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary containing model data.
            
        Returns:
            T: Instance of the model.
        """
        return cls(**{
            k: v for k, v in data.items() 
            if k in inspect(cls).mapper.column_attrs.keys()
        })
    
    def update(self, **kwargs: Any) -> None:
        """Update the model with the given keyword arguments.
        
        Args:
            **kwargs (Any): Key-value pairs to update the model with.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """Return a string representation of the model.
        
        Returns:
            str: String representation of the model.
        """
        attrs = ", ".join(
            f"{c.key}={getattr(self, c.key)}" 
            for c in inspect(self).mapper.column_attrs
            if c.key in ["id", "name", "agent_id", "event_id"]
            and hasattr(self, c.key)
        )
        return f"<{self.__class__.__name__}({attrs})>" 