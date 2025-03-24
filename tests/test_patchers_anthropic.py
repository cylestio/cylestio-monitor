"""Tests for the Anthropic patcher module."""

from unittest.mock import MagicMock, patch, ANY
import pytest

from cylestio_monitor.patchers.anthropic import (
    AnthropicPatcher, 
    patch_anthropic_module,
    unpatch_anthropic_module
)


class MockClient:
    """Mock Anthropic client for testing."""
    
    def __init__(self, api_key=None, base_url=None):
        """Initialize the mock client."""
        self.api_key = api_key or "dummy_key"
        self.base_url = base_url or "https://api.anthropic.com"
        self.messages = MagicMock()
        self.messages.create = self._create_message
        
    def _create_message(self, *args, **kwargs):
        """Mock message creation method."""
        return {
            "id": "msg_mock",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Hello, world!"}],
            "model": kwargs.get("model", "claude-3-opus-20240229"),
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5
            }
        }


@pytest.fixture
def mock_anthropic_module():
    """Create a mock Anthropic module."""
    module = MagicMock()
    module.Anthropic = MockClient
    module.__version__ = "0.18.0"
    return module


def test_anthropic_patcher_initialization():
    """Test the AnthropicPatcher class initialization."""
    # Create a mock client
    mock_client = MagicMock()
    
    # Create an AnthropicPatcher instance
    patcher = AnthropicPatcher(client=mock_client)
    
    # Check that the client is set correctly
    assert patcher.client == mock_client
    assert patcher.is_patched is False
    assert patcher.original_funcs == {}


@patch("cylestio_monitor.patchers.anthropic.sys")
@patch("cylestio_monitor.patchers.anthropic.logging.getLogger")
def test_anthropic_module_patch(mock_get_logger, mock_sys, mock_anthropic_module):
    """Test patching the Anthropic module globally."""
    # Setup mock sys.modules
    mock_sys.modules = {"anthropic": mock_anthropic_module}
    
    # Apply the patch - add custom behavior to the mock to simulate patching
    with patch("cylestio_monitor.patchers.anthropic.AnthropicPatcher.patch_module") as mock_patch_module:
        # Set up mock to change Anthropic class
        def patch_effect():
            mock_anthropic_module.Anthropic = MagicMock()
        
        mock_patch_module.side_effect = patch_effect
        
        # Save the original class
        original_class = mock_anthropic_module.Anthropic
        
        # Apply the patch
        patch_anthropic_module()
        
        # Verify the method was called
        mock_patch_module.assert_called_once()


@patch("cylestio_monitor.patchers.anthropic.sys")
def test_restore_anthropic_patches(mock_sys, mock_anthropic_module):
    """Test restoring the Anthropic patches."""
    # Setup mock sys.modules
    mock_sys.modules = {"anthropic": mock_anthropic_module}
    
    # Apply the patch - add custom behavior to the mock to simulate patching
    with patch("cylestio_monitor.patchers.anthropic.AnthropicPatcher.patch_module") as mock_patch_module:
        # Set up mock to change Anthropic class
        def patch_effect():
            mock_anthropic_module.Anthropic = MagicMock()
        
        mock_patch_module.side_effect = patch_effect
        
        # Apply patches
        patch_anthropic_module()
        
        # Reset mocks for unpatch
        with patch("cylestio_monitor.patchers.anthropic.AnthropicPatcher.unpatch_module") as mock_unpatch_module:
            # Set up mock to restore original Anthropic class
            mock_original = mock_anthropic_module.Anthropic
            
            def unpatch_effect():
                # Simulate restoration
                mock_anthropic_module.Anthropic = MockClient
            
            mock_unpatch_module.side_effect = unpatch_effect
            
            # Restore the patches
            unpatch_anthropic_module()
            
            # Verify unpatch was called
            mock_unpatch_module.assert_called_once()
