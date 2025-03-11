#!/usr/bin/env python3
"""
Test script to verify that synthetic data was generated correctly.

This script connects to the Cylestio Monitor database and runs various queries
to check that the synthetic data was generated with the expected properties.
"""

import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple

def get_db_connection() -> sqlite3.Connection:
    """Connect to the Cylestio Monitor database."""
    db_path = Path.home() / ".cylestio" / "monitor.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}. Run generate_synthetic_data.py first.")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def test_agents_exist(conn: sqlite3.Connection) -> None:
    """Test that all expected agents exist in the database."""
    expected_agents = [
        "weather-agent",
        "finance-agent",
        "healthcare-agent",
        "retail-agent",
        "security-agent",
    ]
    
    cursor = conn.cursor()
    cursor.execute("SELECT agent_id FROM agents")
    agents = [row["agent_id"] for row in cursor.fetchall()]
    
    print("\n=== Agent Test ===")
    print(f"Found {len(agents)} agents in the database")
    
    for agent in expected_agents:
        if agent in agents:
            print(f"✅ Agent '{agent}' exists")
        else:
            print(f"❌ Agent '{agent}' not found")

def test_event_counts(conn: sqlite3.Connection) -> None:
    """Test that events were generated for each agent."""
    cursor = conn.cursor()
    
    # Get total event count
    cursor.execute("SELECT COUNT(*) as count FROM events")
    total_count = cursor.fetchone()["count"]
    
    # Get event count per agent
    cursor.execute("""
        SELECT a.agent_id, COUNT(e.id) as count
        FROM events e
        JOIN agents a ON e.agent_id = a.id
        GROUP BY a.agent_id
    """)
    agent_counts = {row["agent_id"]: row["count"] for row in cursor.fetchall()}
    
    print("\n=== Event Count Test ===")
    print(f"Total events: {total_count}")
    
    for agent_id, count in agent_counts.items():
        print(f"Agent '{agent_id}': {count} events")

def test_event_types(conn: sqlite3.Connection) -> None:
    """Test that various event types were generated."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT event_type, COUNT(*) as count
        FROM events
        GROUP BY event_type
        ORDER BY count DESC
    """)
    event_types = {row["event_type"]: row["count"] for row in cursor.fetchall()}
    
    print("\n=== Event Type Test ===")
    print(f"Found {len(event_types)} different event types")
    
    for event_type, count in event_types.items():
        print(f"Event type '{event_type}': {count} events")

def test_channels(conn: sqlite3.Connection) -> None:
    """Test that events were generated for different channels."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT channel, COUNT(*) as count
        FROM events
        GROUP BY channel
        ORDER BY count DESC
    """)
    channels = {row["channel"]: row["count"] for row in cursor.fetchall()}
    
    print("\n=== Channel Test ===")
    print(f"Found {len(channels)} different channels")
    
    for channel, count in channels.items():
        print(f"Channel '{channel}': {count} events")

def test_alert_levels(conn: sqlite3.Connection) -> None:
    """Test that events were generated with different alert levels."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT json_extract(data, '$.alert') as alert, COUNT(*) as count
        FROM events
        WHERE json_extract(data, '$.alert') IS NOT NULL
        GROUP BY alert
        ORDER BY count DESC
    """)
    alerts = {row["alert"]: row["count"] for row in cursor.fetchall()}
    
    print("\n=== Alert Level Test ===")
    print(f"Found {len(alerts)} different alert levels")
    
    for alert, count in alerts.items():
        print(f"Alert level '{alert}': {count} events")

def test_time_distribution(conn: sqlite3.Connection) -> None:
    """Test that events were distributed over the expected time period."""
    cursor = conn.cursor()
    
    # Get time range
    cursor.execute("SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time FROM events")
    time_range = cursor.fetchone()
    min_time = datetime.fromisoformat(time_range["min_time"])
    max_time = datetime.fromisoformat(time_range["max_time"])
    
    # Get events per day
    cursor.execute("""
        SELECT date(timestamp) as day, COUNT(*) as count
        FROM events
        GROUP BY day
        ORDER BY day
    """)
    days = {row["day"]: row["count"] for row in cursor.fetchall()}
    
    print("\n=== Time Distribution Test ===")
    print(f"Time range: {min_time} to {max_time}")
    print(f"Total days: {len(days)}")
    
    # Check if weekends have fewer events
    weekday_counts = []
    weekend_counts = []
    
    for day_str, count in days.items():
        day = datetime.fromisoformat(day_str)
        if day.weekday() >= 5:  # Saturday or Sunday
            weekend_counts.append(count)
        else:
            weekday_counts.append(count)
    
    avg_weekday = sum(weekday_counts) / len(weekday_counts) if weekday_counts else 0
    avg_weekend = sum(weekend_counts) / len(weekend_counts) if weekend_counts else 0
    
    print(f"Average events on weekdays: {avg_weekday:.2f}")
    print(f"Average events on weekends: {avg_weekend:.2f}")
    
    if avg_weekend < avg_weekday:
        print("✅ Weekends have fewer events than weekdays, as expected")
    else:
        print("❌ Weekends do not have fewer events than weekdays")

def test_business_hours(conn: sqlite3.Connection) -> None:
    """Test that more events occur during business hours."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
        FROM events
        GROUP BY hour
        ORDER BY hour
    """)
    hours = {int(row["hour"]): row["count"] for row in cursor.fetchall()}
    
    business_hours_count = sum(count for hour, count in hours.items() if 9 <= hour <= 17)
    non_business_hours_count = sum(count for hour, count in hours.items() if hour < 9 or hour > 17)
    
    print("\n=== Business Hours Test ===")
    print(f"Events during business hours (9 AM - 5 PM): {business_hours_count}")
    print(f"Events outside business hours: {non_business_hours_count}")
    
    if business_hours_count > non_business_hours_count:
        print("✅ More events during business hours, as expected")
    else:
        print("❌ Not more events during business hours")
    
    # Print hourly distribution
    print("\nHourly distribution:")
    for hour in range(24):
        count = hours.get(hour, 0)
        bar = "█" * (count // 100)
        print(f"{hour:02d}:00 - {hour:02d}:59: {count:5d} {bar}")

def test_agent_specific_data(conn: sqlite3.Connection) -> None:
    """Test that agent-specific data was generated correctly."""
    cursor = conn.cursor()
    
    agent_specific_fields = {
        "weather-agent": ["location", "temperature", "condition"],
        "finance-agent": ["transaction_id", "transaction_type", "amount"],
        "healthcare-agent": ["patient_id", "department", "priority"],
        "retail-agent": ["order_id", "product", "category"],
        "security-agent": ["event_source", "ip_address", "severity"],
    }
    
    print("\n=== Agent-Specific Data Test ===")
    
    for agent_id, fields in agent_specific_fields.items():
        # Get agent database ID
        cursor.execute("SELECT id FROM agents WHERE agent_id = ?", (agent_id,))
        agent_db_id = cursor.fetchone()
        
        if not agent_db_id:
            print(f"❌ Agent '{agent_id}' not found in database")
            continue
        
        # Get a sample event for this agent
        cursor.execute(
            "SELECT data FROM events WHERE agent_id = ? LIMIT 1", 
            (agent_db_id["id"],)
        )
        sample = cursor.fetchone()
        
        if not sample:
            print(f"❌ No events found for agent '{agent_id}'")
            continue
        
        data = json.loads(sample["data"])
        
        print(f"\nSample data for '{agent_id}':")
        for field in fields:
            if field in data:
                print(f"✅ Field '{field}' found with value: {data[field]}")
            else:
                print(f"❌ Field '{field}' not found")

def main():
    """Run all tests."""
    print("Cylestio Monitor - Synthetic Data Test")
    print("======================================")
    
    try:
        conn = get_db_connection()
        
        # Run tests
        test_agents_exist(conn)
        test_event_counts(conn)
        test_event_types(conn)
        test_channels(conn)
        test_alert_levels(conn)
        test_time_distribution(conn)
        test_business_hours(conn)
        test_agent_specific_data(conn)
        
        conn.close()
        
        print("\n✅ All tests completed")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 