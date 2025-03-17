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
from ..exceptions import DatabaseError

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
        try:
            # Get the data directory
            data_dir = platformdirs.user_data_dir("cylestio_monitor")
            
            # Create the data directory if it doesn't exist
            os.makedirs(data_dir, exist_ok=True)
            
            # Set the database path
            self.db_path = os.path.join(data_dir, "cylestio_monitor.db")
            
            # Create the database if it doesn't exist
            self._ensure_db_exists()
            
            # Initialize the SQLAlchemy engine
            self.engine = create_engine(f"sqlite:///{self.db_path}")
            
            # Create all tables
            Base.metadata.create_all(self.engine)
            
            # Create the session factory
            self.Session = sessionmaker(bind=self.engine)
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    def _ensure_db_exists(self) -> None:
        """
        Ensure that the global database file exists.
        
        If the file doesn't exist, create it and initialize the schema.
        """
        if not self.db_path:
            logger.info(f"Creating global database at {self.db_path}")
            
            try:
                # Create all tables
                Base.metadata.create_all(self.engine)
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
        session = self.Session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self) -> None:
        """Close all database connections in the pool."""
        if hasattr(self, 'engine'):
            self.engine.dispose()
    
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
        data: Optional[Dict[str, Any]] = None,
        channel: str = "SYSTEM",
        level: str = "info",
        timestamp: Optional[datetime] = None
    ) -> int:
        """
        Log an event to the database.
        
        Args:
            agent_id: The ID of the agent that generated the event
            event_type: The type of event
            data: Additional event data
            channel: The channel the event was generated on (defaults to "SYSTEM")
            level: The log level of the event (defaults to "info")
            timestamp: The event timestamp (defaults to now)
            
        Returns:
            The event ID
        """
        try:
            # Validate agent exists
            agent = self._get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} does not exist")
            
            # Create event
            event = Event(
                agent=agent,
                event_type=event_type,
                channel=channel,
                level=level,
                data=data or {},
                timestamp=timestamp or datetime.now()
            )
            
            # Log to database
            with self._get_session() as session:
                session.add(event)
                session.commit()
                event_id = event.id
            
            # Log to system logger
            log_level = getattr(logging, level.upper(), logging.INFO)
            logger.log(
                log_level,
                f"Event logged - Type: {event_type}, Channel: {channel}, Agent: {agent_id}",
                extra={
                    "event_id": event_id,
                    "agent_id": agent_id,
                    "event_type": event_type,
                    "channel": channel,
                    "data": data
                }
            )
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            raise DatabaseError(f"Failed to log event: {e}")
    
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
                output_result=output,
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
                matched_terms=related_data.get("matched_terms"),
                action_taken=related_data.get("action_taken")
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
        sort_by: str = 'timestamp',
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get LLM calls from the database with advanced filtering and sorting.
        
        Args:
            agent_id: Filter by agent ID
            model: Filter by LLM model
            start_time: Filter by start time
            end_time: Filter by end time
            sort_by: Field to sort by (timestamp, duration_ms, tokens_in, tokens_out, cost)
            limit: Maximum number of events to return
            offset: Offset for pagination
            
        Returns:
            List of LLM call events with detailed information
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
            
            # Apply dynamic sorting
            sort_field = getattr(LLMCall, sort_by, Event.timestamp)
            query = query.order_by(sort_field.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to dictionaries with detailed information
            llm_calls = []
            for llm_call, event, agent in result:
                call_dict = {
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
                llm_calls.append(call_dict)
            
            return llm_calls
    
    def get_tool_usage(
        self,
        agent_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sort_by: str = 'timestamp',
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get tool usage data with advanced filtering and sorting.
        
        Args:
            agent_id: Filter by agent ID
            tool_name: Filter by tool name
            success: Filter by success status
            start_time: Filter by start time
            end_time: Filter by end time
            sort_by: Field to sort by (timestamp, duration_ms)
            limit: Maximum number of events to return
            offset: Offset for pagination
            
        Returns:
            List of tool usage events with detailed information
        """
        with self._get_session() as session:
            # Start with a query that joins ToolCall, Event, and Agent
            query = (
                select(ToolCall, Event, Agent)
                .join(Event, ToolCall.event_id == Event.id)
                .join(Agent, Event.agent_id == Agent.id)
            )
            
            # Apply filters
            if agent_id:
                query = query.where(Agent.agent_id == agent_id)
            
            if tool_name:
                query = query.where(ToolCall.tool_name == tool_name)
            
            if success is not None:
                query = query.where(ToolCall.success == success)
            
            if start_time:
                query = query.where(Event.timestamp >= start_time)
            
            if end_time:
                query = query.where(Event.timestamp <= end_time)
            
            # Apply dynamic sorting
            sort_field = getattr(ToolCall, sort_by, Event.timestamp)
            query = query.order_by(sort_field.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to dictionaries with detailed information
            tool_calls = []
            for tool_call, event, agent in result:
                call_dict = {
                    "id": event.id,
                    "agent_id": agent.agent_id,
                    "event_type": event.event_type,
                    "channel": event.channel,
                    "level": event.level,
                    "timestamp": event.timestamp,
                    "tool_name": tool_call.tool_name,
                    "input_params": tool_call.input_params or {},
                    "output_result": tool_call.output_result or {},
                    "success": tool_call.success,
                    "error_message": tool_call.error_message,
                    "duration_ms": tool_call.duration_ms,
                    "blocking": tool_call.blocking,
                    "data": event.data or {}
                }
                tool_calls.append(call_dict)
            
            return tool_calls
    
    def get_security_alerts(
        self,
        agent_id: Optional[str] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sort_by: str = 'timestamp',
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get security alerts with advanced filtering and sorting.
        
        Args:
            agent_id: Filter by agent ID
            severity: Filter by alert severity
            alert_type: Filter by alert type
            start_time: Filter by start time
            end_time: Filter by end time
            sort_by: Field to sort by (timestamp, severity)
            limit: Maximum number of alerts to return
            offset: Offset for pagination
            
        Returns:
            List of security alerts with detailed information
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
            
            # Apply dynamic sorting
            sort_field = getattr(SecurityAlert, sort_by, Event.timestamp)
            query = query.order_by(sort_field.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to dictionaries with detailed information
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
                    "severity": alert.severity,
                    "description": alert.description,
                    "matched_terms": alert.matched_terms or [],
                    "action_taken": alert.action_taken,
                    "data": event.data or {}
                }
                alerts.append(alert_dict)
            
            return alerts
    
    def get_performance_metrics(
        self,
        agent_id: Optional[str] = None,
        metric_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sort_by: str = 'timestamp',
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics with advanced filtering and sorting.
        
        Args:
            agent_id: Filter by agent ID
            metric_type: Filter by metric type (memory, cpu, duration, tokens, cost)
            start_time: Filter by start time
            end_time: Filter by end time
            sort_by: Field to sort by (timestamp, memory_usage, cpu_usage, duration_ms, tokens_processed, cost)
            limit: Maximum number of events to return
            offset: Offset for pagination
            
        Returns:
            List of performance metrics with detailed information
        """
        with self._get_session() as session:
            # Start with a query that joins PerformanceMetric, Event, and Agent
            query = (
                select(PerformanceMetric, Event, Agent)
                .join(Event, PerformanceMetric.event_id == Event.id)
                .join(Agent, Event.agent_id == Agent.id)
            )
            
            # Apply filters
            if agent_id:
                query = query.where(Agent.agent_id == agent_id)
            
            if metric_type:
                # Filter based on metric type
                if metric_type == 'memory':
                    query = query.where(PerformanceMetric.memory_usage.isnot(None))
                elif metric_type == 'cpu':
                    query = query.where(PerformanceMetric.cpu_usage.isnot(None))
                elif metric_type == 'duration':
                    query = query.where(PerformanceMetric.duration_ms.isnot(None))
                elif metric_type == 'tokens':
                    query = query.where(PerformanceMetric.tokens_processed.isnot(None))
                elif metric_type == 'cost':
                    query = query.where(PerformanceMetric.cost.isnot(None))
            
            if start_time:
                query = query.where(Event.timestamp >= start_time)
            
            if end_time:
                query = query.where(Event.timestamp <= end_time)
            
            # Apply dynamic sorting
            sort_field = getattr(PerformanceMetric, sort_by, Event.timestamp)
            query = query.order_by(sort_field.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to dictionaries with detailed information
            metrics = []
            for metric, event, agent in result:
                metric_dict = {
                    "id": event.id,
                    "agent_id": agent.agent_id,
                    "event_type": event.event_type,
                    "channel": event.channel,
                    "level": event.level,
                    "timestamp": event.timestamp,
                    "memory_usage": metric.memory_usage,
                    "cpu_usage": metric.cpu_usage,
                    "duration_ms": metric.duration_ms,
                    "tokens_processed": metric.tokens_processed,
                    "cost": metric.cost,
                    "data": event.data or {}
                }
                metrics.append(metric_dict)
            
            return metrics
    
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
                (text("json_extract(data, '$') LIKE :pattern"))
            ).params(pattern=search_pattern)
            
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
        """
        Vacuum the SQLite database to optimize storage and performance.
        """
        # Ensure database exists
        self._ensure_db_exists()
        
        # Get database path
        db_path = self.db_path
        
        # Close any existing connections
        self.close()
        
        try:
            # Create a new connection directly to the database file
            conn = sqlite3.connect(db_path)
            conn.execute("VACUUM")
            conn.close()
            
            # Reinitialize the engine
            self._initialize()
            
        except sqlite3.Error as e:
            logger.error(f"Failed to vacuum database: {e}")
            raise DatabaseError(f"Failed to vacuum database: {e}")
    
    def get_db_path(self) -> Path:
        """
        Get the path to the database file.
        
        Returns:
            Path to the database file
        """
        return self.db_path
    
    def get_conversation_flow(
        self,
        session_id: str,
        include_llm_details: bool = False,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get the full flow of a conversation with optional LLM details.
        
        Args:
            session_id: The session ID to get the conversation flow for
            include_llm_details: Whether to include detailed LLM information
            limit: Maximum number of events to return
            
        Returns:
            List of conversation events in chronological order
        """
        with self._get_session() as session:
            # Start with a query that joins Event, Agent, and Session
            query = (
                select(Event, Agent, SessionModel)
                .join(Agent, Event.agent_id == Agent.id)
                .join(SessionModel, Event.session_id == SessionModel.id)
                .where(SessionModel.session_id == session_id)
            )
            
            # Add optional LLM call join if details are requested
            if include_llm_details:
                query = query.outerjoin(LLMCall, Event.id == LLMCall.event_id)
            
            # Order by timestamp ascending for chronological flow
            query = query.order_by(Event.timestamp.asc())
            
            # Apply limit
            query = query.limit(limit)
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to dictionaries with conversation flow
            flow = []
            for event, agent, session_model in result:
                event_dict = {
                    "id": event.id,
                    "agent_id": agent.agent_id,
                    "session_id": session_model.session_id,
                    "event_type": event.event_type,
                    "channel": event.channel,
                    "level": event.level,
                    "timestamp": event.timestamp,
                    "data": event.data or {}
                }
                
                # Add LLM details if requested and available
                if include_llm_details and event.llm_call:
                    event_dict.update({
                        "model": event.llm_call.model,
                        "prompt": event.llm_call.prompt,
                        "response": event.llm_call.response,
                        "tokens_in": event.llm_call.tokens_in,
                        "tokens_out": event.llm_call.tokens_out,
                        "duration_ms": event.llm_call.duration_ms,
                        "temperature": event.llm_call.temperature,
                        "cost": event.llm_call.cost
                    })
                
                flow.append(event_dict)
            
            return flow

    def get_agent_activity(
        self,
        agent_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        group_by: str = 'day'
    ) -> List[Dict[str, Any]]:
        """
        Get overall activity for an agent with optional time-based grouping.
        
        Args:
            agent_id: The agent ID to get activity for
            start_time: Filter by start time
            end_time: Filter by end time
            group_by: Time unit to group by (hour, day, week, month)
            
        Returns:
            List of activity metrics grouped by time period
        """
        with self._get_session() as session:
            # Build the base query with necessary joins
            query = (
                select(
                    Event.timestamp,
                    func.count(Event.id).label('event_count'),
                    func.count(LLMCall.id).label('llm_call_count'),
                    func.count(ToolCall.id).label('tool_call_count'),
                    func.count(SecurityAlert.id).label('security_alert_count')
                )
                .join(Agent, Event.agent_id == Agent.id)
                .outerjoin(LLMCall, Event.id == LLMCall.event_id)
                .outerjoin(ToolCall, Event.id == ToolCall.event_id)
                .outerjoin(SecurityAlert, Event.id == SecurityAlert.event_id)
                .where(Agent.agent_id == agent_id)
            )
            
            # Apply time filters
            if start_time:
                query = query.where(Event.timestamp >= start_time)
            if end_time:
                query = query.where(Event.timestamp <= end_time)
            
            # Apply grouping based on time unit
            if group_by == 'hour':
                query = query.group_by(
                    func.strftime('%Y-%m-%d %H:00:00', Event.timestamp)
                )
            elif group_by == 'day':
                query = query.group_by(
                    func.date(Event.timestamp)
                )
            elif group_by == 'week':
                query = query.group_by(
                    func.strftime('%Y-W%W', Event.timestamp)
                )
            elif group_by == 'month':
                query = query.group_by(
                    func.strftime('%Y-%m', Event.timestamp)
                )
            
            # Order by timestamp
            query = query.order_by(Event.timestamp.asc())
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to list of dictionaries
            activity = []
            for timestamp, event_count, llm_count, tool_count, alert_count in result:
                activity.append({
                    "timestamp": timestamp,
                    "event_count": event_count,
                    "llm_call_count": llm_count,
                    "tool_call_count": tool_count,
                    "security_alert_count": alert_count
                })
            
            return activity

    def search_across_events(
        self,
        query: str,
        event_types: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search across all events with advanced filtering.
        
        Args:
            query: The search query string
            event_types: List of event types to search in
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            List of matching events with search context
        """
        with self._get_session() as session:
            # Convert query string to SQLite FTS pattern
            search_pattern = f"%{query}%"
            
            # Build the base query with all necessary joins
            base_query = (
                select(Event, Agent)
                .join(Agent, Event.agent_id == Agent.id)
            )
            
            # Apply filters
            if event_types:
                base_query = base_query.where(Event.event_type.in_(event_types))
            
            if start_time:
                base_query = base_query.where(Event.timestamp >= start_time)
            
            if end_time:
                base_query = base_query.where(Event.timestamp <= end_time)
            
            # Apply search filter using JSON functions for data
            base_query = base_query.where(
                (Event.event_type.like(search_pattern)) |
                (Event.channel.like(search_pattern)) |
                (Event.level.like(search_pattern)) |
                (Event.data['$'].like(search_pattern))
            )
            
            # Apply pagination
            base_query = base_query.limit(limit).offset(offset)
            
            # Execute query
            result = session.execute(base_query).all()
            
            # Convert to dictionaries with search context
            events = []
            for event, agent in result:
                event_dict = {
                    "id": event.id,
                    "agent_id": agent.agent_id,
                    "event_type": event.event_type,
                    "channel": event.channel,
                    "level": event.level,
                    "timestamp": event.timestamp,
                    "data": event.data or {}
                }
                
                # Add search context if available
                if event.data and isinstance(event.data, dict):
                    # Look for the search term in data values
                    for key, value in event.data.items():
                        if isinstance(value, str) and query.lower() in value.lower():
                            event_dict["search_context"] = {
                                "field": key,
                                "value": value
                            }
                            break
                
                events.append(event_dict)
            
            return events
    
    def count_events_by_type(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate event counts by type with optional filtering.
        
        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            agent_id: Filter by agent ID
            
        Returns:
            List of event type counts with percentages
        """
        with self._get_session() as session:
            # Build the base query
            query = (
                select(
                    Event.event_type,
                    func.count(Event.id).label('count')
                )
                .join(Agent, Event.agent_id == Agent.id)
            )
            
            # Apply filters
            if agent_id:
                query = query.where(Agent.agent_id == agent_id)
            
            if start_time:
                query = query.where(Event.timestamp >= start_time)
            
            if end_time:
                query = query.where(Event.timestamp <= end_time)
            
            # Group by event type
            query = query.group_by(Event.event_type)
            
            # Execute query
            result = session.execute(query).all()
            
            # Calculate total for percentage
            total = sum(count for _, count in result)
            
            # Convert to list of dictionaries with percentages
            counts = []
            for event_type, count in result:
                counts.append({
                    "event_type": event_type,
                    "count": count,
                    "percentage": (count / total * 100) if total > 0 else 0
                })
            
            return counts

    def count_security_alerts_by_severity(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get security alert counts by severity level with optional filtering.
        
        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            agent_id: Filter by agent ID
            
        Returns:
            List of security alert counts by severity
        """
        with self._get_session() as session:
            # Build the base query
            query = (
                select(
                    SecurityAlert.severity,
                    func.count(SecurityAlert.id).label('count')
                )
                .join(Event, SecurityAlert.event_id == Event.id)
                .join(Agent, Event.agent_id == Agent.id)
            )
            
            # Apply filters
            if agent_id:
                query = query.where(Agent.agent_id == agent_id)
            
            if start_time:
                query = query.where(Event.timestamp >= start_time)
            
            if end_time:
                query = query.where(Event.timestamp <= end_time)
            
            # Group by severity
            query = query.group_by(SecurityAlert.severity)
            
            # Execute query
            result = session.execute(query).all()
            
            # Calculate total for percentage
            total = sum(count for _, count in result)
            
            # Convert to list of dictionaries with percentages
            counts = []
            for severity, count in result:
                counts.append({
                    "severity": severity,
                    "count": count,
                    "percentage": (count / total * 100) if total > 0 else 0
                })
            
            return counts

    def calculate_avg_response_time(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        group_by: str = 'model'
    ) -> List[Dict[str, Any]]:
        """
        Calculate average LLM response times with optional grouping.
        
        Args:
            agent_id: Filter by agent ID
            start_time: Filter by start time
            end_time: Filter by end time
            group_by: Field to group by (model, hour, day, week, month)
            
        Returns:
            List of average response times by group
        """
        with self._get_session() as session:
            # Build the base query
            query = (
                select(
                    LLMCall.model,
                    func.avg(LLMCall.duration_ms).label('avg_duration'),
                    func.count(LLMCall.id).label('call_count')
                )
                .join(Event, LLMCall.event_id == Event.id)
                .join(Agent, Event.agent_id == Agent.id)
                .where(LLMCall.duration_ms.isnot(None))
            )
            
            # Apply filters
            if agent_id:
                query = query.where(Agent.agent_id == agent_id)
            
            if start_time:
                query = query.where(Event.timestamp >= start_time)
            
            if end_time:
                query = query.where(Event.timestamp <= end_time)
            
            # Apply grouping based on specified field
            if group_by == 'model':
                query = query.group_by(LLMCall.model)
            elif group_by == 'hour':
                query = query.group_by(
                    func.strftime('%Y-%m-%d %H:00:00', Event.timestamp)
                )
            elif group_by == 'day':
                query = query.group_by(
                    func.date(Event.timestamp)
                )
            elif group_by == 'week':
                query = query.group_by(
                    func.strftime('%Y-W%W', Event.timestamp)
                )
            elif group_by == 'month':
                query = query.group_by(
                    func.strftime('%Y-%m', Event.timestamp)
                )
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to list of dictionaries
            response_times = []
            for group, avg_duration, call_count in result:
                response_times.append({
                    "group": group,
                    "avg_duration_ms": round(avg_duration, 2),
                    "call_count": call_count
                })
            
            return response_times

    def identify_slowest_operations(
        self,
        limit: int = 10,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        operation_type: str = 'llm'
    ) -> List[Dict[str, Any]]:
        """
        Find slowest operations by type with optional time filtering.
        
        Args:
            limit: Maximum number of slow operations to return
            start_time: Filter by start time
            end_time: Filter by end time
            operation_type: Type of operation to analyze (llm, tool)
            
        Returns:
            List of slowest operations with timing details
        """
        with self._get_session() as session:
            if operation_type == 'llm':
                # Query for slowest LLM calls
                query = (
                    select(LLMCall, Event, Agent)
                    .join(Event, LLMCall.event_id == Event.id)
                    .join(Agent, Event.agent_id == Agent.id)
                    .where(LLMCall.duration_ms.isnot(None))
                )
            else:
                # Query for slowest tool calls
                query = (
                    select(ToolCall, Event, Agent)
                    .join(Event, ToolCall.event_id == Event.id)
                    .join(Agent, Event.agent_id == Agent.id)
                    .where(ToolCall.duration_ms.isnot(None))
                )
            
            # Apply time filters
            if start_time:
                query = query.where(Event.timestamp >= start_time)
            
            if end_time:
                query = query.where(Event.timestamp <= end_time)
            
            # Order by duration and limit results
            duration_field = LLMCall.duration_ms if operation_type == 'llm' else ToolCall.duration_ms
            query = query.order_by(duration_field.desc()).limit(limit)
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to list of dictionaries
            slow_ops = []
            for op, event, agent in result:
                if operation_type == 'llm':
                    op_dict = {
                        "id": event.id,
                        "agent_id": agent.agent_id,
                        "timestamp": event.timestamp,
                        "model": op.model,
                        "duration_ms": op.duration_ms,
                        "tokens_in": op.tokens_in,
                        "tokens_out": op.tokens_out,
                        "cost": op.cost
                    }
                else:
                    op_dict = {
                        "id": event.id,
                        "agent_id": agent.agent_id,
                        "timestamp": event.timestamp,
                        "tool_name": op.tool_name,
                        "duration_ms": op.duration_ms,
                        "success": op.success,
                        "error_message": op.error_message
                    }
                slow_ops.append(op_dict)
            
            return slow_ops

    def calculate_token_usage_by_model(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get token usage statistics by model with optional filtering.
        
        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            agent_id: Filter by agent ID
            
        Returns:
            List of token usage statistics by model
        """
        with self._get_session() as session:
            # Build the base query
            query = (
                select(
                    LLMCall.model,
                    func.sum(LLMCall.tokens_in).label('total_tokens_in'),
                    func.sum(LLMCall.tokens_out).label('total_tokens_out'),
                    func.count(LLMCall.id).label('call_count'),
                    func.sum(LLMCall.cost).label('total_cost')
                )
                .join(Event, LLMCall.event_id == Event.id)
                .join(Agent, Event.agent_id == Agent.id)
                .where(LLMCall.tokens_in.isnot(None))
            )
            
            # Apply filters
            if agent_id:
                query = query.where(Agent.agent_id == agent_id)
            
            if start_time:
                query = query.where(Event.timestamp >= start_time)
            
            if end_time:
                query = query.where(Event.timestamp <= end_time)
            
            # Group by model
            query = query.group_by(LLMCall.model)
            
            # Execute query
            result = session.execute(query).all()
            
            # Convert to list of dictionaries
            usage_stats = []
            for model, tokens_in, tokens_out, call_count, total_cost in result:
                usage_stats.append({
                    "model": model,
                    "total_tokens_in": tokens_in or 0,
                    "total_tokens_out": tokens_out or 0,
                    "call_count": call_count,
                    "total_cost": round(total_cost or 0, 4),
                    "avg_tokens_per_call": round((tokens_in or 0) / call_count, 2) if call_count > 0 else 0
                })
            
            return usage_stats

    def _get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID, creating it if it doesn't exist.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            The agent object or None if it couldn't be created
        """
        try:
            with self._get_session() as session:
                agent = Agent.get_or_create(session, agent_id)
                session.flush()
                return agent
        except Exception as e:
            logger.error(f"Failed to get/create agent: {e}")
            return None 