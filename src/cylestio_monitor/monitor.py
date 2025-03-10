"""Cylestio Monitor core module.

This module provides a framework-agnostic monitoring solution for AI agents.
It supports monitoring of MCP and LLM API calls.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from .events_listener import monitor_call, monitor_llm_call
from .events_processor import log_event

# Configure root logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def enable_monitoring(
    logger_id: Optional[str] = None,
    llm_client: Any = None,
    llm_method_path: str = "messages.create",
    log_file: str = "cylestio_monitoring.json",
    debug_level: str = "INFO",
):
    """
    Enable monitoring by patching MCP and LLM clients.

    This is the main entry point for the Cylestio Monitor SDK. It automatically detects
    and patches supported frameworks and clients.

    Args:
        logger_id: Optional identifier for the logger
        llm_client: Optional LLM client instance (Anthropic, OpenAI, etc.)
        llm_method_path: Path to the LLM client method to patch (default: "messages.create")
        log_file: Path to the output log file
        debug_level: Logging level for SDK's internal debug logs (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Set up logging configuration for the monitor
    monitor_logger = logging.getLogger("CylestioMonitor")

    # Set the logging level based on the debug_level parameter
    level = getattr(logging, debug_level.upper(), logging.INFO)
    monitor_logger.setLevel(level)

    # Remove any existing handlers to avoid duplicate logs
    for handler in monitor_logger.handlers[:]:
        monitor_logger.removeHandler(handler)

    # Add a file handler for JSON logs
    json_handler = logging.FileHandler(log_file)
    json_handler.setLevel(logging.INFO)

    # Create a JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            try:
                data = json.loads(record.msg)
            except Exception:
                data = {"message": record.msg}
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "channel": getattr(record, "channel", "SYSTEM"),
            }
            log_entry.update(data)
            return json.dumps(log_entry)

    json_formatter = JSONFormatter()
    json_handler.setFormatter(json_formatter)
    monitor_logger.addHandler(json_handler)

    # Add a console handler for debug logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter("CylestioSDK - %(levelname)s: %(message)s"))
    monitor_logger.addHandler(console_handler)

    # Log the debug level
    monitor_logger.debug(f"Cylestio Monitor SDK initialized with debug level: {debug_level}")

    # Patch MCP if available
    try:
        from mcp import ClientSession

        # Patch ClientSession.call_tool method
        original_call_tool = ClientSession.call_tool
        ClientSession.call_tool = monitor_call(original_call_tool, "MCP")

        # Log the patch
        log_event("MCP_patch", {"message": "MCP client patched"}, "SYSTEM")

    except ImportError:
        # MCP not available, skip patching
        monitor_logger.debug("MCP module not available, skipping ClientSession patching")

    # If an LLM client was provided, patch it
    llm_provider = "Unknown"
    if llm_client:
        # Extract the provider name if possible
        if hasattr(llm_client, "__class__"):
            llm_provider = f"{llm_client.__class__.__module__}/{llm_client.__class__.__name__}"
            if hasattr(llm_client, "_client") and hasattr(llm_client._client, "user_agent"):
                llm_provider = llm_client._client.user_agent

        # Patch the LLM client
        parts = llm_method_path.split(".")
        target = llm_client
        for part in parts[:-1]:
            target = getattr(target, part)
        method_name = parts[-1]
        original_method = getattr(target, method_name)

        # Apply the appropriate monitor decorator
        patched_method = monitor_llm_call(original_method, "LLM")
        setattr(target, method_name, patched_method)

        # Log the patch
        log_event("LLM_patch", {"method": llm_method_path, "provider": llm_provider}, "SYSTEM")

    # Log that monitoring is enabled
    log_event(
        "monitoring_enabled", {"MCP_server_id": logger_id, "LLM_provider": llm_provider}, "SYSTEM"
    )


def disable_monitoring():
    """Disable monitoring and clean up resources."""
    # Flush all handlers
    logging.shutdown()

    # Log that monitoring is disabled
    log_event("monitoring_disabled", {"timestamp": datetime.now().isoformat()}, "SYSTEM")
