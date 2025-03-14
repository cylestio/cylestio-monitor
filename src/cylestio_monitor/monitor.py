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
        llm_method_path: Path to the LLM client method to patch (default: "messages.create")
        log_file: Path to the output log file (if None, only SQLite logging is used)
            - If a directory is provided, a file named "{agent_id}_monitoring_{timestamp}.json" will be created
            - If a file without extension is provided, ".json" will be added
        debug_level: Logging level for SDK's internal debug logs (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_langchain: Whether to enable LangChain monitoring
        enable_langgraph: Whether to enable LangGraph monitoring
        enable_mcp: Whether to enable MCP monitoring
        config: Optional configuration dictionary
    """
    config = config or {}
    
    # Set up logging configuration for the monitor
    monitor_logger = logging.getLogger("CylestioMonitor")

    # Set the logging level based on the debug_level parameter
    level = getattr(logging, debug_level.upper(), logging.INFO)
    monitor_logger.setLevel(level)

    # Remove any existing handlers to avoid duplicate logs
    for handler in monitor_logger.handlers[:]:
        monitor_logger.removeHandler(handler)

    # Store the agent ID and log file in the configuration
    config_manager = ConfigManager()
    config_manager.set("monitoring.agent_id", agent_id)
    config_manager.set("monitoring.log_file", log_file)
    config_manager.save()
    
    # Create JSON log file directory if needed
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
                    "agent_id": agent_id,
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
    
    # Initialize the event processor
    event_processor = EventProcessor(agent_id=agent_id, config=config)
    
    # Get LLM provider info (will be updated by patchers when detected)
    llm_provider = "Unknown"
    
    # Get database path
    db_path = db_utils.get_db_path()
    
    try:
        # Step 1: Patch MCP if available and enabled
        if enable_mcp:
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
        
        # Step 2: Add LangChain monitoring if enabled
        if enable_langchain:
            try:
                from .patchers.langchain_patcher import patch_langchain
                import langchain
                
                patch_langchain(event_processor)
                logger.info("LangChain monitoring enabled")
                
                if llm_provider == "Unknown":
                    llm_provider = "LangChain"
            except ImportError:
                logger.debug("LangChain not installed, skipping monitoring")
        
        # Step 3: Add LangGraph monitoring if enabled
        if enable_langgraph:
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
        
        # Log to both database and JSON file
        log_event("monitoring_enabled", monitoring_data, "SYSTEM", "info")
        
        # Also log to JSON file if specified
        if log_file:
            with open(log_file, "a") as f:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "level": "INFO",
                    "channel": "SYSTEM",
                    "agent_id": agent_id,
                    "event_type": "monitoring_enabled",
                    "data": monitoring_data
                }
                f.write(json.dumps(log_entry) + "\n")
        
        logger.info(f"Monitoring enabled for agent {agent_id}")
        
    except Exception as e:
        logger.error(f"Failed to enable monitoring: {e}")
        raise


def disable_monitoring() -> None:
    """Disable all active monitoring."""
    # Get agent_id from configuration
    config_manager = ConfigManager()
    agent_id = config_manager.get("monitoring.agent_id")
    log_file = config_manager.get("monitoring.log_file")
    
    if agent_id:
        # Log monitoring disabled event
        monitoring_data = {"agent_id": agent_id, "timestamp": datetime.now().isoformat()}
        
        # Log to database
        log_event("monitoring_disabled", monitoring_data, "SYSTEM", "info")
        
        # Also log to JSON file if specified
        if log_file:
            with open(log_file, "a") as f:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "level": "INFO",
                    "channel": "SYSTEM",
                    "agent_id": agent_id,
                    "event_type": "monitoring_disabled", 
                    "data": monitoring_data
                }
                f.write(json.dumps(log_entry) + "\n")
    
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
    
    # Log to database
    try:
        # Log to the database using the events_processor
        log_event(event_type, data, channel, level, direction)
    except Exception as e:
        logger.error(f"Failed to log event to database: {e}")
    
    # Log to JSON file if specified
    if log_file:
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
            
            # Create base record with required fields
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level.upper(),
                "agent_id": agent_id,
                "event_type": event_type,
                "channel": channel.upper(),
                "data": data
            }
            
            # Add direction if provided
            if direction:
                log_entry["direction"] = direction
                
            # Write to JSON file
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log event to file {log_file}: {e}")

__all__ = ["enable_monitoring", "disable_monitoring", "log_to_file_and_db"]
