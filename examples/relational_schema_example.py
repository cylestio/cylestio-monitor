#!/usr/bin/env python3
"""Example script demonstrating the new relational database schema for monitoring.

This example shows how to use the updated monitoring system with different types of events
and how to query the relational database.
"""

import json
import os
import time
from datetime import datetime, timedelta
import random
from pathlib import Path

from cylestio_monitor import (
    enable_monitoring, 
    disable_monitoring, 
    log_to_file_and_db
)
from cylestio_monitor.db.utils import (
    get_recent_events,
    get_session_events,
    get_conversation_events,
    get_related_events,
    get_agent_stats
)
from cylestio_monitor.events_processor import log_event


def simulate_agent_conversation():
    """Simulate a conversation with an agent and log various events."""
    # Start a new session
    session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Log the session start (this will create a session if it doesn't exist)
    log_event(
        "session_start",
        {
            "agent_id": "example_agent",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"environment": "testing"}
        }
    )
    
    # Generate a unique conversation ID
    conversation_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Log user message
    log_event(
        "user_message",
        {
            "content": "Hello, can you help me find information about machine learning?",
            "timestamp": datetime.now().isoformat(),
            "metadata": {"source": "chat_interface"},
            "conversation_id": conversation_id
        }
    )
    
    # Log LLM request
    log_event(
        "llm_request",
        {
            "model": "claude-3-opus-20240229",
            "temperature": 0.7,
            "max_tokens": 2000,
            "prompt": "Hello, can you help me find information about machine learning?",
            "timestamp": datetime.now().isoformat(),
            "conversation_id": conversation_id
        }
    )
    
    # Log LLM response
    log_event(
        "llm_response",
        {
            "model": "claude-3-opus-20240229",
            "content": "I'd be happy to help you find information about machine learning! Machine learning is a subset of artificial intelligence...",
            "completion_tokens": 250,
            "timestamp": datetime.now().isoformat(),
            "conversation_id": conversation_id
        }
    )
    
    # Log tool call
    log_event(
        "tool_call",
        {
            "tool_name": "search_documents",
            "parameters": {"query": "machine learning"},
            "result": {"success": True, "num_matches": 3},
            "timestamp": datetime.now().isoformat(),
            "conversation_id": conversation_id
        }
    )
    
    # Log security alert
    log_event(
        "security_alert",
        {
            "alert_type": "prompt_injection",
            "severity": "medium",
            "content": "Potential prompt injection detected in user message",
            "timestamp": datetime.now().isoformat(),
            "conversation_id": conversation_id
        },
        level="warning"
    )
    
    # Log performance metric
    log_event(
        "performance_metric",
        {
            "metric_type": "latency",
            "value": 0.87,
            "unit": "seconds",
            "timestamp": datetime.now().isoformat(),
            "conversation_id": conversation_id
        }
    )
    
    return session_id, conversation_id


def main():
    """Run the example script."""
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Define paths for monitoring
    db_path = "output/example_monitoring.db"
    log_file = "output/example_monitoring.json"
    
    # Remove old files if they exist
    for file_path in [db_path, log_file]:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed old file: {file_path}")
    
    print("Enabling monitoring with relational database schema...")
    
    # Enable monitoring with the new configuration
    enable_monitoring(
        agent_id="example_agent",
        config={
            "db_path": db_path,
            "log_file": log_file,
            "development_mode": True  # Enable development features including SQL logging
        }
    )
    
    # Generate unique session and conversation IDs
    session_id, conversation_id = simulate_agent_conversation()
    
    # Log session start
    log_event("session_start", {
        "agent_id": "example_agent",
        "session_id": session_id,
        "metadata": {"client_info": "example script"}
    }, "SYSTEM", "info")
    
    # Simulate agent conversation
    print(f"Simulating a conversation (session_id: {session_id}, conversation_id: {conversation_id})...")
    
    # Wait for events to be processed
    time.sleep(0.5)
    
    # Query the database to show the benefits of the relational schema
    print("\nQuerying the database to show the benefits of the relational schema...")
    
    # Get recent events
    recent_events = get_recent_events(limit=5)
    print(f"\n1. Recent events (showing 5 of {len(recent_events)}):")
    for i, event in enumerate(recent_events[:5], 1):
        print(f"  {i}. {event['event_type']} ({event['channel']}) - {event['timestamp']}")
    
    # Get session events
    session_events = get_session_events(session_id, limit=100)
    print(f"\n2. Events for session {session_id} ({len(session_events)} events):")
    event_types = {}
    for event in session_events:
        event_type = event["event_type"]
        event_types[event_type] = event_types.get(event_type, 0) + 1
    for event_type, count in event_types.items():
        print(f"  - {event_type}: {count} events")
    
    # Get conversation events
    conversation_events = get_conversation_events(conversation_id, limit=100)
    print(f"\n3. Events for conversation {conversation_id} ({len(conversation_events)} events):")
    # Find a request-response pair
    request_event = next((e for e in conversation_events if e["event_type"] == "llm_request"), None)
    if request_event:
        print(f"  - Found LLM request event (ID: {request_event['id']})")
        # Get related events (should find the response)
        related_events = get_related_events(request_event["id"])
        print(f"  - Related events for this request: {len(related_events)}")
        for i, related in enumerate(related_events, 1):
            print(f"    {i}. {related['event_type']} ({related['level']})")
    
    # Get agent statistics
    agent_stats = get_agent_stats()[0]  # Just get the first agent
    print("\n4. Agent statistics:")
    print(f"  - Agent ID: {agent_stats['agent_id']}")
    print(f"  - Total events: {agent_stats['event_count']}")
    print(f"  - First event: {agent_stats['first_event']}")
    print(f"  - Last event: {agent_stats['last_event']}")
    
    # Check JSON file
    with open(log_file, "r") as f:
        json_events = [json.loads(line) for line in f.readlines()]
    
    print(f"\n5. JSON file contains {len(json_events)} events")
    print("  - Event types found in JSON:")
    json_event_types = {}
    for event in json_events:
        event_type = event["event_type"]
        json_event_types[event_type] = json_event_types.get(event_type, 0) + 1
    
    for event_type, count in json_event_types.items():
        print(f"    - {event_type}: {count} events")
    
    # Disable monitoring
    print("\nDisabling monitoring...")
    disable_monitoring()
    
    print("\nExample completed successfully!")


if __name__ == "__main__":
    main() 