"""Test event context management functionality."""

import unittest
import threading
import socket
import platform
import os
from typing import Dict, Any

from cylestio_monitor.utils.event_context import (
    get_context,
    set_context,
    set_global_context,
    clear_context,
    set_session_id,
    get_session_id,
    enrich_event_with_context,
    ContextManager,
    _global_context
)


class TestEventContext(unittest.TestCase):
    """Test case for event context module."""
    
    def setUp(self):
        """Set up test fixture."""
        clear_context()  # Ensure clean context for each test
        
    def tearDown(self):
        """Tear down test fixture."""
        clear_context()  # Clean up after tests
    
    def test_global_context_has_system_info(self):
        """Test that global context contains system information."""
        self.assertIn("host.name", _global_context)
        self.assertEqual(_global_context["host.name"], socket.gethostname())
        
        self.assertIn("os.type", _global_context)
        self.assertEqual(_global_context["os.type"], platform.system())
        
        self.assertIn("process.id", _global_context)
        self.assertEqual(_global_context["process.id"], os.getpid())
    
    def test_set_and_get_context(self):
        """Test setting and getting context values."""
        # Set context value
        set_context("test.key", "test_value")
        
        # Get context and verify value exists
        context = get_context()
        self.assertIn("test.key", context)
        self.assertEqual(context["test.key"], "test_value")
    
    def test_set_global_context(self):
        """Test setting global context values."""
        # Set global context value
        original_value = _global_context.get("test.global.key", None)
        set_global_context("test.global.key", "global_value")
        
        # Get context and verify global value exists
        context = get_context()
        self.assertIn("test.global.key", context)
        self.assertEqual(context["test.global.key"], "global_value")
        
        # Clean up
        if original_value is not None:
            _global_context["test.global.key"] = original_value
        else:
            del _global_context["test.global.key"]
    
    def test_thread_local_context(self):
        """Test that context is thread-local."""
        # Set context in main thread
        set_context("thread.key", "main_thread")
        
        # Value to be set by thread
        thread_value = [None]
        
        def thread_func():
            set_context("thread.key", "worker_thread")
            thread_value[0] = get_context().get("thread.key")
        
        # Run thread
        thread = threading.Thread(target=thread_func)
        thread.start()
        thread.join()
        
        # Verify thread had its own context
        self.assertEqual(thread_value[0], "worker_thread")
        self.assertEqual(get_context().get("thread.key"), "main_thread")
    
    def test_session_id(self):
        """Test session ID functionality."""
        # Test default session ID is set
        session_id = get_session_id()
        self.assertIsNotNone(session_id)
        
        # Test setting custom session ID
        custom_id = "custom-session-123"
        set_session_id(custom_id)
        self.assertEqual(get_session_id(), custom_id)
    
    def test_enrich_event_with_context(self):
        """Test enriching events with context data."""
        # Set up context
        set_context("user.id", "test-user")
        set_context("request.id", "test-request")
        
        # Create event
        event = {
            "name": "test.event",
            "attributes": {
                "custom.attr": "value"
            }
        }
        
        # Enrich event
        enriched = enrich_event_with_context(event)
        
        # Verify context data was added
        self.assertIn("user.id", enriched["attributes"])
        self.assertEqual(enriched["attributes"]["user.id"], "test-user")
        self.assertIn("request.id", enriched["attributes"])
        self.assertEqual(enriched["attributes"]["request.id"], "test-request")
        
        # Verify original attributes remain
        self.assertIn("custom.attr", enriched["attributes"])
        self.assertEqual(enriched["attributes"]["custom.attr"], "value")
    
    def test_enrich_event_with_no_attributes(self):
        """Test enriching events that have no attributes."""
        # Set up context
        set_context("user.id", "test-user")
        
        # Create event with no attributes
        event = {
            "name": "test.event",
        }
        
        # Enrich event
        enriched = enrich_event_with_context(event)
        
        # Verify attributes were created and context added
        self.assertIn("attributes", enriched)
        self.assertIn("user.id", enriched["attributes"])
        self.assertEqual(enriched["attributes"]["user.id"], "test-user")
    
    def test_context_manager(self):
        """Test context manager functionality."""
        # Set initial context
        set_context("user.id", "initial-user")
        
        # Use context manager to temporarily set values
        with ContextManager(user_id="temp-user", request_id="temp-request"):
            context = get_context()
            self.assertEqual(context.get("user_id"), "temp-user")
            self.assertEqual(context.get("request_id"), "temp-request")
            self.assertEqual(context.get("user.id"), "initial-user")  # Original value preserved
        
        # Verify context is restored after context manager exits
        context = get_context()
        self.assertEqual(context.get("user.id"), "initial-user")
        self.assertNotIn("user_id", context)
        self.assertNotIn("request_id", context)
    
    def test_clear_context(self):
        """Test clearing context."""
        # Set context
        set_context("user.id", "test-user")
        set_context("request.id", "test-request")
        
        # Verify context contains set values
        context = get_context()
        self.assertIn("user.id", context)
        self.assertIn("request.id", context)
        
        # Clear context
        clear_context()
        
        # Verify context values are cleared (except session.id)
        context = get_context()
        self.assertNotIn("user.id", context)
        self.assertNotIn("request.id", context)
        self.assertIn("session.id", context)  # Session ID is preserved


if __name__ == "__main__":
    unittest.main() 