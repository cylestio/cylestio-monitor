"""
Event converter registry.

This module provides a central registry for all event converters, initializing
them and making them available through a single factory instance.
"""

import logging
from cylestio_monitor.events.converters.factory import EventConverterFactory
from cylestio_monitor.events.converters.anthropic import AnthropicEventConverter
from cylestio_monitor.events.converters.default import DefaultEventConverter
from cylestio_monitor.events.converters.langchain import LangChainEventConverter
from cylestio_monitor.events.converters.mcp import MCPEventConverter

# Set up module-level logger
logger = logging.getLogger(__name__)

def create_converter_factory() -> EventConverterFactory:
    """
    Create and initialize the event converter factory with all available converters.
    
    Returns:
        EventConverterFactory: Initialized factory with all converters registered
    """
    factory = EventConverterFactory()
    
    # Register framework-specific converters
    factory.register_converter("LANGCHAIN", LangChainEventConverter())
    
    # Try to register LangGraph converter if available
    try:
        from cylestio_monitor.events.converters.langgraph import LangGraphEventConverter
        factory.register_converter("LANGGRAPH", LangGraphEventConverter())
        logger.debug("LangGraph event converter registered")
    except ImportError:
        logger.debug("LangGraph not available, skipping event converter registration")
    
    factory.register_converter("ANTHROPIC", AnthropicEventConverter())
    factory.register_converter("SYSTEM", MCPEventConverter())
    factory.register_converter("MCP", MCPEventConverter())
    
    # Register default converter
    factory.register_default_converter(DefaultEventConverter())
    
    return factory


# Create a global converter factory instance
converter_factory = create_converter_factory() 