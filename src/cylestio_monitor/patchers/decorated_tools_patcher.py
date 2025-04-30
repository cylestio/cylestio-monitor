"""Decorated Tools Patcher for Cylestio Monitor.

This module provides functionality to find and patch functions that have already been
decorated with LangChain's @tool decorator, allowing monitoring of all tool calls.
"""

import functools
import inspect
import logging
import sys
import importlib
import types
from typing import Any, Callable

from cylestio_monitor.patchers.base import BasePatcher
from cylestio_monitor.utils.event_logging import log_error, log_event
from cylestio_monitor.utils.trace_context import TraceContext

logger = logging.getLogger("CylestioMonitor")


class DecoratedToolsPatcher(BasePatcher):
    """Patcher for functions already decorated with LangChain @tool."""

    def __init__(self):
        """Initialize the decorated tools patcher."""
        super().__init__({"name": "decorated_tools"})
        self._patched = False
        self._patched_functions = {}  # {module_name: {func_name: original_func}}
        self._patch_count = 0

    def patch(self) -> None:
        """Find and patch all functions already decorated with @tool.

        Implementation of the required abstract method from BasePatcher.
        """
        self._apply()

    def _apply(self) -> bool:
        """Find and patch all functions already decorated with @tool.

        Returns:
            bool: True if successful, False otherwise
        """
        if self._patched:
            logger.warning("Decorated tools already patched")
            return False

        try:
            # Log patch event
            context = TraceContext.get_current_context()
            log_event(
                name="framework.patch",
                attributes={
                    "framework.name": "decorated_tools",
                    "patch.type": "decorator",
                    "patch.components": ["functions", "tools"],
                },
                trace_id=context.get("trace_id"),
                agent_id=context.get("agent_id"),
            )

            # Reset patch count
            self._patch_count = 0

            # Patch function calling utilities if available to ensure compatibility
            self._patch_function_calling_utils()

            # Find and patch tools in modules
            self._find_and_patch_tools_in_modules()

            # Find and patch tools in module lists
            self._find_and_patch_tools_in_lists()

            # Find and patch tools in agent executors
            self._find_and_patch_tools_in_agent_executors()

            if self._patch_count > 0:
                self._patched = True
                logger.info(
                    f"Successfully patched {self._patch_count} pre-existing @tool functions"
                )
                return True
            else:
                logger.info("No pre-existing @tool functions found to patch")
                return False

        except Exception as e:
            log_error(
                name="framework.patch.error",
                error=e,
                attributes={"framework.name": "decorated_tools"},
                trace_id=context.get("trace_id"),
                agent_id=context.get("agent_id"),
            )
            logger.exception(f"Error patching decorated tools: {e}")
            return False

    def _patch_function_calling_utils(self) -> None:
        """Patch LangChain's function calling utilities to handle Annotated types.

        This ensures that the OpenAI function conversion process can handle our patched tools.
        """
        try:
            # Check if langchain_core.utils.function_calling is available
            if "langchain_core.utils.function_calling" not in sys.modules:
                return

            # Get the module
            module = sys.modules["langchain_core.utils.function_calling"]

            # Check if the convert_to_openai_function function exists
            if not hasattr(module, "convert_to_openai_function"):
                return

            # Get the original function
            original_convert = module.convert_to_openai_function

            # Skip if already patched
            if hasattr(original_convert, "__cylestio_patched__"):
                return

            @functools.wraps(original_convert)
            def patched_convert_to_openai_function(function):
                """Patched version of convert_to_openai_function that handles our monitored tools."""
                try:
                    # Check if this is our monitored tool
                    if hasattr(function, "__cylestio_patched__"):
                        # If it has __wrapped__, use the original function for schema creation
                        if hasattr(function, "__wrapped__"):
                            # Create schema from original
                            schema = original_convert(function.__wrapped__)
                            # Keep the monitored version for execution
                            schema["function"]["implementation"] = function
                            return schema
                except Exception as e:
                    logger.debug(f"Error in patched convert_to_openai_function: {e}")

                # Use original function for all other cases
                return original_convert(function)

            # Mark as patched
            patched_convert_to_openai_function.__cylestio_patched__ = True

            # Replace the original function
            module.convert_to_openai_function = patched_convert_to_openai_function

            logger.debug(
                "Patched LangChain function calling utilities for tool compatibility"
            )

        except Exception as e:
            logger.debug(f"Error patching function calling utilities: {e}")

    def _find_and_patch_tools_in_modules(self) -> None:
        """Find and patch tools in all module attributes."""
        # Skip these modules
        skip_modules = {
            "langchain",
            "langchain_core",
            "langchain_community",
            "cylestio_monitor",
            "sys",
            "os",
            "typing",
            "types",
            "functools",
            "inspect",
            "logging",
        }

        # Skip modules that start with these prefixes
        skip_prefixes = ("_", "importlib", "pkg_resources")

        # Process all loaded modules
        for module_name, module in list(sys.modules.items()):
            # Skip internal/system modules and libraries
            if any(module_name.startswith(prefix) for prefix in skip_prefixes) or any(
                module_name == skip or module_name.startswith(f"{skip}.")
                for skip in skip_modules
            ):
                continue

            try:
                # Skip if not a module
                if not module or not inspect.ismodule(module):
                    continue

                # Look for tools in the module
                for name in dir(module):
                    # Skip private/dunder attributes
                    if name.startswith("_"):
                        continue

                    try:
                        obj = getattr(module, name)

                        # Skip classes and non-callable objects
                        if not callable(obj) or inspect.isclass(obj):
                            continue

                        # Check if it's a tool
                        if self._is_tool_function(obj):
                            # Skip if already patched
                            if hasattr(obj, "__cylestio_patched__"):
                                continue

                            # Patch the function
                            patched_func = self._create_monitored_tool(obj)

                            # Store original for unpatching
                            if module_name not in self._patched_functions:
                                self._patched_functions[module_name] = {}
                            self._patched_functions[module_name][name] = obj

                            # Replace with patched version
                            setattr(module, name, patched_func)
                            self._patch_count += 1

                    except (AttributeError, ImportError):
                        # Skip if attribute can't be accessed
                        continue
            except Exception as e:
                # Skip problematic modules
                logger.debug(f"Error inspecting module {module_name}: {str(e)}")
                continue

    def _find_and_patch_tools_in_lists(self) -> None:
        """Find and patch tool functions stored in lists."""
        # Process all loaded modules
        for module_name, module in list(sys.modules.items()):
            # Skip problematic modules
            if not module or not hasattr(module, "__dict__"):
                continue

            try:
                # Look for lists in module attributes
                for name, obj in list(module.__dict__.items()):
                    if not isinstance(obj, list):
                        continue

                    # Check if this looks like a tools list
                    tools_list = False
                    if len(obj) > 0 and all(callable(item) for item in obj):
                        # If any item has tool-like attributes, assume it's a tools list
                        tools_list = any(self._is_tool_function(item) for item in obj)

                    # Skip if not a tools list
                    if not tools_list:
                        continue

                    # Track original tool objects to preserve them for type checking
                    original_tools = {}

                    # Patch all items in the list
                    for i, item in enumerate(obj):
                        if callable(item) and not hasattr(item, "__cylestio_patched__"):
                            # Store the original function and its index for reference
                            original_tools[id(item)] = (i, item)

                            # Create lightweight proxy that preserves object identity for type checking
                            patched_item = self._create_monitored_tool_proxy(item)

                            # Replace in the list
                            obj[i] = patched_item
                            self._patch_count += 1

                    # Store original tools for unpatching
                    if original_tools:
                        # Store module and list name for unpatching
                        if module_name not in self._patched_functions:
                            self._patched_functions[module_name] = {}
                        self._patched_functions[module_name][name] = original_tools

            except Exception as e:
                logger.debug(
                    f"Error processing lists in module {module_name}: {str(e)}"
                )
                continue

    def _find_and_patch_tools_in_agent_executors(self) -> None:
        """Find and patch tools in AgentExecutor instances."""
        try:
            # Check for langchain AgentExecutor
            agent_executor_found = False

            for package_name in [
                "langchain.agents.agent",
                "langchain.agents.agent_executor",
            ]:
                if package_name in sys.modules:
                    # Get the AgentExecutor class
                    agent_executor_class = sys.modules[package_name].AgentExecutor
                    agent_executor_found = True
                    break

            if not agent_executor_found:
                return

            # Special patch for the custom executor in langgraph customer support example
            # This ensures we catch tools even in non-standard implementations
            self._patch_customer_support_agent()

            # Look for instances of AgentExecutor
            for module_name, module in list(sys.modules.items()):
                if not module or not hasattr(module, "__dict__"):
                    continue

                try:
                    for obj_name, obj in list(module.__dict__.items()):
                        # Skip non-AgentExecutor objects
                        if not isinstance(obj, agent_executor_class):
                            continue

                        # Skip if already patched
                        if hasattr(obj, "__cylestio_tools_patched__"):
                            continue

                        # We will NOT modify the tools list directly, only monitor via invoke/run methods

                        # Most important: Patch the call_tool method directly to monitor tool calls
                        # This is the method that actually executes tools in the AgentExecutor
                        if hasattr(obj, "_call_tool"):
                            original_call_tool = obj._call_tool

                            # Only wrap if not already patched
                            if not hasattr(original_call_tool, "__cylestio_patched__"):

                                @functools.wraps(original_call_tool)
                                def patched_call_tool(
                                    tool_name, tool_input, color=None, llm_prefix=None
                                ):
                                    # Start span for tool execution
                                    span_id = TraceContext.start_span(
                                        f"tool.{tool_name}"
                                    )

                                    # Log tool start
                                    try:
                                        log_event(
                                            name="tool.start",
                                            attributes={
                                                "tool.name": tool_name,
                                                "tool.input": str(tool_input),
                                                "framework.name": "langchain",
                                                "framework.component": "AgentExecutor._call_tool",
                                            },
                                        )
                                    except Exception as e:
                                        logger.debug(f"Error logging tool start: {e}")

                                    # Call original method
                                    try:
                                        result = original_call_tool(
                                            tool_name, tool_input, color, llm_prefix
                                        )

                                        # Extract result info
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
                                                    "framework.name": "langchain",
                                                    "framework.component": "AgentExecutor._call_tool",
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
                                                    "framework.name": "langchain",
                                                    "framework.component": "AgentExecutor._call_tool",
                                                },
                                            )
                                        except Exception:
                                            pass
                                        raise
                                    finally:
                                        # End span
                                        TraceContext.end_span()

                                # Mark as patched
                                patched_call_tool.__cylestio_patched__ = True

                                # Replace method - this is a bound method so we need to use types.MethodType
                                import types

                                obj._call_tool = types.MethodType(
                                    patched_call_tool, obj
                                )
                                logger.debug("Patched AgentExecutor._call_tool method")

                        # Also patch the newer _get_tool_return method if available
                        if hasattr(obj, "_get_tool_return"):
                            original_get_tool_return = obj._get_tool_return

                            # Only wrap if not already patched
                            if not hasattr(
                                original_get_tool_return, "__cylestio_patched__"
                            ):

                                @functools.wraps(original_get_tool_return)
                                def patched_get_tool_return(
                                    name, tool_input, color, observation, llm_prefix
                                ):
                                    # Start span
                                    span_id = TraceContext.start_span(f"tool.{name}")

                                    # Log tool start
                                    try:
                                        log_event(
                                            name="tool.start",
                                            attributes={
                                                "tool.name": name,
                                                "tool.input": str(tool_input),
                                                "framework.name": "langchain",
                                                "framework.component": "AgentExecutor._get_tool_return",
                                            },
                                        )
                                    except Exception as e:
                                        logger.debug(f"Error logging tool start: {e}")

                                    # Call original method
                                    try:
                                        result = original_get_tool_return(
                                            name,
                                            tool_input,
                                            color,
                                            observation,
                                            llm_prefix,
                                        )

                                        # Extract result info
                                        result_str = str(result)
                                        if len(result_str) > 1000:
                                            result_str = result_str[:997] + "..."

                                        # Log success
                                        try:
                                            log_event(
                                                name="tool.end",
                                                attributes={
                                                    "tool.name": name,
                                                    "tool.status": "success",
                                                    "tool.result": result_str,
                                                    "framework.name": "langchain",
                                                    "framework.component": "AgentExecutor._get_tool_return",
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
                                                    "tool.name": name,
                                                    "framework.name": "langchain",
                                                    "framework.component": "AgentExecutor._get_tool_return",
                                                },
                                            )
                                        except Exception:
                                            pass
                                        raise
                                    finally:
                                        # End span
                                        TraceContext.end_span()

                                # Mark as patched
                                patched_get_tool_return.__cylestio_patched__ = True

                                # Replace method - this is a bound method so we need to use types.MethodType
                                import types

                                obj._get_tool_return = types.MethodType(
                                    patched_get_tool_return, obj
                                )
                                logger.debug(
                                    "Patched AgentExecutor._get_tool_return method"
                                )

                        # Patch invoke method if present
                        if hasattr(obj, "invoke"):
                            original_invoke = obj.invoke

                            # Only wrap if not already patched
                            if not hasattr(original_invoke, "__cylestio_patched__"):

                                @functools.wraps(original_invoke)
                                def patched_invoke(*args, **kwargs):
                                    # Log agent invoke start
                                    try:
                                        # Create trace context
                                        span_id = TraceContext.start_span(
                                            "agent.invoke"
                                        )

                                        log_event(
                                            name="agent.invoke.start",
                                            attributes={
                                                "agent.type": "AgentExecutor",
                                                "framework.name": "langchain",
                                            },
                                        )
                                    except Exception:
                                        pass

                                    # Call original method
                                    try:
                                        result = original_invoke(*args, **kwargs)

                                        # Log success
                                        try:
                                            log_event(
                                                name="agent.invoke.end",
                                                attributes={
                                                    "agent.type": "AgentExecutor",
                                                    "framework.name": "langchain",
                                                    "agent.status": "success",
                                                },
                                            )
                                        except Exception:
                                            pass

                                        return result
                                    except Exception as e:
                                        # Log error
                                        try:
                                            log_error(
                                                name="agent.invoke.error",
                                                error=e,
                                                attributes={
                                                    "agent.type": "AgentExecutor",
                                                    "framework.name": "langchain",
                                                },
                                            )
                                        except Exception:
                                            pass
                                        raise
                                    finally:
                                        # End span
                                        try:
                                            TraceContext.end_span()
                                        except Exception:
                                            pass

                                # Mark as patched
                                patched_invoke.__cylestio_patched__ = True

                                # Replace method
                                obj.invoke = patched_invoke

                        # Patch run method if present (older versions)
                        if hasattr(obj, "run"):
                            original_run = obj.run

                            # Only wrap if not already patched
                            if not hasattr(original_run, "__cylestio_patched__"):

                                @functools.wraps(original_run)
                                def patched_run(*args, **kwargs):
                                    # Log agent run start
                                    try:
                                        # Create trace context
                                        span_id = TraceContext.start_span("agent.run")

                                        log_event(
                                            name="agent.run.start",
                                            attributes={
                                                "agent.type": "AgentExecutor",
                                                "framework.name": "langchain",
                                            },
                                        )
                                    except Exception:
                                        pass

                                    # Call original method
                                    try:
                                        result = original_run(*args, **kwargs)

                                        # Log success
                                        try:
                                            log_event(
                                                name="agent.run.end",
                                                attributes={
                                                    "agent.type": "AgentExecutor",
                                                    "framework.name": "langchain",
                                                    "agent.status": "success",
                                                },
                                            )
                                        except Exception:
                                            pass

                                        return result
                                    except Exception as e:
                                        # Log error
                                        try:
                                            log_error(
                                                name="agent.run.error",
                                                error=e,
                                                attributes={
                                                    "agent.type": "AgentExecutor",
                                                    "framework.name": "langchain",
                                                },
                                            )
                                        except Exception:
                                            pass
                                        raise
                                    finally:
                                        # End span
                                        try:
                                            TraceContext.end_span()
                                        except Exception:
                                            pass

                                # Mark as patched
                                patched_run.__cylestio_patched__ = True

                                # Replace method
                                obj.run = patched_run

                        # Mark agent as patched
                        obj.__cylestio_tools_patched__ = True
                        self._patch_count += 1

                except Exception as e:
                    logger.debug(
                        f"Error patching tools in module {module_name}: {str(e)}"
                    )
                    continue
        except Exception as e:
            logger.debug(f"Error patching AgentExecutor tools: {str(e)}")

    def _patch_customer_support_agent(self):
        """Apply a targeted patch for the customer support agent's tool execution.

        This addresses the specific case in the customer support bot example
        which uses a unique approach to tool execution.
        """
        try:
            # Look for modules with "customer_support" in the name
            for module_name, module in list(sys.modules.items()):
                if "customer_support" not in module_name or not module:
                    continue

                # Patch the 'run_agent' function which is commonly used in these examples
                if hasattr(module, "run_agent") and not hasattr(
                    module.run_agent, "__cylestio_patched__"
                ):
                    original_run_agent = module.run_agent

                    @functools.wraps(original_run_agent)
                    def patched_run_agent(state, *args, **kwargs):
                        # Log agent invoke
                        try:
                            log_event(
                                name="agent.invoke.start",
                                attributes={
                                    "agent.type": "run_agent",
                                    "framework.name": "langgraph",
                                    "framework.component": "customer_support_bot",
                                },
                            )
                        except Exception:
                            pass

                        # Call original
                        try:
                            result = original_run_agent(state, *args, **kwargs)

                            # Extract tool usage from the result if available
                            try:
                                if isinstance(result, dict) and "messages" in result:
                                    messages = result["messages"]
                                    for msg in messages:
                                        # Look for tool usage in message content
                                        if hasattr(msg, "content"):
                                            content = msg.content
                                            # Simple heuristic to detect tool usage
                                            if (
                                                "I'll search for" in content
                                                or "I'll look up" in content
                                            ):
                                                # This likely used a tool
                                                tool_match = None
                                                for tool_keyword in [
                                                    "flight",
                                                    "hotel",
                                                    "policy",
                                                    "car",
                                                    "excursion",
                                                ]:
                                                    if tool_keyword in content.lower():
                                                        tool_match = tool_keyword
                                                        break

                                                if tool_match:
                                                    # Log inferred tool usage
                                                    log_event(
                                                        name="tool.inferred",
                                                        attributes={
                                                            "tool.name": f"{tool_match}_tool",
                                                            "tool.result": content[
                                                                :500
                                                            ],
                                                            "framework.name": "langgraph",
                                                            "framework.component": "customer_support_bot",
                                                        },
                                                    )
                            except Exception:
                                pass

                            # Log end
                            try:
                                log_event(
                                    name="agent.invoke.end",
                                    attributes={
                                        "agent.type": "run_agent",
                                        "framework.name": "langgraph",
                                        "framework.component": "customer_support_bot",
                                        "agent.status": "success",
                                    },
                                )
                            except Exception:
                                pass

                            return result
                        except Exception as e:
                            # Log error
                            try:
                                log_error(
                                    name="agent.invoke.error",
                                    error=e,
                                    attributes={
                                        "agent.type": "run_agent",
                                        "framework.name": "langgraph",
                                        "framework.component": "customer_support_bot",
                                    },
                                )
                            except Exception:
                                pass
                            raise

                    # Mark as patched
                    patched_run_agent.__cylestio_patched__ = True

                    # Replace function
                    module.run_agent = patched_run_agent
                    logger.debug(f"Patched run_agent in {module_name}")
                    self._patch_count += 1

                # Also look for agent executor instances in the module
                for attr_name in dir(module):
                    if attr_name.startswith("_"):
                        continue

                    try:
                        obj = getattr(module, attr_name)

                        # Check if it's an agent executor with tools
                        if (
                            hasattr(obj, "tools")
                            and hasattr(obj, "invoke")
                            and not hasattr(obj, "__cylestio_patched__")
                        ):
                            # Patch invoke method
                            original_invoke = obj.invoke

                            @functools.wraps(original_invoke)
                            def patched_invoke(*args, **kwargs):
                                # Log start
                                try:
                                    span_id = TraceContext.start_span("agent.invoke")
                                    log_event(
                                        name="agent.invoke.start",
                                        attributes={
                                            "agent.type": attr_name,
                                            "framework.name": "langchain",
                                            "framework.component": "customer_support_bot",
                                        },
                                    )
                                except Exception:
                                    pass

                                # Call original
                                try:
                                    result = original_invoke(*args, **kwargs)

                                    # Detect tool usage in result
                                    try:
                                        if (
                                            isinstance(result, dict)
                                            and "output" in result
                                        ):
                                            output = result["output"]
                                            # Look for tool usage indicators
                                            for tool in getattr(obj, "tools", []):
                                                if (
                                                    hasattr(tool, "name")
                                                    and tool.name in output
                                                ):
                                                    # Likely used this tool
                                                    log_event(
                                                        name="tool.inferred",
                                                        attributes={
                                                            "tool.name": tool.name,
                                                            "tool.result": output[:500],
                                                            "framework.name": "langchain",
                                                            "framework.component": "customer_support_bot",
                                                        },
                                                    )
                                    except Exception:
                                        pass

                                    # Log end
                                    try:
                                        log_event(
                                            name="agent.invoke.end",
                                            attributes={
                                                "agent.type": attr_name,
                                                "framework.name": "langchain",
                                                "framework.component": "customer_support_bot",
                                                "agent.status": "success",
                                            },
                                        )
                                    except Exception:
                                        pass

                                    return result
                                except Exception as e:
                                    # Log error
                                    try:
                                        log_error(
                                            name="agent.invoke.error",
                                            error=e,
                                            attributes={
                                                "agent.type": attr_name,
                                                "framework.name": "langchain",
                                                "framework.component": "customer_support_bot",
                                            },
                                        )
                                    except Exception:
                                        pass
                                    raise
                                finally:
                                    # End span
                                    try:
                                        TraceContext.end_span()
                                    except Exception:
                                        pass

                            # Mark as patched
                            patched_invoke.__cylestio_patched__ = True

                            # Replace method
                            obj.invoke = patched_invoke

                            # Mark as patched
                            obj.__cylestio_patched__ = True
                            logger.debug(f"Patched {attr_name} in {module_name}")
                            self._patch_count += 1
                    except Exception:
                        continue

        except Exception as e:
            logger.debug(f"Error patching customer support bot: {e}")

    def _is_tool_function(self, obj: Any) -> bool:
        """Check if an object is a function decorated with @tool.

        Args:
            obj: The object to check

        Returns:
            bool: True if it's a tool function, False otherwise
        """
        # Must be callable
        if not callable(obj):
            return False

        # Check for standard tool indicators (most reliable)
        tool_indicators = [
            # Has tool_metadata attribute
            lambda o: hasattr(o, "tool_metadata"),
            # Has specific tool attributes
            lambda o: hasattr(o, "name") and hasattr(o, "description"),
            # Has args_schema
            lambda o: hasattr(o, "args_schema"),
            # BaseTool instance
            lambda o: hasattr(o, "_run")
            and hasattr(o, "name")
            and hasattr(o, "description"),
            # Tool function with schema
            lambda o: hasattr(o, "schema") and callable(o),
        ]

        # Check each indicator
        for indicator in tool_indicators:
            try:
                if indicator(obj):
                    return True
            except Exception:
                continue

        # Special case for the customer support agent tools
        # Check name and function signature
        try:
            if hasattr(obj, "__name__"):
                # Check if the function has a docstring describing it as a tool
                if obj.__doc__ and (
                    "tool" in obj.__doc__.lower()
                    or "look up" in obj.__doc__.lower()
                    or "search" in obj.__doc__.lower()
                ):
                    # Look at signature - tools often have typed args/return
                    sig = inspect.signature(obj)
                    # If it has typed annotations and a descriptive docstring, it's likely a tool
                    if sig.return_annotation != inspect.Signature.empty:
                        return True
        except Exception:
            pass

        return False

    def _create_monitored_tool(self, tool_func: Callable) -> Callable:
        """Create a monitored version of a tool function.

        Args:
            tool_func: The tool function to monitor

        Returns:
            Callable: The monitored version of the function
        """
        # Check if already patched to prevent double-wrapping
        if hasattr(tool_func, "__cylestio_patched__"):
            return tool_func

        # Preserve all original attributes and type annotations
        original_annotations = getattr(tool_func, "__annotations__", {})
        original_signature = inspect.signature(tool_func)

        # Create a lightweight wrapper that preserves all original attributes
        @functools.wraps(tool_func)
        def monitored_tool(*args, **kwargs):
            # Get tool name - try multiple sources
            tool_name = None

            # 1. Try tool_metadata attribute
            if hasattr(tool_func, "tool_metadata"):
                tool_name = tool_func.tool_metadata.get("name")

            # 2. Try direct name attribute
            if tool_name is None and hasattr(tool_func, "name"):
                tool_name = tool_func.name

            # 3. Fall back to function name
            if tool_name is None:
                tool_name = getattr(tool_func, "__name__", "unknown_tool")

            # Get function module
            func_module = getattr(tool_func, "__module__", "unknown")

            # Start the monitoring span
            span_id = TraceContext.start_span(f"tool.{tool_name}")

            # Prepare attributes for event logging
            attributes = {
                "tool.name": tool_name,
                "tool.type": "function",
                "tool.module": func_module,
                "framework.name": "langchain",
            }

            # Get description if available
            if hasattr(tool_func, "description"):
                attributes["tool.description"] = tool_func.description

            # Get return type if available
            if (
                hasattr(tool_func, "__annotations__")
                and "return" in tool_func.__annotations__
            ):
                try:
                    return_type = str(tool_func.__annotations__["return"])
                    attributes["tool.return_type"] = return_type
                except Exception:
                    pass

            # Safely extract args/kwargs for logging
            try:
                # Handle args (safely)
                arg_str = ""
                if args:
                    # Try to serialize args - handle case where first arg might be self
                    if (
                        len(args) > 0
                        and hasattr(args[0], "__class__")
                        and tool_name in dir(args[0].__class__)
                    ):
                        # This is likely 'self' - skip it
                        arg_str = str(args[1:]) if len(args) > 1 else ""
                    else:
                        arg_str = str(args)

                # Handle kwargs
                kwarg_str = str(kwargs) if kwargs else ""

                # Add to attributes if not empty
                if arg_str and arg_str != "()":
                    attributes["tool.args"] = arg_str
            except Exception as e:
                logger.debug(f"Error serializing tool arguments: {e}")

            if kwarg_str and kwarg_str != "{}":
                attributes["tool.kwargs"] = kwarg_str

            # Log tool start
            log_event(name="tool.start", attributes=attributes)

            try:
                # Call the tool function
                result = tool_func(*args, **kwargs)

                # Prepare result attributes
                result_attributes = attributes.copy()
                result_attributes["tool.status"] = "success"

                # Add result info (safely)
                try:
                    result_str = str(result)
                    if len(result_str) > 1000:
                        result_str = result_str[:997] + "..."
                    result_attributes["tool.result"] = result_str
                    result_attributes["tool.result.type"] = type(result).__name__
                except Exception:
                    result_attributes["tool.result.type"] = type(result).__name__

                # Log tool end event
                log_event(name="tool.end", attributes=result_attributes)

                return result
            except Exception as e:
                # Log tool error
                log_error(name="tool.error", error=e, attributes=attributes)
                raise
            finally:
                # End span
                TraceContext.end_span()

        # Mark as patched
        monitored_tool.__cylestio_patched__ = True

        # Copy all original annotations and signature info to maintain compatibility with type systems
        monitored_tool.__annotations__ = original_annotations
        monitored_tool.__signature__ = original_signature

        # Special handling for LangChain tool attributes
        for attr in [
            "name",
            "description",
            "args_schema",
            "return_type",
            "tool_metadata",
            "schema",
        ]:
            if hasattr(tool_func, attr):
                setattr(monitored_tool, attr, getattr(tool_func, attr))

        return monitored_tool

    def _create_monitored_tool_proxy(self, tool_func: Callable) -> Callable:
        """Create a proxy for a tool that preserves its original identity.

        This method creates a wrapper that maintains the original tool's identity
        for type checking while still monitoring its calls.

        Args:
            tool_func: The original tool function

        Returns:
            A monitored proxy that preserves type checking capability
        """
        # Create monitored version
        monitored_version = self._create_monitored_tool(tool_func)

        # Copy all original attributes directly - this is key to preserving type information
        for attr_name in dir(tool_func):
            if not attr_name.startswith("__"):
                try:
                    if not hasattr(monitored_version, attr_name):
                        original_attr = getattr(tool_func, attr_name)
                        setattr(monitored_version, attr_name, original_attr)
                except (AttributeError, TypeError):
                    pass

        # Override the __wrapped__ attribute to point to the original function
        # This helps with inspection tools and type checking
        monitored_version.__wrapped__ = tool_func

        # Specifically preserve schema information to avoid Pydantic validation errors
        if hasattr(tool_func, "schema"):
            monitored_version.schema = tool_func.schema

        # Set special flag to indicate this is a proxy (not just a wrapped function)
        monitored_version.__cylestio_proxy__ = True

        return monitored_version

    def unpatch(self) -> None:
        """Remove the patches.

        Implementation of the required abstract method from BasePatcher.
        """
        if not self._patched:
            return

        success = True

        # Restore original functions
        for module_name, functions in self._patched_functions.items():
            try:
                module = sys.modules.get(module_name)
                if not module:
                    continue

                for func_name, original_func in functions.items():
                    try:
                        setattr(module, func_name, original_func)
                    except Exception as e:
                        logger.warning(
                            f"Error restoring {module_name}.{func_name}: {e}"
                        )
                        success = False
            except Exception as e:
                logger.warning(f"Error unpatching module {module_name}: {e}")
                success = False

        self._patched = not success


def patch_decorated_tools(safe_mode=True):
    """Find and patch functions already decorated with @tool.

    Args:
        safe_mode: If True, only patch agent executors and avoid direct tool patching
                  This prevents type system breakage at the cost of less detailed monitoring

    Returns:
        bool: True if patching was successful
    """
    patcher = DecoratedToolsPatcher()

    # In safe mode, skip direct tool patching to avoid breaking type system
    if safe_mode:
        # Only apply agent executor patching which doesn't modify tools directly
        try:
            patcher._find_and_patch_tools_in_agent_executors()
            return True
        except Exception:
            return False
    else:
        # Apply full patching (may break type system in complex environments)
        patcher.patch()
        return patcher._patched


def unpatch_decorated_tools():
    """Unpatch functions that were decorated with @tool."""
    patcher = DecoratedToolsPatcher()
    patcher.unpatch()
    return not patcher._patched
