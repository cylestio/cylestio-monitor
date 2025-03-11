# Events Listener Module

The events listener module is responsible for intercepting and monitoring events from LLM clients and MCP.

## Decorator Functions

### `monitor_call`

```python
def monitor_call(func, channel="GENERIC"):
```

Decorator for non-LLM calls (MCP, or any other function). It decides if the function is async or sync and wraps it accordingly.

#### Parameters

- `func` (Callable): The function to monitor
- `channel` (str, optional): The channel of the event (e.g., "MCP", "GENERIC")

#### Example

```python
from cylestio_monitor.events_listener import monitor_call

# Decorate a function
@monitor_call(channel="CUSTOM")
def my_function(arg1, arg2):
    return arg1 + arg2
```

### `monitor_llm_call`

```python
def monitor_llm_call(func, channel="LLM"):
```

Decorator specifically for LLM API calls. It handles the specific structure of LLM API calls.

#### Parameters

- `func` (Callable): The LLM API function to monitor
- `channel` (str, optional): The channel of the event (e.g., "LLM")

#### Example

```python
from cylestio_monitor.events_listener import monitor_llm_call

# Decorate an LLM API function
@monitor_llm_call(channel="LLM")
def create_message(model, messages, max_tokens=None):
    # LLM API call implementation
    pass
```

## Internal Wrapper Functions

### Synchronous Wrapper

```python
@functools.wraps(func)
def sync_wrapper(*args, **kwargs):
    start_time = time.time()
    pre_monitor_call(func, channel, args, kwargs)
    try:
        result = func(*args, **kwargs)
        post_monitor_call(func, channel, start_time, result)
        return result
    except Exception as e:
        # Log the error but don't interfere with the exception
        from .events_processor import log_event

        log_event(
            "call_error", {"function": func.__name__, "error": str(e)}, channel, "error"
        )
        raise
```

This wrapper is used for synchronous functions. It:

1. Records the start time
2. Calls `pre_monitor_call` to log the call and check for security issues
3. Calls the original function
4. Calls `post_monitor_call` to log the result and performance metrics
5. Returns the result
6. If an exception occurs, logs the error and re-raises the exception

### Asynchronous Wrapper

```python
@functools.wraps(func)
async def async_wrapper(*args, **kwargs):
    start_time = time.time()
    pre_monitor_call(func, channel, args, kwargs)
    try:
        result = await func(*args, **kwargs)
        post_monitor_call(func, channel, start_time, result)
        return result
    except Exception as e:
        # Log the error but don't interfere with the exception
        from .events_processor import log_event

        log_event(
            "call_error", {"function": func.__name__, "error": str(e)}, channel, "error"
        )
        raise
```

This wrapper is used for asynchronous functions. It works the same way as the synchronous wrapper but uses `await` to call the original function.

## Usage Notes

### Automatic Patching

In most cases, you don't need to use these decorators directly. The `enable_monitoring` function in the monitor module automatically patches the appropriate functions based on the provided parameters.

### Manual Patching

If you need to monitor a custom function that isn't automatically patched, you can use the decorators directly:

```python
from cylestio_monitor.events_listener import monitor_call

# Original function
def my_function(arg1, arg2):
    return arg1 + arg2

# Patched function
my_function = monitor_call(my_function, "CUSTOM")
```

### Async Support

Both decorators support both synchronous and asynchronous functions. The `monitor_call` decorator automatically detects whether the function is async or sync and applies the appropriate wrapper.

### Error Handling

The wrappers include error handling to ensure that monitoring doesn't interfere with the normal operation of your code. If an exception occurs in the monitored function, it's logged and then re-raised, preserving the original exception.

### Security Checks

The wrappers call the `pre_monitor_call` or `pre_monitor_llm` functions from the events processor module, which perform security checks on the function arguments. If dangerous content is detected, a `SecurityException` is raised, preventing the call from proceeding.

### Performance Metrics

The wrappers record the start time of the call and pass it to the `post_monitor_call` or `post_monitor_llm` functions, which calculate the duration of the call and include it in the logged event. 