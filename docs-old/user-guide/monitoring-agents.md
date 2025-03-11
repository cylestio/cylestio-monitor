# Monitoring AI Agents

Cylestio Monitor provides comprehensive monitoring for AI agents throughout their lifecycle, from development to production deployment.

## Development-Time Monitoring

During the development of AI agents, Cylestio Monitor helps you:

- **Detect security issues early** by identifying dangerous patterns in prompts and responses
- **Optimize performance** by tracking response times and token usage
- **Debug interactions** with detailed logs of all AI interactions
- **Validate behavior** by analyzing patterns in tool usage and responses

### Development Setup

```python
from cylestio_monitor import enable_monitoring, get_database_path
import your_llm_client

# Enable monitoring with development-specific settings
enable_monitoring(
    agent_id="agent-dev",
    llm_client=your_llm_client,
    development_mode=True,  # Enables additional debug information
    log_file="./logs/dev-logs.json"  # Local logging for development
)

# Run your development tests and interactions

# Analyze results directly
from cylestio_monitor.db import utils as db_utils
debug_info = db_utils.get_recent_events(agent_id="agent-dev", limit=20)
```

## Production Monitoring

For production deployments, Cylestio Monitor provides:

- **Real-time security protection** against injection attacks and abuse
- **Performance monitoring** to detect issues before they impact users
- **Compliance logging** for audit and regulatory requirements
- **Anomaly detection** to identify unusual patterns or behaviors

### Production Setup

```python
from cylestio_monitor import enable_monitoring
import your_llm_client

# Enable monitoring with production-specific settings
enable_monitoring(
    agent_id="agent-prod",
    llm_client=your_llm_client,
    block_dangerous=True,       # Block dangerous prompts
    alert_log_path="/var/log/cylestio/alerts.json",  # Separate alert logging
    security_level="high"       # Higher security threshold
)
```

## Continuous Monitoring Patterns

For long-running applications, implement continuous monitoring:

```python
from cylestio_monitor import enable_monitoring, setup_periodic_reporting
import your_llm_client

# Enable basic monitoring
enable_monitoring(
    agent_id="continuous-agent",
    llm_client=your_llm_client
)

# Setup periodic reporting (every 4 hours)
setup_periodic_reporting(
    hours=4,
    report_path="/var/log/cylestio/reports/",
    include_security=True,
    include_performance=True,
    notify_email="security@yourcompany.com"
)
```

## A/B Testing AI Agents

Cylestio Monitor can help with A/B testing different models or prompts:

```python
from cylestio_monitor import enable_monitoring
import your_llm_client_a, your_llm_client_b

# Monitor version A
enable_monitoring(
    agent_id="agent-version-a",
    llm_client=your_llm_client_a
)

# In a separate process, monitor version B
enable_monitoring(
    agent_id="agent-version-b",
    llm_client=your_llm_client_b
)

# Later, compare performance metrics
from cylestio_monitor.db import utils as db_utils
stats_a = db_utils.get_performance_stats(agent_id="agent-version-a")
stats_b = db_utils.get_performance_stats(agent_id="agent-version-b")
```

## Security Monitoring Best Practices

1. **Use unique agent IDs** for different environments (dev, staging, prod)
2. **Enable blocking mode** in production to prevent dangerous prompts
3. **Set up alert notifications** for security incidents
4. **Regularly review security logs** to identify potential issues
5. **Update your security rules** as new threats emerge

## Performance Monitoring Best Practices

1. **Monitor token usage** to control costs
2. **Track response times** to ensure good user experience
3. **Set performance baselines** and monitor for deviations
4. **Use the dashboard** for visual analysis of performance trends
5. **Implement performance alerts** for slow responses

## Next Steps

- Explore specific [Framework Support](frameworks/index.md)
- Learn about [Security Features](security-features.md)
- Set up [Logging Options](logging-options.md) 