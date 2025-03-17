"""LLM models for the Cylestio Monitor database.

This module defines models related to LLM calls, including model types,
prompts, responses, tokens, and other LLM-specific information.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import ForeignKey, Index, String, Text, Boolean, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from cylestio_monitor.db.models.base import Base


class LLMCall(Base):
    """LLM Call model representing an LLM API call.
    
    This model stores detailed information about LLM API calls,
    including the model used, prompt, response, tokens, and performance metrics.
    """
    
    __tablename__ = "llm_calls"
    
    # Override id from Base to add auto-increment
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # LLM Call specific fields from schema
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), 
        nullable=False
    )
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_in: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_stream: Mapped[bool] = mapped_column(Boolean, default=False)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="llm_call")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_llm_calls_event_id", "event_id"),
        Index("idx_llm_calls_model", "model"),
    )
    
    @validates('tokens_in', 'tokens_out')
    def validate_tokens(self, key: str, value: Optional[int]) -> Optional[int]:
        """Validate the token count fields.
        
        Args:
            key (str): The field name.
            value (Optional[int]): The field value.
            
        Returns:
            Optional[int]: The validated value.
            
        Raises:
            ValueError: If the value is negative.
        """
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @validates('duration_ms')
    def validate_duration(self, key: str, value: Optional[int]) -> Optional[int]:
        """Validate the duration field.
        
        Args:
            key (str): The field name.
            value (Optional[int]): The field value.
            
        Returns:
            Optional[int]: The validated value.
            
        Raises:
            ValueError: If the value is negative.
        """
        if value is not None and value < 0:
            raise ValueError("duration_ms cannot be negative")
        return value
    
    @validates('cost')
    def validate_cost(self, key: str, value: Optional[float]) -> Optional[float]:
        """Validate the cost field.
        
        Args:
            key (str): The field name.
            value (Optional[float]): The field value.
            
        Returns:
            Optional[float]: The validated value.
            
        Raises:
            ValueError: If the value is negative.
        """
        if value is not None and value < 0:
            raise ValueError("cost cannot be negative")
        return value
    
    @property
    def total_tokens(self) -> Optional[int]:
        """Calculate the total number of tokens used in the LLM call.
        
        Returns:
            Optional[int]: The total tokens, or None if either tokens_in or tokens_out is None.
        """
        if self.tokens_in is None or self.tokens_out is None:
            return None
        return self.tokens_in + self.tokens_out
    
    @property
    def truncated_prompt(self, max_length: int = 100) -> str:
        """Get a truncated version of the prompt for display.
        
        Args:
            max_length (int, optional): The maximum length of the truncated prompt.
            
        Returns:
            str: The truncated prompt.
        """
        if len(self.prompt) <= max_length:
            return self.prompt
        return self.prompt[:max_length] + "..."
    
    @property
    def truncated_response(self, max_length: int = 100) -> str:
        """Get a truncated version of the response for display.
        
        Args:
            max_length (int, optional): The maximum length of the truncated response.
            
        Returns:
            str: The truncated response.
        """
        if len(self.response) <= max_length:
            return self.response
        return self.response[:max_length] + "..."
    
    @classmethod
    def create_llm_call(cls, session, event_id: int, model: str, prompt: str, 
                       response: str, tokens_in: Optional[int] = None, 
                       tokens_out: Optional[int] = None, duration_ms: Optional[int] = None,
                       is_stream: bool = False, temperature: Optional[float] = None,
                       cost: Optional[float] = None) -> "LLMCall":
        """Create a new LLM call.
        
        Args:
            session: The database session to use.
            event_id (int): The ID of the event this LLM call is for.
            model (str): The LLM model used.
            prompt (str): The prompt sent to the LLM.
            response (str): The response received from the LLM.
            tokens_in (Optional[int], optional): Number of input tokens.
            tokens_out (Optional[int], optional): Number of output tokens.
            duration_ms (Optional[int], optional): Duration of the call in milliseconds.
            is_stream (bool, optional): Whether streaming was used.
            temperature (Optional[float], optional): Temperature setting used for generation.
            cost (Optional[float], optional): Estimated cost of the call.
            
        Returns:
            LLMCall: The newly created LLM call.
        """
        llm_call = cls(
            event_id=event_id,
            model=model,
            prompt=prompt,
            response=response,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_ms=duration_ms,
            is_stream=is_stream,
            temperature=temperature,
            cost=cost
        )
        session.add(llm_call)
        return llm_call
    
    @classmethod
    def get_model_statistics(cls, session, model: Optional[str] = None, 
                           agent_id: Optional[int] = None,
                           start_time: Optional[datetime.datetime] = None,
                           end_time: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """Get statistics about LLM model usage.
        
        Args:
            session: The database session to use.
            model (Optional[str], optional): Filter by model name.
            agent_id (Optional[int], optional): Filter by agent ID.
            start_time (Optional[datetime.datetime], optional): The earliest time to include.
            end_time (Optional[datetime.datetime], optional): The latest time to include.
            
        Returns:
            Dict[str, Any]: Statistics about LLM model usage.
        """
        from sqlalchemy import func, and_
        from cylestio_monitor.db.models.event import Event
        
        # Build query with all necessary joins
        base_query = (
            session.query(cls)
            .join(Event, cls.event_id == Event.id)
        )
        
        # Apply filters
        filters = []
        if model is not None:
            filters.append(cls.model == model)
        if agent_id is not None:
            filters.append(Event.agent_id == agent_id)
        if start_time is not None:
            filters.append(Event.timestamp >= start_time)
        if end_time is not None:
            filters.append(Event.timestamp <= end_time)
        
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # Compute statistics
        stats = {
            "total_calls": base_query.count(),
            "avg_tokens_in": session.query(func.avg(cls.tokens_in)).filter(and_(*filters)).scalar() or 0,
            "avg_tokens_out": session.query(func.avg(cls.tokens_out)).filter(and_(*filters)).scalar() or 0,
            "avg_duration_ms": session.query(func.avg(cls.duration_ms)).filter(and_(*filters)).scalar() or 0,
            "total_cost": session.query(func.sum(cls.cost)).filter(and_(*filters)).scalar() or 0,
        }
        
        # Get model breakdown if not filtering by a specific model
        if model is None:
            model_counts = (
                session.query(
                    cls.model, 
                    func.count().label("count")
                )
                .filter(and_(*filters))
                .group_by(cls.model)
                .all()
            )
            stats["model_breakdown"] = {model: count for model, count in model_counts}
        
        return stats 