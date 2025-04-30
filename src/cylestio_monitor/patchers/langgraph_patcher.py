"""LangGraph framework patcher for Cylestio Monitor.

This module provides patching functionality to intercept and monitor LangGraph events,
including graph node executions, data source interactions, and state transitions.
"""

import functools
import logging
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional

from cylestio_monitor.patchers.base import BasePatcher

from ..utils.event_logging import log_error, log_event
from ..utils.event_utils import format_timestamp
from ..utils.trace_context import TraceContext

logger = logging.getLogger("CylestioMonitor")


class LangGraphPatcher(BasePatcher):
    """Patcher for LangGraph."""

    def __init__(self):
        """Initialize LangGraph patcher."""
        super().__init__({"name": "langgraph"})
        self._patched = False
        self._patched_functions = {}

    def patch(self) -> None:
        """Apply LangGraph patches for monitoring."""
        self._apply()

    def _apply(self) -> bool:
        """Apply LangGraph patches.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self._patched:
            logger.warning("LangGraph already patched")
            return False

        try:
            # Try to import LangGraph modules
            import langgraph

            # Log patch attempt
            context = TraceContext.get_current_context()
            log_event(
                name="framework.patch",
                attributes={
                    "framework.name": "langgraph",
                    "patch.type": "module",
                    "patch.components": ["StateGraph", "Graph"],
                },
                trace_id=context.get("trace_id"),
                agent_id=context.get("agent_id"),
            )

            # Patch Graph module if available
            patch_count = 0
            try:
                patch_count += self._patch_state_graph()
            except Exception as e:
                logger.warning(f"Failed to patch LangGraph StateGraph: {e}")

            # Patch tool execution if available
            try:
                patch_count += self._patch_tool_execution()
            except Exception as e:
                logger.warning(f"Failed to patch LangGraph tool execution: {e}")

            # Set patched flag if any patches were applied
            self._patched = patch_count > 0
            if self._patched:
                logger.info(
                    f"LangGraph patched successfully ({patch_count} components)"
                )
                return True
            else:
                logger.warning("No LangGraph components found to patch")
                return False

        except ImportError:
            logger.debug("LangGraph not found, skipping patch")
            return False
        except Exception as e:
            log_error(
                name="framework.patch.error",
                error=e,
                attributes={"framework.name": "langgraph"},
                trace_id=context.get("trace_id"),
                agent_id=context.get("agent_id"),
            )
            logger.exception(f"Error patching LangGraph: {e}")
            return False

    def _patch_state_graph(self) -> int:
        """Patch the StateGraph class for monitoring.

        Returns:
            int: Number of components patched
        """
        # Track number of patches applied
        patch_count = 0

        # Try to import StateGraph
        try:
            from langgraph.graph import StateGraph
            from langgraph.prebuilt import create_react_agent

            # Patch StateGraph compile method
            if hasattr(StateGraph, "compile") and not hasattr(
                StateGraph.compile, "__cylestio_patched__"
            ):
                orig_compile = StateGraph.compile

                @functools.wraps(orig_compile)
                def patched_compile(self, *args, **kwargs):
                    # Call original
                    try:
                        logger.debug(f"Compiling StateGraph: {self}")
                        result = orig_compile(self, *args, **kwargs)

                        # Now patch the compiled graph's invoke method to track executions
                        if hasattr(result, "invoke") and not hasattr(
                            result.invoke, "__cylestio_patched__"
                        ):
                            orig_invoke = result.invoke

                            @functools.wraps(orig_invoke)
                            def patched_invoke(*invoke_args, **invoke_kwargs):
                                # Start monitoring span
                                span_id = TraceContext.start_span("langgraph.invoke")

                                # Log start
                                try:
                                    log_event(
                                        name="langgraph.invoke.start",
                                        attributes={
                                            "framework.name": "langgraph",
                                            "graph.type": "StateGraph",
                                        },
                                    )
                                except Exception as e:
                                    logger.debug(
                                        f"Error logging LangGraph invoke start: {e}"
                                    )

                                # Call original
                                try:
                                    invoke_result = orig_invoke(
                                        *invoke_args, **invoke_kwargs
                                    )

                                    # Log success
                                    try:
                                        log_event(
                                            name="langgraph.invoke.end",
                                            attributes={
                                                "framework.name": "langgraph",
                                                "graph.type": "StateGraph",
                                                "graph.status": "success",
                                            },
                                        )
                                    except Exception as e:
                                        logger.debug(
                                            f"Error logging LangGraph invoke success: {e}"
                                        )

                                    return invoke_result
                                except Exception as e:
                                    # Log error
                                    try:
                                        log_error(
                                            name="langgraph.invoke.error",
                                            error=e,
                                            attributes={
                                                "framework.name": "langgraph",
                                                "graph.type": "StateGraph",
                                            },
                                        )
                                    except Exception:
                                        pass
                                    raise
                                finally:
                                    # End span
                                    TraceContext.end_span()

                            # Mark as patched
                            patched_invoke.__cylestio_patched__ = True

                            # Replace invoke method
                            result.invoke = patched_invoke

                        return result
                    except Exception as e:
                        logger.warning(f"Error in patched compile: {e}")
                        return orig_compile(self, *args, **kwargs)

                # Mark as patched
                patched_compile.__cylestio_patched__ = True

                # Replace the method
                StateGraph.compile = patched_compile
                patch_count += 1
                logger.debug("Patched StateGraph compile method")

            # Try to patch the React Agent creator function for tool monitoring
            if callable(create_react_agent) and not hasattr(
                create_react_agent, "__cylestio_patched__"
            ):
                orig_create_react_agent = create_react_agent

                @functools.wraps(orig_create_react_agent)
                def patched_create_react_agent(*args, **kwargs):
                    # Extract tools if available
                    tools = kwargs.get("tools", [])
                    if not tools and len(args) >= 2:
                        tools = args[1]

                    # Log the tools being used
                    try:
                        tool_names = []
                        for tool in tools:
                            if hasattr(tool, "name"):
                                tool_names.append(tool.name)
                            elif hasattr(tool, "__name__"):
                                tool_names.append(tool.__name__)

                        log_event(
                            name="langgraph.react_agent.create",
                            attributes={
                                "framework.name": "langgraph",
                                "agent.type": "react",
                                "agent.tools": str(tool_names),
                            },
                        )
                    except Exception as e:
                        logger.debug(f"Error logging React agent creation: {e}")

                    # Call original
                    return orig_create_react_agent(*args, **kwargs)

                # Mark as patched
                patched_create_react_agent.__cylestio_patched__ = True

                # Replace the function
                create_react_agent = patched_create_react_agent
                sys.modules[
                    "langgraph.prebuilt"
                ].create_react_agent = patched_create_react_agent
                patch_count += 1
                logger.debug("Patched create_react_agent function")

            return patch_count

        except ImportError:
            logger.debug("LangGraph StateGraph not available")
            return 0
        except Exception as e:
            logger.warning(f"Error patching StateGraph: {e}")
            return 0

    def _patch_tool_execution(self) -> int:
        """Patch LangGraph tool execution to track tool calls.

        Returns:
            int: Number of components patched
        """
        patch_count = 0

        # First try to patch the newer 'tool_call_with_retry' function in langgraph.pregel
        try:
            if "langgraph.pregel" in sys.modules:
                module = sys.modules["langgraph.pregel"]

                # Look for the tool call functions
                for func_name in ["tool_call_with_retry", "tool_call"]:
                    if hasattr(module, func_name) and not hasattr(
                        getattr(module, func_name), "__cylestio_patched__"
                    ):
                        orig_func = getattr(module, func_name)

                        @functools.wraps(orig_func)
                        def patched_tool_call(state, *args, **kwargs):
                            # Extract tool info from state
                            tool_name = "unknown_tool"
                            tool_input = "{}"

                            try:
                                # Extract tool info differently based on function
                                if func_name == "tool_call_with_retry":
                                    # For tool_call_with_retry, we need to extract from the state
                                    if "current_tool" in state:
                                        current_tool = state["current_tool"]
                                        if isinstance(current_tool, dict):
                                            tool_name = current_tool.get(
                                                "name", tool_name
                                            )
                                            tool_input = str(
                                                current_tool.get("input", "{}")
                                            )
                                else:
                                    # For direct tool_call, name is often in args[0]
                                    if args and args[0]:
                                        tool_name = args[0]

                                    # Input may be in args[1] or kwargs
                                    if len(args) > 1:
                                        tool_input = str(args[1])
                                    elif "tool_input" in kwargs:
                                        tool_input = str(kwargs["tool_input"])
                            except Exception as e:
                                logger.debug(f"Error extracting tool info: {e}")

                            # Start span for tool execution
                            span_id = TraceContext.start_span(f"tool.{tool_name}")

                            # Log tool start
                            try:
                                log_event(
                                    name="tool.start",
                                    attributes={
                                        "tool.name": tool_name,
                                        "tool.input": tool_input,
                                        "framework.name": "langgraph",
                                        "framework.component": "pregel",
                                    },
                                )
                            except Exception as e:
                                logger.debug(f"Error logging tool start: {e}")

                            # Call original function
                            try:
                                result = orig_func(state, *args, **kwargs)

                                # Extract result
                                result_str = str(result)
                                if len(result_str) > 1000:
                                    result_str = result_str[:997] + "..."

                                # Log success
                                try:
                                    log_event(
                                        name="tool.end",
                                        attributes={
                                            "tool.name": tool_name,
                                            "tool.status": "success",
                                            "tool.result": result_str,
                                            "framework.name": "langgraph",
                                            "framework.component": "pregel",
                                        },
                                    )
                                except Exception as e:
                                    logger.debug(f"Error logging tool end: {e}")

                                return result
                            except Exception as e:
                                # Log error
                                try:
                                    log_error(
                                        name="tool.error",
                                        error=e,
                                        attributes={
                                            "tool.name": tool_name,
                                            "framework.name": "langgraph",
                                            "framework.component": "pregel",
                                        },
                                    )
                                except Exception:
                                    pass
                                raise
                            finally:
                                # End span
                                TraceContext.end_span()

                        # Mark as patched
                        patched_tool_call.__cylestio_patched__ = True

                        # Replace the function
                        setattr(module, func_name, patched_tool_call)
                        patch_count += 1
                        logger.debug(f"Patched langgraph.pregel.{func_name}")

            # Also try to patch the execute_tools function in langgraph.prebuilt
            if "langgraph.prebuilt" in sys.modules:
                module = sys.modules["langgraph.prebuilt"]

                if hasattr(module, "execute_tools") and not hasattr(
                    module.execute_tools, "__cylestio_patched__"
                ):
                    orig_execute = module.execute_tools

                    @functools.wraps(orig_execute)
                    def patched_execute_tools(state, *args, **kwargs):
                        # Extract tool info
                        tool_name = "batch_tools"
                        tool_input = "{}"

                        try:
                            # Try to extract specific tool info if available
                            if "current_tool" in state:
                                tool_name = state["current_tool"]
                            elif "tool_calls" in state:
                                tool_calls = state["tool_calls"]
                                if isinstance(tool_calls, list) and tool_calls:
                                    if isinstance(tool_calls[0], dict):
                                        tool_name = tool_calls[0].get("name", tool_name)
                                        tool_input = str(
                                            tool_calls[0].get("args", "{}")
                                        )
                        except Exception as e:
                            logger.debug(f"Error extracting batch tool info: {e}")

                        # Start span for tool execution
                        span_id = TraceContext.start_span(f"tool.{tool_name}")

                        # Log tool start
                        try:
                            log_event(
                                name="tool.start",
                                attributes={
                                    "tool.name": tool_name,
                                    "tool.input": tool_input,
                                    "framework.name": "langgraph",
                                    "framework.component": "prebuilt.execute_tools",
                                },
                            )
                        except Exception as e:
                            logger.debug(f"Error logging batch tool start: {e}")

                        # Call original function
                        try:
                            result = orig_execute(state, *args, **kwargs)

                            # Extract result info
                            result_type = type(result).__name__
                            result_str = str(result)
                            if len(result_str) > 1000:
                                result_str = result_str[:997] + "..."

                            # Log success
                            try:
                                log_event(
                                    name="tool.end",
                                    attributes={
                                        "tool.name": tool_name,
                                        "tool.status": "success",
                                        "tool.result.type": result_type,
                                        "tool.result": result_str,
                                        "framework.name": "langgraph",
                                        "framework.component": "prebuilt.execute_tools",
                                    },
                                )
                            except Exception as e:
                                logger.debug(f"Error logging batch tool end: {e}")

                            return result
                        except Exception as e:
                            # Log error
                            try:
                                log_error(
                                    name="tool.error",
                                    error=e,
                                    attributes={
                                        "tool.name": tool_name,
                                        "framework.name": "langgraph",
                                        "framework.component": "prebuilt.execute_tools",
                                    },
                                )
                            except Exception:
                                pass
                            raise
                        finally:
                            # End span
                            TraceContext.end_span()

                    # Mark as patched
                    patched_execute_tools.__cylestio_patched__ = True

                    # Replace the function
                    module.execute_tools = patched_execute_tools
                    patch_count += 1
                    logger.debug("Patched langgraph.prebuilt.execute_tools")

            return patch_count

        except Exception as e:
            logger.warning(f"Error patching LangGraph tool execution: {e}")
            return 0

    def unpatch(self) -> None:
        """Remove patches applied to LangGraph."""
        if not self._patched:
            return

        success = True

        # Try to restore StateGraph
        try:
            from langgraph.graph import StateGraph

            if hasattr(StateGraph, "compile") and hasattr(
                StateGraph.compile, "__cylestio_patched__"
            ):
                # We would need the original function to restore it
                # Since we didn't store it (an oversight), we'll need to reload the module
                try:
                    import importlib

                    importlib.reload(sys.modules["langgraph.graph"])
                    logger.info("Reloaded langgraph.graph module to remove patches")
                except Exception as e:
                    logger.warning(f"Failed to reload langgraph.graph module: {e}")
                    success = False
        except Exception as e:
            logger.warning(f"Error unpatching StateGraph: {e}")
            success = False

        # Try to restore tool call functions
        if "langgraph.pregel" in sys.modules:
            try:
                import importlib

                importlib.reload(sys.modules["langgraph.pregel"])
                logger.info("Reloaded langgraph.pregel module to remove patches")
            except Exception as e:
                logger.warning(f"Failed to reload langgraph.pregel module: {e}")
                success = False

        if "langgraph.prebuilt" in sys.modules:
            try:
                import importlib

                importlib.reload(sys.modules["langgraph.prebuilt"])
                logger.info("Reloaded langgraph.prebuilt module to remove patches")
            except Exception as e:
                logger.warning(f"Failed to reload langgraph.prebuilt module: {e}")
                success = False

        self._patched = not success


def patch_langgraph():
    """Patch LangGraph for monitoring."""
    patcher = LangGraphPatcher()
    patcher.patch()
    return patcher._patched


def unpatch_langgraph():
    """Unpatch LangGraph."""
    patcher = LangGraphPatcher()
    patcher.unpatch()
    return not patcher._patched


class LangGraphMonitor:
    """Monitor for LangGraph events."""

    def __init__(self):
        """Initialize the LangGraph monitor."""
        self._start_times: Dict[str, float] = {}
        self._node_types: Dict[str, str] = {}
        self._session_id = f"langgraph-{format_timestamp()}"
        self._turn_counters: Dict[str, int] = {}

    def _get_langgraph_version(self) -> str:
        """Get the installed LangGraph version."""
        try:
            import langgraph

            return getattr(langgraph, "__version__", "unknown")
        except:
            return "unknown"

    def _create_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        *,
        direction: Optional[str] = None,
        level: str = "INFO",
    ) -> None:
        """Create and process a LangGraph event with enhanced metadata."""
        # Add LangGraph-specific metadata
        enhanced_data = {
            **data,
            "framework_version": self._get_langgraph_version(),
            "components": {
                "node_type": data.get("node_type"),
                "graph_type": data.get("graph_type"),
            },
        }

        # Add session/conversation tracking
        if "graph_id" in data:
            enhanced_data["session_id"] = f"langgraph-{data['graph_id']}"

            # Track turn numbers
            if "graph_id" in data and "turn_number" not in enhanced_data:
                graph_id = data["graph_id"]
                if graph_id not in self._turn_counters:
                    self._turn_counters[graph_id] = 0
                else:
                    self._turn_counters[graph_id] += 1
                enhanced_data["turn_number"] = self._turn_counters[graph_id]
        else:
            enhanced_data["session_id"] = self._session_id

        # Add direction if provided
        if direction:
            enhanced_data["direction"] = direction

        # Log the event
        log_event(name=f"langgraph.{event_type}", attributes=enhanced_data, level=level)

    def on_graph_start(
        self, graph_id: str, graph_config: Dict[str, Any], inputs: Dict[str, Any]
    ) -> None:
        """Handle graph start event."""
        self._start_times[graph_id] = time.time()

        # Format inputs for better readability
        formatted_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, (list, dict)):
                formatted_inputs[key] = value
            else:
                formatted_inputs[key] = str(value)

        self._create_event(
            "graph_start",
            {
                "graph_id": graph_id,
                "graph_type": graph_config.get("name", "unknown"),
                "input": formatted_inputs,
                "metadata": graph_config.get("metadata", {}),
                "config": {
                    "name": graph_config.get("name"),
                    "description": graph_config.get("description"),
                    "nodes": list(graph_config.get("nodes", {}).keys()),
                },
            },
            direction="incoming",
        )

    def on_graph_end(self, graph_id: str, outputs: Dict[str, Any]) -> None:
        """Handle graph end event."""
        if graph_id in self._start_times:
            duration = time.time() - self._start_times.pop(graph_id)

            # Format outputs for better readability
            formatted_outputs = {}
            for key, value in outputs.items():
                if isinstance(value, (list, dict)):
                    formatted_outputs[key] = value
                else:
                    formatted_outputs[key] = str(value)

            self._create_event(
                "graph_finish",
                {
                    "graph_id": graph_id,
                    "output": formatted_outputs,
                    "performance": {
                        "duration_ms": duration * 1000,
                        "graphs_per_second": 1.0 / duration if duration > 0 else None,
                    },
                },
                direction="outgoing",
            )

    def on_graph_error(self, graph_id: str, error: Exception) -> None:
        """Handle graph error event."""
        if graph_id in self._start_times:
            duration = time.time() - self._start_times.pop(graph_id)

            self._create_event(
                "graph_error",
                {
                    "graph_id": graph_id,
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "performance": {
                        "duration_ms": duration * 1000,
                        "error_time": format_timestamp(),
                    },
                },
                level="error",
            )

    def on_node_start(
        self, graph_id: str, node_id: str, node_type: str, inputs: Dict[str, Any]
    ) -> None:
        """Handle node start event."""
        node_run_id = f"{graph_id}:{node_id}:{time.time()}"
        self._start_times[node_run_id] = time.time()
        self._node_types[node_run_id] = node_type

        # Format inputs for better readability
        formatted_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, (list, dict)):
                formatted_inputs[key] = value
            else:
                formatted_inputs[key] = str(value)

        # Estimate token count
        estimated_tokens = sum(len(str(v)) // 4 for v in inputs.values())

        self._create_event(
            "node_start",
            {
                "graph_id": graph_id,
                "node_id": node_id,
                "node_type": node_type,
                "run_id": node_run_id,
                "input": {
                    "content": formatted_inputs,
                    "estimated_tokens": estimated_tokens,
                },
            },
            direction="incoming",
        )

    def on_node_end(self, graph_id: str, node_id: str, outputs: Dict[str, Any]) -> None:
        """Handle node end event."""
        # Find the matching node_run_id
        node_run_id_prefix = f"{graph_id}:{node_id}:"
        matching_keys = [
            k for k in self._start_times.keys() if k.startswith(node_run_id_prefix)
        ]

        if matching_keys:
            node_run_id = matching_keys[0]  # Use the first matching key
            duration = time.time() - self._start_times.pop(node_run_id)
            node_type = self._node_types.pop(node_run_id, "unknown")

            # Format outputs for better readability
            formatted_outputs = {}
            for key, value in outputs.items():
                if isinstance(value, (list, dict)):
                    formatted_outputs[key] = value
                else:
                    formatted_outputs[key] = str(value)

            # Estimate token count
            estimated_tokens = sum(len(str(v)) // 4 for v in outputs.values())

            self._create_event(
                "node_end",
                {
                    "graph_id": graph_id,
                    "node_id": node_id,
                    "node_type": node_type,
                    "run_id": node_run_id,
                    "output": {
                        "content": formatted_outputs,
                        "estimated_tokens": estimated_tokens,
                    },
                    "performance": {
                        "duration_ms": duration * 1000,
                        "nodes_per_second": 1.0 / duration if duration > 0 else None,
                    },
                },
                direction="outgoing",
            )

    def on_node_error(self, graph_id: str, node_id: str, error: Exception) -> None:
        """Handle node error event."""
        # Find the matching node_run_id
        node_run_id_prefix = f"{graph_id}:{node_id}:"
        matching_keys = [
            k for k in self._start_times.keys() if k.startswith(node_run_id_prefix)
        ]

        if matching_keys:
            node_run_id = matching_keys[0]  # Use the first matching key
            duration = time.time() - self._start_times.pop(node_run_id)
            node_type = self._node_types.pop(node_run_id, "unknown")

            self._create_event(
                "node_error",
                {
                    "graph_id": graph_id,
                    "node_id": node_id,
                    "node_type": node_type,
                    "run_id": node_run_id,
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "performance": {
                        "duration_ms": duration * 1000,
                        "error_time": format_timestamp(),
                    },
                },
                level="error",
            )

    def on_state_update(
        self, graph_id: str, old_state: Dict[str, Any], new_state: Dict[str, Any]
    ) -> None:
        """Handle state update event."""
        # Find changed keys
        changed_keys = []
        for key in set(old_state.keys()) | set(new_state.keys()):
            if key not in old_state:
                changed_keys.append(f"+{key}")  # Added
            elif key not in new_state:
                changed_keys.append(f"-{key}")  # Removed
            elif old_state[key] != new_state[key]:
                changed_keys.append(f"~{key}")  # Modified

        # Format states for better readability
        formatted_old_state = {}
        formatted_new_state = {}

        for key in set(old_state.keys()) | set(new_state.keys()):
            # Old state
            if key in old_state:
                value = old_state[key]
            if isinstance(value, (list, dict)):
                formatted_old_state[key] = value
            else:
                formatted_old_state[key] = str(value)

            # New state
            if key in new_state:
                value = new_state[key]
            if isinstance(value, (list, dict)):
                formatted_new_state[key] = value
            else:
                formatted_new_state[key] = str(value)

        self._create_event(
            "state_update",
            {
                "graph_id": graph_id,
                "changes": {
                    "keys": changed_keys,
                    "count": len(changed_keys),
                    "old_state": formatted_old_state,
                    "new_state": formatted_new_state,
                    "timestamp": format_timestamp(),
                },
            },
        )

    def on_state_transition(
        self, graph_id: str, from_node: str, to_node: str, state: Dict[str, Any]
    ) -> None:
        """Handle state transition between nodes."""
        # Format state for better readability
        formatted_state = {}
        for key, value in state.items():
            if isinstance(value, (list, dict)):
                formatted_state[key] = value
            else:
                formatted_state[key] = str(value)

        self._create_event(
            "state_transition",
            {
                "graph_id": graph_id,
                "transition": {
                    "from_node": from_node,
                    "to_node": to_node,
                    "timestamp": format_timestamp(),
                },
                "state": formatted_state,
            },
        )

    def on_agent_action(
        self, graph_id: str, agent_id: str, action: Dict[str, Any]
    ) -> None:
        """Handle agent action event."""
        self._create_event(
            "agent_action",
            {
                "graph_id": graph_id,
                "agent_id": agent_id,
                "action": action,
                "timestamp": format_timestamp(),
            },
        )


def _wrap_node_function(func, node_name, monitor):
    """Wrap a node function to monitor its execution."""

    @functools.wraps(func)
    def monitored_node_function(state):
        # Generate a unique ID for this execution
        exec_id = f"{node_name}:{id(state)}:{time.time()}"

        # Start span
        span_id = TraceContext.start_span(f"langgraph.node.{node_name}")

        # Notify function start with details
        try:
            # Format state for better readability
            formatted_state = {}
            for key, value in state.items():
                if isinstance(value, (list, dict)):
                    formatted_state[key] = value
                else:
                    formatted_state[key] = str(value)

            # Create input attributes
            input_attributes = {
                "node.name": node_name,
                "node.exec_id": exec_id,
                "node.state": formatted_state,
                "framework.name": "langgraph",
                "framework.type": "node_function",
            }

            # Log node execution start
            log_event(name="langgraph.node.start", attributes=input_attributes)
        except Exception as e:
            # Handle serialization errors
            log_error(
                name="langgraph.node.error",
                error=e,
                attributes={
                    "node.name": node_name,
                    "node.exec_id": exec_id,
                    "error.context": "state_serialization",
                    "framework.name": "langgraph",
                },
            )

        try:
            # Call the original function
            result = func(state)

            # Log node execution success
            try:
                # Format result for better readability
                if isinstance(result, dict):
                    formatted_result = {}
                    for key, value in result.items():
                        if isinstance(value, (list, dict)):
                            formatted_result[key] = value
                        else:
                            formatted_result[key] = str(value)
                else:
                    formatted_result = str(result)

                # Create result attributes
                result_attributes = {
                    "node.name": node_name,
                    "node.exec_id": exec_id,
                    "node.result": formatted_result,
                    "node.result.type": type(result).__name__,
                    "framework.name": "langgraph",
                    "framework.type": "node_function",
                }

                # Log node execution end
                log_event(name="langgraph.node.end", attributes=result_attributes)
            except Exception as e:
                # Handle serialization errors
                log_error(
                    name="langgraph.node.error",
                    error=e,
                    attributes={
                        "node.name": node_name,
                        "node.exec_id": exec_id,
                        "error.context": "result_serialization",
                        "framework.name": "langgraph",
                    },
                )

            return result
        except Exception as e:
            # Log node execution error
            log_error(
                name="langgraph.node.error",
                error=e,
                attributes={
                    "node.name": node_name,
                    "node.exec_id": exec_id,
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                    "framework.name": "langgraph",
                },
            )
            raise
        finally:
            # End span
            TraceContext.end_span()

    return monitored_node_function


def _wrap_conditional_edge_function(func, from_node, monitor):
    """Wrap a conditional edge function to monitor state transitions."""

    @functools.wraps(func)
    def monitored_edge_function(state):
        # Start span
        span_id = TraceContext.start_span(f"langgraph.transition.{from_node}")

        try:
            # Call the original function
            result = func(state)

            # Format result for better readability
            if isinstance(result, str):
                to_node = result
                formatted_result = result
            else:
                # Handle the case where the result is a list of nodes or other structures
                to_node = str(result)
                formatted_result = str(result)

            # Create result attributes
            result_attributes = {
                "transition.from_node": from_node,
                "transition.to_node": to_node,
                "transition.result": formatted_result,
                "transition.result.type": type(result).__name__,
                "framework.name": "langgraph",
                "framework.type": "edge_function",
            }

            # Log transition event
            log_event(name="langgraph.transition", attributes=result_attributes)

            # Also notify the monitor
            try:
                # Format state for monitoring
                formatted_state = {}
                for key, value in state.items():
                    if isinstance(value, (list, dict)):
                        formatted_state[key] = value
                    else:
                        formatted_state[key] = str(value)

                # Use the monitor's state transition event
                monitor.on_state_transition(
                    graph_id=str(id(state)),
                    from_node=from_node,
                    to_node=to_node,
                    state=formatted_state,
                )
            except Exception:
                # Ignore monitoring errors
                pass

            return result
        except Exception as e:
            # Log transition error
            log_error(
                name="langgraph.transition.error",
                error=e,
                attributes={
                    "transition.from_node": from_node,
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                    "framework.name": "langgraph",
                },
            )
            raise
        finally:
            # End span
            TraceContext.end_span()

    return monitored_edge_function


def patch_langgraph() -> None:
    """Patch LangGraph classes for monitoring."""
    try:
        import langgraph.graph
        from langgraph.graph import StateGraph

        # Create a monitor instance
        monitor = LangGraphMonitor()

        # Store original methods
        original_add_node = StateGraph.add_node
        original_add_edge = StateGraph.add_edge
        original_add_conditional_edges = StateGraph.add_conditional_edges

        # Patch add_node
        @functools.wraps(original_add_node)
        def patched_add_node(self, name, fn, *args, **kwargs):
            # Wrap the node function
            monitored_fn = _wrap_node_function(fn, name, monitor)

            # Call original method with wrapped function
            return original_add_node(self, name, monitored_fn, *args, **kwargs)

        # Patch add_conditional_edges
        @functools.wraps(original_add_conditional_edges)
        def patched_add_conditional_edges(self, source, condition, *args, **kwargs):
            # Wrap the condition function
            monitored_condition = _wrap_conditional_edge_function(
                condition, source, monitor
            )

            # Call original method with wrapped function
            return original_add_conditional_edges(
                self, source, monitored_condition, *args, **kwargs
            )

        # Apply patches
        StateGraph.add_node = patched_add_node
        StateGraph.add_conditional_edges = patched_add_conditional_edges

        # Log patch event
        log_event(
            name="framework.patch",
            attributes={
                "framework": "langgraph",
                "version": getattr(langgraph, "__version__", "unknown"),
                "patch_time": format_timestamp(),
                "method": "monkey_patch",
                "note": "Using monkey patching as callbacks module is not available",
            },
        )

        # Try to patch the Graph.compile method to automatically register our monitor
        try:
            original_compile = StateGraph.compile

            @functools.wraps(original_compile)
            def patched_compile(self, *args, **kwargs):
                # Call original method
                compiled_graph = original_compile(self, *args, **kwargs)

                # Try to attach listeners/callbacks if possible
                try:
                    # Different versions of LangGraph use different approaches for callbacks
                    if hasattr(compiled_graph, "add_listener"):
                        compiled_graph.add_listener(monitor)
                    elif hasattr(compiled_graph, "register_callback"):
                        compiled_graph.register_callback(monitor)
                except Exception:
                    # Ignore errors in callback registration
                    pass

                return compiled_graph

            # Apply patch
            StateGraph.compile = patched_compile
        except Exception:
            # Ignore errors in patching compile
            pass

        return True

    except ImportError:
        # LangGraph not available
        return False
    except Exception as e:
        # Log error and continue
        log_error(
            name="framework.patch.error", error=e, attributes={"framework": "langgraph"}
        )
        return False


def unpatch_langgraph():
    """Remove LangGraph patches."""
    try:
        import langgraph.graph
        from langgraph.graph import StateGraph

        # Restore original method if not already restored
        if hasattr(StateGraph, "_original_add_node"):
            StateGraph.add_node = StateGraph._original_add_node
            del StateGraph._original_add_node

        if hasattr(StateGraph, "_original_add_conditional_edges"):
            StateGraph.add_conditional_edges = (
                StateGraph._original_add_conditional_edges
            )
            del StateGraph._original_add_conditional_edges

        if hasattr(StateGraph, "_original_compile"):
            StateGraph.compile = StateGraph._original_compile
            del StateGraph._original_compile

        return True

    except ImportError:
        # LangGraph not available
        return False
    except Exception as e:
        # Log error and continue
        log_error(
            name="framework.unpatch.error",
            error=e,
            attributes={"framework": "langgraph"},
        )
        return False
