"""SQLAlchemy models for the Cylestio Monitor database.

This package contains all SQLAlchemy models used in the Cylestio Monitor database,
implementing the relational database schema for monitoring AI agents.
"""
from __future__ import annotations

# Import and re-export all models
from cylestio_monitor.db.models.base import Base
from cylestio_monitor.db.models.agent import Agent
from cylestio_monitor.db.models.session import Session, Conversation
from cylestio_monitor.db.models.event import (
    Event, EventType, EventLevel, EventDirection, EventChannel
)
from cylestio_monitor.db.models.llm import LLMCall
from cylestio_monitor.db.models.tool import ToolCall
from cylestio_monitor.db.models.security import (
    EventSecurity, SecurityAlert, AlertLevel, AlertSeverity
)
from cylestio_monitor.db.models.performance import PerformanceMetric

# Define a list of all models for use in database operations
__all__ = [
    "Base",
    "Agent",
    "Session",
    "Conversation",
    "Event", 
    "EventType", 
    "EventLevel", 
    "EventDirection", 
    "EventChannel",
    "LLMCall",
    "ToolCall",
    "EventSecurity", 
    "SecurityAlert", 
    "AlertLevel", 
    "AlertSeverity",
    "PerformanceMetric",
]

# Convenience function to get all models for metadata creation
def get_all_models():
    """Get a list of all model classes.
    
    Returns:
        list: A list of all model classes.
    """
    return [
        Agent,
        Session,
        Conversation,
        Event,
        LLMCall,
        ToolCall,
        EventSecurity,
        SecurityAlert,
        PerformanceMetric,
    ] 