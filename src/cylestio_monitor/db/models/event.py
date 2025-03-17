"""Event model for the Cylestio Monitor database.

This module defines the Event model, which is the core table for all monitoring events
in the Cylestio Monitor system.
"""
from __future__ import annotations

import datetime
import enum
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import ForeignKey, Index, String, Text, DateTime, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from cylestio_monitor.db.models.base import Base


class EventType(str, enum.Enum):
    """Enumeration of event types."""
    
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    USER_MESSAGE = "user_message"
    SYSTEM_MESSAGE = "system_message"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SECURITY_ALERT = "security_alert"
    PERFORMANCE_METRIC = "performance_metric"
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"


class EventLevel(str, enum.Enum):
    """Enumeration of event severity levels."""
    
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventDirection(str, enum.Enum):
    """Enumeration of event directions."""
    
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    INTERNAL = "internal"


class EventChannel(str, enum.Enum):
    """Enumeration of event channels."""
    
    SYSTEM = "system"
    LLM = "llm"
    TOOL = "tool"
    USER = "user"
    LANGCHAIN = "langchain"
    LANGGRAPH = "langgraph"
    MCP = "mcp"
    CUSTOM = "custom"


class Event(Base):
    """Event model representing a monitoring event.
    
    This is the core table for all monitoring events in the system,
    with specialized tables linking to it for different event types.
    """
    
    __tablename__ = "events"
    
    # Override id from Base to add auto-increment
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Event specific fields from schema
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), 
        nullable=True
    )
    conversation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), 
        nullable=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False
    )
    channel: Mapped[str] = mapped_column(
        String(50), 
        nullable=False
    )
    level: Mapped[str] = mapped_column(
        String(20), 
        nullable=False
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime, 
        default=datetime.datetime.utcnow
    )
    direction: Mapped[Optional[str]] = mapped_column(
        String(20), 
        nullable=True
    )
    data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Additional event data not captured in specialized tables"
    )
    
    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="events")
    session: Mapped[Optional["Session"]] = relationship("Session", back_populates="events")
    conversation: Mapped[Optional["Conversation"]] = relationship("Conversation", back_populates="events")
    
    # Specialized event relationships (one-to-one)
    llm_call: Mapped[Optional["LLMCall"]] = relationship(
        "LLMCall", 
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan"
    )
    tool_call: Mapped[Optional["ToolCall"]] = relationship(
        "ToolCall", 
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan"
    )
    security_event: Mapped[Optional["EventSecurity"]] = relationship(
        "EventSecurity", 
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan"
    )
    performance_metric: Mapped[Optional["PerformanceMetric"]] = relationship(
        "PerformanceMetric", 
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan"
    )
    security_alert: Mapped[Optional["SecurityAlert"]] = relationship(
        "SecurityAlert", 
        back_populates="event",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_events_agent_id", "agent_id"),
        Index("idx_events_session_id", "session_id"),
        Index("idx_events_conversation_id", "conversation_id"),
        Index("idx_events_event_type", "event_type"),
        Index("idx_events_level", "level"),
        Index("idx_events_timestamp", "timestamp"),
    )
    
    @validates('event_type')
    def validate_event_type(self, key: str, value: str) -> str:
        """Validate the event_type field.
        
        Args:
            key (str): The field name.
            value (str): The field value.
            
        Returns:
            str: The validated value.
            
        Raises:
            ValueError: If the value is not a valid event type.
        """
        # Allow both string values and enum values
        if isinstance(value, EventType):
            return value.value
        
        # Check if it's a valid event type
        try:
            return EventType(value).value
        except ValueError:
            # If not in the enum, at least ensure it's not empty
            if not value.strip():
                raise ValueError("Event type cannot be empty")
            return value
    
    @validates('level')
    def validate_level(self, key: str, value: str) -> str:
        """Validate the level field.
        
        Args:
            key (str): The field name.
            value (str): The field value.
            
        Returns:
            str: The validated value.
            
        Raises:
            ValueError: If the value is not a valid event level.
        """
        # Allow both string values and enum values
        if isinstance(value, EventLevel):
            return value.value
        
        # Check if it's a valid level
        try:
            return EventLevel(value).value
        except ValueError:
            # If not in the enum, at least ensure it's not empty
            if not value.strip():
                raise ValueError("Event level cannot be empty")
            return value
    
    @validates('direction')
    def validate_direction(self, key: str, value: Optional[str]) -> Optional[str]:
        """Validate the direction field.
        
        Args:
            key (str): The field name.
            value (Optional[str]): The field value.
            
        Returns:
            Optional[str]: The validated value.
            
        Raises:
            ValueError: If the value is not a valid event direction.
        """
        if value is None:
            return None
            
        # Allow both string values and enum values
        if isinstance(value, EventDirection):
            return value.value
        
        # Check if it's a valid direction
        try:
            return EventDirection(value).value
        except ValueError:
            # If not in the enum, at least ensure it's not empty
            if not value.strip():
                raise ValueError("Event direction cannot be empty if provided")
            return value
    
    @validates('channel')
    def validate_channel(self, key: str, value: str) -> str:
        """Validate the channel field.
        
        Args:
            key (str): The field name.
            value (str): The field value.
            
        Returns:
            str: The validated value.
            
        Raises:
            ValueError: If the value is not a valid event channel.
        """
        # Allow both string values and enum values
        if isinstance(value, EventChannel):
            return value.value
        
        # Check if it's a valid channel
        try:
            return EventChannel(value).value
        except ValueError:
            # If not in the enum, at least ensure it's not empty
            if not value.strip():
                raise ValueError("Event channel cannot be empty")
            return value
    
    @classmethod
    def create_event(cls, session, agent_id: int, event_type: Union[str, EventType], 
                     channel: Union[str, EventChannel], level: Union[str, EventLevel],
                     data: Optional[Dict[str, Any]] = None,
                     session_id: Optional[int] = None,
                     conversation_id: Optional[int] = None,
                     direction: Optional[Union[str, EventDirection]] = None) -> "Event":
        """Create a new event.
        
        Args:
            session: The database session to use.
            agent_id (int): The ID of the agent this event is for.
            event_type (Union[str, EventType]): The type of event.
            channel (Union[str, EventChannel]): The channel this event is from.
            level (Union[str, EventLevel]): The severity level of the event.
            data (Optional[Dict[str, Any]], optional): Additional event data.
            session_id (Optional[int], optional): The ID of the session this event is part of.
            conversation_id (Optional[int], optional): The ID of the conversation this event is part of.
            direction (Optional[Union[str, EventDirection]], optional): The direction of the event.
            
        Returns:
            Event: The newly created event.
        """
        event = cls(
            agent_id=agent_id,
            session_id=session_id,
            conversation_id=conversation_id,
            event_type=event_type,
            channel=channel,
            level=level,
            direction=direction,
            data=data or {}
        )
        session.add(event)
        return event
    
    @classmethod
    def find_events_by_agent(cls, session, agent_id: int, 
                            event_types: Optional[List[str]] = None,
                            start_time: Optional[datetime.datetime] = None,
                            end_time: Optional[datetime.datetime] = None,
                            level: Optional[str] = None,
                            limit: int = 100) -> List["Event"]:
        """Find events for the given agent matching the criteria.
        
        Args:
            session: The database session to use.
            agent_id (int): The ID of the agent to find events for.
            event_types (Optional[List[str]], optional): The types of events to find.
            start_time (Optional[datetime.datetime], optional): The earliest time to include.
            end_time (Optional[datetime.datetime], optional): The latest time to include.
            level (Optional[str], optional): The minimum severity level to include.
            limit (int, optional): The maximum number of events to return.
            
        Returns:
            List[Event]: The events matching the criteria.
        """
        from sqlalchemy import and_
        
        # Start with base query
        query = session.query(cls).filter(cls.agent_id == agent_id)
        
        # Apply filters if provided
        if event_types:
            query = query.filter(cls.event_type.in_(event_types))
        
        if start_time:
            query = query.filter(cls.timestamp >= start_time)
            
        if end_time:
            query = query.filter(cls.timestamp <= end_time)
            
        if level:
            # Get the numeric value of the level for comparison
            level_value = EventLevel(level).value if isinstance(level, str) else level.value
            level_values = [l.value for l in EventLevel]
            min_level_index = level_values.index(level_value)
            included_levels = level_values[min_level_index:]
            query = query.filter(cls.level.in_(included_levels))
        
        # Order by timestamp descending and limit results
        return query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def count_by_type(cls, session, agent_id: Optional[int] = None,
                     start_time: Optional[datetime.datetime] = None,
                     end_time: Optional[datetime.datetime] = None) -> Dict[str, int]:
        """Count events by type.
        
        Args:
            session: The database session to use.
            agent_id (Optional[int], optional): The ID of the agent to count events for.
            start_time (Optional[datetime.datetime], optional): The earliest time to include.
            end_time (Optional[datetime.datetime], optional): The latest time to include.
            
        Returns:
            Dict[str, int]: A dictionary mapping event types to counts.
        """
        from sqlalchemy import func, and_
        
        # Build query with filters
        filters = []
        if agent_id is not None:
            filters.append(cls.agent_id == agent_id)
        if start_time is not None:
            filters.append(cls.timestamp >= start_time)
        if end_time is not None:
            filters.append(cls.timestamp <= end_time)
        
        # Execute query with appropriate filters
        query = (
            session.query(
                cls.event_type,
                func.count().label("count")
            )
            .filter(and_(*filters))
            .group_by(cls.event_type)
        )
        
        # Convert to dictionary
        return {
            event_type: count
            for event_type, count in query.all()
        } 