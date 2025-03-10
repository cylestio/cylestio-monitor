#!/usr/bin/env python3
"""
Generate Synthetic Monitoring Data for Cylestio Monitor

This script generates synthetic monitoring events for five different agents over a one-month period
and inserts them into the SQLite database used by Cylestio Monitor.

The generated data includes varied event types, alert levels, and metrics to provide a comprehensive
demo of the monitoring system's capabilities.
"""

import json
import random
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Define the agents
AGENTS = [
    "weather-agent",  # Handling weather queries
    "finance-agent",  # Processing financial transactions or market data
    "healthcare-agent",  # Managing patient data queries or alerts
    "retail-agent",  # Tracking e-commerce or store activity
    "security-agent",  # Monitoring cybersecurity events
]

# Define event types
EVENT_TYPES = {
    "LLM": [
        "LLM_call_start",
        "LLM_call_finish",
        "LLM_call_blocked",
        "LLM_call_error",
    ],
    "MCP": [
        "MCP_tool_call_start",
        "MCP_tool_call_finish",
        "MCP_tool_call_error",
        "MCP_patch",
    ],
    "SYSTEM": [
        "monitoring_enabled",
        "monitoring_disabled",
        "config_updated",
        "agent_registered",
    ],
    "SECURITY": [
        "security_alert",
        "security_scan_start",
        "security_scan_finish",
        "security_policy_updated",
    ],
    "CUSTOM": [
        "user_query",
        "api_request",
        "data_processed",
        "report_generated",
    ]
}

# Define alert levels
ALERT_LEVELS = ["none", "suspicious", "dangerous"]

# Define suspicious and dangerous keywords for security checks
SUSPICIOUS_KEYWORDS = [
    "REMOVE", "CLEAR", "HACK", "BOMB", "PASSWORD", "CREDENTIALS", 
    "EXPLOIT", "VULNERABILITY", "BYPASS", "OVERRIDE"
]

DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "SHUTDOWN", "EXEC(", "FORMAT", "RM -RF", "KILL",
    "SUDO", "CHMOD 777", "TRUNCATE", "WIPE", "DESTROY"
]

# Define agent-specific data generators
def generate_weather_data() -> Dict[str, Any]:
    """Generate synthetic data for the weather agent."""
    locations = ["New York", "London", "Tokyo", "Sydney", "Paris", "Berlin", "Moscow", "Beijing", "Cairo", "Rio de Janeiro"]
    weather_conditions = ["sunny", "cloudy", "rainy", "snowy", "windy", "foggy", "stormy", "hazy"]
    
    return {
        "location": random.choice(locations),
        "temperature": round(random.uniform(-10, 40), 1),
        "condition": random.choice(weather_conditions),
        "humidity": random.randint(0, 100),
        "wind_speed": round(random.uniform(0, 30), 1),
        "query": f"What's the weather in {random.choice(locations)}?",
    }

def generate_finance_data() -> Dict[str, Any]:
    """Generate synthetic data for the finance agent."""
    transaction_types = ["deposit", "withdrawal", "transfer", "payment", "refund", "investment"]
    currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "BTC", "ETH"]
    stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "WMT"]
    
    return {
        "transaction_id": f"TRX-{random.randint(10000, 99999)}",
        "transaction_type": random.choice(transaction_types),
        "amount": round(random.uniform(1, 10000), 2),
        "currency": random.choice(currencies),
        "stock_symbol": random.choice(stocks) if random.random() > 0.5 else None,
        "account_id": f"ACC-{random.randint(1000, 9999)}",
        "query": "What is the current price of Tesla stock?",
    }

def generate_healthcare_data() -> Dict[str, Any]:
    """Generate synthetic data for the healthcare agent."""
    departments = ["Cardiology", "Neurology", "Oncology", "Pediatrics", "Emergency", "Radiology", "Surgery", "Psychiatry"]
    test_types = ["Blood Test", "X-Ray", "MRI", "CT Scan", "Ultrasound", "EKG", "Biopsy"]
    
    return {
        "patient_id": f"P-{random.randint(10000, 99999)}",
        "department": random.choice(departments),
        "test_type": random.choice(test_types) if random.random() > 0.3 else None,
        "priority": random.choice(["low", "medium", "high", "urgent"]),
        "doctor_id": f"D-{random.randint(100, 999)}",
        "query": "When is my next appointment?",
    }

def generate_retail_data() -> Dict[str, Any]:
    """Generate synthetic data for the retail agent."""
    products = ["Laptop", "Smartphone", "Headphones", "TV", "Camera", "Tablet", "Watch", "Speaker", "Monitor", "Keyboard"]
    categories = ["Electronics", "Clothing", "Home", "Beauty", "Sports", "Books", "Toys", "Grocery", "Furniture"]
    payment_methods = ["Credit Card", "Debit Card", "PayPal", "Apple Pay", "Google Pay", "Gift Card", "Store Credit"]
    
    return {
        "order_id": f"ORD-{random.randint(100000, 999999)}",
        "product": random.choice(products),
        "category": random.choice(categories),
        "quantity": random.randint(1, 10),
        "price": round(random.uniform(10, 2000), 2),
        "payment_method": random.choice(payment_methods),
        "customer_id": f"CUST-{random.randint(1000, 9999)}",
        "query": "Where is my order?",
    }

def generate_security_data() -> Dict[str, Any]:
    """Generate synthetic data for the security agent."""
    event_sources = ["Firewall", "IDS", "Antivirus", "Authentication", "Access Control", "Encryption", "Backup", "Audit"]
    ip_addresses = [f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}" for _ in range(10)]
    threat_types = ["Malware", "Phishing", "DDoS", "Brute Force", "SQL Injection", "XSS", "CSRF", "Insider Threat"]
    
    return {
        "event_source": random.choice(event_sources),
        "ip_address": random.choice(ip_addresses),
        "threat_type": random.choice(threat_types) if random.random() > 0.7 else None,
        "severity": random.choice(["low", "medium", "high", "critical"]),
        "action_taken": random.choice(["blocked", "quarantined", "alerted", "logged", "ignored"]),
        "query": "Has there been any suspicious activity on my account?",
    }

# Map agents to their data generators
AGENT_DATA_GENERATORS = {
    "weather-agent": generate_weather_data,
    "finance-agent": generate_finance_data,
    "healthcare-agent": generate_healthcare_data,
    "retail-agent": generate_retail_data,
    "security-agent": generate_security_data,
}

def generate_llm_call_data(agent_id: str, is_start: bool = True) -> Dict[str, Any]:
    """Generate data for LLM call events."""
    base_data = AGENT_DATA_GENERATORS[agent_id]()
    
    if is_start:
        # For start events, include the prompt
        data = {
            "model": random.choice(["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "llama-3-70b"]),
            "prompt": base_data.get("query", "Default query"),
            "max_tokens": random.choice([256, 512, 1024, 2048, 4096]),
            "temperature": round(random.uniform(0, 1), 1),
        }
    else:
        # For finish events, include response and metrics
        data = {
            "model": random.choice(["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "llama-3-70b"]),
            "tokens_used": random.randint(50, 2000),
            "duration_ms": random.randint(200, 5000),
            "response": f"Response to: {base_data.get('query', 'Default query')}",
        }
    
    # Add agent-specific data
    data.update(base_data)
    return data

def generate_mcp_tool_call_data(agent_id: str, is_start: bool = True) -> Dict[str, Any]:
    """Generate data for MCP tool call events."""
    tools = ["search_web", "query_database", "call_api", "process_file", "send_email", "generate_report"]
    base_data = AGENT_DATA_GENERATORS[agent_id]()
    
    if is_start:
        # For start events, include the tool and parameters
        data = {
            "tool": random.choice(tools),
            "parameters": {"query": base_data.get("query", "Default query")},
            "context": "User requested information",
        }
    else:
        # For finish events, include result and metrics
        data = {
            "tool": random.choice(tools),
            "result": f"Result for: {base_data.get('query', 'Default query')}",
            "duration_ms": random.randint(50, 3000),
            "success": random.random() > 0.1,  # 90% success rate
        }
    
    # Add agent-specific data
    data.update(base_data)
    return data

def generate_security_event_data(agent_id: str, alert_level: str) -> Dict[str, Any]:
    """Generate data for security events with specified alert level."""
    base_data = AGENT_DATA_GENERATORS[agent_id]()
    
    if alert_level == "none":
        data = {
            "alert": "none",
            "message": "Normal operation",
            "scan_result": "No issues found",
        }
    elif alert_level == "suspicious":
        matched_terms = random.sample(SUSPICIOUS_KEYWORDS, k=random.randint(1, 3))
        data = {
            "alert": "suspicious",
            "matched_terms": matched_terms,
            "message": f"Suspicious terms detected: {', '.join(matched_terms)}",
            "action": "logged",
        }
    else:  # dangerous
        matched_terms = random.sample(DANGEROUS_KEYWORDS, k=random.randint(1, 3))
        data = {
            "alert": "dangerous",
            "matched_terms": matched_terms,
            "message": f"Dangerous terms detected: {', '.join(matched_terms)}",
            "action": "blocked",
        }
    
    # Add agent-specific data
    data.update(base_data)
    return data

def generate_system_event_data(agent_id: str, event_type: str) -> Dict[str, Any]:
    """Generate data for system events."""
    base_data = AGENT_DATA_GENERATORS[agent_id]()
    
    if event_type == "monitoring_enabled":
        data = {
            "enabled_by": "admin",
            "config": {
                "log_level": "info",
                "security_checks": True,
                "performance_tracking": True,
            },
        }
    elif event_type == "monitoring_disabled":
        data = {
            "disabled_by": "admin",
            "reason": "maintenance",
            "duration": "1 hour",
        }
    elif event_type == "config_updated":
        data = {
            "updated_by": "admin",
            "changes": {
                "log_level": "debug",
                "security_checks": True,
                "performance_tracking": True,
            },
        }
    else:  # agent_registered
        data = {
            "registered_by": "admin",
            "agent_name": agent_id,
            "capabilities": ["text_generation", "tool_use", "data_processing"],
        }
    
    # Add agent-specific data
    data.update(base_data)
    return data

def generate_custom_event_data(agent_id: str, event_type: str) -> Dict[str, Any]:
    """Generate data for custom events."""
    base_data = AGENT_DATA_GENERATORS[agent_id]()
    
    if event_type == "user_query":
        data = {
            "user_id": f"user-{random.randint(1000, 9999)}",
            "query": base_data.get("query", "Default query"),
            "session_id": f"session-{random.randint(10000, 99999)}",
        }
    elif event_type == "api_request":
        data = {
            "endpoint": f"/api/{random.choice(['query', 'data', 'process', 'analyze'])}",
            "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "status_code": random.choice([200, 201, 400, 401, 403, 404, 500]),
            "duration_ms": random.randint(10, 500),
        }
    elif event_type == "data_processed":
        data = {
            "data_type": random.choice(["text", "image", "audio", "video", "structured"]),
            "size_kb": random.randint(1, 10000),
            "processing_time_ms": random.randint(50, 5000),
            "result": "Processed successfully" if random.random() > 0.1 else "Processing error",
        }
    else:  # report_generated
        data = {
            "report_type": random.choice(["summary", "analysis", "forecast", "recommendation"]),
            "report_id": f"report-{random.randint(1000, 9999)}",
            "generation_time_ms": random.randint(100, 3000),
            "size_kb": random.randint(10, 1000),
        }
    
    # Add agent-specific data
    data.update(base_data)
    return data

def generate_event_data(agent_id: str, event_type: str, alert_level: str = "none") -> Dict[str, Any]:
    """Generate data for a specific event type with the given alert level."""
    if event_type.startswith("LLM_call_"):
        if event_type == "LLM_call_start":
            return generate_llm_call_data(agent_id, is_start=True)
        elif event_type == "LLM_call_finish":
            return generate_llm_call_data(agent_id, is_start=False)
        elif event_type == "LLM_call_blocked":
            return generate_security_event_data(agent_id, "dangerous")
        else:  # LLM_call_error
            data = generate_llm_call_data(agent_id, is_start=False)
            data["error"] = random.choice([
                "Rate limit exceeded",
                "Invalid request",
                "Model overloaded",
                "Connection timeout",
                "Internal server error",
            ])
            return data
    
    elif event_type.startswith("MCP_tool_"):
        if event_type == "MCP_tool_call_start":
            return generate_mcp_tool_call_data(agent_id, is_start=True)
        elif event_type == "MCP_tool_call_finish":
            return generate_mcp_tool_call_data(agent_id, is_start=False)
        elif event_type == "MCP_tool_call_error":
            data = generate_mcp_tool_call_data(agent_id, is_start=False)
            data["error"] = random.choice([
                "Tool not found",
                "Invalid parameters",
                "Execution error",
                "Permission denied",
                "Timeout",
            ])
            return data
        else:  # MCP_patch
            return {
                "patch_id": f"patch-{random.randint(1000, 9999)}",
                "description": "Automatic patch applied",
                "affected_components": random.sample(["parser", "executor", "validator", "logger"], k=random.randint(1, 3)),
                "success": random.random() > 0.1,  # 90% success rate
            }
    
    elif event_type.startswith("security_"):
        return generate_security_event_data(agent_id, alert_level)
    
    elif event_type in ["monitoring_enabled", "monitoring_disabled", "config_updated", "agent_registered"]:
        return generate_system_event_data(agent_id, event_type)
    
    else:  # custom events
        return generate_custom_event_data(agent_id, event_type)

def get_channel_from_event_type(event_type: str) -> str:
    """Determine the channel based on the event type."""
    for channel, events in EVENT_TYPES.items():
        if event_type in events:
            return channel
    return "SYSTEM"  # Default channel

def get_level_from_alert(data: Dict[str, Any]) -> str:
    """Determine the log level based on the alert level in the data."""
    alert = data.get("alert", "none")
    if alert == "dangerous":
        return "error"
    elif alert == "suspicious":
        return "warning"
    else:
        return "info"

def create_database() -> sqlite3.Connection:
    """Create the SQLite database with the required schema."""
    # Get the database path (same as used by Cylestio Monitor)
    db_path = Path.home() / ".cylestio" / "monitor.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
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
    return conn

def get_or_create_agent(conn: sqlite3.Connection, agent_id: str) -> int:
    """Get or create an agent in the database."""
    cursor = conn.cursor()
    
    # Try to get the agent
    cursor.execute("SELECT id FROM agents WHERE agent_id = ?", (agent_id,))
    result = cursor.fetchone()
    
    if result:
        # Update last_seen timestamp
        cursor.execute(
            "UPDATE agents SET last_seen = ? WHERE id = ?",
            (datetime.now(), result[0])
        )
        conn.commit()
        return result[0]
    
    # Create the agent
    cursor.execute(
        "INSERT INTO agents (agent_id, created_at, last_seen) VALUES (?, ?, ?)",
        (agent_id, datetime.now(), datetime.now())
    )
    conn.commit()
    return cursor.lastrowid

def log_event(
    conn: sqlite3.Connection,
    agent_db_id: int,
    event_type: str,
    data: Dict[str, Any],
    channel: str,
    level: str,
    timestamp: datetime
) -> int:
    """Log an event to the database."""
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

def generate_synthetic_data(
    conn: sqlite3.Connection,
    start_date: datetime,
    end_date: datetime,
    events_per_day_per_agent: Tuple[int, int] = (50, 200)
) -> None:
    """Generate synthetic data for all agents over the specified time period."""
    # Get or create agents
    agent_db_ids = {}
    for agent_id in AGENTS:
        agent_db_ids[agent_id] = get_or_create_agent(conn, agent_id)
    
    # Generate events for each day in the time period
    current_date = start_date
    day_count = 0
    
    while current_date <= end_date:
        day_count += 1
        print(f"Generating data for day {day_count}: {current_date.date()}")
        
        for agent_id in AGENTS:
            # Determine number of events for this agent on this day
            # Vary the number of events to create realistic patterns
            # Weekends have fewer events
            is_weekend = current_date.weekday() >= 5
            base_events = events_per_day_per_agent[0] if is_weekend else int(events_per_day_per_agent[0] * 1.5)
            max_events = events_per_day_per_agent[1] if is_weekend else int(events_per_day_per_agent[1] * 1.2)
            
            # Add some randomness to event count
            num_events = random.randint(base_events, max_events)
            
            # Generate timestamps for this day
            # More events during business hours (9 AM - 5 PM)
            timestamps = []
            for _ in range(num_events):
                if random.random() < 0.8:  # 80% during business hours
                    hour = random.randint(9, 17)
                else:
                    hour = random.randint(0, 23)
                
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                microsecond = random.randint(0, 999999)
                
                event_time = current_date.replace(
                    hour=hour, minute=minute, second=second, microsecond=microsecond
                )
                timestamps.append(event_time)
            
            # Sort timestamps chronologically
            timestamps.sort()
            
            # Generate events for this agent on this day
            for timestamp in timestamps:
                # Determine event channel
                channel = random.choice(list(EVENT_TYPES.keys()))
                
                # Determine event type from the selected channel
                event_type = random.choice(EVENT_TYPES[channel])
                
                # Determine alert level with appropriate probabilities
                # Most events should have no alert, some suspicious, few dangerous
                alert_level_rand = random.random()
                if alert_level_rand < 0.85:
                    alert_level = "none"
                elif alert_level_rand < 0.97:
                    alert_level = "suspicious"
                else:
                    alert_level = "dangerous"
                
                # Generate event data
                data = generate_event_data(agent_id, event_type, alert_level)
                
                # Determine the actual channel and level based on the event type and data
                actual_channel = get_channel_from_event_type(event_type)
                actual_level = get_level_from_alert(data)
                
                # Log the event
                log_event(
                    conn,
                    agent_db_ids[agent_id],
                    event_type,
                    data,
                    actual_channel,
                    actual_level,
                    timestamp
                )
        
        # Move to the next day
        current_date += timedelta(days=1)

def main():
    """Main function to generate synthetic data."""
    print("Cylestio Monitor - Synthetic Data Generator")
    print("===========================================")
    
    # Create or connect to the database
    print("Creating/connecting to database...")
    conn = create_database()
    
    # Define the time period (one month)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"Generating data from {start_date.date()} to {end_date.date()}")
    
    # Generate the data
    generate_synthetic_data(conn, start_date, end_date, (50, 200))
    
    # Close the database connection
    conn.close()
    
    print("Data generation complete!")
    print(f"Database location: {Path.home() / '.cylestio' / 'monitor.db'}")

if __name__ == "__main__":
    main() 