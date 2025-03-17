"""Database manager for Cylestio Monitor.

This module provides a SQLAlchemy-based database manager for storing monitoring events.
"""

import json
import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import platformdirs
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from cylestio_monitor.db.models import (
    Agent, Base, Conversation, Event, EventChannel, EventLevel, EventSecurity,
    EventType, LLMCall, PerformanceMetric, SecurityAlert, Session as SessionModel,
    ToolCall, AlertLevel, AlertSeverity
)

logger = logging.getLogger("CylestioMonitor")


class DBManager:
    """
    Manages the SQLAlchemy database for Cylestio Monitor.
    
    This class handles database operations for storing and retrieving monitoring events.
    It uses a global SQLite database stored in a shared location determined by platformdirs,
    ensuring that all instances of the SDK write to the same database regardless of the
    virtual environment in which they're installed.
    """

    _instance: Optional["DBManager"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "DBManager":
        """Implement the singleton pattern.
        
        Returns:
            DBManager: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize the database manager."""
        # Check if we're in test mode
        test_db_dir = os.environ.get("CYLESTIO_TEST_DB_DIR")
        if test_db_dir:
            self._data_dir = test_db_dir
        else:
            self._data_dir = platformdirs.user_data_dir(
                appname="cylestio-monitor",
                appauthor="cylestio"
            )
        self._db_path = Path(self._data_dir) / "cylestio_monitor.db"
        
        # Create the directory if it doesn't exist
        os.makedirs(self._data_dir, exist_ok=True)
        
        # Create SQLAlchemy engine with connection pooling
        sqlite_url = f"sqlite:///{self._db_path}"
        self._engine = create_engine(
            sqlite_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            connect_args={"check_same_thread": False}
        )
        
        # Create session factory
        self._Session = sessionmaker(bind=self._engine)
        
        # Initialize the database if it doesn't exist
        self._ensure_db_exists()
        
    def _ensure_db_exists(self) -> None:
        """
        Ensure that the global database file exists.
        
        If the file doesn't exist, create it and initialize the schema.
        """
        if not self._db_path.exists():
            logger.info(f"Creating global database at {self._db_path}")
            
            try:
                # Create all tables
                Base.metadata.create_all(self._engine)
                logger.info("Database schema created successfully")
            except Exception as e:
                logger.error(f"Failed to create database schema: {e}")
                raise
    
    @contextmanager
    def _get_session(self) -> Session:
        """
        Get a session for database operations and handle cleanup.
        
        Yields:
            Session: SQLAlchemy session
        """
        session = self._Session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self) -> None:
        """Close all database connections in the pool."""
        if hasattr(self, '_engine'):
            self._engine.dispose()
    
    def get_or_create_agent(self, agent_id: str) -> int:
        """
        Get or create an agent by ID.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            The agent's database ID
        """
        with self._lock, self._get_session() as session:
            agent = Agent.get_or_create(session, agent_id)
            session.commit()
            
            # Update last_seen timestamp
            agent.update_last_seen()
            session.commit()
            
            return agent.id
    
    def log_event(
        self,
        agent_id: str,
        event_type: str,
        data: Dict[str, Any],
        channel: str = "SYSTEM",
        level: str = "info",
        timestamp: Optional[datetime] = None
    ) -> int:
        """
        Log an event to the database.
        
        Args:
            agent_id: The ID of the agent
            event_type: The type of event
            data: The event data
            channel: The event channel
            level: The event level
            timestamp: The event timestamp (defaults to now)
            
        Returns:
            The event ID
        """
        timestamp = timestamp or datetime.now()
        
        with self._get_session() as session:
            # Get or create the agent and get its ID
            agent_db_obj = Agent.get_or_create(session, agent_id)
            session.flush()  # Flush to ensure agent has an ID
            
            # Create the event
            event = Event.create_event(
                session=session,
                agent_id=agent_db_obj.id,
                event_type=event_type,
                channel=channel,
                level=level.lower(),
                data=data,
                timestamp=timestamp
            )
            
            # Commit the transaction
            session.commit()
            
            return event.id
    
    def log_llm_call(
        self,
        agent_id: str,
        model: str,
        prompt: str,
        response: str,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
        duration_ms: Optional[int] = None,
        is_stream: bool = False,
        temperature: Optional[float] = None,
        cost: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        level: str = "info"
    ) -> int:
        """
        Log an LLM call to the database.
        
        Args:
            agent_id: The ID of the agent
            model: The LLM model name
            prompt: The prompt text
            response: The LLM response text
            tokens_in: Number of input tokens
            tokens_out: Number of output tokens
            duration_ms: Duration in milliseconds
            is_stream: Whether the response was streamed
            temperature: LLM temperature setting
            cost: Cost of the LLM call
            timestamp: The event timestamp (defaults to now)
            level: The event level (defaults to info)
            
        Returns:
            The event ID
        """
        timestamp = timestamp or datetime.now()
        
        with self._get_session() as session:
            # Get or create the agent and get its ID
            agent_db_obj = Agent.get_or_create(session, agent_id)
            session.flush()
            
            # Create the base event first
            event = Event.create_event(
                session=session,
                agent_id=agent_db_obj.id,
                event_type=EventType.LLM_REQUEST,
                channel=EventChannel.LLM,
                level=level.lower(),
                timestamp=timestamp,
                data={"model": model}
            )
            session.flush()
            
            # Create the LLM call record
            llm_call = LLMCall.create_llm_call(
                session=session,
                event_id=event.id,
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
            
            # Commit the transaction
            session.commit()
            
            return event.id
    
    def log_tool_call(
        self,
        agent_id: str,
        tool_name: str,
        input_params: Dict[str, Any],
        output: Optional[Dict[str, Any]] = None,
        success: bool = True,
        duration_ms: Optional[int] = None,
        timestamp: Optional[datetime] = None,
        level: str = "info"
    ) -> int:
        """
        Log a tool call to the database.
        
        Args:
            agent_id: The ID of the agent
            tool_name: The name of the tool
            input_params: The input parameters
            output: The tool output
            success: Whether the tool call succeeded
            duration_ms: Duration in milliseconds
            timestamp: The event timestamp (defaults to now)
            level: The event level (defaults to info)
            
        Returns:
            The event ID
        """
        timestamp = timestamp or datetime.now()
        
        with self._get_session() as session:
            # Get or create the agent and get its ID
            agent_db_obj = Agent.get_or_create(session, agent_id)
            session.flush()
            
            # Create the base event first
            event = Event.create_event(
                session=session,
                agent_id=agent_db_obj.id,
                event_type=EventType.TOOL_CALL,
                channel=EventChannel.TOOL,
                level=level.lower(),
                timestamp=timestamp,
                data={"tool_name": tool_name}
            )
            session.flush()
            
            # Create the tool call record
            tool_call = ToolCall.create_tool_call(
                session=session,
                event_id=event.id,
                tool_name=tool_name,
                input_params=input_params,
                output=output or {},
                success=success,
                duration_ms=duration_ms
            )
            
            # Commit the transaction
            session.commit()
            
            return event.id
    
    def log_security_event(
        self,
        agent_id: str,
        alert_type: str,
        description: str,
        severity: str = "medium",
        related_data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        level: str = "warning"
    ) -> int:
        """
        Log a security event to the database.
        
        Args:
            agent_id: The ID of the agent
            alert_type: The type of security alert
            description: Description of the security alert
            severity: The severity of the alert
            related_data: Additional data related to the alert
            timestamp: The event timestamp (defaults to now)
            level: The event level (defaults to warning)
            
        Returns:
            The event ID
        """
        timestamp = timestamp or datetime.now()
        
        with self._get_session() as session:
            # Get or create the agent and get its ID
            agent_db_obj = Agent.get_or_create(session, agent_id)
            session.flush()
            
            # Create the base event first
            event = Event.create_event(
                session=session,
                agent_id=agent_db_obj.id,
                event_type=EventType.SECURITY_ALERT,
                channel=EventChannel.SYSTEM,
                level=level.lower(),
                timestamp=timestamp,
                data={"alert_type": alert_type}
            )
            session.flush()
            
            # Create the security alert record
            security_alert = SecurityAlert.create_security_alert(
                session=session,
                event_id=event.id,
                alert_type=alert_type,
                description=description,
                severity=severity,
                related_data=related_data or {}
            )
            
            # Commit the transaction
            session.commit()
            
            return event.id
    
    def get_events(
        self,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        channel: Optional[str] = None,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get events from the database.
        
        Args:
            agent_id: Filter by agent ID
            event_type: Filter by event type
            channel: Filter by channel
            level: Filter by level
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of events to return
            offset: Offset for pagination
            
        Returns:
            List of events
        """
        with self._get_session() as session:
            # Start with a query that joins Event and Agent
            query = select(Event).join(Agent)
            
            # Apply filters
            if agent_id:
                query = query.where(Agent.agent_id == agent_id)
            
            if event_type:
                query = query.where(Event.event_type == event_type)
            
            if channel:
                query = query.where(Event.channel == channel)
            
            if level:
                query = query.where(Event.level == level.lower())
            
            if start_time:
                query = query.where(Event.timestamp >= start_time)
            
            if end_time:
                query = query.where(Event.timestamp <= end_time)
            
            # Apply sorting and pagination
            query = query.order_by(Event.timestamp.desc())
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = session.execute(query).scalars().all()
            
            # Convert to dictionaries
            events = []
            for event in result:
                # Get the agent_id from the agent relationship
                agent_id_value = event.agent.agent_id
                
                # Convert to dictionary
                event_dict = {
                    "id": event.id,
                    "agent_id": agent_id_value,
                    "event_type": event.event_type,
                    "channel": event.channel,
                    "level": event.level,
                    "timestamp": event.timestamp,
                    "data": event.data or {}
                }
                events.append(event_dict)
            
            return events
    
    def get_llm_calls(
        self,
        agent_id: Optional[str] = None,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get LLM calls from the database.
        
        Args:
            agent_id: Filter by agent ID
            model: Filter by LLM model
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of events to return
            offset: Offset for pagination
            
        Returns:
            List of LLM call events
        """
        with self._get_session() as session:
            # Start with a query that joins LLMCall, Event, and Agent
            query = (
                select(LLMCall, Event, Agent)
                .join(Event, LLMCall.event_id == Event.id)
                .join(Agent, Event.agent_id == Agent.id)
            )
            
            # Apply filters
            if agent_id:
                query = query.where(Agent.agent_id == agent_id)
            
            if model:
                query = query.where(LLMCall.model == model)
            
            if start_time:
                query = query.where(Event.timestamp >= start_time)
            
            if end_time:
                query = query.where(Event.timestamp <= end_time)
            
            # Apply sorting and pagination
            query = query.order_by(Event.timestamp.desc())
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to dictionaries
            llm_calls = []
            for llm_call, event, agent in result:
                llm_call_dict = {
                    "id": event.id,
                    "agent_id": agent.agent_id,
                    "event_type": event.event_type,
                    "channel": event.channel,
                    "level": event.level,
                    "timestamp": event.timestamp,
                    "model": llm_call.model,
                    "prompt": llm_call.prompt,
                    "response": llm_call.response,
                    "tokens_in": llm_call.tokens_in,
                    "tokens_out": llm_call.tokens_out,
                    "duration_ms": llm_call.duration_ms,
                    "is_stream": llm_call.is_stream,
                    "temperature": llm_call.temperature,
                    "cost": llm_call.cost,
                    "data": event.data or {}
                }
                llm_calls.append(llm_call_dict)
            
            return llm_calls
    
    def get_security_alerts(
        self,
        agent_id: Optional[str] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get security alerts from the database.
        
        Args:
            agent_id: Filter by agent ID
            severity: Filter by alert severity
            alert_type: Filter by alert type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of alerts to return
            offset: Offset for pagination
            
        Returns:
            List of security alert events
        """
        with self._get_session() as session:
            # Start with a query that joins SecurityAlert, Event, and Agent
            query = (
                select(SecurityAlert, Event, Agent)
                .join(Event, SecurityAlert.event_id == Event.id)
                .join(Agent, Event.agent_id == Agent.id)
            )
            
            # Apply filters
            if agent_id:
                query = query.where(Agent.agent_id == agent_id)
            
            if severity:
                query = query.where(SecurityAlert.severity == severity)
            
            if alert_type:
                query = query.where(SecurityAlert.alert_type == alert_type)
            
            if start_time:
                query = query.where(Event.timestamp >= start_time)
            
            if end_time:
                query = query.where(Event.timestamp <= end_time)
            
            # Apply sorting and pagination
            query = query.order_by(Event.timestamp.desc())
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to dictionaries
            alerts = []
            for alert, event, agent in result:
                alert_dict = {
                    "id": event.id,
                    "agent_id": agent.agent_id,
                    "event_type": event.event_type,
                    "channel": event.channel,
                    "level": event.level,
                    "timestamp": event.timestamp,
                    "alert_type": alert.alert_type,
                    "description": alert.description,
                    "severity": alert.severity,
                    "related_data": alert.related_data or {},
                    "data": event.data or {}
                }
                alerts.append(alert_dict)
            
            return alerts
    
    def get_agent_stats(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get agent statistics from the database.
        
        Args:
            agent_id: Filter by agent ID
            
        Returns:
            List of agent statistics
        """
        with self._get_session() as session:
            # Start with a query that selects from Agent
            query = select(Agent)
            
            # Apply filters
            if agent_id:
                query = query.where(Agent.agent_id == agent_id)
            
            # Execute query
            result = session.execute(query).scalars().all()
            
            # Convert to dictionaries with event counts
            stats = []
            for agent in result:
                # Count events for this agent
                events_count = session.execute(
                    select(func.count(Event.id)).where(Event.agent_id == agent.id)
                ).scalar_one()
                
                # Count LLM calls for this agent
                llm_calls_count = session.execute(
                    select(func.count(LLMCall.id))
                    .join(Event, LLMCall.event_id == Event.id)
                    .where(Event.agent_id == agent.id)
                ).scalar_one()
                
                # Get first and last event timestamp
                first_event = session.execute(
                    select(Event.timestamp)
                    .where(Event.agent_id == agent.id)
                    .order_by(Event.timestamp.asc())
                    .limit(1)
                ).scalar_one_or_none()
                
                last_event = session.execute(
                    select(Event.timestamp)
                    .where(Event.agent_id == agent.id)
                    .order_by(Event.timestamp.desc())
                    .limit(1)
                ).scalar_one_or_none()
                
                stats.append({
                    "agent_id": agent.agent_id,
                    "created_at": agent.created_at,
                    "last_seen": agent.last_seen,
                    "events_count": events_count,
                    "llm_calls_count": llm_calls_count,
                    "first_event": first_event,
                    "last_event": last_event
                })
            
            return stats
    
    def get_event_types(self, agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
        """
        Get event types and their counts.
        
        Args:
            agent_id: Filter by agent ID
            
        Returns:
            List of tuples (event_type, count)
        """
        with self._get_session() as session:
            # Build the query
            if agent_id:
                query = (
                    select(Event.event_type, func.count(Event.id).label("count"))
                    .join(Agent, Event.agent_id == Agent.id)
                    .where(Agent.agent_id == agent_id)
                    .group_by(Event.event_type)
                    .order_by(text("count DESC"))
                )
            else:
                query = (
                    select(Event.event_type, func.count(Event.id).label("count"))
                    .group_by(Event.event_type)
                    .order_by(text("count DESC"))
                )
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to list of tuples
            return [(event_type, count) for event_type, count in result]
    
    def get_channels(self, agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
        """
        Get channels and their counts.
        
        Args:
            agent_id: Filter by agent ID
            
        Returns:
            List of tuples (channel, count)
        """
        with self._get_session() as session:
            # Build the query
            if agent_id:
                query = (
                    select(Event.channel, func.count(Event.id).label("count"))
                    .join(Agent, Event.agent_id == Agent.id)
                    .where(Agent.agent_id == agent_id)
                    .group_by(Event.channel)
                    .order_by(text("count DESC"))
                )
            else:
                query = (
                    select(Event.channel, func.count(Event.id).label("count"))
                    .group_by(Event.channel)
                    .order_by(text("count DESC"))
                )
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to list of tuples
            return [(channel, count) for channel, count in result]
    
    def get_levels(self, agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
        """
        Get levels and their counts.
        
        Args:
            agent_id: Filter by agent ID
            
        Returns:
            List of tuples (level, count)
        """
        with self._get_session() as session:
            # Build the query
            if agent_id:
                query = (
                    select(Event.level, func.count(Event.id).label("count"))
                    .join(Agent, Event.agent_id == Agent.id)
                    .where(Agent.agent_id == agent_id)
                    .group_by(Event.level)
                    .order_by(text("count DESC"))
                )
            else:
                query = (
                    select(Event.level, func.count(Event.id).label("count"))
                    .group_by(Event.level)
                    .order_by(text("count DESC"))
                )
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to list of tuples
            return [(level, count) for level, count in result]
    
    def search_events(self, query: str, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search events by full-text search.
        
        Args:
            query: The search query
            agent_id: Filter by agent ID
            limit: Maximum number of events to return
            
        Returns:
            List of matching events
        """
        with self._get_session() as session:
            # Convert query string to SQLite FTS pattern
            search_pattern = f"%{query}%"
            
            # Build the base query
            stmt = (
                select(Event)
                .join(Agent)
            )
            
            # Apply agent filter if provided
            if agent_id:
                stmt = stmt.where(Agent.agent_id == agent_id)
            
            # Apply search filter using JSON functions for data
            stmt = stmt.where(
                (Event.event_type.like(search_pattern)) |
                (Event.channel.like(search_pattern)) |
                (Event.level.like(search_pattern)) |
                (cast(Event.data.as_string(), type_=String).like(search_pattern))
            )
            
            # Apply limit
            stmt = stmt.limit(limit)
            
            # Execute query and convert to dictionaries
            events = []
            for event in session.execute(stmt).scalars().all():
                # Get the agent_id from the agent relationship
                agent_id_value = event.agent.agent_id
                
                event_dict = {
                    "id": event.id,
                    "agent_id": agent_id_value,
                    "event_type": event.event_type,
                    "channel": event.channel,
                    "level": event.level,
                    "timestamp": event.timestamp,
                    "data": event.data or {}
                }
                events.append(event_dict)
            
            return events
    
    def delete_events_before(self, timestamp: datetime) -> int:
        """
        Delete events before the given timestamp.
        
        Args:
            timestamp: Delete events before this timestamp
            
        Returns:
            Number of deleted events
        """
        with self._get_session() as session:
            # Query to count events before timestamp
            count_query = select(func.count(Event.id)).where(Event.timestamp < timestamp)
            count = session.execute(count_query).scalar_one()
            
            # Delete events before timestamp
            delete_query = select(Event).where(Event.timestamp < timestamp)
            events_to_delete = session.execute(delete_query).scalars().all()
            
            for event in events_to_delete:
                session.delete(event)
            
            session.commit()
            
            return count
    
    def vacuum(self) -> None:
        """Vacuum the database to reclaim space."""
        # SQLAlchemy doesn't have a direct method for VACUUM
        # so we use the raw connection
        self._engine.execute(text("VACUUM"))
    
    def get_db_path(self) -> Path:
        """
        Get the path to the database file.
        
        Returns:
            Path to the database file
        """
        return self._db_path 