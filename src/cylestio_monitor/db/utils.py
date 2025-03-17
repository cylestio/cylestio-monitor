"""Utility functions for database operations."""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import func, and_, or_

from .database_manager import DatabaseManager
from .models import (
    Agent, Event, LLMCall, ToolCall, SecurityAlert, 
    Session, Conversation, PerformanceMetric
)

logger = logging.getLogger("CylestioMonitor")


def get_db_manager() -> DatabaseManager:
    """
    Get the database manager instance.
    
    Returns:
        DatabaseManager instance
    """
    return DatabaseManager()


def log_to_db(
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
    from cylestio_monitor.event_logger import log_to_db as event_logger_log_to_db
    
    # Use the new event_logger.log_to_db function which handles the relational schema
    event_logger_log_to_db(
        agent_id=agent_id,
        event_type=event_type,
        data=data,
        channel=channel,
        level=level,
        timestamp=timestamp
    )
    return 0  # Return a dummy ID for backward compatibility


def get_recent_events(
    agent_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get recent events from the database.
    
    Args:
        agent_id: Filter by agent ID
        limit: Maximum number of events to return
        offset: Offset for pagination
        
    Returns:
        List of events
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        query = session.query(Event)
        
        if agent_id:
            # Join with Agent to filter by agent_id string
            query = query.join(Agent).filter(Agent.agent_id == agent_id)
        
        # Order by timestamp descending
        query = query.order_by(Event.timestamp.desc())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute the query
        events = query.all()
        
        # Convert to dictionaries
        return [event.to_dict() for event in events]


def get_events_by_type(
    event_type: str,
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get events by type from the database.
    
    Args:
        event_type: The event type to filter by
        agent_id: Filter by agent ID
        limit: Maximum number of events to return
        
    Returns:
        List of events
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        query = session.query(Event).filter(Event.event_type == event_type)
        
        if agent_id:
            # Join with Agent to filter by agent_id string
            query = query.join(Agent).filter(Agent.agent_id == agent_id)
        
        # Order by timestamp descending
        query = query.order_by(Event.timestamp.desc())
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute the query
        events = query.all()
        
        # Convert to dictionaries
        return [event.to_dict() for event in events]


def get_events_by_channel(
    channel: str,
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get events by channel from the database.
    
    Args:
        channel: The channel to filter by
        agent_id: Filter by agent ID
        limit: Maximum number of events to return
        
    Returns:
        List of events
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        query = session.query(Event).filter(Event.channel == channel.lower())
        
        if agent_id:
            # Join with Agent to filter by agent_id string
            query = query.join(Agent).filter(Agent.agent_id == agent_id)
        
        # Order by timestamp descending
        query = query.order_by(Event.timestamp.desc())
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute the query
        events = query.all()
        
        # Convert to dictionaries
        return [event.to_dict() for event in events]


def get_events_by_level(
    level: str,
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get events by level from the database.
    
    Args:
        level: The level to filter by
        agent_id: Filter by agent ID
        limit: Maximum number of events to return
        
    Returns:
        List of events
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        query = session.query(Event).filter(Event.level == level.lower())
        
        if agent_id:
            # Join with Agent to filter by agent_id string
            query = query.join(Agent).filter(Agent.agent_id == agent_id)
        
        # Order by timestamp descending
        query = query.order_by(Event.timestamp.desc())
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute the query
        events = query.all()
        
        # Convert to dictionaries
        return [event.to_dict() for event in events]


def get_events_by_timeframe(
    start_time: datetime,
    end_time: datetime,
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get events within a timeframe from the database.
    
    Args:
        start_time: The start time
        end_time: The end time
        agent_id: Filter by agent ID
        limit: Maximum number of events to return
        
    Returns:
        List of events
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        query = session.query(Event).filter(
            Event.timestamp >= start_time,
            Event.timestamp <= end_time
        )
        
        if agent_id:
            # Join with Agent to filter by agent_id string
            query = query.join(Agent).filter(Agent.agent_id == agent_id)
        
        # Order by timestamp descending
        query = query.order_by(Event.timestamp.desc())
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute the query
        events = query.all()
        
        # Convert to dictionaries
        return [event.to_dict() for event in events]


def get_events_last_hours(
    hours: int,
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get events from the last N hours from the database.
    
    Args:
        hours: Number of hours to look back
        agent_id: Filter by agent ID
        limit: Maximum number of events to return
        
    Returns:
        List of events
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    return get_events_by_timeframe(start_time, end_time, agent_id, limit)


def get_events_last_days(
    days: int,
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get events from the last N days from the database.
    
    Args:
        days: Number of days to look back
        agent_id: Filter by agent ID
        limit: Maximum number of events to return
        
    Returns:
        List of events
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    return get_events_by_timeframe(start_time, end_time, agent_id, limit)


def search_events(
    query: str,
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Search events by content.
    
    Args:
        query: The search query
        agent_id: Filter by agent ID
        limit: Maximum number of events to return
        
    Returns:
        List of matching events
    """
    db_manager = get_db_manager()
    query_lower = query.lower()
    
    with db_manager.get_session() as session:
        # Create a query for events that might contain the search term
        # This is a simple implementation - a production system would use full-text search
        search_query = session.query(Event).filter(
            or_(
                Event.event_type.ilike(f"%{query_lower}%"),
                Event.channel.ilike(f"%{query_lower}%"),
                Event.level.ilike(f"%{query_lower}%"),
                Event.data.cast(str).ilike(f"%{query_lower}%")
            )
        )
        
        if agent_id:
            # Join with Agent to filter by agent_id string
            search_query = search_query.join(Agent).filter(Agent.agent_id == agent_id)
        
        # Apply limit
        search_query = search_query.limit(limit)
        
        # Execute the query
        events = search_query.all()
        
        # Convert to dictionaries
        return [event.to_dict() for event in events]


def get_agent_stats(agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get statistics for agents.
    
    Args:
        agent_id: Filter by agent ID
        
    Returns:
        List of agent statistics
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        query = session.query(
            Agent.agent_id,
            Agent.name,
            func.count(Event.id).label("event_count"),
            func.min(Event.timestamp).label("first_event"),
            func.max(Event.timestamp).label("last_event")
        ).join(Event, Agent.id == Event.agent_id)
        
        if agent_id:
            query = query.filter(Agent.agent_id == agent_id)
        
        query = query.group_by(Agent.id, Agent.agent_id, Agent.name)
        
        results = query.all()
        
        # Convert to list of dictionaries
        return [
            {
                "agent_id": row.agent_id,
                "name": row.name,
                "event_count": row.event_count,
                "first_event": row.first_event.isoformat() if row.first_event else None,
                "last_event": row.last_event.isoformat() if row.last_event else None
            }
            for row in results
        ]


def get_event_type_distribution(agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
    """
    Get distribution of event types.
    
    Args:
        agent_id: Filter by agent ID
        
    Returns:
        List of tuples (event_type, count)
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        query = session.query(
            Event.event_type,
            func.count(Event.id).label("count")
        ).group_by(Event.event_type)
        
        if agent_id:
            # Join with Agent to filter by agent_id string
            query = query.join(Agent).filter(Agent.agent_id == agent_id)
        
        # Execute the query
        results = query.all()
        
        # Convert to list of tuples
        return [(row.event_type, row.count) for row in results]


def get_channel_distribution(agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
    """
    Get distribution of channels.
    
    Args:
        agent_id: Filter by agent ID
        
    Returns:
        List of tuples (channel, count)
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        query = session.query(
            Event.channel,
            func.count(Event.id).label("count")
        ).group_by(Event.channel)
        
        if agent_id:
            # Join with Agent to filter by agent_id string
            query = query.join(Agent).filter(Agent.agent_id == agent_id)
        
        # Execute the query
        results = query.all()
        
        # Convert to list of tuples
        return [(row.channel, row.count) for row in results]


def get_level_distribution(agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
    """
    Get distribution of event levels.
    
    Args:
        agent_id: Filter by agent ID
        
    Returns:
        List of tuples (level, count)
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        query = session.query(
            Event.level,
            func.count(Event.id).label("count")
        ).group_by(Event.level)
        
        if agent_id:
            # Join with Agent to filter by agent_id string
            query = query.join(Agent).filter(Agent.agent_id == agent_id)
        
        # Execute the query
        results = query.all()
        
        # Convert to list of tuples
        return [(row.level, row.count) for row in results]


def cleanup_old_events(days: int = 30) -> int:
    """
    Remove events older than the specified number of days.
    
    Args:
        days: Number of days to keep
        
    Returns:
        Number of deleted events
    """
    db_manager = get_db_manager()
    cutoff_date = datetime.now() - timedelta(days=days)
    
    with db_manager.get_session() as session:
        # Delete events older than the cutoff date
        deleted_count = session.query(Event).filter(
            Event.timestamp < cutoff_date
        ).delete()
        
        # Commit the changes
        session.commit()
        
        return deleted_count


def optimize_database() -> None:
    """Optimize the database by running VACUUM."""
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        session.execute("PRAGMA optimize")
        session.execute("VACUUM")


def get_db_path() -> str:
    """
    Get the path to the database file.
    
    Returns:
        Path to the database file
    """
    db_manager = get_db_manager()
    db_path = db_manager.get_db_path()
    return str(db_path) if db_path else ""


def get_session_events(session_id: int, agent_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Get all events from a specific session.
    
    Args:
        session_id (int): The session ID to get events for.
        agent_id (Optional[str], optional): Optional agent ID to filter by.
        limit (int, optional): Maximum number of events to return. Defaults to 100.
        offset (int, optional): Offset for pagination. Defaults to 0.
        
    Returns:
        List[Dict[str, Any]]: List of events from the session.
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # First, find the session object
        session_query = session.query(Session).filter(Session.id == session_id)
        
        if agent_id:
            # Join with Agent to filter by agent_id string
            session_query = session_query.join(Agent).filter(Agent.agent_id == agent_id)
        
        session_obj = session_query.first()
        if not session_obj:
            return []
        
        # Now query for events in this session
        events_query = (
            session.query(Event)
            .filter(Event.session_id == session_id)
            .order_by(Event.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        
        # Convert to dictionaries
        return [event.to_dict() for event in events_query.all()]


def get_conversation_events(conversation_id: int, agent_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Get all events from a specific conversation.
    
    Args:
        conversation_id (int): The conversation ID to get events for.
        agent_id (Optional[str], optional): Optional agent ID to filter by.
        limit (int, optional): Maximum number of events to return. Defaults to 100.
        offset (int, optional): Offset for pagination. Defaults to 0.
        
    Returns:
        List[Dict[str, Any]]: List of events from the conversation.
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # First, find the conversation object
        conversation_query = session.query(Conversation).filter(Conversation.id == conversation_id)
        
        if agent_id:
            # Join with Agent through Session to filter by agent_id string
            conversation_query = (
                conversation_query
                .join(Session)
                .join(Agent)
                .filter(Agent.agent_id == agent_id)
            )
        
        conversation_obj = conversation_query.first()
        if not conversation_obj:
            return []
        
        # Now query for events in this conversation
        events_query = (
            session.query(Event)
            .filter(Event.conversation_id == conversation_id)
            .order_by(Event.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        
        # Convert to dictionaries
        return [event.to_dict() for event in events_query.all()]


def get_related_events(
    event_id: int,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get events related to a specific event (e.g., request and response pairs).
    
    Args:
        event_id: The event ID to find related events for
        limit: Maximum number of events to return
        
    Returns:
        List of related events
    """
    db_manager = get_db_manager()
    
    with db_manager.get_session() as session:
        # Get the original event
        event = session.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            return []
        
        related_events = []
        
        # If it's a request, find the corresponding response(s)
        if event.event_type.endswith('_request'):
            # The base event type without the "_request" suffix
            base_type = event.event_type[:-8]
            response_type = f"{base_type}_response"
            
            # Find events with matching response type and the same conversation
            responses = session.query(Event).filter(
                Event.event_type == response_type,
                Event.conversation_id == event.conversation_id,
                Event.timestamp > event.timestamp
            ).order_by(Event.timestamp).limit(limit).all()
            
            related_events.extend(responses)
            
        # If it's a response, find the corresponding request(s)
        elif event.event_type.endswith('_response'):
            # The base event type without the "_response" suffix
            base_type = event.event_type[:-9]
            request_type = f"{base_type}_request"
            
            # Find events with matching request type and the same conversation
            requests = session.query(Event).filter(
                Event.event_type == request_type,
                Event.conversation_id == event.conversation_id,
                Event.timestamp < event.timestamp
            ).order_by(Event.timestamp.desc()).limit(limit).all()
            
            related_events.extend(requests)
            
        # If it has a session, find other events in the same session
        elif event.session_id:
            # Find other events in the same session
            session_events = session.query(Event).filter(
                Event.session_id == event.session_id,
                Event.id != event.id
            ).order_by(Event.timestamp).limit(limit).all()
            
            related_events.extend(session_events)
            
        # Convert to dictionaries
        return [e.to_dict() for e in related_events] 