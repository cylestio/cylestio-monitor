"""Cylestio Monitor core module.

This module provides a framework-agnostic monitoring solution for AI agents.
It supports monitoring of MCP, LLM API calls, LangChain, and LangGraph.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from .api_client import get_api_client
from .config import ConfigManager
from .patchers.mcp_patcher import patch_mcp, unpatch_mcp
from .utils.event_logging import log_event
from .utils.trace_context import TraceContext

# Configure root logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def start_monitoring(
    agent_id: str,
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Initialize monitoring for AI agents across various frameworks.

    Args:
        agent_id: Unique identifier for the agent
        config: Optional configuration dictionary that can include:
            - debug_level: Logging level for SDK's internal logs (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            - log_file: Path to the output log file (if None, only API logging is used)
                - If a directory is provided, a file named "{agent_id}_monitoring_{timestamp}.json" will be created
                - If a file without extension is provided, ".json" will be added
            - api_endpoint: URL of the remote API endpoint to send events to
            - development_mode: Enable additional development features like detailed logging

    Note:
        The SDK automatically detects which frameworks are installed and available to monitor.
        No explicit configuration is needed to enable monitoring for specific frameworks,
        including Anthropic clients which are now automatically detected and patched.
    """
    config = config or {}

    # Ensure essential typing modules are properly imported
    # This prevents type-related errors when patching decorated functions
    try:
        # These imports ensure proper type resolution when patching tools
        import inspect
        import types
        from typing import (Annotated, Any, Dict, Generic, List, Optional,
                            Protocol, TypeVar, Union)
    except ImportError:
        logger.debug(
            "Failed to import some typing modules, type annotation compatibility may be limited"
        )

    # Extract debug level from config
    debug_level = config.get("debug_level", "INFO")

    # Extract log file path from config
    log_file = config.get("log_file")

    # Check if development mode is enabled
    development_mode = config.get("development_mode", False)
    if development_mode:
        # Set environment variable for other components
        os.environ["CYLESTIO_DEVELOPMENT_MODE"] = "1"
        # Use debug level if not explicitly set
        if "debug_level" not in config:
            debug_level = "DEBUG"

    # Set up logging configuration for the monitor
    monitor_logger = logging.getLogger("CylestioMonitor")

    # Set the logging level based on the debug_level parameter
    level = getattr(logging, debug_level.upper(), logging.INFO)
    monitor_logger.setLevel(level)

    # Remove any existing handlers to avoid duplicate logs
    for handler in monitor_logger.handlers[:]:
        monitor_logger.removeHandler(handler)

    # Process log_file path if provided
    if log_file:
        # If log_file is a directory, create a file with the agent_id in the name
        if os.path.isdir(log_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"{agent_id}_monitoring_{timestamp}.json"
            log_file = os.path.join(log_file, log_filename)
        # If log_file doesn't have an extension, add .json
        elif not os.path.splitext(log_file)[1]:
            log_file = f"{log_file}.json"

        # Create the directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    # Add a console handler for debug logs only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(
        logging.Formatter("CylestioSDK - %(levelname)s: %(message)s")
    )
    monitor_logger.addHandler(console_handler)

    # Store the agent ID and log file in the configuration
    config_manager = ConfigManager()
    config_manager.set("monitoring.agent_id", agent_id)
    config_manager.set("monitoring.log_file", log_file)
    config_manager.save()

    # Initialize the API client if endpoint is provided
    api_endpoint = config.get("api_endpoint")
    if api_endpoint:
        # Set the environment variable for the API endpoint
        os.environ["CYLESTIO_API_ENDPOINT"] = api_endpoint

        # Initialize the API client
        api_client = get_api_client()
        if api_client.endpoint:
            logger.info(f"API client initialized with endpoint: {api_client.endpoint}")
        else:
            logger.warning(
                "API endpoint not configured. Events will only be logged to file."
            )

    # Initialize trace context
    trace_id = TraceContext.initialize_trace(agent_id)

    # Log initialization event
    log_event(
        name="monitoring.start",
        attributes={"agent.id": agent_id, "monitoring.version": "2.0.0"},
    )

    # Check if framework patching is enabled (default to True)
    enable_framework_patching = config.get("enable_framework_patching", True)

    # Check if safe mode is enabled for tool patching (default to True)
    safe_tool_patching = config.get("safe_tool_patching", True)

    try:
        # Ensure critical patching is done early for tool schema creation
        # This must be done early to prevent type evaluation errors
        try:
            from .patchers.tool_decorator_patcher import \
                patch_openai_function_schema_creation

            schema_patched = patch_openai_function_schema_creation()
            if schema_patched:
                logger.info(
                    "OpenAI function schema creation patched for tool monitoring"
                )
        except Exception as e:
            logger.warning(f"Failed to patch OpenAI function schema creation: {e}")

        # Step 1: Patch MCP if available and enabled
        try:
            # Apply MCP patcher directly using our imported function
            patch_result = patch_mcp()

            if patch_result:
                logger.info("MCP patched for monitoring")
                monitor_logger.info("MCP integration enabled")
            else:
                logger.warning(
                    "Failed to patch MCP. MCP monitoring will not be available."
                )

        except ImportError:
            # MCP not installed or available
            logger.debug("MCP not available, skipping patch")

        except Exception as e:
            logger.error(f"Error patching MCP: {e}")

        # Step 2: Apply global module patching for Anthropic (new approach)
        try:
            # Import patcher module and apply global patch
            from .patchers.anthropic import patch_anthropic_module

            patch_anthropic_module()
            logger.info("Anthropic module patched for global monitoring")
            monitor_logger.info(
                "Anthropic integration enabled (global module patching)"
            )
        except ImportError:
            logger.debug("Anthropic module not available for global patching")
        except Exception as e:
            logger.warning(f"Failed to apply global Anthropic patches: {e}")

        # Step 3: Apply global module patching for OpenAI
        try:
            # Import patcher module and apply global patch
            from .patchers.openai_patcher import patch_openai_module

            patch_openai_module()
            logger.info("OpenAI module patched for global monitoring")
            monitor_logger.info("OpenAI integration enabled (global module patching)")
        except ImportError:
            logger.debug("OpenAI module not available for global patching")
        except Exception as e:
            logger.warning(f"Failed to apply global OpenAI patches: {e}")

        # Step 4: Apply tool patchers early to ensure all tools are intercepted
        try:
            # Patch @tool decorator BEFORE framework patches so all new tools get instrumented
            from .patchers.tool_decorator_patcher import patch_tool_decorator

            patch_result = patch_tool_decorator()
            if patch_result:
                logger.info("LangChain @tool decorator patched for monitoring")
                monitor_logger.info("Tool decorator monitoring enabled")
            else:
                logger.debug("LangChain @tool decorator not available for patching")
        except Exception as e:
            logger.warning(f"Failed to patch @tool decorator: {e}")

        # Step 5: Try to patch framework libraries if enabled
        if enable_framework_patching:
            # Try to patch LangChain if present
            try:
                import langchain

                # Only import the LangChain patcher if LangChain is available
                try:
                    from .patchers.langchain_patcher import patch_langchain

                    patch_langchain()
                    logger.info("LangChain patched for monitoring")
                    monitor_logger.info("LangChain integration enabled")
                except Exception as e:
                    logger.error(f"Failed to patch LangChain: {e}")

            except ImportError:
                # LangChain not installed or available
                pass

            # Try to patch LangGraph if present
            try:
                import langgraph

                # Only import the LangGraph patcher if LangGraph is available
                try:
                    from .patchers.langgraph_patcher import patch_langgraph

                    patch_langgraph()
                    logger.info("LangGraph patched for monitoring")
                    monitor_logger.info("LangGraph integration enabled")
                except Exception as e:
                    logger.error(f"Failed to patch LangGraph: {e}")

            except ImportError:
                # LangGraph not installed or available
                pass

            # Step 6: Find and patch already-decorated tools (after framework patches)
            try:
                # Try to patch already-decorated tools
                from .patchers.decorated_tools_patcher import \
                    patch_decorated_tools

                # Use safe mode by default to prevent type system errors
                # In safe mode we only patch agent executors and don't modify tools directly
                tools_patched = patch_decorated_tools(safe_mode=safe_tool_patching)

                if tools_patched:
                    if safe_tool_patching:
                        logger.info("Agent executors patched for tool monitoring")
                        monitor_logger.info("Agent monitoring enabled (safe mode)")
                    else:
                        logger.info("All tool functions patched directly")
                        monitor_logger.info(
                            "Tool function monitoring enabled (invasive mode)"
                        )
                else:
                    logger.debug("No agent executors or tools found for patching")
            except Exception as e:
                logger.warning(f"Failed to patch pre-existing tools: {e}")

    except Exception as e:
        logger.error(f"Error during monitoring setup: {e}")

    logger.info(f"Monitoring started for agent: {agent_id}")


def stop_monitoring() -> None:
    """
    Stop monitoring and clean up resources.

    This function should be called when the application is shutting down
    to ensure proper cleanup of monitoring resources and flush pending logs.
    """
    logger.info("Stopping monitoring...")

    # Get agent ID from config for logging
    config_manager = ConfigManager()
    agent_id = config_manager.get("monitoring.agent_id")

    # Log monitoring stop event
    log_event(
        name="monitoring.stop", attributes={"agent.id": agent_id} if agent_id else {}
    )

    # Unpatch MCP if it was patched
    try:
        unpatch_mcp()
    except Exception as e:
        logger.warning(f"Error while unpatching MCP: {e}")

    # Unpatch Anthropic if it was patched
    try:
        from .patchers.anthropic import unpatch_anthropic_module

        unpatch_anthropic_module()
    except Exception as e:
        logger.warning(f"Error while unpatching Anthropic: {e}")

    # Unpatch OpenAI if it was patched
    try:
        from .patchers.openai_patcher import unpatch_openai_module

        unpatch_openai_module()
    except Exception as e:
        logger.warning(f"Error while unpatching OpenAI: {e}")

    # Unpatch LangChain if it was patched
    try:
        from .patchers.langchain_patcher import unpatch_langchain

        unpatch_langchain()
    except Exception as e:
        logger.warning(f"Error while unpatching LangChain: {e}")

    # Unpatch tool decorator if it was patched
    try:
        from .patchers.tool_decorator_patcher import unpatch_tool_decorator

        unpatch_tool_decorator()
    except Exception as e:
        logger.warning(f"Error while unpatching tool decorator: {e}")

    # Unpatch decorated tools if they were patched
    try:
        from .patchers.decorated_tools_patcher import unpatch_decorated_tools

        unpatch_decorated_tools()
    except Exception as e:
        logger.warning(f"Error while unpatching decorated tools: {e}")

    # Unpatch LangGraph if it was patched
    try:
        from .patchers.langgraph_patcher import unpatch_langgraph

        unpatch_langgraph()
    except Exception as e:
        logger.warning(f"Error while unpatching LangGraph: {e}")

    # Stop the background API thread
    try:
        from cylestio_monitor.api_client import stop_background_thread

        stop_background_thread()
    except Exception as e:
        logger.warning(f"Error stopping background API thread: {e}")

    # Reset the trace context
    TraceContext.reset()

    logger.info("Monitoring stopped")
    monitor_logger = logging.getLogger("CylestioMonitor")
    monitor_logger.info("Monitoring stopped")


def get_api_endpoint() -> str:
    """
    Get the currently configured API endpoint.

    Returns:
        str: The API endpoint URL or an empty string if not configured
    """
    api_client = get_api_client()
    return api_client.endpoint or ""


__all__ = ["start_monitoring", "stop_monitoring", "get_api_endpoint"]
