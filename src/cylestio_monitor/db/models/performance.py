"""Performance models for the Cylestio Monitor database.

This module defines models related to performance monitoring, including
resource usage, request durations, and other performance metrics.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import ForeignKey, Index, Integer, Float, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from cylestio_monitor.db.models.base import Base


class PerformanceMetric(Base):
    """Performance Metric model for tracking resource usage and performance.
    
    This model stores performance-related metrics for events, including
    memory usage, CPU usage, duration, tokens processed, and estimated cost.
    """
    
    __tablename__ = "performance_metrics"
    
    # Override id from Base to add auto-increment
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Performance Metric specific fields from schema
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), 
        nullable=False
    )
    memory_usage: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True,
        comment="Memory usage in bytes"
    )
    cpu_usage: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        comment="CPU usage percentage"
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True,
        comment="Duration in milliseconds"
    )
    tokens_processed: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True,
        comment="Number of tokens processed"
    )
    cost: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        comment="Estimated cost"
    )
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="performance_metric")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_performance_metrics_event_id", "event_id"),
    )
    
    @validates('memory_usage', 'tokens_processed')
    def validate_non_negative_int(self, key: str, value: Optional[int]) -> Optional[int]:
        """Validate non-negative integer fields.
        
        Args:
            key (str): The field name.
            value (Optional[int]): The field value.
            
        Returns:
            Optional[int]: The validated value.
            
        Raises:
            ValueError: If the value is negative.
        """
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @validates('cpu_usage')
    def validate_cpu_usage(self, key: str, value: Optional[float]) -> Optional[float]:
        """Validate the cpu_usage field.
        
        Args:
            key (str): The field name.
            value (Optional[float]): The field value.
            
        Returns:
            Optional[float]: The validated value.
            
        Raises:
            ValueError: If the value is negative or greater than 100.
        """
        if value is not None:
            if value < 0:
                raise ValueError("cpu_usage cannot be negative")
            if value > 100:
                raise ValueError("cpu_usage cannot be greater than 100")
        return value
    
    @validates('duration_ms')
    def validate_duration(self, key: str, value: Optional[int]) -> Optional[int]:
        """Validate the duration_ms field.
        
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
    
    @validates('cost')
    def validate_cost(self, key: str, value: Optional[float]) -> Optional[float]:
        """Validate the cost field.
        
        Args:
            key (str): The field name.
            value (Optional[float]): The field value.
            
        Returns:
            Optional[float]: The validated value.
            
        Raises:
            ValueError: If the value is negative.
        """
        if value is not None and value < 0:
            raise ValueError("cost cannot be negative")
        return value
    
    @property
    def duration_sec(self) -> Optional[float]:
        """Get the duration in seconds.
        
        Returns:
            Optional[float]: The duration in seconds, or None if duration_ms is None.
        """
        if self.duration_ms is None:
            return None
        return self.duration_ms / 1000.0
    
    @classmethod
    def create_performance_metric(cls, session, event_id: int,
                                memory_usage: Optional[int] = None,
                                cpu_usage: Optional[float] = None,
                                duration_ms: Optional[int] = None,
                                tokens_processed: Optional[int] = None,
                                cost: Optional[float] = None) -> "PerformanceMetric":
        """Create a new performance metric.
        
        Args:
            session: The database session to use.
            event_id (int): The ID of the event this performance metric is for.
            memory_usage (Optional[int], optional): Memory usage in bytes.
            cpu_usage (Optional[float], optional): CPU usage percentage.
            duration_ms (Optional[int], optional): Duration in milliseconds.
            tokens_processed (Optional[int], optional): Number of tokens processed.
            cost (Optional[float], optional): Estimated cost.
            
        Returns:
            PerformanceMetric: The newly created performance metric.
        """
        performance_metric = cls(
            event_id=event_id,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            duration_ms=duration_ms,
            tokens_processed=tokens_processed,
            cost=cost
        )
        session.add(performance_metric)
        return performance_metric
    
    @classmethod
    def get_aggregated_metrics(cls, session, agent_id: Optional[int] = None,
                             start_time: Optional[datetime.datetime] = None,
                             end_time: Optional[datetime.datetime] = None,
                             interval: str = "day") -> List[Dict[str, Any]]:
        """Get aggregated performance metrics over time.
        
        Args:
            session: The database session to use.
            agent_id (Optional[int], optional): Filter by agent ID.
            start_time (Optional[datetime.datetime], optional): The earliest time to include.
            end_time (Optional[datetime.datetime], optional): The latest time to include.
            interval (str, optional): The time interval to group by ('hour', 'day', 'week', 'month').
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing aggregated metrics.
        """
        from sqlalchemy import func, cast, Date
        from cylestio_monitor.db.models.event import Event
        
        # Determine the date function based on the interval
        if interval == "hour":
            date_fn = func.date_trunc("hour", Event.timestamp)
        elif interval == "day":
            date_fn = func.date_trunc("day", Event.timestamp)
        elif interval == "week":
            date_fn = func.date_trunc("week", Event.timestamp)
        elif interval == "month":
            date_fn = func.date_trunc("month", Event.timestamp)
        else:
            date_fn = func.date_trunc("day", Event.timestamp)
        
        # Build query with all necessary joins
        query = (
            session.query(
                date_fn.label("time_period"),
                func.avg(cls.memory_usage).label("avg_memory_usage"),
                func.avg(cls.cpu_usage).label("avg_cpu_usage"),
                func.avg(cls.duration_ms).label("avg_duration_ms"),
                func.sum(cls.tokens_processed).label("total_tokens"),
                func.sum(cls.cost).label("total_cost"),
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
        
        # Group by time period, order by time period, and execute
        query = query.group_by(date_fn).order_by(date_fn)
        
        # Convert to list of dictionaries
        return [
            {
                "time_period": time_period.isoformat() if time_period else None,
                "avg_memory_usage": float(avg_memory_usage) if avg_memory_usage is not None else 0,
                "avg_cpu_usage": float(avg_cpu_usage) if avg_cpu_usage is not None else 0,
                "avg_duration_ms": float(avg_duration_ms) if avg_duration_ms is not None else 0,
                "total_tokens": int(total_tokens) if total_tokens is not None else 0,
                "total_cost": float(total_cost) if total_cost is not None else 0,
                "count": int(count) if count is not None else 0
            }
            for time_period, avg_memory_usage, avg_cpu_usage, avg_duration_ms, total_tokens, total_cost, count in query.all()
        ]
    
    @classmethod
    def get_performance_summary(cls, session, agent_id: Optional[int] = None,
                              days: int = 7) -> Dict[str, Any]:
        """Get a summary of performance metrics.
        
        Args:
            session: The database session to use.
            agent_id (Optional[int], optional): Filter by agent ID.
            days (int, optional): Number of days to include.
            
        Returns:
            Dict[str, Any]: A summary of performance metrics.
        """
        from sqlalchemy import func, and_
        from cylestio_monitor.db.models.event import Event
        
        # Calculate date range
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Build query with all necessary joins
        base_query = (
            session.query(cls)
            .join(Event, cls.event_id == Event.id)
        )
        
        # Apply filters
        filters = []
        if agent_id is not None:
            filters.append(Event.agent_id == agent_id)
        filters.append(Event.timestamp >= start_date)
        filters.append(Event.timestamp <= end_date)
        
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # Calculate aggregate metrics
        count = base_query.count()
        avg_memory = session.query(func.avg(cls.memory_usage)).filter(and_(*filters)).scalar() or 0
        avg_cpu = session.query(func.avg(cls.cpu_usage)).filter(and_(*filters)).scalar() or 0
        avg_duration = session.query(func.avg(cls.duration_ms)).filter(and_(*filters)).scalar() or 0
        total_tokens = session.query(func.sum(cls.tokens_processed)).filter(and_(*filters)).scalar() or 0
        total_cost = session.query(func.sum(cls.cost)).filter(and_(*filters)).scalar() or 0
        
        # Get max values for each metric
        max_memory = session.query(func.max(cls.memory_usage)).filter(and_(*filters)).scalar() or 0
        max_cpu = session.query(func.max(cls.cpu_usage)).filter(and_(*filters)).scalar() or 0
        max_duration = session.query(func.max(cls.duration_ms)).filter(and_(*filters)).scalar() or 0
        
        return {
            "count": count,
            "avg_memory_usage": float(avg_memory),
            "avg_cpu_usage": float(avg_cpu),
            "avg_duration_ms": float(avg_duration),
            "max_memory_usage": float(max_memory),
            "max_cpu_usage": float(max_cpu),
            "max_duration_ms": float(max_duration),
            "total_tokens": int(total_tokens),
            "total_cost": float(total_cost),
            "days": days
        } 