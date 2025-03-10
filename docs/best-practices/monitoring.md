# Monitoring Best Practices

Effective monitoring of AI agents is essential for security, performance optimization, and understanding how your AI systems are being used. This guide outlines best practices for monitoring AI agents using Cylestio Monitor.

## Establishing a Monitoring Strategy

### 1. Define Monitoring Goals

Before implementing monitoring, clearly define what you want to achieve:

- **Security Monitoring**: Detecting and preventing harmful or malicious use
- **Performance Monitoring**: Tracking response times and resource usage
- **Usage Monitoring**: Understanding how your AI agents are being used
- **Compliance Monitoring**: Ensuring compliance with regulations and policies
- **Quality Monitoring**: Tracking the quality of AI responses

### 2. Determine What to Monitor

Based on your goals, determine what aspects of your AI agents to monitor:

- **Inputs**: User prompts and queries
- **Outputs**: AI responses and actions
- **Performance**: Response times, token usage, and resource consumption
- **Errors**: Failures, exceptions, and error rates
- **Security Events**: Suspicious or dangerous activities

### 3. Establish Baselines

Establish baseline metrics to understand normal behavior:

```python
from cylestio_monitor.db import utils as db_utils
import statistics

# Get response times for the last week
conn = sqlite3.connect(db_utils.get_db_path())
conn.row_factory = sqlite3.Row

cursor = conn.execute("""
    SELECT json_extract(data, '$.duration_ms') as duration
    FROM events
    WHERE event_type = 'LLM_call_finish'
    AND timestamp > datetime('now', '-7 days')
""")

durations = [row['duration'] for row in cursor if row['duration'] is not None]
conn.close()

# Calculate baseline metrics
avg_duration = statistics.mean(durations)
median_duration = statistics.median(durations)
p95_duration = sorted(durations)[int(len(durations) * 0.95)]

print(f"Average duration: {avg_duration:.2f} ms")
print(f"Median duration: {median_duration:.2f} ms")
print(f"95th percentile duration: {p95_duration:.2f} ms")
```

## Implementing Effective Monitoring

### 1. Use Appropriate Agent IDs

Use meaningful agent IDs to organize your monitoring data:

```python
from cylestio_monitor import enable_monitoring

# Good: Descriptive agent ID
enable_monitoring(agent_id="customer-support-bot-production")

# Bad: Generic agent ID
enable_monitoring(agent_id="agent1")
```

Consider including environment information in the agent ID to distinguish between production, staging, and development environments.

### 2. Monitor All Relevant Channels

Ensure you're monitoring all relevant channels for your application:

```python
# In your configuration file
monitoring:
  channels:
    - "SYSTEM"
    - "LLM"
    - "API"
    - "MCP"
    - "CUSTOM"
```

Create custom channels for specific components of your application.

### 3. Implement Comprehensive Logging

Log all relevant events with appropriate context:

```python
from cylestio_monitor import log_event

# Log a user interaction
log_event(
    "user_interaction",
    {
        "user_id": user.id,
        "session_id": session.id,
        "interaction_type": "question",
        "content": user_question,
        "metadata": {
            "client_ip": request.remote_addr,
            "user_agent": request.user_agent.string,
            "referrer": request.referrer
        }
    },
    "USER",
    "info"
)
```

Include enough context to understand the event, but be mindful of privacy and security concerns.

### 4. Implement Real-time Alerting

Set up real-time alerting for critical events:

```python
from cylestio_monitor.db import utils as db_utils
import sqlite3
import requests
import time
import threading

def alert_on_dangerous_events(webhook_url, check_interval=60):
    """
    Monitor for dangerous events and send alerts.
    
    Args:
        webhook_url: URL to send alerts to
        check_interval: How often to check for new events (in seconds)
    """
    last_event_id = 0
    
    while True:
        # Get new dangerous events
        conn = sqlite3.connect(db_utils.get_db_path())
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT * FROM events
            WHERE id > ?
            AND json_extract(data, '$.alert') = 'dangerous'
            ORDER BY id ASC
        """, (last_event_id,))
        
        events = []
        for row in cursor:
            event = dict(row)
            events.append(event)
            last_event_id = max(last_event_id, event["id"])
        
        conn.close()
        
        # Send alerts for dangerous events
        for event in events:
            requests.post(
                webhook_url,
                json={
                    "text": f"🚨 ALERT: Dangerous event detected!\n"
                            f"Event type: {event['event_type']}\n"
                            f"Channel: {event['channel']}\n"
                            f"Timestamp: {event['timestamp']}\n"
                            f"Data: {event['data']}"
                }
            )
        
        # Wait for the next check
        time.sleep(check_interval)

# Start the alerting thread
threading.Thread(
    target=alert_on_dangerous_events,
    args=("https://hooks.slack.com/services/YOUR/WEBHOOK/URL",),
    daemon=True
).start()
```

Consider different alerting thresholds for different types of events.

### 5. Implement Log Rotation and Retention

Implement log rotation and retention policies to manage log growth:

```python
from cylestio_monitor import cleanup_old_events

# Delete events older than 90 days
cleanup_old_events(days=90)
```

Consider different retention periods for different types of events based on their importance and compliance requirements.

## Analyzing Monitoring Data

### 1. Regular Review Process

Establish a regular process for reviewing monitoring data:

- **Daily**: Review critical security events and performance anomalies
- **Weekly**: Review usage patterns and trends
- **Monthly**: Conduct a comprehensive review of all monitoring data

### 2. Performance Analysis

Analyze performance metrics to identify optimization opportunities:

```python
from cylestio_monitor.db import utils as db_utils
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Get performance data for the last 30 days
conn = sqlite3.connect(db_utils.get_db_path())
conn.row_factory = sqlite3.Row

cursor = conn.execute("""
    SELECT 
        date(timestamp) as date,
        avg(json_extract(data, '$.duration_ms')) as avg_duration,
        count(*) as call_count
    FROM events
    WHERE event_type = 'LLM_call_finish'
    AND timestamp > datetime('now', '-30 days')
    GROUP BY date(timestamp)
    ORDER BY date(timestamp)
""")

data = [dict(row) for row in cursor]
conn.close()

# Create a DataFrame for analysis
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])

# Plot the data
fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.set_xlabel('Date')
ax1.set_ylabel('Average Duration (ms)', color='tab:blue')
ax1.plot(df['date'], df['avg_duration'], color='tab:blue')
ax1.tick_params(axis='y', labelcolor='tab:blue')

ax2 = ax1.twinx()
ax2.set_ylabel('Call Count', color='tab:red')
ax2.plot(df['date'], df['call_count'], color='tab:red')
ax2.tick_params(axis='y', labelcolor='tab:red')

fig.tight_layout()
plt.title('LLM API Call Performance (Last 30 Days)')
plt.savefig('llm_performance.png')
```

Look for trends and patterns that might indicate performance issues or opportunities for optimization.

### 3. Security Analysis

Analyze security events to identify potential threats:

```python
from cylestio_monitor.db import utils as db_utils
import sqlite3
import pandas as pd

# Get security events for the last 30 days
conn = sqlite3.connect(db_utils.get_db_path())
conn.row_factory = sqlite3.Row

cursor = conn.execute("""
    SELECT 
        json_extract(data, '$.alert') as alert_level,
        count(*) as event_count
    FROM events
    WHERE json_extract(data, '$.alert') IS NOT NULL
    AND timestamp > datetime('now', '-30 days')
    GROUP BY json_extract(data, '$.alert')
    ORDER BY event_count DESC
""")

alert_data = [dict(row) for row in cursor]

# Get top matched terms
cursor = conn.execute("""
    SELECT 
        json_extract(data, '$.matched_terms[0]') as term,
        count(*) as match_count
    FROM events
    WHERE json_extract(data, '$.matched_terms') IS NOT NULL
    AND timestamp > datetime('now', '-30 days')
    GROUP BY json_extract(data, '$.matched_terms[0]')
    ORDER BY match_count DESC
    LIMIT 10
""")

term_data = [dict(row) for row in cursor]
conn.close()

# Print the results
print("Security Alert Levels:")
for row in alert_data:
    print(f"{row['alert_level']}: {row['event_count']} events")

print("\nTop Matched Terms:")
for row in term_data:
    print(f"{row['term']}: {row['match_count']} matches")
```

Look for patterns in security events that might indicate targeted attacks or vulnerabilities in your system.

### 4. Usage Analysis

Analyze usage patterns to understand how your AI agents are being used:

```python
from cylestio_monitor.db import utils as db_utils
import sqlite3
import pandas as pd

# Get usage data for the last 30 days
conn = sqlite3.connect(db_utils.get_db_path())
conn.row_factory = sqlite3.Row

cursor = conn.execute("""
    SELECT 
        strftime('%H', timestamp) as hour_of_day,
        count(*) as call_count
    FROM events
    WHERE event_type = 'LLM_call_start'
    AND timestamp > datetime('now', '-30 days')
    GROUP BY strftime('%H', timestamp)
    ORDER BY hour_of_day
""")

hourly_data = [dict(row) for row in cursor]
conn.close()

# Create a DataFrame for analysis
df = pd.DataFrame(hourly_data)
df['hour_of_day'] = df['hour_of_day'].astype(int)
df['call_count'] = df['call_count'].astype(int)

# Plot the data
plt.figure(figsize=(12, 6))
plt.bar(df['hour_of_day'], df['call_count'])
plt.xlabel('Hour of Day (UTC)')
plt.ylabel('Call Count')
plt.title('LLM API Call Distribution by Hour of Day (Last 30 Days)')
plt.xticks(range(24))
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.savefig('usage_by_hour.png')
```

Use usage analysis to optimize resource allocation, identify peak usage times, and understand user behavior.

## Continuous Improvement

### 1. Refine Monitoring Based on Insights

Continuously refine your monitoring based on insights from the data:

- **Adjust Alert Thresholds**: Fine-tune alert thresholds based on observed patterns
- **Add New Metrics**: Identify and add new metrics that provide valuable insights
- **Remove Noise**: Eliminate metrics that don't provide actionable insights

### 2. Automate Routine Tasks

Automate routine monitoring tasks to improve efficiency:

```python
import schedule
import time
import threading
from cylestio_monitor import cleanup_old_events
from cylestio_monitor.db import utils as db_utils

def daily_maintenance():
    """Perform daily maintenance tasks."""
    # Clean up old events
    deleted_count = cleanup_old_events(days=90)
    print(f"Deleted {deleted_count} old events")
    
    # Optimize the database
    db_utils.optimize_database()
    print("Database optimized")
    
    # Generate daily report
    generate_daily_report()
    print("Daily report generated")

def generate_daily_report():
    """Generate a daily monitoring report."""
    # Implementation of report generation
    pass

# Schedule daily maintenance at 2 AM
schedule.every().day.at("02:00").do(daily_maintenance)

# Run the scheduler in a background thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()
```

### 3. Document Monitoring Practices

Document your monitoring practices to ensure consistency and knowledge sharing:

- **Monitoring Plan**: Document what you monitor and why
- **Alert Procedures**: Document how to respond to different types of alerts
- **Analysis Procedures**: Document how to analyze monitoring data
- **Improvement Process**: Document how monitoring practices are reviewed and improved

## Conclusion

Effective monitoring of AI agents requires a strategic approach that goes beyond simply collecting data. By following these best practices, you can implement a monitoring system that provides valuable insights, enhances security, and helps you continuously improve your AI applications. 