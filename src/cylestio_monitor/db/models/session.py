"""Session and Conversation models for the Cylestio Monitor.

This module defines Session and Conversation models that represent
individual execution sessions and conversation flows within an agent.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import ForeignKey, Index, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cylestio_monitor.db.models.base import Base


class Session(Base):
    """Session model representing execution sessions of an agent.
    
    A session represents a distinct execution period of an agent,
    usually corresponding to a single run or activation period.
    """
    
    __tablename__ = "sessions"
    
    # Override id from Base to add auto-increment
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Session specific fields from schema
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    start_time: Mapped[datetime.datetime] = mapped_column(
        DateTime, 
        default=datetime.datetime.utcnow
    )
    end_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    session_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Flexible session metadata"
    )
    
    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="sessions")
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", 
        back_populates="session",
        cascade="all, delete-orphan"
    )
    events: Mapped[List["Event"]] = relationship(
        "Event", 
        back_populates="session",
        cascade="all, delete-orphan"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_sessions_agent_id", "agent_id"),
        Index("idx_sessions_start_time", "start_time"),
        Index("idx_sessions_end_time", "end_time"),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if the session is currently active.
        
        Returns:
            bool: True if the session is active, False otherwise.
        """
        return self.end_time is None
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate the duration of the session in seconds.
        
        Returns:
            Optional[float]: Duration in seconds, or None if the session is still active.
        """
        if not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds()
    
    def end(self) -> None:
        """End the session by setting the end_time to the current time."""
        if self.is_active:
            self.end_time = datetime.datetime.utcnow()
    
    @classmethod
    def create_new_session(cls, session, agent_id: int, session_metadata: Optional[Dict[str, Any]] = None) -> "Session":
        """Create a new session for the given agent.
        
        Args:
            session: The database session to use.
            agent_id (int): The ID of the agent to create a session for.
            metadata (Optional[Dict[str, Any]], optional): Session metadata.
            
        Returns:
            Session: The newly created session.
        """
        new_session = cls(
            agent_id=agent_id,
            session_metadata=session_metadata or {}
        )
        session.add(new_session)
        return new_session
    
    def get_event_summary(self, session) -> Dict[str, Any]:
        """Get a summary of events in this session.
        
        Args:
            session: The database session to use.
            
        Returns:
            Dict[str, Any]: A summary of events in this session.
        """
        from cylestio_monitor.db.models.event import Event
        from sqlalchemy import func
        
        # Count events by type
        event_counts = (
            session.query(
                Event.event_type,
                func.count().label("count")
            )
            .filter(Event.session_id == self.id)
            .group_by(Event.event_type)
            .all()
        )
        
        # Count events by level
        level_counts = (
            session.query(
                Event.level,
                func.count().label("count")
            )
            .filter(Event.session_id == self.id)
            .group_by(Event.level)
            .all()
        )
        
        return {
            "session_id": self.id,
            "duration": self.duration,
            "is_active": self.is_active,
            "conversation_count": len(self.conversations),
            "event_counts": {event_type: count for event_type, count in event_counts},
            "level_counts": {level: count for level, count in level_counts}
        }


class Conversation(Base):
    """Conversation model representing conversations within sessions.
    
    A conversation represents a distinct dialogue or interaction flow
    within a session, typically involving multiple events.
    """
    
    __tablename__ = "conversations"
    
    # Override id from Base to add auto-increment
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Conversation specific fields from schema
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    start_time: Mapped[datetime.datetime] = mapped_column(
        DateTime, 
        default=datetime.datetime.utcnow
    )
    end_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    conversation_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Flexible conversation metadata"
    )
    
    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="conversations")
    events: Mapped[List["Event"]] = relationship(
        "Event", 
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_conversations_session_id", "session_id"),
        Index("idx_conversations_start_time", "start_time"),
        Index("idx_conversations_end_time", "end_time"),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if the conversation is currently active.
        
        Returns:
            bool: True if the conversation is active, False otherwise.
        """
        return self.end_time is None
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate the duration of the conversation in seconds.
        
        Returns:
            Optional[float]: Duration in seconds, or None if the conversation is still active.
        """
        if not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds()
    
    def end(self) -> None:
        """End the conversation by setting the end_time to the current time."""
        if self.is_active:
            self.end_time = datetime.datetime.utcnow()
    
    @classmethod
    def create_new_conversation(cls, session, session_id: int, conversation_metadata: Optional[Dict[str, Any]] = None) -> "Conversation":
        """Create a new conversation within the given session.
        
        Args:
            session: The database session to use.
            session_id (int): The ID of the session to create a conversation in.
            metadata (Optional[Dict[str, Any]], optional): Conversation metadata.
            
        Returns:
            Conversation: The newly created conversation.
        """
        new_conversation = cls(
            session_id=session_id,
            session_metadata=session_metadata or {}
        )
        session.add(new_conversation)
        return new_conversation
    
    def get_message_flow(self, session) -> List[Dict[str, Any]]:
        """Get the flow of messages in this conversation.
        
        Args:
            session: The database session to use.
            
        Returns:
            List[Dict[str, Any]]: A list of messages in chronological order.
        """
        from cylestio_monitor.db.models.event import Event
        
        # Query events sorted by timestamp
        events = (
            session.query(Event)
            .filter(Event.conversation_id == self.id)
            .order_by(Event.timestamp)
            .all()
        )
        
        # Extract message data
        messages = []
        for event in events:
            # Only include relevant event types
            if event.event_type in ["llm_request", "llm_response", "user_message", "system_message"]:
                messages.append({
                    "timestamp": event.timestamp,
                    "type": event.event_type,
                    "direction": event.direction,
                    "data": event.data
                })
        
        return messages 