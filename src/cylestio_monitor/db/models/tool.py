"""Tool models for the Cylestio Monitor database.

This module defines models related to tool/function calls, including
input parameters, output results, and tool usage metrics.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import ForeignKey, Index, String, Text, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from cylestio_monitor.db.models.base import Base


class ToolCall(Base):
    """Tool Call model representing a tool/function call.
    
    This model stores detailed information about tool calls,
    including input parameters, output results, and performance metrics.
    """
    
    __tablename__ = "tool_calls"
    
    # Override id from Base to add auto-increment
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Tool Call specific fields from schema
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), 
        nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Input parameters to the tool"
    )
    output_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Output result of the tool call"
    )
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    blocking: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="tool_call")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_tool_calls_event_id", "event_id"),
        Index("idx_tool_calls_tool_name", "tool_name"),
        Index("idx_tool_calls_success", "success"),
    )
    
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
    
    @property
    def has_error(self) -> bool:
        """Check if the tool call resulted in an error.
        
        Returns:
            bool: True if the tool call resulted in an error, False otherwise.
        """
        return not self.success
    
    @property
    def formatted_input(self) -> str:
        """Get a formatted string representation of the input parameters.
        
        Returns:
            str: Formatted input parameters.
        """
        import json
        if self.input_params is None:
            return "<no input>"
        try:
            return json.dumps(self.input_params, indent=2)
        except (TypeError, ValueError):
            return str(self.input_params)
    
    @property
    def formatted_output(self) -> str:
        """Get a formatted string representation of the output result.
        
        Returns:
            str: Formatted output result.
        """
        import json
        if self.output_result is None:
            return "<no output>"
        try:
            return json.dumps(self.output_result, indent=2)
        except (TypeError, ValueError):
            return str(self.output_result)
    
    @classmethod
    def create_tool_call(cls, session, event_id: int, tool_name: str,
                        input_params: Optional[Dict[str, Any]] = None,
                        output_result: Optional[Dict[str, Any]] = None,
                        success: bool = True,
                        error_message: Optional[str] = None,
                        duration_ms: Optional[int] = None,
                        blocking: bool = True) -> "ToolCall":
        """Create a new tool call.
        
        Args:
            session: The database session to use.
            event_id (int): The ID of the event this tool call is for.
            tool_name (str): The name of the tool.
            input_params (Optional[Dict[str, Any]], optional): Input parameters to the tool.
            output_result (Optional[Dict[str, Any]], optional): Output result of the tool call.
            success (bool, optional): Whether the call was successful.
            error_message (Optional[str], optional): Error message if the call failed.
            duration_ms (Optional[int], optional): Duration of the call in milliseconds.
            blocking (bool, optional): Whether the call was blocking.
            
        Returns:
            ToolCall: The newly created tool call.
        """
        tool_call = cls(
            event_id=event_id,
            tool_name=tool_name,
            input_params=input_params,
            output_result=output_result,
            success=success,
            error_message=error_message,
            duration_ms=duration_ms,
            blocking=blocking
        )
        session.add(tool_call)
        return tool_call
    
    @classmethod
    def get_tool_statistics(cls, session, tool_name: Optional[str] = None,
                           agent_id: Optional[int] = None,
                           start_time: Optional[datetime.datetime] = None,
                           end_time: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """Get statistics about tool usage.
        
        Args:
            session: The database session to use.
            tool_name (Optional[str], optional): Filter by tool name.
            agent_id (Optional[int], optional): Filter by agent ID.
            start_time (Optional[datetime.datetime], optional): The earliest time to include.
            end_time (Optional[datetime.datetime], optional): The latest time to include.
            
        Returns:
            Dict[str, Any]: Statistics about tool usage.
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
        if tool_name is not None:
            filters.append(cls.tool_name == tool_name)
        if agent_id is not None:
            filters.append(Event.agent_id == agent_id)
        if start_time is not None:
            filters.append(Event.timestamp >= start_time)
        if end_time is not None:
            filters.append(Event.timestamp <= end_time)
        
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # Count total calls and success/failure breakdown
        total_calls = base_query.count()
        success_count = base_query.filter(cls.success == True).count()
        failure_count = total_calls - success_count
        
        # Calculate average duration
        avg_duration = (
            session.query(func.avg(cls.duration_ms))
            .filter(and_(*filters))
            .scalar()
        ) or 0
        
        stats = {
            "total_calls": total_calls,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": (success_count / total_calls) * 100 if total_calls > 0 else 0,
            "avg_duration_ms": avg_duration,
        }
        
        # Get tool breakdown if not filtering by a specific tool
        if tool_name is None:
            tool_counts = (
                session.query(
                    cls.tool_name, 
                    func.count().label("count"),
                    func.sum(cls.success.cast(Integer)).label("success_count")
                )
                .filter(and_(*filters))
                .group_by(cls.tool_name)
                .all()
            )
            
            tool_stats = {}
            for tool, count, success_count in tool_counts:
                failure_count = count - success_count
                tool_stats[tool] = {
                    "total_calls": count,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "success_rate": (success_count / count) * 100 if count > 0 else 0
                }
            
            stats["tool_breakdown"] = tool_stats
        
        return stats
    
    @classmethod
    def get_common_errors(cls, session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most common tool call errors.
        
        Args:
            session: The database session to use.
            limit (int, optional): The maximum number of errors to return.
            
        Returns:
            List[Dict[str, Any]]: The most common tool call errors.
        """
        from sqlalchemy import func, and_
        from cylestio_monitor.db.models.event import Event
        
        # Count error occurrences grouped by tool_name and error_message
        error_counts = (
            session.query(
                cls.tool_name,
                cls.error_message,
                func.count().label("count")
            )
            .filter(and_(
                cls.success == False,
                cls.error_message.isnot(None)
            ))
            .group_by(cls.tool_name, cls.error_message)
            .order_by(func.count().desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                "tool_name": tool_name,
                "error_message": error_message,
                "count": count
            }
            for tool_name, error_message, count in error_counts
        ] 