"""Agent model for the Cylestio Monitor database.

This module defines the Agent model, which stores information about
AI agents being monitored by Cylestio Monitor.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Index, String, Text, DateTime, JSON, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from cylestio_monitor.db.models.base import Base


class Agent(Base):
    """Agent model representing an AI agent being monitored.
    
    This model stores basic information about an agent, including its
    identifier, name, description, and metadata.
    """
    
    __tablename__ = "agents"
    
    # Override id from Base to add auto-increment
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Agent specific fields from schema
    agent_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    # created_at from Base class
    last_seen: Mapped[datetime.datetime] = mapped_column(
        DateTime, 
        default=datetime.datetime.utcnow,
        server_default=text('CURRENT_TIMESTAMP')
    )
    agent_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, 
        comment="Flexible agent metadata (framework info, version, etc.)"
    )
    
    # Relationships (back-references)
    sessions: Mapped[List["Session"]] = relationship(
        "Session", 
        back_populates="agent", 
        cascade="all, delete-orphan"
    )
    events: Mapped[List["Event"]] = relationship(
        "Event", 
        back_populates="agent", 
        cascade="all, delete-orphan"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_agents_agent_id", "agent_id"),
        Index("idx_agents_last_seen", "last_seen"),
    )
    
    @hybrid_property
    def session_count(self) -> int:
        """Get the number of sessions for this agent.
        
        Returns:
            int: Number of sessions.
        """
        return len(self.sessions)
    
    def update_last_seen(self) -> None:
        """Update the last seen timestamp to the current time."""
        self.last_seen = datetime.datetime.utcnow()
        
    @classmethod
    def find_by_agent_id(cls, agent_id: str, session=None) -> Optional[Agent]:
        """Find an agent by its agent_id.
        
        Args:
            agent_id (str): The agent_id to search for.
            session: The database session to use.
            
        Returns:
            Optional[Agent]: The agent if found, None otherwise.
        """
        if session is None:
            return None
        return session.query(cls).filter(cls.agent_id == agent_id).first()
    
    @classmethod
    def get_or_create(cls, session, agent_id: str, **kwargs) -> Agent:
        """Get an existing agent or create a new one if it doesn't exist.
        
        Args:
            session: The database session to use.
            agent_id (str): The agent_id to look for or create.
            **kwargs: Additional attributes to set on the agent if created.
            
        Returns:
            Agent: The existing or newly created agent.
        """
        agent = cls.find_by_agent_id(agent_id, session)
        if agent:
            # Update last_seen
            agent.update_last_seen()
            # Update any provided fields
            if kwargs:
                agent.update(**kwargs)
            return agent
        
        # Create a new agent
        agent = cls(
            agent_id=agent_id,
            **kwargs
        )
        session.add(agent)
        return agent
    
    def get_activity_summary(self, session, days: int = 7) -> Dict[str, Any]:
        """Get a summary of agent activity over the specified period.
        
        Args:
            session: The database session to use.
            days (int): Number of days to include in the summary.
            
        Returns:
            Dict[str, Any]: A summary of agent activity.
        """
        from cylestio_monitor.db.models.event import Event
        from sqlalchemy import func, and_, literal_column
        
        # Calculate date range
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Count events by day and type
        daily_events = (
            session.query(
                func.date(Event.timestamp).label("date"), 
                Event.event_type,
                func.count().label("count")
            )
            .filter(
                and_(
                    Event.agent_id == self.id,
                    Event.timestamp >= start_date,
                    Event.timestamp <= end_date
                )
            )
            .group_by(func.date(Event.timestamp), Event.event_type)
            .all()
        )
        
        # Transform into a more usable structure
        result = {
            "agent_id": self.agent_id,
            "name": self.name,
            "total_sessions": self.session_count,
            "days_active": len(set(day for day, _, _ in daily_events)),
            "event_counts": {},
            "daily_activity": {}
        }
        
        for day, event_type, count in daily_events:
            day_str = day.strftime("%Y-%m-%d")
            
            # Update event counts
            if event_type not in result["event_counts"]:
                result["event_counts"][event_type] = 0
            result["event_counts"][event_type] += count
            
            # Update daily activity
            if day_str not in result["daily_activity"]:
                result["daily_activity"][day_str] = {}
            result["daily_activity"][day_str][event_type] = count
            
        return result 