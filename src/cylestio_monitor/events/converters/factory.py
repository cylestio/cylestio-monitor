"""
Factory for creating event converters based on channel.

This module provides a factory pattern implementation for selecting and using
the appropriate event converter based on the event's channel.
"""

from typing import Any, Dict, Optional, Type

from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class EventConverterFactory:
    """
    Factory for creating event converters based on channel.
    
    This class manages the registration and retrieval of event converters
    for different channels, ensuring the appropriate converter is used
    for each event type.
    """
    
    def __init__(self):
        """Initialize with an empty converter registry."""
        self._converters = {}
        self._default_converter = None
        
    def register_converter(self, channel: str, converter: BaseEventConverter) -> None:
        """
        Register a converter for a specific channel.
        
        Args:
            channel: The channel identifier (e.g., "LANGCHAIN", "LANGGRAPH")
            converter: The converter instance
        """
        self._converters[channel.upper()] = converter
        
    def register_default_converter(self, converter: BaseEventConverter) -> None:
        """
        Register a default converter to use when no specific converter is found.
        
        Args:
            converter: The default converter instance
        """
        self._default_converter = converter
        
    def get_converter(self, channel: str) -> BaseEventConverter:
        """
        Get the appropriate converter for a channel.
        
        Args:
            channel: The channel identifier
            
        Returns:
            The converter for the channel or the default converter
            
        Raises:
            ValueError: If no converter is found and no default is registered
        """
        converter = self._converters.get(channel.upper())
        
        if converter is None:
            if self._default_converter is None:
                raise ValueError(f"No converter found for channel '{channel}' and no default converter registered")
            return self._default_converter
            
        return converter
        
    def convert_event(self, event: Dict[str, Any]) -> StandardizedEvent:
        """
        Convert an event using the appropriate converter.
        
        Args:
            event: The event to convert
            
        Returns:
            The standardized event
            
        Raises:
            ValueError: If no converter is found and no default is registered
        """
        channel = event.get("channel", "SYSTEM").upper()
        converter = self.get_converter(channel)
        return converter.convert(event) 