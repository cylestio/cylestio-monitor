"""Cylestio Monitor core module.

This module provides a framework-agnostic monitoring solution for AI agents.
It supports monitoring of MCP, LLM API calls, LangChain, and LangGraph.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Union
from pathlib import Path

import platformdirs

from .config import ConfigManager
from .api_client import get_api_client, ApiClient
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
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Enable monitoring for AI agents across various frameworks.
    
    Args:
        agent_id: Unique identifier for the agent
        llm_client: Optional LLM client instance (Anthropic, OpenAI, etc.)
                    Note: This parameter is maintained for backward compatibility but
                    is no longer required for Anthropic clients.
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
    console_handler.setFormatter(logging.Formatter("CylestioSDK - %(levelname)s: %(message)s"))
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
            logger.warning("API endpoint not configured. Events will only be logged to file.")
    
    # Initialize the event processor
    event_processor = EventProcessor(agent_id=agent_id, config=config)
    
    # Get LLM provider info (will be updated by patchers when detected)
    llm_provider = "Unknown"
    
    # Check if framework patching is enabled (default to True)
    enable_framework_patching = config.get("enable_framework_patching", True)
    
    # Special case for weather-agent: disable framework patching
    if agent_id == "weather-agent":
        enable_framework_patching = False
        logger.info(f"Framework patching disabled for agent: {agent_id}")
    
    try:
        # Step 1: Patch MCP if available and enabled
        try:
            # Try patching using ClientSession approach first (working method from main branch)
            from mcp import ClientSession
            
            # Patch ClientSession.call_tool method
            original_call_tool = ClientSession.call_tool
            ClientSession.call_tool = monitor_call(original_call_tool, "MCP")
            
            # Log the patch
            logger.info("MCP patched for monitoring")
            monitor_logger.info("MCP integration enabled")
            
        except ImportError:
            # MCP not installed or available
            pass
            
        # Step 2: Apply global module patching for Anthropic (new approach)
        try:
            # Import patcher module and apply global patch
            from .patchers.anthropic import patch_anthropic_module
            patch_anthropic_module()
            llm_provider = "Anthropic (Auto-detected)"
            logger.info("Anthropic module patched for global monitoring")
            monitor_logger.info("Anthropic integration enabled (global module patching)")
        except ImportError:
            logger.debug("Anthropic module not available for global patching")
        except Exception as e:
            logger.warning(f"Failed to apply global Anthropic patches: {e}")
            
        # Step 3: For backward compatibility, patch explicit llm_client if provided
        if llm_client:
            # Attempt to determine the provider
            provider_name = llm_client.__class__.__name__
            module_name = llm_client.__class__.__module__.split('.')[0].lower()
            
            if "anthropic" in module_name or "claude" in provider_name.lower():
                llm_provider = "Anthropic"
                # Log LLM client info
                logger.info(f"LLM client detected: {llm_provider}")
                
                # Import and apply Anthropic patcher explicitly
                try:
                    # Import only the necessary patcher
                    from .patchers.anthropic import AnthropicPatcher
                    
                    # Create and apply the patcher
                    patcher = AnthropicPatcher(client=llm_client)
                    logger.debug("Created AnthropicPatcher instance")
                    
                    # Apply the patch
                    patcher.patch()
                    logger.debug("Applied AnthropicPatcher.patch()")
                    
                    # Log success
                    logger.info("Anthropic client patched for monitoring")
                except Exception as e:
                    logger.error(f"Failed to patch Anthropic client: {e}")
                
                monitor_logger.info(f"Monitoring enabled for {llm_provider}")
                
            elif "openai" in module_name:
                llm_provider = "OpenAI"
                # Log LLM client info
                logger.info(f"LLM client detected: {llm_provider}")
                monitor_logger.info(f"Monitoring enabled for {llm_provider}")
        
        # Step 4: Try to patch framework libraries if enabled
        if enable_framework_patching:
            # Try to patch LangChain if present
            try:
                import langchain
                
                # Only import the LangChain patcher if LangChain is available
                try:
                    from .patchers.langchain_patcher import patch_langchain
                    
                    # Create event processor for LangChain
                    langchain_processor = EventProcessor(agent_id=agent_id, config=config)
                    
                    # Apply patches
                    patch_langchain(langchain_processor)
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
                    
                    # Apply patches
                    patch_langgraph()
                    logger.info("LangGraph patched for monitoring")
                    monitor_logger.info("LangGraph integration enabled")
                except Exception as e:
                    logger.error(f"Failed to patch LangGraph: {e}")
                    
            except ImportError:
                # LangGraph not installed or available
                pass
        else:
            logger.info("Framework patching is disabled. Skipping LangChain and LangGraph patching.")
            
    except Exception as e:
        logger.error(f"Error during monitoring setup: {e}")
        monitor_logger.error(f"Error during monitoring setup: {e}")
        
    # Log successful initialization
    logger.info(f"Cylestio monitoring enabled for agent: {agent_id}")
    monitor_logger.info(f"Monitoring initialized for agent: {agent_id}")
    
    # Log the initialization event
    process_and_log_event(
        agent_id=agent_id,
        event_type="monitor_init",
        data={
            "timestamp": datetime.now().isoformat(),
            "api_endpoint": os.environ.get("CYLESTIO_API_ENDPOINT", "Not configured"),
            "log_file": log_file,
            "llm_provider": llm_provider
        },
        channel="SYSTEM"
    )


def disable_monitoring() -> None:
    """
    Disable all monitoring and clean up resources.
    
    This will restore any patched functions to their original state.
    """
    logger.info("Disabling Cylestio monitoring")
    
    # Get agent_id from configuration
    config_manager = ConfigManager()
    agent_id = config_manager.get("monitoring.agent_id")
    
    # Log the monitoring finish event before unpatching everything
    if agent_id:
        process_and_log_event(
            agent_id=agent_id,
            event_type="monitor_finish",
            data={
                "timestamp": datetime.now().isoformat(),
            },
            channel="SYSTEM"
        )
    
    # Try to unpatch module-level patches
    try:
        # Unpatch Anthropic module
        from .patchers.anthropic import unpatch_anthropic_module
        unpatch_anthropic_module()
        logger.info("Anthropic module unpatched")
    except ImportError:
        logger.debug("Anthropic module not available for unpatching")
    except Exception as e:
        logger.warning(f"Failed to unpatch Anthropic module: {e}")
    
    # Try to unpatch LangChain if it was patched
    try:
        # Import only if LangChain is available
        import langchain
        
        try:
            from .patchers.langchain_patcher import unpatch_langchain
            unpatch_langchain()
            logger.info("LangChain unpatched")
        except Exception as e:
            logger.warning(f"Error unpatching LangChain: {e}")
            
    except ImportError:
        # LangChain not installed
        pass
    
    # Try to unpatch LangGraph if it was patched
    try:
        # Import only if LangGraph is available
        import langgraph
        
        try:
            from .patchers.langgraph_patcher import unpatch_langgraph
            unpatch_langgraph()
            logger.info("LangGraph unpatched")
        except Exception as e:
            logger.warning(f"Error unpatching LangGraph: {e}")
            
    except ImportError:
        # LangGraph not installed
        pass
    
    # Log the cleanup
    logger.info("Cylestio monitoring disabled")


def get_api_endpoint() -> str:
    """
    Get the API endpoint URL.
    
    Returns:
        str: API endpoint URL
    """
    api_client = get_api_client()
    return api_client.endpoint or "Not configured"


def log_to_file_and_api(
    event_type: str,
    data: Dict[str, Any],
    agent_id: Optional[str] = None,
    log_file: Optional[str] = None,
    channel: str = "APPLICATION",
    level: str = "info",
    direction: Optional[str] = None
) -> None:
    """
    Log an event to file and API.
    
    Args:
        event_type: Event type
        data: Event data
        agent_id: Agent ID (optional, uses configured agent_id if not provided)
        log_file: Path to log file (optional, uses configured log_file if not provided)
        channel: Event channel
        level: Log level
        direction: Event direction
    """
    # Get agent_id from configuration if not provided
    if agent_id is None:
        config_manager = ConfigManager()
        agent_id = config_manager.get("monitoring.agent_id")
        if not agent_id:
            logger.error("No agent_id provided and none found in configuration")
            return
    
    # Log the event
    process_and_log_event(
        agent_id=agent_id,
        event_type=event_type,
        data=data,
        channel=channel,
        level=level
    )

__all__ = ["enable_monitoring", "disable_monitoring", "log_to_file_and_api", "get_api_endpoint"]
