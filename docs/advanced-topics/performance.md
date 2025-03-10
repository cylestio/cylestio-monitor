# Performance Considerations

Cylestio Monitor is designed to be lightweight and efficient, but like any monitoring solution, it does have some performance impact. This guide explains the performance characteristics of the SDK and how to optimize it for your specific needs.

## Performance Impact

The performance impact of Cylestio Monitor comes from several sources:

1. **Function Interception**: The SDK intercepts function calls to add monitoring, which adds a small overhead to each call.
2. **Security Checks**: The SDK performs security checks on function arguments, which adds processing time.
3. **Database Operations**: The SDK writes events to a SQLite database, which involves disk I/O.
4. **JSON Logging**: If enabled, the SDK writes events to JSON files, which also involves disk I/O.

In most cases, the performance impact is minimal and won't be noticeable in your application. However, if you're making a large number of LLM or MCP calls, or if you're running on resource-constrained hardware, you might want to consider the performance implications.

## Benchmarks

Here are some rough benchmarks for the performance impact of Cylestio Monitor:

| Operation | Without Monitoring | With Monitoring | Overhead |
|-----------|-------------------|----------------|----------|
| LLM API Call | 1000ms | 1005ms | 0.5% |
| MCP Tool Call | 100ms | 101ms | 1% |
| Custom Function | 10ms | 10.1ms | 1% |

These benchmarks are approximate and will vary depending on your specific environment and usage patterns.

## Optimizing Performance

If you're concerned about the performance impact of Cylestio Monitor, here are some strategies to optimize it:

### 1. Selective Monitoring

Only monitor the functions that you actually need to monitor. If you have a high-volume, low-risk function, you might choose not to monitor it:

```python
from cylestio_monitor import enable_monitoring

# Only monitor the LLM client, not MCP
enable_monitoring(
    agent_id="my_agent",
    llm_client=client
)
```

### 2. Disable JSON Logging

If you don't need JSON logging, you can disable it to reduce disk I/O:

```python
from cylestio_monitor import enable_monitoring

# Only use SQLite logging, not JSON
enable_monitoring(
    agent_id="my_agent",
    llm_client=client,
    log_file=None  # Disable JSON logging
)
```

### 3. Reduce Logging Detail

You can reduce the amount of data logged for each event by customizing the events processor:

```python
from cylestio_monitor.events_processor import log_event

# Original log_event function (simplified)
def original_log_event(event_type, data, channel="SYSTEM", level="info"):
    # Log the full event data
    # ...

# Custom log_event function with reduced detail
def custom_log_event(event_type, data, channel="SYSTEM", level="info"):
    # Only log essential fields
    essential_data = {
        key: value for key, value in data.items()
        if key in ["model", "duration_ms", "alert"]
    }
    original_log_event(event_type, essential_data, channel, level)

# Replace the original function
import cylestio_monitor.events_processor
cylestio_monitor.events_processor.log_event = custom_log_event
```

### 4. Optimize Database Operations

The SQLite database is configured for a balance of performance and reliability. You can optimize it further for performance:

```python
from cylestio_monitor.db.db_manager import DBManager

# Get a connection
conn = DBManager()._get_connection()

# Optimize for performance
conn.execute("PRAGMA synchronous=OFF")  # Less reliable but faster
conn.execute("PRAGMA journal_mode=MEMORY")  # Less reliable but faster
```

Note that these optimizations reduce the reliability of the database in case of a crash or power failure. Only use them if you're willing to accept that risk.

### 5. Periodic Database Cleanup

To prevent the database from growing too large and slowing down, periodically clean up old events:

```python
from cylestio_monitor import cleanup_old_events

# Delete events older than 7 days
cleanup_old_events(days=7)
```

You can automate this with a scheduled task or cron job.

### 6. Database Optimization

Periodically optimize the database to improve query performance:

```python
from cylestio_monitor.db import utils as db_utils

# Optimize the database
db_utils.optimize_database()
```

This runs the SQLite VACUUM and ANALYZE commands to optimize the database structure and update statistics.

## Memory Usage

Cylestio Monitor is designed to be memory-efficient. It uses thread-local connections to the database and doesn't keep large amounts of data in memory.

The main sources of memory usage are:

1. **Connection Pool**: Each thread that accesses the database has its own connection.
2. **Event Data**: Event data is temporarily stored in memory before being written to the database or JSON file.

In most cases, the memory usage is minimal and won't be a concern. However, if you're running in a memory-constrained environment, you might want to monitor the memory usage of your application.

## Thread Safety and Concurrency

Cylestio Monitor is thread-safe and can be used in multi-threaded applications. It uses thread-local connections to the database and locks to protect critical sections.

However, if you have a high-concurrency application with many threads making LLM or MCP calls simultaneously, you might experience contention on the database. In this case, you might want to consider using a more robust database solution like PostgreSQL or MongoDB.

## Scaling Considerations

Cylestio Monitor is designed for single-machine deployments. If you need to scale to multiple machines or very high volumes, consider the following:

1. **Distributed Database**: Replace the SQLite database with a distributed database like PostgreSQL or MongoDB.
2. **Event Streaming**: Instead of writing directly to a database, stream events to a message queue like Kafka or RabbitMQ.
3. **Sampling**: Only monitor a sample of calls rather than every call.

## Monitoring the Monitor

To understand the performance impact of Cylestio Monitor in your specific application, you can monitor the monitor itself:

```python
import time
from cylestio_monitor import enable_monitoring, log_event

# Time how long it takes to enable monitoring
start_time = time.time()
enable_monitoring(agent_id="performance_test")
enable_time = time.time() - start_time
print(f"Time to enable monitoring: {enable_time:.6f} seconds")

# Time how long it takes to log an event
start_time = time.time()
log_event("performance_test", {"test": "data"})
log_time = time.time() - start_time
print(f"Time to log an event: {log_time:.6f} seconds")
```

This will give you a better understanding of the performance characteristics in your specific environment. 