"""Security models for the Cylestio Monitor database.

This module defines models related to security monitoring, including
security checks, alerts, and event security information.
"""
from __future__ import annotations

import datetime
import enum
from typing import Any, Dict, List, Optional

from sqlalchemy import ForeignKey, Index, String, Text, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from cylestio_monitor.db.models.base import Base


class AlertLevel(str, enum.Enum):
    """Enumeration of security alert levels."""
    
    NONE = "none"
    SUSPICIOUS = "suspicious"
    DANGEROUS = "dangerous"


class AlertSeverity(str, enum.Enum):
    """Enumeration of security alert severities."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventSecurity(Base):
    """Event Security model for storing security-related information for events.
    
    This model captures security-related information for monitored events,
    including alert levels, matched terms, and reasons for alerts.
    """
    
    __tablename__ = "event_security"
    
    # Override id from Base to add auto-increment
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Event Security specific fields from schema
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), 
        nullable=False
    )
    alert_level: Mapped[str] = mapped_column(String(20), nullable=False)
    matched_terms: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        comment="Terms that triggered the alert"
    )
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_field: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="security_event")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_event_security_event_id", "event_id"),
        Index("idx_event_security_alert_level", "alert_level"),
    )
    
    @validates('alert_level')
    def validate_alert_level(self, key: str, value: str) -> str:
        """Validate the alert_level field.
        
        Args:
            key (str): The field name.
            value (str): The field value.
            
        Returns:
            str: The validated value.
            
        Raises:
            ValueError: If the value is not a valid alert level.
        """
        # Allow both string values and enum values
        if isinstance(value, AlertLevel):
            return value.value
        
        # Check if it's a valid alert level
        try:
            return AlertLevel(value).value
        except ValueError:
            # If not in the enum, at least ensure it's not empty
            if not value.strip():
                raise ValueError("Alert level cannot be empty")
            return value
    
    @property
    def is_dangerous(self) -> bool:
        """Check if the security event is marked as dangerous.
        
        Returns:
            bool: True if the event is dangerous, False otherwise.
        """
        return self.alert_level == AlertLevel.DANGEROUS.value
    
    @property
    def is_suspicious(self) -> bool:
        """Check if the security event is marked as suspicious.
        
        Returns:
            bool: True if the event is suspicious, False otherwise.
        """
        return self.alert_level == AlertLevel.SUSPICIOUS.value
    
    @classmethod
    def create_security_event(cls, session, event_id: int, alert_level: str,
                            matched_terms: Optional[List[str]] = None,
                            reason: Optional[str] = None,
                            source_field: Optional[str] = None) -> "EventSecurity":
        """Create a new security event.
        
        Args:
            session: The database session to use.
            event_id (int): The ID of the event this security event is for.
            alert_level (str): The alert level for this security event.
            matched_terms (Optional[List[str]], optional): Terms that triggered the alert.
            reason (Optional[str], optional): Reason for the alert.
            source_field (Optional[str], optional): Field that triggered the alert.
            
        Returns:
            EventSecurity: The newly created security event.
        """
        security_event = cls(
            event_id=event_id,
            alert_level=alert_level,
            matched_terms=matched_terms,
            reason=reason,
            source_field=source_field
        )
        session.add(security_event)
        return security_event
    
    @classmethod
    def count_by_alert_level(cls, session, agent_id: Optional[int] = None,
                           start_time: Optional[datetime.datetime] = None,
                           end_time: Optional[datetime.datetime] = None) -> Dict[str, int]:
        """Count security events by alert level.
        
        Args:
            session: The database session to use.
            agent_id (Optional[int], optional): Filter by agent ID.
            start_time (Optional[datetime.datetime], optional): The earliest time to include.
            end_time (Optional[datetime.datetime], optional): The latest time to include.
            
        Returns:
            Dict[str, int]: A dictionary mapping alert levels to counts.
        """
        from sqlalchemy import func, and_
        from cylestio_monitor.db.models.event import Event
        
        # Build query with all necessary joins
        query = (
            session.query(
                cls.alert_level,
                func.count().label("count")
            )
            .join(Event, cls.event_id == Event.id)
        )
        
        # Apply filters
        filters = []
        if agent_id is not None:
            filters.append(Event.agent_id == agent_id)
        if start_time is not None:
            filters.append(Event.timestamp >= start_time)
        if end_time is not None:
            filters.append(Event.timestamp <= end_time)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Group by alert level and execute
        query = query.group_by(cls.alert_level)
        
        # Convert to dictionary
        return {
            alert_level: count
            for alert_level, count in query.all()
        }


class SecurityAlert(Base):
    """Security Alert model for high-level security alerts requiring attention.
    
    This model represents higher-level security alerts that require attention,
    often summarizing or aggregating multiple security events.
    """
    
    __tablename__ = "security_alerts"
    
    # Override id from Base to add auto-increment
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Security Alert specific fields from schema
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), 
        nullable=False
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    matched_terms: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        comment="Terms that triggered the alert"
    )
    action_taken: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime, 
        default=datetime.datetime.utcnow
    )
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="security_alert")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_security_alerts_event_id", "event_id"),
        Index("idx_security_alerts_alert_type", "alert_type"),
        Index("idx_security_alerts_severity", "severity"),
        Index("idx_security_alerts_timestamp", "timestamp"),
    )
    
    @validates('severity')
    def validate_severity(self, key: str, value: str) -> str:
        """Validate the severity field.
        
        Args:
            key (str): The field name.
            value (str): The field value.
            
        Returns:
            str: The validated value.
            
        Raises:
            ValueError: If the value is not a valid severity level.
        """
        # Allow both string values and enum values
        if isinstance(value, AlertSeverity):
            return value.value
        
        # Check if it's a valid severity
        try:
            return AlertSeverity(value).value
        except ValueError:
            # If not in the enum, at least ensure it's not empty
            if not value.strip():
                raise ValueError("Alert severity cannot be empty")
            return value
    
    @property
    def is_critical(self) -> bool:
        """Check if the security alert is critical.
        
        Returns:
            bool: True if the alert is critical, False otherwise.
        """
        return self.severity == AlertSeverity.CRITICAL.value
    
    @property
    def is_high(self) -> bool:
        """Check if the security alert is high severity.
        
        Returns:
            bool: True if the alert is high severity, False otherwise.
        """
        return self.severity == AlertSeverity.HIGH.value
    
    @classmethod
    def create_security_alert(cls, session, event_id: int, alert_type: str,
                             severity: str, description: str,
                             matched_terms: Optional[List[str]] = None,
                             action_taken: Optional[str] = None) -> "SecurityAlert":
        """Create a new security alert.
        
        Args:
            session: The database session to use.
            event_id (int): The ID of the event this security alert is for.
            alert_type (str): The type of security alert.
            severity (str): The severity level of the alert.
            description (str): A description of the alert.
            matched_terms (Optional[List[str]], optional): Terms that triggered the alert.
            action_taken (Optional[str], optional): Action taken in response to the alert.
            
        Returns:
            SecurityAlert: The newly created security alert.
        """
        security_alert = cls(
            event_id=event_id,
            alert_type=alert_type,
            severity=severity,
            description=description,
            matched_terms=matched_terms,
            action_taken=action_taken
        )
        session.add(security_alert)
        return security_alert
    
    @classmethod
    def find_critical_alerts(cls, session, agent_id: Optional[int] = None,
                            days: int = 7, limit: int = 100) -> List["SecurityAlert"]:
        """Find critical security alerts.
        
        Args:
            session: The database session to use.
            agent_id (Optional[int], optional): Filter by agent ID.
            days (int, optional): Number of days to look back.
            limit (int, optional): Maximum number of alerts to return.
            
        Returns:
            List[SecurityAlert]: The critical security alerts.
        """
        from sqlalchemy import and_
        from cylestio_monitor.db.models.event import Event
        
        # Calculate date range
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Build query with all necessary joins
        query = (
            session.query(cls)
            .join(Event, cls.event_id == Event.id)
            .filter(and_(
                cls.severity.in_([AlertSeverity.HIGH.value, AlertSeverity.CRITICAL.value]),
                cls.timestamp >= start_date,
                cls.timestamp <= end_date
            ))
        )
        
        # Apply additional filter if agent_id is provided
        if agent_id is not None:
            query = query.filter(Event.agent_id == agent_id)
        
        # Order by timestamp descending and limit results
        return query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def count_by_severity(cls, session, agent_id: Optional[int] = None,
                         start_time: Optional[datetime.datetime] = None,
                         end_time: Optional[datetime.datetime] = None) -> Dict[str, int]:
        """Count security alerts by severity.
        
        Args:
            session: The database session to use.
            agent_id (Optional[int], optional): Filter by agent ID.
            start_time (Optional[datetime.datetime], optional): The earliest time to include.
            end_time (Optional[datetime.datetime], optional): The latest time to include.
            
        Returns:
            Dict[str, int]: A dictionary mapping severity levels to counts.
        """
        from sqlalchemy import func, and_
        from cylestio_monitor.db.models.event import Event
        
        # Build query with all necessary joins
        query = (
            session.query(
                cls.severity,
                func.count().label("count")
            )
            .join(Event, cls.event_id == Event.id)
        )
        
        # Apply filters
        filters = []
        if agent_id is not None:
            filters.append(Event.agent_id == agent_id)
        if start_time is not None:
            filters.append(cls.timestamp >= start_time)
        if end_time is not None:
            filters.append(cls.timestamp <= end_time)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Group by severity and execute
        query = query.group_by(cls.severity)
        
        # Convert to dictionary
        return {
            severity: count
            for severity, count in query.all()
        } 