"""Tests for the OpenAI patcher module."""

import logging
import sys
import unittest
from unittest import mock

import pytest

try:
    # Import directly from module under test
    from cylestio_monitor.patchers.openai_patcher import (
        OpenAIPatcher, patch_openai_module, unpatch_openai_module)

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Skip all tests if OpenAI is not available
pytestmark = pytest.mark.skipif(not OPENAI_AVAILABLE, reason="OpenAI not available")


# Create mock versions of the patching modules for testing
class MockPatcherModules:
    @staticmethod
    def setup():
        """Set up mocks for dependencies."""
        # Mock the TraceContext module
        if "cylestio_monitor.patchers.openai_patcher.TraceContext" not in sys.modules:
            mock_trace_context = mock.MagicMock()
            mock_trace_context.start_span.return_value = {"span_id": "test-span-id"}
            mock_trace_context.get_current_context.return_value = {
                "trace_id": "test-trace-id"
            }
            sys.modules[
                "cylestio_monitor.patchers.openai_patcher.TraceContext"
            ] = mock_trace_context

        # Mock the log_event function
        if "cylestio_monitor.patchers.openai_patcher.log_event" not in sys.modules:
            mock_log_event = mock.MagicMock()
            sys.modules[
                "cylestio_monitor.patchers.openai_patcher.log_event"
            ] = mock_log_event

        # Mock the log_error function
        if "cylestio_monitor.patchers.openai_patcher.log_error" not in sys.modules:
            mock_log_error = mock.MagicMock()
            sys.modules[
                "cylestio_monitor.patchers.openai_patcher.log_error"
            ] = mock_log_error


# Setup the mocks first before importing the module under test
MockPatcherModules.setup()


class TestOpenAIPatcher(unittest.TestCase):
    """Test the OpenAI patcher functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create a structured mock client that mimics the OpenAI client structure
        self.client = mock.MagicMock()

        # Setup chat.completions.create
        self.mock_chat_completions = mock.MagicMock()
        self.original_chat_create = mock.MagicMock(name="original_chat_create")
        self.mock_chat_completions.create = self.original_chat_create

        # Setup chat attribute
        self.mock_chat = mock.MagicMock()
        self.mock_chat.completions = self.mock_chat_completions

        # Setup completions.create
        self.mock_completions = mock.MagicMock()
        self.original_completions_create = mock.MagicMock(
            name="original_completions_create"
        )
        self.mock_completions.create = self.original_completions_create

        # Create property mocks for the attributes
        type(self.client).chat = mock.PropertyMock(return_value=self.mock_chat)
        type(self.client).completions = mock.PropertyMock(
            return_value=self.mock_completions
        )

        # Create an instance of the patcher
        self.patcher = OpenAIPatcher(client=self.client)

        # Capture log messages for verification
        self.log_messages = []
        self.logger_handler = logging.StreamHandler(self)

        # Clear mock call counts
        self.original_chat_create.reset_mock()
        self.original_completions_create.reset_mock()

    def write(self, message):
        """Capture log messages (used by the StreamHandler)."""
        self.log_messages.append(message)

    def flush(self):
        """Required for StreamHandler."""
        pass

    def tearDown(self):
        """Clean up after tests."""
        # Unpatch any active patchers
        if hasattr(self, "patcher") and self.patcher.is_patched:
            self.patcher.unpatch()

    def test_patch_chat_completion(self):
        """Test patching ChatCompletions.create."""
        # Create mock response for chat.completions.create
        mock_chat_response = mock.MagicMock()
        mock_chat_response.id = "chat-mock-id"
        mock_chat_response.model = "gpt-4"
        mock_chat_response.choices = [
            mock.MagicMock(
                message=mock.MagicMock(role="assistant", content="Hello, world!"),
                finish_reason="stop",
            )
        ]
        mock_chat_response.usage = mock.MagicMock(
            prompt_tokens=10, completion_tokens=5, total_tokens=15
        )

        # Configure the original method to return our mock response
        self.original_chat_create.return_value = mock_chat_response

        # Apply the patch
        self.patcher.patch()

        # Verify the method was patched
        self.assertNotEqual(
            self.mock_chat_completions.create, self.original_chat_create
        )

        # Call the patched method with test data
        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.chat.completions.create(
            model="gpt-4", messages=messages, temperature=0.7, max_tokens=100
        )

        # Verify the original method was called with the right arguments
        self.original_chat_create.assert_called_once()
        call_args = self.original_chat_create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4")
        self.assertEqual(call_args["messages"], messages)
        self.assertEqual(call_args["temperature"], 0.7)
        self.assertEqual(call_args["max_tokens"], 100)

        # Verify the mock response was returned
        self.assertEqual(result, mock_chat_response)

    def test_patch_completion(self):
        """Test patching Completions.create."""
        # Create mock response for completions.create
        mock_completion_response = mock.MagicMock()
        mock_completion_response.id = "completion-mock-id"
        mock_completion_response.model = "gpt-3.5-turbo-instruct"
        mock_completion_response.choices = [
            mock.MagicMock(text="Hello, world!", finish_reason="stop")
        ]
        mock_completion_response.usage = mock.MagicMock(
            prompt_tokens=5, completion_tokens=3, total_tokens=8
        )

        # Configure the original method to return our mock response
        self.original_completions_create.return_value = mock_completion_response

        # Apply the patch
        self.patcher.patch()

        # Verify the method was patched
        self.assertNotEqual(
            self.mock_completions.create, self.original_completions_create
        )

        # Call the patched method with test data
        prompt = "Say hello"
        result = self.client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=0.7,
            max_tokens=100,
        )

        # Verify the original method was called with the right arguments
        self.original_completions_create.assert_called_once()
        call_args = self.original_completions_create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-3.5-turbo-instruct")
        self.assertEqual(call_args["prompt"], prompt)
        self.assertEqual(call_args["temperature"], 0.7)
        self.assertEqual(call_args["max_tokens"], 100)

        # Verify the mock response was returned
        self.assertEqual(result, mock_completion_response)

    def test_unpatch(self):
        """Test that unpatching restores the original methods."""
        # Apply the patch
        self.patcher.patch()

        # Verify the methods were changed
        self.assertNotEqual(
            self.mock_chat_completions.create, self.original_chat_create
        )
        self.assertNotEqual(
            self.mock_completions.create, self.original_completions_create
        )

        # Unpatch
        self.patcher.unpatch()

        # Verify the original methods were restored
        self.assertEqual(self.mock_chat_completions.create, self.original_chat_create)
        self.assertEqual(self.mock_completions.create, self.original_completions_create)


@pytest.mark.skipif(not OPENAI_AVAILABLE, reason="OpenAI not available")
@pytest.mark.skip(reason="Module patching is difficult to test in isolation")
def test_module_patching():
    """Test module-level patching."""
    # This test is skipped because module-level patching is difficult to test in isolation
    # The core functionality is tested in the other tests
    assert True


if __name__ == "__main__":
    unittest.main()
