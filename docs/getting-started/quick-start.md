# Quick Start Guide

This guide will help you quickly set up Cylestio Monitor to start monitoring your AI agents.

## Basic Setup

!!! example "Basic Setup"
    ```python
    from cylestio_monitor import enable_monitoring
    from anthropic import Anthropic

    # Create your LLM client
    client = Anthropic()

    # Enable monitoring
    enable_monitoring(
        agent_id="my_agent",
        llm_client=client
    )

    # Use your client as normal - monitoring happens automatically
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": "Hello, Claude!"}]
    )
    ```

## Monitoring with JSON Logging

!!! tip "JSON Logging"
    You can log events to JSON files in addition to the SQLite database:

    ```python
    # Enable monitoring with both SQLite and JSON logging
    enable_monitoring(
        agent_id="my_agent",
        llm_client=client,
        log_file="/path/to/logs/monitoring.json"
    )

    # Log to a directory (a timestamped file will be created)
    enable_monitoring(
        agent_id="my_agent",
        llm_client=client,
        log_file="/path/to/logs/"
    )
    ```

## Monitoring MCP

!!! example "MCP Monitoring"
    ```python
    from mcp import ClientSession
    from cylestio_monitor import enable_monitoring

    # Enable monitoring before creating your MCP session
    enable_monitoring(agent_id="mcp-project")

    # Create and use your MCP client as normal
    session = ClientSession(stdio, write)
    result = await session.call_tool("weather", {"location": "New York"})
    ```

## Disabling Monitoring

!!! warning "Disabling Monitoring"
    When you're done, you can disable monitoring:

    ```python
    from cylestio_monitor import disable_monitoring

    # Disable monitoring
    disable_monitoring()
    ```

## Accessing the Database

!!! info "Database Access"
    ```python
    from cylestio_monitor import get_database_path
    from cylestio_monitor.db import utils as db_utils

    # Get the path to the database
    db_path = get_database_path()
    print(f"Database path: {db_path}")

    # Get recent events for a specific agent
    events = db_utils.get_recent_events(agent_id="my-project", limit=10)

    # Get events by type
    llm_events = db_utils.get_events_by_type("LLM_call_start", agent_id="my-project")

    # Get events from the last 24 hours
    recent_events = db_utils.get_events_last_hours(24, agent_id="my-project")
    ```

## Next Steps

Now that you have the basics set up, you can:

1. Learn more about [configuration options](configuration.md)
2. Explore the [user guide](../user-guide/overview.md) for more advanced usage
3. Check out the [API reference](../api-reference/overview.md) for detailed documentation
4. Review [best practices](../best-practices/security.md) for securing your AI agents 