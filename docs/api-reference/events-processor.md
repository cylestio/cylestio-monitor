# Events Processor Module

The events processor module is responsible for processing and logging monitoring events in Cylestio Monitor.

## Public Functions

### `log_event`

```python
def log_event(
    event_type: str, data: Dict[str, Any], channel: str = "SYSTEM", level: str = "info"
) -> None:
```

Logs a structured JSON event to both the SQLite database and JSON log file (if configured).

#### Parameters

- `event_type` (str): The type of event (e.g., "LLM_call_start", "MCP_tool_call_finish")
- `data` (Dict[str, Any]): The event data as a dictionary
- `channel` (str, optional): The channel of the event (e.g., "LLM", "MCP", "SYSTEM")
- `level` (str, optional): The log level (e.g., "info", "warning", "error")

#### Example

```python
from cylestio_monitor import log_event

# Log a custom event
log_event(
    event_type="custom_event",
    data={"key": "value"},
    channel="SYSTEM",
    level="info"
)
```

## Security Check Functions

### `normalize_text`

```python
def normalize_text(text: str) -> str:
```

Normalizes text for keyword matching by converting to uppercase and removing extra whitespace.

### `contains_suspicious`

```python
def contains_suspicious(text: str) -> bool:
```

Checks if text contains suspicious keywords from the configuration.

### `contains_dangerous`

```python
def contains_dangerous(text: str) -> bool:
```

Checks if text contains dangerous keywords from the configuration.

## LLM Event Processing Functions

### `pre_monitor_llm`

```python
def pre_monitor_llm(func: Callable, channel: str, args: Tuple, kwargs: Dict) -> None:
```

Processes an LLM API call before it's executed, checking for suspicious or dangerous content.

#### Parameters

- `func` (Callable): The LLM API function being called
- `channel` (str): The channel of the event (e.g., "LLM")
- `args` (Tuple): The positional arguments to the function
- `kwargs` (Dict): The keyword arguments to the function

#### Returns

- None

#### Raises

- `SecurityException`: If the call contains dangerous content

### `post_monitor_llm`

```python
def post_monitor_llm(func: Callable, channel: str, start_time: float, result: Any) -> None:
```

Processes an LLM API call after it's executed, logging the result and performance metrics.

#### Parameters

- `func` (Callable): The LLM API function that was called
- `channel` (str): The channel of the event (e.g., "LLM")
- `start_time` (float): The time when the call started
- `result` (Any): The result of the call

#### Returns

- None

## MCP Event Processing Functions

### `pre_monitor_call`

```python
def pre_monitor_call(func: Callable, channel: str, args: Tuple, kwargs: Dict) -> None:
```

Processes an MCP tool call before it's executed, checking for suspicious or dangerous content.

#### Parameters

- `func` (Callable): The MCP tool function being called
- `channel` (str): The channel of the event (e.g., "MCP")
- `args` (Tuple): The positional arguments to the function
- `kwargs` (Dict): The keyword arguments to the function

#### Returns

- None

#### Raises

- `SecurityException`: If the call contains dangerous content

### `post_monitor_call`

```python
def post_monitor_call(func: Callable, channel: str, start_time: float, result: Any) -> None:
```

Processes an MCP tool call after it's executed, logging the result and performance metrics.

#### Parameters

- `func` (Callable): The MCP tool function that was called
- `channel` (str): The channel of the event (e.g., "MCP")
- `start_time` (float): The time when the call started
- `result` (Any): The result of the call

#### Returns

- None

## Exception Classes

### `SecurityException`

```python
class SecurityException(Exception):
```

Exception raised when a security check fails.

#### Attributes

- `message` (str): The exception message
- `matched_terms` (List[str]): The terms that triggered the security check

## Usage Notes

### Logging Custom Events

You can use the `log_event` function to log custom events to the monitoring system:

```python
from cylestio_monitor import log_event

# Log a custom event
log_event(
    event_type="user_login",
    data={"user_id": "123", "ip_address": "192.168.1.1"},
    channel="AUTH",
    level="info"
)
```

### Security Checks

The security check functions are used internally by the SDK to detect suspicious or dangerous content in LLM prompts and MCP tool calls. They compare the normalized text against the lists of suspicious and dangerous keywords in the configuration.

### Event Processing Flow

1. When an LLM API call or MCP tool call is intercepted, the pre-monitor function is called.
2. The pre-monitor function checks for suspicious or dangerous content and logs an event.
3. If dangerous content is detected, a `SecurityException` is raised, preventing the call from proceeding.
4. If the call is allowed to proceed, the post-monitor function is called after the call completes.
5. The post-monitor function logs the result and performance metrics.

### Event Structure

All events logged by the events processor have a consistent structure:

```json
{
  "event": "EVENT_TYPE",
  "data": {
    // Event-specific data
  },
  "timestamp": "2024-03-10T22:15:30.123456",
  "channel": "CHANNEL",
  "level": "LEVEL"
}
``` 