#!/usr/bin/env python3
"""
Example demonstrating the enhanced data collection with the Anthropic patcher.
This script shows how to use the patched Anthropic client for comprehensive monitoring.

Usage:
  python anthropic_enhanced_monitoring.py
"""

import os
import json
import logging
from typing import Dict, Any, List
import time

# Setup logging for better visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a mock implementation for demonstration purposes
class MockTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text

class MockUsage:
    def __init__(self, input_tokens, output_tokens):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

class MockResponse:
    def __init__(self):
        self.id = "msg_mock123"
        self.model = "claude-3-mock-20240229"
        self.role = "assistant"
        self.content = [MockTextBlock("This is a mock response for demonstration purposes.")]
        self.stop_reason = "end_turn"
        self.usage = MockUsage(10, 25)

class MockMessages:
    def create(self, **kwargs):
        print(f"Mock anthropic.messages.create called with: {json.dumps(kwargs, indent=2)}")
        time.sleep(0.5)  # Simulate API call latency
        
        # Check for error simulation
        if 'invalid_parameter' in kwargs:
            raise ValueError("Mock error: Invalid parameter provided")
            
        return MockResponse()

class MockAnthropic:
    def __init__(self, api_key=None):
        self.api_key = api_key or "mock-api-key"
        self.messages = MockMessages()


# Import our patchers
from cylestio_monitor.patchers import AnthropicPatcher
from cylestio_monitor.utils.trace_context import TraceContext


# Create a custom event handler to capture logged events 
class EventCapture:
    """Class to capture and display logged events."""
    
    def __init__(self):
        self.events = []
        self.setup()
        
    def setup(self):
        """Setup event capture by monkey patching the log_event function."""
        # Import and monkey patch the log_event function
        from cylestio_monitor.utils import event_logging
        self.original_log_event = event_logging.log_event
        
        def patched_log_event(name, attributes=None, level="INFO", span_id=None, trace_id=None, parent_span_id=None):
            # Call original function but capture errors
            try:
                result = self.original_log_event(
                    name=name, 
                    attributes=attributes, 
                    level=level, 
                    span_id=span_id, 
                    trace_id=trace_id, 
                    parent_span_id=parent_span_id
                )
            except Exception as e:
                # Just create a simple dict if original function fails
                result = {
                    'name': name,
                    'attributes': attributes or {},
                    'level': level,
                    'span_id': span_id,
                    'trace_id': trace_id,
                    'parent_span_id': parent_span_id,
                    'error': str(e)
                }
            
            # Capture the event
            self.events.append(result)
            return result
            
        event_logging.log_event = patched_log_event
        
    def restore(self):
        """Restore original log_event function."""
        from cylestio_monitor.utils import event_logging
        event_logging.log_event = self.original_log_event
        
    def display_events(self):
        """Display captured events in a readable format."""
        print("\n===== CAPTURED EVENTS =====")
        if not self.events:
            print("No events were captured.")
            return
            
        for i, event in enumerate(self.events):
            print(f"\nEvent #{i+1}: {event.get('name', 'UNNAMED')} (Level: {event.get('level', 'UNKNOWN')})")
            if 'span_id' in event:
                print(f"  Span ID: {event['span_id']}")
            if 'trace_id' in event:
                print(f"  Trace ID: {event['trace_id']}")
            
            # Display attributes in a readable format
            attributes = event.get('attributes', {})
            if attributes:
                print("  Attributes:")
                for key, value in attributes.items():
                    # Truncate long values
                    str_value = str(value)
                    if len(str_value) > 100:
                        str_value = str_value[:100] + "..."
                    print(f"    {key}: {str_value}")
        
        print("\n===== END OF EVENTS =====\n")


def main():
    """Main function demonstrating the enhanced data collection."""
    # Disable API and file logging for this demo
    from cylestio_monitor import api_client
    api_client.send_event_to_api = lambda x: None
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Create a configuration file with mock settings
    from cylestio_monitor.config import ConfigManager
    config_manager = ConfigManager()
    
    # Remember original config values
    original_api_endpoint = config_manager.get("api_endpoint")
    original_log_file = config_manager.get("log_file")
    original_enable_file_logging = config_manager.get("enable_file_logging")
    original_enable_api_logging = config_manager.get("enable_api_logging")
    original_security_scan_content = config_manager.get("security.scan_content")
    original_blocked_keywords = config_manager.get("security.blocked_keywords")
    
    # Set temporary config values
    config_manager.set("api_endpoint", "http://localhost:8000/api/v1/telemetry/")
    config_manager.set("log_file", "output/chatbot_monitoring.json")
    config_manager.set("enable_file_logging", True)
    config_manager.set("enable_api_logging", False)  # Disable API logging for demo
    config_manager.set("security.scan_content", True)
    config_manager.set("security.blocked_keywords", ["exploit", "vulnerability", "hack"])
    
    # Initialize the event capture
    event_capture = EventCapture()
    
    # Initialize trace context
    TraceContext.initialize_trace("demo-agent")
    
    # Create mock Anthropic client
    client = MockAnthropic(api_key="this-is-a-mock-key")
    
    # Create and apply patcher with debug mode enabled
    patcher = AnthropicPatcher(client, {"debug": True})
    patcher.patch()
    
    print("\n🚀 Making API request with patched client...")
    
    try:
        # Make a normal request (mocked)
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": "Tell me a short joke about programming."}],
            max_tokens=300,
            temperature=0.7,
            top_p=0.95
        )
        
        print(f"\n✅ Response received: {response.id}")
        
        # Try with a potentially suspicious query
        print("\n⚠️ Making a request with potentially suspicious content...")
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": "What is a vulnerability exploit?"}],
            max_tokens=300,
            temperature=0.5
        )
        
        print(f"\n✅ Response received: {response.id}")
        
        # Simulate an error
        print("\n🔥 Simulating an error condition...")
        try:
            # Force a mocked error
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                messages=[{"role": "user", "content": "This should fail"}],
                invalid_parameter="this will cause an error"
            )
        except Exception as e:
            print(f"Caught expected error: {type(e).__name__}: {e}")
            pass  # The patcher should log the error
        
    finally:
        # Display all captured events
        event_capture.display_events()
        
        # Unpatch when done
        patcher.unpatch()
        event_capture.restore()
        
        # Restore original config values
        if original_api_endpoint is not None:
            config_manager.set("api_endpoint", original_api_endpoint)
        if original_log_file is not None:
            config_manager.set("log_file", original_log_file)
        if original_enable_file_logging is not None:
            config_manager.set("enable_file_logging", original_enable_file_logging)
        if original_enable_api_logging is not None:
            config_manager.set("enable_api_logging", original_enable_api_logging)
        if original_security_scan_content is not None:
            config_manager.set("security.scan_content", original_security_scan_content)
        if original_blocked_keywords is not None:
            config_manager.set("security.blocked_keywords", original_blocked_keywords)
        
        # Check the log file
        log_file = "output/chatbot_monitoring.json"
        if os.path.exists(log_file):
            print(f"\n📋 Checking content of log file: {log_file}")
            try:
                with open(log_file, 'r') as f:
                    log_contents = f.read()
                
                # Print first 500 characters to not overwhelm output
                if log_contents:
                    print(f"Log file contents (truncated): {log_contents[:500]}...")
                    if len(log_contents) > 500:
                        print(f"... ({len(log_contents)} bytes total)")
                else:
                    print("Log file is empty")
            except Exception as e:
                print(f"Error reading log file: {e}")


if __name__ == "__main__":
    main() 