"""Tool Decorator Patcher for Cylestio Monitor.

This module provides patching functionality for LangChain's @tool decorator,
allowing automatic monitoring of all tool calls in an application.
"""

import functools
import logging
import sys
import inspect
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, TypeVar

from cylestio_monitor.patchers.base import BasePatcher
from cylestio_monitor.utils.event_logging import log_error, log_event
from cylestio_monitor.utils.trace_context import TraceContext

logger = logging.getLogger("CylestioMonitor")

# Import LangChain components from their new locations
from langchain_core.tools import BaseTool


class ToolDecoratorPatcher(BasePatcher):
    """Patcher for LangChain @tool decorator."""

    def __init__(self):
        """Initialize the tool decorator patcher."""
        super().__init__({"name": "langchain_tools"})
        self._patched = False
        self._original_decorators = {}

    def patch(self) -> None:
        """Apply the patches for @tool decorator.

        Implementation of the required abstract method from BasePatcher.
        """
        self._apply()

    def _apply(self) -> bool:
        """Apply the patches for @tool decorator.

        Returns:
            bool: True if successful, False otherwise
        """
        if self._patched:
            logger.warning("LangChain @tool decorator already patched")
            return False

        try:
            # Try to patch both langchain and langchain_core if available
            patched_any = False

            # Log patch event
            context = TraceContext.get_current_context()
            log_event(
                name="framework.patch",
                attributes={
                    "framework.name": "langchain_tools",
                    "patch.type": "tool_decorator",
                    "patch.components": ["@tool"],
                },
                trace_id=context.get("trace_id"),
                agent_id=context.get("agent_id"),
            )

            # Try to patch langchain_core first (newer versions)
            if self._patch_core_tools():
                patched_any = True
                logger.info("Patched LangChain Core @tool decorator")

            # Try to patch langchain (older versions)
            if self._patch_langchain_tools():
                patched_any = True
                logger.info("Patched LangChain @tool decorator")

            self._patched = patched_any
            if patched_any:
                logger.info("Successfully patched LangChain @tool decorator")
                return True
            else:
                logger.warning("No LangChain @tool decorators found to patch")
                return False

        except Exception as e:
            log_error(
                name="framework.patch.error",
                error=e,
                attributes={"framework.name": "langchain_tools"},
                trace_id=context.get("trace_id"),
                agent_id=context.get("agent_id"),
            )
            logger.exception(f"Error patching LangChain @tool decorator: {e}")
            return False

    def _patch_core_tools(self) -> bool:
        """Patch langchain_core.tools module.

        Returns:
            bool: True if successful, False if not available
        """
        try:
            # Import the module
            import langchain_core.tools

            # Check if it has the tool decorator
            if not hasattr(langchain_core.tools, "tool"):
                logger.debug("langchain_core.tools.tool not found")
                return False

            # Store the original decorator
            original_decorator = langchain_core.tools.tool
            self._original_decorators["langchain_core.tools.tool"] = original_decorator

            # Create the patched decorator
            @functools.wraps(original_decorator)
            def patched_tool_decorator(*dec_args, **dec_kwargs):
                # Handle different ways the decorator might be used

                # Case 1: @tool used directly on function
                if len(dec_args) == 1 and callable(dec_args[0]) and not dec_kwargs:
                    func = dec_args[0]
                    decorated_func = original_decorator(func)
                    return self._wrap_decorated_function(func, decorated_func)

                # Case 2: @tool() - no args but called as function
                if not dec_args and not dec_kwargs:

                    def wrapper(func):
                        decorated_func = original_decorator()(func)
                        return self._wrap_decorated_function(func, decorated_func)

                    return wrapper

                # Case 3: @tool(name="xyz") or other parameters
                original_inner = original_decorator(*dec_args, **dec_kwargs)

                # Handle both function and class returns from original decorator
                @functools.wraps(original_inner)
                def inner_wrapper(func):
                    # Apply original decorator first
                    decorated_func = original_inner(func)
                    # Then wrap with monitoring
                    return self._wrap_decorated_function(func, decorated_func)

                return inner_wrapper

            # Apply the patch
            langchain_core.tools.tool = patched_tool_decorator
            logger.debug("Patched langchain_core.tools.tool decorator")

            # For complete coverage, also patch BaseTool class in a non-breaking way
            self._patch_base_tool_class()

            return True

        except ImportError:
            logger.debug("langchain_core.tools not available")
            return False
        except Exception as e:
            logger.warning(f"Error patching langchain_core.tools: {e}")
            return False

    def _patch_base_tool_class(self):
        """Patch the BaseTool class for safe monitoring without breaking validation.

        Instead of patching the _run method directly which can break validation,
        we patch the __call__ method which is used to invoke the tool.
        """
        try:
            # Skip if already patched
            if hasattr(BaseTool, "__cylestio_patched__"):
                return True

            # Get the original __call__ method
            original_call = BaseTool.__call__

            # Only patch if not already patched
            if hasattr(original_call, "__cylestio_patched__"):
                return True

            # Create patched version
            @functools.wraps(original_call)
            def patched_call(self, *args, **kwargs):
                # Extract tool details
                tool_name = getattr(self, "name", self.__class__.__name__)

                # Start span for monitoring
                span_id = None
                try:
                    span_id = TraceContext.start_span(f"tool.{tool_name}")

                    # Log tool start
                    log_event(
                        name="tool.start",
                        attributes={
                            "tool.name": tool_name,
                            "tool.type": "BaseTool",
                            "tool.class": self.__class__.__name__,
                            "framework.name": "langchain",
                            "tool.args": str(args),
                            "tool.kwargs": str(kwargs),
                        },
                    )
                except Exception as e:
                    logger.debug(f"Error logging tool start: {e}")

                try:
                    # Call original method
                    result = original_call(self, *args, **kwargs)

                    # Log success
                    try:
                        log_event(
                            name="tool.end",
                            attributes={
                                "tool.name": tool_name,
                                "tool.type": "BaseTool",
                                "tool.class": self.__class__.__name__,
                                "tool.status": "success",
                                "framework.name": "langchain",
                                "tool.result": str(result)[:1000],
                                "tool.result.type": type(result).__name__,
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
                                "tool.type": "BaseTool",
                                "tool.class": self.__class__.__name__,
                                "framework.name": "langchain",
                            },
                        )
                    except Exception:
                        pass
                    raise
                finally:
                    # End span
                    if span_id:
                        try:
                            TraceContext.end_span()
                        except Exception:
                            pass

            # Mark as patched
            patched_call.__cylestio_patched__ = True

            # Replace the method
            BaseTool.__call__ = patched_call

            # Mark the class as patched
            BaseTool.__cylestio_patched__ = True

            logger.debug("Patched BaseTool.__call__ for monitoring")
            return True

        except Exception as e:
            logger.debug(f"Error patching BaseTool class: {e}")
            return False

    def _patch_langchain_tools(self) -> bool:
        """Patch langchain.agents.tools module.

        Returns:
            bool: True if successful, False if not available
        """
        try:
            # Import the module
            import langchain.agents.tools

            # Check if it has the tool decorator
            if not hasattr(langchain.agents.tools, "tool"):
                logger.debug("langchain.agents.tools.tool not found")
                return False

            # Store the original decorator
            original_decorator = langchain.agents.tools.tool
            self._original_decorators[
                "langchain.agents.tools.tool"
            ] = original_decorator

            # Create the patched decorator
            @functools.wraps(original_decorator)
            def patched_tool_decorator(*dec_args, **dec_kwargs):
                # Handle different ways the decorator might be used

                # Case 1: @tool used directly on function
                if len(dec_args) == 1 and callable(dec_args[0]) and not dec_kwargs:
                    func = dec_args[0]
                    decorated_func = original_decorator(func)
                    return self._wrap_decorated_function(func, decorated_func)

                # Case 2: @tool() - no args but called as function
                if not dec_args and not dec_kwargs:

                    def wrapper(func):
                        decorated_func = original_decorator()(func)
                        return self._wrap_decorated_function(func, decorated_func)

                    return wrapper

                # Case 3: @tool(name="xyz") or other parameters
                original_inner = original_decorator(*dec_args, **dec_kwargs)

                # Handle both function and class returns from original decorator
                @functools.wraps(original_inner)
                def inner_wrapper(func):
                    # Apply original decorator first
                    decorated_func = original_inner(func)
                    # Then wrap with monitoring
                    return self._wrap_decorated_function(func, decorated_func)

                return inner_wrapper

            # Apply the patch
            langchain.agents.tools.tool = patched_tool_decorator
            logger.debug("Patched langchain.agents.tools.tool decorator")

            return True

        except ImportError:
            logger.debug("langchain.agents.tools not available")
            return False
        except Exception as e:
            logger.warning(f"Error patching langchain.agents.tools: {e}")
            return False

    def _wrap_decorated_function(self, original_func, decorated_func):
        """Wrap a function that has been decorated with @tool.

        Args:
            original_func: The original function before decoration
            decorated_func: The function after @tool decoration

        Returns:
            Callable: The instrumented function
        """
        # Check if already patched to prevent double-wrapping
        if hasattr(decorated_func, "__cylestio_patched__"):
            return decorated_func

        # Create a lightweight wrapper that preserves all original attributes
        @functools.wraps(decorated_func)
        def monitored_tool_function(*args, **kwargs):
            # Extract function details
            func_name = original_func.__name__
            func_module = original_func.__module__

            # Get tool metadata if available
            tool_name = func_name
            tool_description = ""

            if hasattr(decorated_func, "name"):
                tool_name = decorated_func.name

            if hasattr(decorated_func, "description"):
                tool_description = decorated_func.description

            if hasattr(decorated_func, "tool_metadata"):
                metadata = decorated_func.tool_metadata
                tool_name = metadata.get("name", tool_name)

            # Extract args/kwargs for monitoring (safely)
            arg_str = ""
            kwarg_str = ""

            try:
                # Handle potential pydantic model in first arg (common pattern)
                if args and len(args) > 0:
                    if hasattr(args[0], "__dict__") and not (
                        hasattr(args[0], "__class__")
                        and func_name in dir(args[0].__class__)
                    ):
                        # This is likely a pydantic model
                        try:
                            arg_str = str(args[0].__dict__)
                        except:
                            arg_str = str(args)
                    elif hasattr(args[0], "__class__") and func_name in dir(
                        args[0].__class__
                    ):
                        # This is likely self
                        arg_str = str(args[1:]) if len(args) > 1 else ""
                    else:
                        arg_str = str(args)

                kwarg_str = str(kwargs) if kwargs else ""
            except Exception as e:
                logger.debug(f"Error serializing tool arguments: {e}")

            # Start span for tool execution
            span_id = TraceContext.start_span(f"tool.{tool_name}")

            # Create attributes dictionary
            tool_attributes = {
                "tool.name": tool_name,
                "tool.function": func_name,
                "tool.module": func_module,
                "framework.name": "langchain",
                "framework.type": "tool",
            }

            # Add description if available
            if tool_description:
                tool_attributes["tool.description"] = tool_description

            # Add args/kwargs if available
            if arg_str:
                tool_attributes["tool.args"] = arg_str
            if kwarg_str:
                tool_attributes["tool.kwargs"] = kwarg_str

            # Log tool start event
            log_event(name="tool.start", attributes=tool_attributes)

            try:
                # Call the decorated function
                result = decorated_func(*args, **kwargs)

                # Prepare result attributes
                result_attributes = tool_attributes.copy()
                result_attributes.update(
                    {
                        "tool.status": "success",
                    }
                )

                # Add result details (safely)
                try:
                    result_str = str(result)
                    # Truncate if too long
                    if len(result_str) > 1000:
                        result_str = result_str[:997] + "..."
                    result_attributes["tool.result"] = result_str
                    result_attributes["tool.result.type"] = type(result).__name__
                except Exception as e:
                    logger.debug(f"Error serializing tool result: {e}")
                    result_attributes["tool.result.type"] = type(result).__name__

                # Log tool end event
                log_event(name="tool.end", attributes=result_attributes)

                return result
            except Exception as e:
                # Log tool error event
                log_error(name="tool.error", error=e, attributes=tool_attributes)
                raise
            finally:
                # End the span
                TraceContext.end_span()

        # Mark as patched
        monitored_tool_function.__cylestio_patched__ = True

        # Make sure all original attributes are preserved exactly
        for attr_name in dir(decorated_func):
            if not attr_name.startswith("__"):
                try:
                    original_attr = getattr(decorated_func, attr_name)
                    if not hasattr(monitored_tool_function, attr_name):
                        setattr(monitored_tool_function, attr_name, original_attr)
                except (AttributeError, TypeError):
                    pass

        return monitored_tool_function

    def unpatch(self) -> None:
        """Remove the patches.

        Implementation of the required abstract method from BasePatcher.
        """
        if not self._patched:
            return

        success = True

        # Restore original decorators
        for path, original_decorator in self._original_decorators.items():
            try:
                module_path, attr_name = path.rsplit(".", 1)
                module = sys.modules.get(module_path)
                if module:
                    setattr(module, attr_name, original_decorator)
                    logger.debug(f"Restored original {path}")
            except Exception as e:
                logger.warning(f"Error unpatching {path}: {e}")
                success = False

        # Try to unpatch BaseTool class
        try:
            if hasattr(BaseTool, "__original_init__"):
                BaseTool.__init__ = BaseTool.__original_init__
                logger.debug("Restored original BaseTool.__init__")
        except Exception:
            pass

        self._patched = not success


def patch_openai_function_schema_creation():
    """Patch the OpenAI function schema creation process to handle our monitoring.

    This is a direct approach to solve the Annotated type error by patching the conversion
    function itself rather than patching individual tools.
    """
    try:
        # Only patch if langchain_core is available
        import sys

        if "langchain_core.utils.function_calling" not in sys.modules:
            return False

        # Import directly to ensure type compatibility

        module = sys.modules["langchain_core.utils.function_calling"]

        # Get the original schema creation function
        if not hasattr(module, "_convert_python_function_to_openai_function"):
            return False

        original_convert = module._convert_python_function_to_openai_function

        # Skip if already patched
        if hasattr(original_convert, "__cylestio_patched__"):
            return True

        # Create patched version that handles monitoring wrappers
        import functools

        from cylestio_monitor.utils.event_logging import log_event

        @functools.wraps(original_convert)
        def patched_convert(function):
            """Patched version of convert function that preserves schema generation."""
            # Skip our patching if this isn't a callable
            if not callable(function):
                return original_convert(function)

            # Check if this is our patched function
            if hasattr(function, "__cylestio_patched__"):
                # Get original function if available
                original_func = getattr(function, "__wrapped__", None)

                if original_func:
                    try:
                        # Use original for schema generation
                        schema = original_convert(original_func)

                        # Log the schema generation for monitoring
                        log_event(
                            name="tool.schema.generated",
                            attributes={
                                "tool.name": getattr(
                                    function,
                                    "name",
                                    getattr(original_func, "__name__", "unknown"),
                                ),
                                "framework.name": "langchain",
                            },
                        )

                        return schema
                    except Exception:
                        # If schema generation with original fails, try with wrapped function
                        # This is safer than failing entirely
                        pass

            # Fall back to original function for all other cases
            return original_convert(function)

        # Mark as patched
        patched_convert.__cylestio_patched__ = True

        # Replace the function
        module._convert_python_function_to_openai_function = patched_convert

        # Also patch the public function for good measure
        if hasattr(module, "convert_to_openai_function"):
            original_public = module.convert_to_openai_function

            @functools.wraps(original_public)
            def patched_public(function):
                """Patched version of convert_to_openai_function."""
                # Skip non-callables
                if not callable(function):
                    return original_public(function)

                if hasattr(function, "__cylestio_patched__"):
                    original_func = getattr(function, "__wrapped__", None)
                    if original_func:
                        try:
                            schema = original_public(original_func)
                            # Keep the monitored function for execution but use original schema
                            if "function" in schema:
                                schema["function"]["implementation"] = function
                            return schema
                        except Exception:
                            # If schema generation with original fails, try with wrapped function
                            pass

                return original_public(function)

            patched_public.__cylestio_patched__ = True
            module.convert_to_openai_function = patched_public

        return True

    except Exception as e:
        import logging

        logger = logging.getLogger("CylestioMonitor")
        logger.warning(f"Failed to patch OpenAI function schema creation: {e}")
        return False


# Original function for patching the tool decorator
def patch_tool_decorator():
    """Patch the LangChain tool decorator."""
    # First ensure the OpenAI function schema creation is patched
    schema_patched = patch_openai_function_schema_creation()

    # Then proceed with normal patching
    patcher = ToolDecoratorPatcher()
    return patcher.patch() or schema_patched


def unpatch_tool_decorator():
    """Unpatch the LangChain @tool decorator."""
    patcher = ToolDecoratorPatcher()
    patcher.unpatch()
    return not patcher._patched
