#!/usr/bin/env python3
"""
Visualization script for Cylestio Monitor synthetic data.

This script generates various visualizations of the synthetic monitoring data
to help analyze patterns and distributions.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple

import matplotlib.pyplot as plt
import pandas as pd

def get_db_connection() -> sqlite3.Connection:
    """Connect to the Cylestio Monitor database."""
    db_path = Path.home() / ".cylestio" / "monitor.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}. Run generate_synthetic_data.py first.")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def load_events_to_dataframe(conn: sqlite3.Connection) -> pd.DataFrame:
    """Load events from the database into a pandas DataFrame."""
    # Query to get all events with agent_id
    query = """
    SELECT 
        e.id, 
        a.agent_id, 
        e.event_type, 
        e.channel, 
        e.level, 
        e.timestamp, 
        e.data
    FROM events e
    JOIN agents a ON e.agent_id = a.id
    ORDER BY e.timestamp
    """
    
    # Load data into DataFrame
    df = pd.read_sql_query(query, conn)
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract alert level from data JSON
    df['alert'] = df['data'].apply(lambda x: json.loads(x).get('alert', 'none'))
    
    return df

def plot_events_over_time(df: pd.DataFrame) -> None:
    """Plot the number of events over time."""
    # Resample by day
    events_per_day = df.resample('D', on='timestamp').size()
    
    plt.figure(figsize=(12, 6))
    events_per_day.plot(kind='line', marker='o')
    plt.title('Events per Day')
    plt.xlabel('Date')
    plt.ylabel('Number of Events')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('events_per_day.png')
    print(f"Saved plot to events_per_day.png")

def plot_events_by_agent(df: pd.DataFrame) -> None:
    """Plot the distribution of events by agent."""
    events_by_agent = df['agent_id'].value_counts()
    
    plt.figure(figsize=(10, 6))
    events_by_agent.plot(kind='bar', color='skyblue')
    plt.title('Events by Agent')
    plt.xlabel('Agent')
    plt.ylabel('Number of Events')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('events_by_agent.png')
    print(f"Saved plot to events_by_agent.png")

def plot_events_by_type(df: pd.DataFrame) -> None:
    """Plot the distribution of events by type."""
    events_by_type = df['event_type'].value_counts().head(15)  # Top 15 event types
    
    plt.figure(figsize=(12, 6))
    events_by_type.plot(kind='bar', color='lightgreen')
    plt.title('Top 15 Event Types')
    plt.xlabel('Event Type')
    plt.ylabel('Number of Events')
    plt.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('events_by_type.png')
    print(f"Saved plot to events_by_type.png")

def plot_events_by_channel(df: pd.DataFrame) -> None:
    """Plot the distribution of events by channel."""
    events_by_channel = df['channel'].value_counts()
    
    plt.figure(figsize=(10, 6))
    plt.pie(events_by_channel, labels=events_by_channel.index, autopct='%1.1f%%', 
            startangle=90, shadow=True, explode=[0.05] * len(events_by_channel))
    plt.title('Events by Channel')
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.tight_layout()
    plt.savefig('events_by_channel.png')
    print(f"Saved plot to events_by_channel.png")

def plot_events_by_level(df: pd.DataFrame) -> None:
    """Plot the distribution of events by level."""
    events_by_level = df['level'].value_counts()
    
    plt.figure(figsize=(10, 6))
    plt.pie(events_by_level, labels=events_by_level.index, autopct='%1.1f%%', 
            startangle=90, shadow=True, colors=['green', 'orange', 'red'])
    plt.title('Events by Level')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('events_by_level.png')
    print(f"Saved plot to events_by_level.png")

def plot_events_by_alert(df: pd.DataFrame) -> None:
    """Plot the distribution of events by alert level."""
    events_by_alert = df['alert'].value_counts()
    
    plt.figure(figsize=(10, 6))
    colors = {'none': 'green', 'suspicious': 'orange', 'dangerous': 'red'}
    plt.pie(events_by_alert, labels=events_by_alert.index, autopct='%1.1f%%', 
            startangle=90, shadow=True, 
            colors=[colors.get(alert, 'gray') for alert in events_by_alert.index])
    plt.title('Events by Alert Level')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('events_by_alert.png')
    print(f"Saved plot to events_by_alert.png")

def plot_hourly_distribution(df: pd.DataFrame) -> None:
    """Plot the distribution of events by hour of day."""
    df['hour'] = df['timestamp'].dt.hour
    events_by_hour = df['hour'].value_counts().sort_index()
    
    plt.figure(figsize=(12, 6))
    events_by_hour.plot(kind='bar', color='purple')
    plt.title('Events by Hour of Day')
    plt.xlabel('Hour')
    plt.ylabel('Number of Events')
    plt.grid(True, alpha=0.3, axis='y')
    plt.xticks(range(24), [f"{h:02d}:00" for h in range(24)], rotation=45)
    plt.tight_layout()
    plt.savefig('events_by_hour.png')
    print(f"Saved plot to events_by_hour.png")

def plot_weekday_distribution(df: pd.DataFrame) -> None:
    """Plot the distribution of events by day of week."""
    df['weekday'] = df['timestamp'].dt.day_name()
    events_by_weekday = df['weekday'].value_counts()
    
    # Reorder days of week
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    events_by_weekday = events_by_weekday.reindex(days_order)
    
    plt.figure(figsize=(10, 6))
    events_by_weekday.plot(kind='bar', color='teal')
    plt.title('Events by Day of Week')
    plt.xlabel('Day')
    plt.ylabel('Number of Events')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('events_by_weekday.png')
    print(f"Saved plot to events_by_weekday.png")

def plot_response_times(df: pd.DataFrame) -> None:
    """Plot the distribution of response times for LLM calls."""
    # Filter for LLM_call_finish events
    llm_finish_df = df[df['event_type'] == 'LLM_call_finish'].copy()
    
    # Extract duration_ms from data JSON
    llm_finish_df['duration_ms'] = llm_finish_df['data'].apply(
        lambda x: json.loads(x).get('duration_ms', 0)
    )
    
    plt.figure(figsize=(12, 6))
    plt.hist(llm_finish_df['duration_ms'], bins=30, alpha=0.7, color='blue')
    plt.title('Distribution of LLM Response Times')
    plt.xlabel('Duration (ms)')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('llm_response_times.png')
    print(f"Saved plot to llm_response_times.png")

def plot_token_usage(df: pd.DataFrame) -> None:
    """Plot the distribution of token usage for LLM calls."""
    # Filter for LLM_call_finish events
    llm_finish_df = df[df['event_type'] == 'LLM_call_finish'].copy()
    
    # Extract tokens_used from data JSON
    llm_finish_df['tokens_used'] = llm_finish_df['data'].apply(
        lambda x: json.loads(x).get('tokens_used', 0)
    )
    
    plt.figure(figsize=(12, 6))
    plt.hist(llm_finish_df['tokens_used'], bins=30, alpha=0.7, color='green')
    plt.title('Distribution of LLM Token Usage')
    plt.xlabel('Tokens Used')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('llm_token_usage.png')
    print(f"Saved plot to llm_token_usage.png")

def plot_alert_trends(df: pd.DataFrame) -> None:
    """Plot trends in alert levels over time."""
    # Create a copy of the dataframe with just the date
    df_alerts = df.copy()
    df_alerts['date'] = df_alerts['timestamp'].dt.date
    
    # Group by date and alert level
    alert_counts = df_alerts.groupby(['date', 'alert']).size().unstack(fill_value=0)
    
    # Make sure all alert levels are represented
    for alert in ['none', 'suspicious', 'dangerous']:
        if alert not in alert_counts.columns:
            alert_counts[alert] = 0
    
    plt.figure(figsize=(12, 6))
    alert_counts.plot(kind='area', stacked=True, alpha=0.7, 
                     color=['green', 'orange', 'red'])
    plt.title('Alert Levels Over Time')
    plt.xlabel('Date')
    plt.ylabel('Number of Events')
    plt.grid(True, alpha=0.3)
    plt.legend(title='Alert Level')
    plt.tight_layout()
    plt.savefig('alert_trends.png')
    print(f"Saved plot to alert_trends.png")

def main():
    """Generate visualizations of the synthetic data."""
    print("Cylestio Monitor - Data Visualization")
    print("=====================================")
    
    try:
        # Connect to the database
        conn = get_db_connection()
        
        # Load data into DataFrame
        print("Loading data from database...")
        df = load_events_to_dataframe(conn)
        print(f"Loaded {len(df)} events")
        
        # Generate visualizations
        print("\nGenerating visualizations...")
        plot_events_over_time(df)
        plot_events_by_agent(df)
        plot_events_by_type(df)
        plot_events_by_channel(df)
        plot_events_by_level(df)
        plot_events_by_alert(df)
        plot_hourly_distribution(df)
        plot_weekday_distribution(df)
        plot_response_times(df)
        plot_token_usage(df)
        plot_alert_trends(df)
        
        # Close the database connection
        conn.close()
        
        print("\nVisualization complete! Check the current directory for PNG files.")
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main() 