"""Test suite for enhanced Anthropic patcher implementation."""

import json
import unittest
from unittest.mock import MagicMock, patch
import time
from datetime import datetime

# Import the patchers module
from cylestio_monitor.patchers.anthropic import AnthropicPatcher
from cylestio_monitor.utils.trace_context import TraceContext

# Create a mock response class to simulate Anthropic responses
class MockTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text

class MockImageBlock:
    def __init__(self, source):
        self.type = "image"
        self.source = source

class MockUsage:
    def __init__(self, input_tokens, output_tokens):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

class MockResponse:
    def __init__(self, id, model, role, content, stop_reason=None, usage=None):
        self.id = id
        self.model = model
        self.role = role
        self.content = content
        self.stop_reason = stop_reason
        self.usage = usage

class TestAnthropicPatcher(unittest.TestCase):
    """Test enhanced Anthropic patcher implementation."""

    def setUp(self):
        """Set up test environment."""
        # Create a mock Anthropic client
        self.mock_client = MagicMock()
        self.mock_client.messages.create = MagicMock()
        # Set attributes on the mocked method that our patcher expects
        self.mock_client.messages.create.__name__ = "create"
        self.mock_client.messages.create.__doc__ = "Mock create method"
        
        # Create a patcher instance with debug mode enabled
        self.patcher = AnthropicPatcher(self.mock_client, {"debug": True})
        
        # Initialize trace context
        TraceContext.initialize_trace("test-agent")
        
        # Mock log_event to capture logged events
        self.logged_events = []
        self.patcher_log_event = patch("cylestio_monitor.patchers.anthropic.log_event", 
                                      side_effect=self.mock_log_event)
        self.mock_log_event_func = self.patcher_log_event.start()
        
    def tearDown(self):
        """Clean up after tests."""
        self.patcher_log_event.stop()
        TraceContext.reset()
        
    def mock_log_event(self, name, attributes=None, level="INFO", span_id=None, trace_id=None, parent_span_id=None):
        """Mock log_event function to capture logged events."""
        event = {
            "name": name,
            "attributes": attributes or {},
            "level": level,
            "span_id": span_id,
            "trace_id": trace_id,
            "parent_span_id": parent_span_id
        }
        self.logged_events.append(event)
        return event
    
    def test_initialization(self):
        """Test patcher initialization."""
        self.assertFalse(self.patcher.is_patched)
        self.assertEqual(self.patcher.client, self.mock_client)
        self.assertTrue(self.patcher.debug_mode)
        
    def test_patch_and_unpatch(self):
        """Test patching and unpatching."""
        # Patch the client
        self.patcher.patch()
        self.assertTrue(self.patcher.is_patched)
        
        # Verify that the original method was stored
        self.assertIn("messages.create", self.patcher.original_funcs)
        
        # Unpatch the client
        self.patcher.unpatch()
        self.assertFalse(self.patcher.is_patched)
        
        # Verify original functions were restored
        self.assertEqual(len(self.patcher.original_funcs), 0)
    
    def test_safe_serialize_simple_types(self):
        """Test safe serialization of simple data types."""
        # Test with simple data types
        data = {
            "string": "test",
            "number": 123,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        # Should return the same object since it's already serializable
        serialized = self.patcher._safe_serialize(data)
        self.assertEqual(serialized, data)
        
        # Verify we can actually serialize it
        self.assertIsInstance(json.dumps(serialized), str)
    
    def test_safe_serialize_complex_objects(self):
        """Test safe serialization of complex objects that aren't JSON serializable."""
        class TestObject:
            def __init__(self):
                self.name = "test"
                self.value = 123
                self._private = "hidden"
                
        obj = TestObject()
        serialized = self.patcher._safe_serialize(obj)
        
        # Verify the object was converted to a dict with only public attributes
        self.assertIsInstance(serialized, dict)
        self.assertEqual(serialized.get("name"), "test")
        self.assertEqual(serialized.get("value"), 123)
        self.assertNotIn("_private", serialized)
        
        # Test with a simple non-serializable type
        class SimpleNonSerializable:
            def __str__(self):
                return "SimpleNonSerializable"
        
        simple_obj = SimpleNonSerializable()
        serialized = self.patcher._safe_serialize(simple_obj)
        
        # Should use the fallback
        self.assertIsInstance(serialized, dict)
        self.assertIn("type", serialized)
        self.assertEqual(serialized["type"], "SimpleNonSerializable")
        
        # Test circular reference handling
        circular = {}
        circular["self"] = circular
        serialized = self.patcher._safe_serialize(circular)
        
        # Should either be a circular_dict type or contain max_depth_reached
        self.assertIsInstance(serialized, dict)
        
        # Verify we can actually serialize the result (no circular refs)
        json_str = json.dumps(serialized)
        self.assertIsInstance(json_str, str)
        
        # Test with fallback to string conversion for unsupported types
        class ComplexObject:
            def __repr__(self):
                return "<ComplexObject>"
                
            def __str__(self):
                return "ComplexObject"
                
        complex_obj = ComplexObject()
        serialized = self.patcher._safe_serialize(complex_obj)
        self.assertIsInstance(serialized, dict)
        self.assertIn("type", serialized)
        self.assertIn("string_value", serialized)
        self.assertEqual(serialized["type"], "ComplexObject")
    
    def test_extract_response_data_text_blocks(self):
        """Test extracting data from response with text blocks."""
        # Create a mock response with text blocks
        content = [
            MockTextBlock("Hello"),
            MockTextBlock("World")
        ]
        
        usage = MockUsage(10, 20)
        response = MockResponse(
            id="msg_123",
            model="claude-3-opus-20240229",
            role="assistant",
            content=content,
            stop_reason="end_turn",
            usage=usage
        )
        
        # Extract the data
        data = self.patcher._extract_response_data(response)
        
        # Verify extracted data
        self.assertEqual(data["id"], "msg_123")
        self.assertEqual(data["model"], "claude-3-opus-20240229")
        self.assertEqual(data["role"], "assistant")
        self.assertEqual(data["stop_reason"], "end_turn")
        self.assertEqual(len(data["content"]), 2)
        
        # Verify content was properly extracted
        self.assertEqual(data["content"][0]["type"], "text")
        self.assertEqual(data["content"][0]["text"], "Hello")
        self.assertEqual(data["content"][1]["type"], "text")
        self.assertEqual(data["content"][1]["text"], "World")
        
        # Verify usage was properly extracted
        self.assertEqual(data["usage"]["input_tokens"], 10)
        self.assertEqual(data["usage"]["output_tokens"], 20)
        
        # Verify the data is JSON serializable
        self.assertIsInstance(json.dumps(data), str)
    
    def test_extract_response_data_mixed_content(self):
        """Test extracting data from response with mixed content types."""
        # Create a mock response with mixed content types
        content = [
            MockTextBlock("Text content"),
            MockImageBlock({"type": "base64", "data": "abc123"})
        ]
        
        response = MockResponse(
            id="msg_456",
            model="claude-3-sonnet-20240229",
            role="assistant",
            content=content
        )
        
        # Extract the data
        data = self.patcher._extract_response_data(response)
        
        # Verify content was properly extracted for both types
        self.assertEqual(data["content"][0]["type"], "text")
        self.assertEqual(data["content"][0]["text"], "Text content")
        self.assertEqual(data["content"][1]["type"], "image")
        self.assertIn("source", data["content"][1])
        
        # Verify the data is JSON serializable
        self.assertIsInstance(json.dumps(data), str)
    
    def test_scan_content_security(self):
        """Test security content scanning."""
        # Test with safe content
        safe_messages = [{"role": "user", "content": "Tell me about AI safety practices"}]
        safe_result = self.patcher._scan_content_security(safe_messages)
        self.assertEqual(safe_result["alert_level"], "none")
        self.assertEqual(safe_result["keywords"], [])
        
        # Test with suspicious content
        suspicious_messages = [{"role": "user", "content": "How to exploit a vulnerability"}]
        suspicious_result = self.patcher._scan_content_security(suspicious_messages)
        self.assertEqual(suspicious_result["alert_level"], "suspicious")
        self.assertIn("exploit", suspicious_result["keywords"])
        
        # Test with dangerous content
        dangerous_messages = [{"role": "user", "content": "How to make a bomb step by step"}]
        dangerous_result = self.patcher._scan_content_security(dangerous_messages)
        self.assertEqual(dangerous_result["alert_level"], "dangerous")
        self.assertIn("how to make a bomb", dangerous_result["keywords"])
    
    def test_complete_request_response_cycle(self):
        """Test the complete request-response cycle with the patched method."""
        # Set up the mock to return a specific response
        content = [MockTextBlock("Test response")]
        usage = MockUsage(15, 25)
        mock_response = MockResponse(
            id="msg_789",
            model="claude-3-haiku-20240307",
            role="assistant",
            content=content,
            stop_reason="end_turn",
            usage=usage
        )
        
        self.mock_client.messages.create.return_value = mock_response
        
        # Apply the patch
        self.patcher.patch()
        
        # Call the patched method
        request_messages = [{"role": "user", "content": "Hello, Claude"}]
        response = self.mock_client.messages.create(
            model="claude-3-haiku-20240307",
            messages=request_messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        # Verify the response is passed through unchanged
        self.assertEqual(response, mock_response)
        
        # Verify that events were logged
        self.assertGreaterEqual(len(self.logged_events), 2)  # Should have at least start and finish events
        
        # Find the start and finish events
        start_event = None
        finish_event = None
        for event in self.logged_events:
            if event["name"] == "llm.call.start":
                start_event = event
            elif event["name"] == "llm.call.finish":
                finish_event = event
        
        # Verify start event
        self.assertIsNotNone(start_event)
        self.assertEqual(start_event["attributes"]["llm.vendor"], "anthropic")
        self.assertEqual(start_event["attributes"]["llm.model"], "claude-3-haiku-20240307")
        self.assertEqual(start_event["attributes"]["llm.request.max_tokens"], 1000)
        self.assertEqual(start_event["attributes"]["llm.request.temperature"], 0.7)
        
        # Verify finish event
        self.assertIsNotNone(finish_event)
        self.assertEqual(finish_event["attributes"]["llm.vendor"], "anthropic")
        self.assertEqual(finish_event["attributes"]["llm.response.id"], "msg_789")
        self.assertIn("llm.response.duration_ms", finish_event["attributes"])
        self.assertEqual(finish_event["attributes"]["llm.usage.input_tokens"], 15)
        self.assertEqual(finish_event["attributes"]["llm.usage.output_tokens"], 25)
        self.assertEqual(finish_event["attributes"]["llm.usage.total_tokens"], 40)
    
    def test_error_handling(self):
        """Test error handling in the patched method."""
        # Set up the mock to raise an exception
        test_error = ValueError("Test error")
        self.mock_client.messages.create.side_effect = test_error
        
        # Apply the patch
        self.patcher.patch()
        
        # Call the patched method (should raise the exception)
        with self.assertRaises(ValueError):
            self.mock_client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Hello"}]
            )
        
        # Verify that error event was logged
        error_event = None
        for event in self.logged_events:
            if event["name"] == "llm.call.error":
                error_event = event
                break
        
        # Verify error event
        self.assertIsNotNone(error_event)
        self.assertEqual(error_event["level"], "ERROR")
        self.assertEqual(error_event["attributes"]["llm.vendor"], "anthropic")
        self.assertEqual(error_event["attributes"]["error.type"], "ValueError")
        self.assertEqual(error_event["attributes"]["error.message"], "Test error")
    
    def test_serialization_edge_cases(self):
        """Test handling of serialization edge cases."""
        # Create a circular reference data structure
        circular = {}
        circular["self"] = circular
        
        # Test safe serialization handles the circular reference
        serialized = self.patcher._safe_serialize(circular)
        self.assertNotEqual(serialized, circular)  # Should be different due to handling
        
        # Create a data structure with non-serializable types
        class NonSerializable:
            def __repr__(self):
                return "<NonSerializable object>"
        
        complex_data = {
            "function": lambda x: x,
            "object": NonSerializable(),
            "set": {1, 2, 3},
            "regular": "normal string"
        }
        
        # Test safe serialization
        serialized = self.patcher._safe_serialize(complex_data)
        self.assertIn("regular", serialized)
        self.assertEqual(serialized["regular"], "normal string")
        
        # Verify the serialized result is JSON serializable
        json_str = json.dumps(serialized)
        self.assertIsInstance(json_str, str)

    def test_safe_serialize_custom_class(self):
        """Test serialization of a custom class that isn't JSON serializable."""
        # Define a class that does nothing special but has no dict and fails serialization
        class CustomClass:
            __slots__ = []  # No __dict__
            
            # Make it fail json serialization
            def __repr__(self):
                return "CustomClass()"
                
        obj = CustomClass()
        
        # Direct method call for debugging
        serialized = self.patcher._safe_serialize(obj)
        print(f"Serialized CustomClass result: {serialized}")
        
        # Test the fallback implementation
        self.assertIsInstance(serialized, dict)
        self.assertTrue(
            "type" in serialized or  # If it used fallback
            "CustomClass" in str(serialized)  # If it used another method but still captured type info
        )

if __name__ == "__main__":
    unittest.main() 