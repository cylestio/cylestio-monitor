"""Utility functions for database operations."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .db_manager import DBManager

logger = logging.getLogger("CylestioMonitor")


def get_db_manager() -> DBManager:
    """
    Get the database manager instance.
    
    Returns:
        DBManager instance
    """
    return DBManager()


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
    db_manager = get_db_manager()
    return db_manager.log_event(agent_id, event_type, data, channel, level, timestamp)


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
    return db_manager.get_events(agent_id=agent_id, limit=limit, offset=offset)


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
    return db_manager.get_events(agent_id=agent_id, event_type=event_type, limit=limit)


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
    return db_manager.get_events(agent_id=agent_id, channel=channel, limit=limit)


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
    return db_manager.get_events(agent_id=agent_id, level=level, limit=limit)


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
    return db_manager.get_events(
        agent_id=agent_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )


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
    return db_manager.search_events(query, agent_id, limit)


def get_agent_stats(agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get statistics for agents.
    
    Args:
        agent_id: Filter by agent ID
        
    Returns:
        List of agent statistics
    """
    db_manager = get_db_manager()
    return db_manager.get_agent_stats(agent_id)


def get_event_type_distribution(agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
    """
    Get distribution of event types.
    
    Args:
        agent_id: Filter by agent ID
        
    Returns:
        List of tuples (event_type, count)
    """
    db_manager = get_db_manager()
    return db_manager.get_event_types(agent_id)


def get_channel_distribution(agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
    """
    Get distribution of channels.
    
    Args:
        agent_id: Filter by agent ID
        
    Returns:
        List of tuples (channel, count)
    """
    db_manager = get_db_manager()
    return db_manager.get_channels(agent_id)


def get_level_distribution(agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
    """
    Get distribution of levels.
    
    Args:
        agent_id: Filter by agent ID
        
    Returns:
        List of tuples (level, count)
    """
    db_manager = get_db_manager()
    return db_manager.get_levels(agent_id)


def cleanup_old_events(days: int = 30) -> int:
    """
    Delete events older than the specified number of days.
    
    Args:
        days: Number of days to keep
        
    Returns:
        Number of deleted events
    """
    db_manager = get_db_manager()
    cutoff_date = datetime.now() - timedelta(days=days)
    return db_manager.delete_events_before(cutoff_date)


def optimize_database() -> None:
    """Optimize the database by vacuuming."""
    db_manager = get_db_manager()
    db_manager.vacuum()


def get_db_path() -> str:
    """
    Get the path to the database file.
    
    Returns:
        Path to the database file as a string
    """
    db_manager = get_db_manager()
    return str(db_manager.get_db_path()) 