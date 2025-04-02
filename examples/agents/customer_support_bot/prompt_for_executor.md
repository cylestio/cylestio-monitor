# Cylestio Monitor SDK: Tool Execution Monitoring Implementation Plan

## Project Context & Current Status

The Cylestio Monitor SDK currently provides comprehensive monitoring for:
- LLM calls (start, end, error events)
- LangGraph state transitions
- API client operations

We've successfully resolved several issues:
- Added the `ApiError` class to handle API interaction errors
- Fixed circular dependencies between modules using deferred imports
- Fixed the `Queue.Empty` exception handling in the background sending thread
- Successfully tested the SDK with the customer support bot example

## Missing Functionality

While the system logs tool invocations in terminal output (e.g., "Invoking: `search_flights`"), we're not capturing dedicated `tool.execution` events in our monitoring stream. These events are crucial for understanding the complete agent workflow, especially for function-calling agents.

## Implementation Plan for Tool Execution Monitoring

### 1. Event Schema Design

Implement these event types with the following schema:

```json
{
  "schema_version": "1.0",
  "timestamp": "...",
  "trace_id": "...",
  "span_id": "...",
  "parent_span_id": "...",
  "name": "tool.execution.start|end|error",
  "level": "INFO|ERROR",
  "attributes": {
    "tool.name": "search_flights",
    "tool.inputs": {...},
    "tool.outputs": {...},
    "tool.duration": 0.123,
    "tool.success": true|false,
    "tool.error": "...",
    "session.id": "...",
    "env.os.type": "...",
    "env.python.version": "..."
  },
  "agent_id": "..."
}
```

### 2. Implementation Files and Structure

Create or modify these files:

1. `src/cylestio_monitor/patchers/langchain_patcher.py`
   - Add `LangChainToolPatcher` class
   - Implement patch methods for tool decorator and BaseTool

2. `src/cylestio_monitor/monitor.py`
   - Update to initialize the tool patcher during startup

### 3. Implementation Details

#### LangChainToolPatcher Class

```python
class LangChainToolPatcher:
    """Patcher for LangChain tool execution monitoring."""

    def __init__(self):
        self._original_tool_decorator = None
        self._original_base_tool_run = None
        self._original_base_tool_arun = None
        self._patched = False

    def patch(self):
        """Apply patches to monitor tool execution."""
        if self._patched:
            logger.warning("LangChain tools are already patched")
            return False

        try:
            import langchain.tools

            # Store original references
            self._original_tool_decorator = langchain.tools.tool
            self._original_base_tool_run = langchain.tools.BaseTool._run
            self._original_base_tool_arun = langchain.tools.BaseTool._arun

            # Apply patches
            langchain.tools.tool = self._create_patched_tool_decorator()
            langchain.tools.BaseTool._run = self._create_patched_run()
            langchain.tools.BaseTool._arun = self._create_patched_arun()

            self._patched = True
            logger.info("Successfully patched LangChain tool execution")
            return True

        except ImportError:
            logger.warning("LangChain is not available, tool patching has no effect")
            return False
        except Exception as e:
            logger.error(f"Failed to patch LangChain tools: {e}")
            self.unpatch()  # Revert any partial patches
            return False

    def unpatch(self):
        """Remove patches and restore original functionality."""
        if not self._patched:
            return

        try:
            import langchain.tools

            # Restore original functions
            if self._original_tool_decorator:
                langchain.tools.tool = self._original_tool_decorator

            if self._original_base_tool_run:
                langchain.tools.BaseTool._run = self._original_base_tool_run

            if self._original_base_tool_arun:
                langchain.tools.BaseTool._arun = self._original_base_tool_arun

            self._patched = False
            logger.info("Successfully unpatched LangChain tool execution")

        except Exception as e:
            logger.error(f"Failed to unpatch LangChain tools: {e}")

    def _create_patched_tool_decorator(self):
        """Create a patched version of the @tool decorator."""
        original_tool = self._original_tool_decorator

        def patched_tool(*args, **kwargs):
            original_decorator = original_tool(*args, **kwargs)

            def wrapper(func):
                wrapped_func = original_decorator(func)

                def monitored_func(*func_args, **func_kwargs):
                    # Generate a span ID for this tool execution
                    span_id = generate_span_id()
                    start_time = time.time()

                    # Get current trace context
                    context = TraceContext.get_current_context()
                    trace_id = context.get("trace_id")
                    parent_span_id = context.get("span_id")

                    # Log tool execution start
                    log_event(
                        name="tool.execution.start",
                        attributes={
                            "tool.name": func.__name__,
                            "tool.inputs": safe_event_serialize(func_args[0] if func_args else func_kwargs)
                        },
                        level="INFO",
                        span_id=span_id,
                        trace_id=trace_id,
                        parent_span_id=parent_span_id
                    )

                    try:
                        # Execute the tool
                        result = wrapped_func(*func_args, **func_kwargs)

                        # Log tool execution end
                        log_event(
                            name="tool.execution.end",
                            attributes={
                                "tool.name": func.__name__,
                                "tool.outputs": safe_event_serialize(result),
                                "tool.duration": time.time() - start_time,
                                "tool.success": True
                            },
                            level="INFO",
                            span_id=span_id,
                            trace_id=trace_id,
                            parent_span_id=parent_span_id
                        )

                        return result

                    except Exception as e:
                        # Log tool execution error
                        log_event(
                            name="tool.execution.error",
                            attributes={
                                "tool.name": func.__name__,
                                "tool.error": str(e),
                                "tool.duration": time.time() - start_time,
                                "tool.success": False
                            },
                            level="ERROR",
                            span_id=span_id,
                            trace_id=trace_id,
                            parent_span_id=parent_span_id
                        )
                        raise

                return monitored_func

            return wrapper

        return patched_tool

    def _create_patched_run(self):
        """Create a patched version of BaseTool._run method."""
        original_run = self._original_base_tool_run

        def patched_run(self, *args, **kwargs):
            # Generate a span ID for this tool execution
            span_id = generate_span_id()
            start_time = time.time()

            # Get current trace context
            context = TraceContext.get_current_context()
            trace_id = context.get("trace_id")
            parent_span_id = context.get("span_id")

            # Log tool execution start
            log_event(
                name="tool.execution.start",
                attributes={
                    "tool.name": self.name,
                    "tool.inputs": safe_event_serialize(args[0] if args else kwargs)
                },
                level="INFO",
                span_id=span_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id
            )

            try:
                # Execute the tool
                result = original_run(self, *args, **kwargs)

                # Log tool execution end
                log_event(
                    name="tool.execution.end",
                    attributes={
                        "tool.name": self.name,
                        "tool.outputs": safe_event_serialize(result),
                        "tool.duration": time.time() - start_time,
                        "tool.success": True
                    },
                    level="INFO",
                    span_id=span_id,
                    trace_id=trace_id,
                    parent_span_id=parent_span_id
                )

                return result

            except Exception as e:
                # Log tool execution error
                log_event(
                    name="tool.execution.error",
                    attributes={
                        "tool.name": self.name,
                        "tool.error": str(e),
                        "tool.duration": time.time() - start_time,
                        "tool.success": False
                    },
                    level="ERROR",
                    span_id=span_id,
                    trace_id=trace_id,
                    parent_span_id=parent_span_id
                )
                raise

        return patched_run

    def _create_patched_arun(self):
        """Create a patched version of BaseTool._arun method."""
        original_arun = self._original_base_tool_arun

        async def patched_arun(self, *args, **kwargs):
            # Generate a span ID for this tool execution
            span_id = generate_span_id()
            start_time = time.time()

            # Get current trace context
            context = TraceContext.get_current_context()
            trace_id = context.get("trace_id")
            parent_span_id = context.get("span_id")

            # Log tool execution start
            log_event(
                name="tool.execution.start",
                attributes={
                    "tool.name": self.name,
                    "tool.inputs": safe_event_serialize(args[0] if args else kwargs)
                },
                level="INFO",
                span_id=span_id,
                trace_id=trace_id,
                parent_span_id=parent_span_id
            )

            try:
                # Execute the tool asynchronously
                result = await original_arun(self, *args, **kwargs)

                # Log tool execution end
                log_event(
                    name="tool.execution.end",
                    attributes={
                        "tool.name": self.name,
                        "tool.outputs": safe_event_serialize(result),
                        "tool.duration": time.time() - start_time,
                        "tool.success": True
                    },
                    level="INFO",
                    span_id=span_id,
                    trace_id=trace_id,
                    parent_span_id=parent_span_id
                )

                return result

            except Exception as e:
                # Log tool execution error
                log_event(
                    name="tool.execution.error",
                    attributes={
                        "tool.name": self.name,
                        "tool.error": str(e),
                        "tool.duration": time.time() - start_time,
                        "tool.success": False
                    },
                    level="ERROR",
                    span_id=span_id,
                    trace_id=trace_id,
                    parent_span_id=parent_span_id
                )
                raise

        return patched_arun
```

### 4. Integration with Monitor Module

Update the `monitor.py` to initialize the tool patcher:

```python
# In src/cylestio_monitor/monitor.py

from cylestio_monitor.patchers.langchain_patcher import LangChainToolPatcher

def start_monitoring(agent_id=None, **kwargs):
    """Start monitoring LLM and agent activity."""
    # ... existing code ...

    # Initialize patchers
    openai_patcher = OpenAIPatcher()
    anthropic_patcher = AnthropicPatcher()
    langchain_patcher = LangChainPatcher()
    langgraph_patcher = LangGraphPatcher()
    mcp_patcher = MCPPatcher()
    tool_patcher = LangChainToolPatcher()  # New patcher

    # Apply patches
    # ... existing patchers ...

    # Apply tool monitoring
    if tool_patcher.patch():
        logger.info("LangChain tool execution monitoring enabled")

    # ... rest of existing code ...
```

### 5. Required Utilities

The implementation depends on these utility functions:

- `generate_span_id()`: Create a unique ID for each tool execution span
- `log_event()`: From existing code in `utils/event_logging.py`
- `safe_event_serialize()`: From existing code in `utils/serialization.py`
- Tracing context utilities in `utils/trace_context.py`

### 6. Testing Approach

1. Create a simple agent with tools for testing:
   ```python
   @tool
   def calculator(expression: str) -> str:
       """Calculate a mathematical expression."""
       return str(eval(expression))

   agent = Agent(llm=OpenAI(), tools=[calculator])
   result = agent.invoke("What is 2+2?")
   ```

2. Verify the following events are logged:
   - `tool.execution.start` when the calculator tool is invoked
   - `tool.execution.end` when the calculator tool completes
   - Check that the tool name, inputs, outputs, and duration are correctly captured

3. Test the example customer support bot to ensure tool execution events are captured

### 7. Implementation Notes & Best Practices

1. **Trace Context Management**: Ensure proper context propagation from LLM calls to tool executions
2. **Error Handling**: Robust exception handling to prevent breaking monitored applications
3. **Serialization Safety**: Handle complex input/output objects safely
4. **Performance**: Minimize overhead of monitoring hooks
5. **Compatibility**: Support different LangChain versions
6. **Thread Safety**: Ensure thread-safe operations for context tracking

### 8. Additional Considerations

1. **LangGraph Integration**: Consider how tools are executed within LangGraph nodes and ensure they're properly monitored
2. **Tool Chains**: Handle cases where tools call other tools
3. **Structured Tool Inputs**: Some tools use Pydantic models for input validation

By implementing this plan, the Cylestio Monitor SDK will provide comprehensive monitoring of the entire agent workflow, capturing not just LLM interactions but also the crucial tool executions that agents perform. This completes the monitoring picture, offering valuable insights into agent behavior and performance.
