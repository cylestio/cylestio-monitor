# Security Features

Cylestio Monitor includes robust security features to help protect your AI agents from potential threats.

## Security Monitoring

The core security feature is the ability to detect and respond to potentially harmful content in LLM prompts and MCP tool calls.

### Security Levels

- **None**: Normal events with no security concerns
- **Suspicious**: Events that contain potentially suspicious content
- **Dangerous**: Events that contain dangerous content that could lead to harmful actions

### Security Keywords

The security monitoring is based on keyword matching against two lists:

1. **Suspicious Keywords**: Terms that trigger a warning but allow the operation to proceed
2. **Dangerous Keywords**: Terms that trigger a block, preventing the operation from proceeding

### Default Keywords

```yaml
suspicious_keywords:
  - "REMOVE"
  - "CLEAR"
  - "HACK"
  - "BOMB"

dangerous_keywords:
  - "DROP"
  - "DELETE"
  - "SHUTDOWN"
  - "EXEC("
  - "FORMAT"
  - "RM -RF"
  - "KILL"
```

## Security Actions

### For Suspicious Content

1. The event is logged with a warning level
2. The `alert` field is set to "suspicious"
3. The matched terms are included in the log
4. The operation is allowed to proceed

### For Dangerous Content

1. The event is logged with an error level
2. The `alert` field is set to "dangerous"
3. The matched terms are included in the log
4. The operation is blocked, and an exception is raised
5. A specific "blocked" event is logged

## Customizing Security Settings

### Adding Custom Keywords

```yaml
security:
  suspicious_keywords:
    - "REMOVE"
    - "CLEAR"
    - "HACK"
    - "BOMB"
    - "YOUR_CUSTOM_TERM"
  
  dangerous_keywords:
    - "DROP"
    - "DELETE"
    - "SHUTDOWN"
    - "EXEC("
    - "FORMAT"
    - "RM -RF"
    - "KILL"
    - "YOUR_CUSTOM_DANGEROUS_TERM"
```

### Disabling Security Checks

```yaml
security:
  enabled: false
```

## Querying Security Events

```python
from cylestio_monitor.db import utils as db_utils
import sqlite3

# Get the database connection
db_path = db_utils.get_db_path()
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Query for suspicious events
cursor = conn.execute("""
    SELECT * FROM events
    WHERE json_extract(data, '$.alert') = 'suspicious'
    AND agent_id = ?
    ORDER BY timestamp DESC
""", ("my-project",))

# Print the results
for row in cursor:
    print(f"Suspicious event: {row['event_type']} at {row['timestamp']}")

conn.close()
```

## Next Steps

Now that you understand the security features of Cylestio Monitor, you can:

1. Review the [security best practices](../best-practices/security.md) for more detailed guidance
2. Learn about [monitoring LLM calls](monitoring-llm.md) and [monitoring MCP](monitoring-mcp.md)
3. Explore the [logging options](logging-options.md) to ensure you're capturing all relevant security events 