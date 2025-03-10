"""Database manager for Cylestio Monitor.

This module provides a SQLite-based database manager for storing monitoring events.
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import platformdirs

logger = logging.getLogger("CylestioMonitor")


class DBManager:
    """
    Manages the SQLite database for Cylestio Monitor.
    
    This class handles database operations for storing and retrieving monitoring events.
    It uses a global SQLite database stored in a shared location determined by platformdirs,
    ensuring that all instances of the SDK write to the same database regardless of the
    virtual environment in which they're installed.
    """

    _instance: Optional["DBManager"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "DBManager":
        """Implement the singleton pattern."""
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
        self._ensure_db_exists()
        
        # Connection is thread-local
        self._local = threading.local()
    
    def _ensure_db_exists(self) -> None:
        """
        Ensure that the global database file exists.
        
        If the file doesn't exist, create it and initialize the schema.
        """
        if not self._db_path.exists():
            logger.info(f"Creating global database at {self._db_path}")
            
            # Create the directory if it doesn't exist
            os.makedirs(self._data_dir, exist_ok=True)
            
            # Create the database and initialize the schema
            try:
                conn = sqlite3.connect(self._db_path)
                self._create_schema(conn)
                conn.close()
                logger.info("Database schema created successfully")
            except Exception as e:
                logger.error(f"Failed to create database schema: {e}")
                raise
    
    def _create_schema(self, conn: sqlite3.Connection) -> None:
        """
        Create the database schema.
        
        Args:
            conn: SQLite connection
        """
        cursor = conn.cursor()
        
        # Create the agents table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create the events table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            channel TEXT NOT NULL,
            level TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            data JSON NOT NULL,
            FOREIGN KEY (agent_id) REFERENCES agents (id)
        )
        """)
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_agent_id ON events (agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_event_type ON events (event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_channel ON events (channel)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_level ON events (level)")
        
        conn.commit()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a thread-local database connection.
        
        Returns:
            SQLite connection
        """
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self._db_path,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            # Enable JSON1 extension
            self._local.connection.enable_load_extension(True)
            try:
                self._local.connection.load_extension("json1")
            except sqlite3.OperationalError:
                # JSON1 extension is built-in in newer SQLite versions
                pass
            self._local.connection.enable_load_extension(False)
            # Set row factory to return dictionaries
            self._local.connection.row_factory = sqlite3.Row
        
        return self._local.connection
    
    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, "connection") and self._local.connection is not None:
            self._local.connection.close()
            self._local.connection = None
    
    def get_or_create_agent(self, agent_id: str) -> int:
        """
        Get or create an agent by ID.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            The agent's database ID
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Try to get the agent
            cursor.execute(
                "SELECT id FROM agents WHERE agent_id = ?",
                (agent_id,)
            )
            result = cursor.fetchone()
            
            if result:
                # Update last_seen timestamp
                agent_db_id = result[0]
                cursor.execute(
                    "UPDATE agents SET last_seen = ? WHERE id = ?",
                    (datetime.now(), agent_db_id)
                )
            else:
                # Create a new agent
                cursor.execute(
                    "INSERT INTO agents (agent_id, created_at, last_seen) VALUES (?, ?, ?)",
                    (agent_id, datetime.now(), datetime.now())
                )
                agent_db_id = cursor.lastrowid
            
            conn.commit()
            return agent_db_id
    
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
        if timestamp is None:
            timestamp = datetime.now()
        
        agent_db_id = self.get_or_create_agent(agent_id)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO events (agent_id, event_type, channel, level, timestamp, data)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (agent_db_id, event_type, channel, level.lower(), timestamp, json.dumps(data))
        )
        
        conn.commit()
        return cursor.lastrowid
    
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT e.id, a.agent_id, e.event_type, e.channel, e.level, 
               e.timestamp, e.data
        FROM events e
        JOIN agents a ON e.agent_id = a.id
        WHERE 1=1
        """
        params = []
        
        if agent_id:
            query += " AND a.agent_id = ?"
            params.append(agent_id)
        
        if event_type:
            query += " AND e.event_type = ?"
            params.append(event_type)
        
        if channel:
            query += " AND e.channel = ?"
            params.append(channel)
        
        if level:
            query += " AND e.level = ?"
            params.append(level.lower())
        
        if start_time:
            query += " AND e.timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND e.timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY e.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            event["data"] = json.loads(event["data"])
            events.append(event)
        
        return events
    
    def get_agent_stats(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get statistics for agents.
        
        Args:
            agent_id: Filter by agent ID
            
        Returns:
            List of agent statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT a.agent_id, 
               COUNT(e.id) as event_count,
               MIN(e.timestamp) as first_event,
               MAX(e.timestamp) as last_event,
               a.created_at,
               a.last_seen
        FROM agents a
        LEFT JOIN events e ON a.id = e.agent_id
        """
        
        params = []
        if agent_id:
            query += " WHERE a.agent_id = ?"
            params.append(agent_id)
        
        query += " GROUP BY a.id ORDER BY a.agent_id"
        
        cursor.execute(query, params)
        
        stats = []
        for row in cursor.fetchall():
            stats.append(dict(row))
        
        return stats
    
    def get_event_types(self, agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
        """
        Get event types and their counts.
        
        Args:
            agent_id: Filter by agent ID
            
        Returns:
            List of tuples (event_type, count)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT e.event_type, COUNT(e.id) as count
        FROM events e
        JOIN agents a ON e.agent_id = a.id
        """
        
        params = []
        if agent_id:
            query += " WHERE a.agent_id = ?"
            params.append(agent_id)
        
        query += " GROUP BY e.event_type ORDER BY count DESC"
        
        cursor.execute(query, params)
        
        return [(row["event_type"], row["count"]) for row in cursor.fetchall()]
    
    def get_channels(self, agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
        """
        Get channels and their counts.
        
        Args:
            agent_id: Filter by agent ID
            
        Returns:
            List of tuples (channel, count)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT e.channel, COUNT(e.id) as count
        FROM events e
        JOIN agents a ON e.agent_id = a.id
        """
        
        params = []
        if agent_id:
            query += " WHERE a.agent_id = ?"
            params.append(agent_id)
        
        query += " GROUP BY e.channel ORDER BY count DESC"
        
        cursor.execute(query, params)
        
        return [(row["channel"], row["count"]) for row in cursor.fetchall()]
    
    def get_levels(self, agent_id: Optional[str] = None) -> List[Tuple[str, int]]:
        """
        Get levels and their counts.
        
        Args:
            agent_id: Filter by agent ID
            
        Returns:
            List of tuples (level, count)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT e.level, COUNT(e.id) as count
        FROM events e
        JOIN agents a ON e.agent_id = a.id
        """
        
        params = []
        if agent_id:
            query += " WHERE a.agent_id = ?"
            params.append(agent_id)
        
        query += " GROUP BY e.level ORDER BY count DESC"
        
        cursor.execute(query, params)
        
        return [(row["level"], row["count"]) for row in cursor.fetchall()]
    
    def search_events(self, query: str, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for events containing the query string in their data.
        
        Args:
            query: The string to search for
            agent_id: Optional agent ID to filter by
            limit: Maximum number of events to return
            
        Returns:
            List of matching events
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql_query = """
        SELECT e.id, a.agent_id, e.event_type, e.channel, e.level, 
               e.timestamp, e.data
        FROM events e
        JOIN agents a ON e.agent_id = a.id
        WHERE (json_extract(e.data, '$.message') LIKE ?
           OR json_extract(e.data, '$.result') LIKE ?
           OR e.data LIKE ?)
        """
        
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]
        
        if agent_id:
            sql_query += " AND a.agent_id = ?"
            params.append(agent_id)
        
        sql_query += " ORDER BY e.timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql_query, params)
        
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            event["data"] = json.loads(event["data"])
            events.append(event)
        
        return events
    
    def delete_events_before(self, timestamp: datetime) -> int:
        """
        Delete events before a specific timestamp.
        
        Args:
            timestamp: The cutoff timestamp
            
        Returns:
            Number of deleted events
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM events WHERE timestamp < ?",
            (timestamp,)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        return deleted_count
    
    def vacuum(self) -> None:
        """Vacuum the database to reclaim space."""
        conn = self._get_connection()
        conn.execute("VACUUM")
        conn.commit()
    
    def get_db_path(self) -> Path:
        """
        Get the path to the database file.
        
        Returns:
            Path to the database file
        """
        return self._db_path 