"""Cylestio Monitor core module.

This module provides a framework-agnostic monitoring solution for AI agents.
It supports monitoring of MCP, LLM API calls, LangChain, and LangGraph.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Union

import platformdirs

from .config import ConfigManager
from .db import utils as db_utils
from .event_logger import log_console_message, process_and_log_event
from .events_listener import monitor_call, monitor_llm_call
from .events_processor import log_event, EventProcessor

# Configure root logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def enable_monitoring(
    agent_id: str,
    llm_client: Any = None,
    log_file: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Enable monitoring for AI agents across various frameworks.
    
    Args:
        agent_id: Unique identifier for the agent
        llm_client: Optional LLM client instance (Anthropic, OpenAI, etc.)
        log_file: Path to the output log file (if None, only SQLite logging is used)
            - If a directory is provided, a file named "{agent_id}_monitoring_{timestamp}.json" will be created
            - If a file without extension is provided, ".json" will be added
        config: Optional configuration dictionary that can include:
            - debug_level: Logging level for SDK's internal logs (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Note:
        The SDK automatically detects which frameworks are installed and available to monitor.
        No explicit configuration is needed to enable monitoring for specific frameworks.
    """
    config = config or {}
    
    # Extract debug level from config
    debug_level = config.get("debug_level", "INFO")
    
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
    console_handler.setFormatter(logging.Formatter("CylestioSDK - %(levelname)s: %(message)s"))
    monitor_logger.addHandler(console_handler)
    
    # Store the agent ID and log file in the configuration
    config_manager = ConfigManager()
    config_manager.set("monitoring.agent_id", agent_id)
    config_manager.set("monitoring.log_file", log_file)
    config_manager.save()
    
    # Initialize the event processor
    event_processor = EventProcessor(agent_id=agent_id, config=config)
    
    # Get LLM provider info (will be updated by patchers when detected)
    llm_provider = "Unknown"
    
    # Get database path
    db_path = db_utils.get_db_path()
    
    try:
        # Step 1: Patch MCP if available and enabled
        try:
            # Try patching using ClientSession approach first (working method from main branch)
            from mcp import ClientSession
            
            # Patch ClientSession.call_tool method
            original_call_tool = ClientSession.call_tool
            ClientSession.call_tool = monitor_call(original_call_tool, "MCP")
            
            # Log the patch
            log_event("MCP_patch", {"message": "MCP client patched"}, "SYSTEM")
            
            logger.info("MCP monitoring enabled")
            if llm_provider == "Unknown":
                llm_provider = "MCP"
        except ImportError:
            # MCP not available, skip patching
            logger.debug("MCP module not available, skipping ClientSession patching")
        except Exception as e:
            # Log the error but continue with other monitoring
            logger.error(f"Failed to enable MCP monitoring: {e}")
        
        # Step 2: Add LangChain monitoring if available
        try:
            from .patchers.langchain_patcher import patch_langchain
            import langchain
            
            patch_langchain(event_processor)
            logger.info("LangChain monitoring enabled")
            
            if llm_provider == "Unknown":
                llm_provider = "LangChain"
        except ImportError:
            logger.debug("LangChain not installed, skipping monitoring")
        
        # Step 3: Add LangGraph monitoring if available
        try:
            from .patchers.langgraph_patcher import patch_langgraph
            import langgraph
            
            patch_langgraph(event_processor)
            logger.info("LangGraph monitoring enabled")
            
            if llm_provider == "Unknown":
                llm_provider = "LangGraph"
        except ImportError:
            logger.debug("LangGraph not installed, skipping monitoring")
            
        # Step 4: If an LLM client was provided directly, patch it (e.g., Anthropic)
        if llm_client:
            # Extract the provider name if possible
            if hasattr(llm_client, "__class__"):
                client_provider = f"{llm_client.__class__.__module__}/{llm_client.__class__.__name__}"
                llm_provider = client_provider
                if hasattr(llm_client, "_client") and hasattr(llm_client._client, "user_agent"):
                    llm_provider = llm_client._client.user_agent

            # Patch the LLM client
            # Default to messages.create method for most LLM clients
            llm_method_path = "messages.create"
            
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
            
        # Log monitoring enabled event
        monitoring_data = {
            "agent_id": agent_id,
            "LLM_provider": llm_provider,
            "database_path": db_path
        }
        
        # Log to both database and JSON file through the log_event function
        log_event("monitoring_enabled", monitoring_data, "SYSTEM", "info")
        
        logger.info(f"Monitoring enabled for agent {agent_id}")
        
    except Exception as e:
        logger.error(f"Failed to enable monitoring: {e}")
        raise


def disable_monitoring() -> None:
    """Disable all active monitoring."""
    # Get agent_id from configuration
    config_manager = ConfigManager()
    agent_id = config_manager.get("monitoring.agent_id")
    
    if agent_id:
        # Log monitoring disabled event
        monitoring_data = {"agent_id": agent_id, "timestamp": datetime.now().isoformat()}
        
        # Log to database and file through the log_event function
        log_event("monitoring_disabled", monitoring_data, "SYSTEM", "info")
    
    logger.info("Monitoring disabled")


def get_database_path() -> str:
    """
    Get the path to the global SQLite database.
    
    Returns:
        Path to the database file
    """
    return db_utils.get_db_path()


def cleanup_old_events(days: int = 30) -> int:
    """
    Delete events older than the specified number of days.
    
    Args:
        days: Number of days to keep
        
    Returns:
        Number of deleted events
    """
    return db_utils.cleanup_old_events(days)


def log_to_file_and_db(
    event_type: str,
    data: Dict[str, Any],
    agent_id: Optional[str] = None,
    log_file: Optional[str] = None,
    channel: str = "APPLICATION",
    level: str = "info",
    direction: Optional[str] = None
) -> None:
    """
    Log detailed application events to both the database and JSON file.
    
    Args:
        event_type: Type of event being logged
        data: Event data dictionary
        agent_id: Agent ID (defaults to configured agent_id)
        log_file: Path to JSON log file (defaults to configured log_file)
        channel: Event channel
        level: Log level (info, warning, error, debug)
        direction: Message direction for chat events ("incoming" or "outgoing")
    """
    # Get configuration if not provided
    config_manager = ConfigManager()
    agent_id = agent_id or config_manager.get("monitoring.agent_id")
    log_file = log_file or config_manager.get("monitoring.log_file")
    
    if not agent_id:
        logger.warning("No agent_id provided for logging. Event will not be logged.")
        return
    
    # Add agent_id to data if not present
    if "agent_id" not in data:
        data["agent_id"] = agent_id
    
    # Set log_file in config temporarily if provided
    if log_file:
        config_manager.set("monitoring.log_file", log_file)
    
    # Log to database and file through the log_event function
    try:
        log_event(event_type, data, channel, level, direction)
    except Exception as e:
        logger.error(f"Failed to log event: {e}")
    
    # Reset to original log_file if we temporarily changed it
    if log_file and log_file != config_manager.get("monitoring.log_file", None):
        config_manager.set("monitoring.log_file", config_manager.get("monitoring.log_file"))

__all__ = ["enable_monitoring", "disable_monitoring", "log_to_file_and_db", "get_database_path", "cleanup_old_events"]
