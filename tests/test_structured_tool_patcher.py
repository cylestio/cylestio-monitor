"""Test for StructuredTool patching functionality."""

import os
import unittest
from typing import Any, Optional, Dict
from unittest.mock import patch, MagicMock, ANY

try:
    from langchain_core.tools import StructuredTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.tools import StructuredTool
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
    

from cylestio_monitor.patchers.structured_tool_patcher import (
    patch_structured_tool,
    unpatch_structured_tool,
)


@unittest.skipIf(not LANGCHAIN_AVAILABLE, "LangChain not available")
class StructuredToolPatcherTest(unittest.TestCase):
    """Test suite for StructuredToolPatcher."""

    def setUp(self):
        """Set up test environment."""
        # Enable development mode for easier testing
        os.environ["CYLESTIO_DEVELOPMENT_MODE"] = "1"
        # Reset patching state before each test
        try:
            unpatch_structured_tool()
        except:
            pass  # Ignore errors on initial unpatching

    def tearDown(self):
        """Clean up after tests."""
        # Ensure patching is reset after each test
        try:
            unpatch_structured_tool()
        except:
            pass  # Ignore errors on final unpatching
            
        if "CYLESTIO_DEVELOPMENT_MODE" in os.environ:
            del os.environ["CYLESTIO_DEVELOPMENT_MODE"]

    @patch("cylestio_monitor.patchers.structured_tool_patcher.log_event")
    def test_structured_tool_patching(self, mock_log_event):
        """Test that StructuredTool patching works correctly."""
        # First, verify we can patch the StructuredTool
        result = patch_structured_tool()
        self.assertTrue(result, "StructuredTool patching should succeed")
        
        # Store original method for comparison
        original_call = StructuredTool.__call__
        
        # Unpatch and verify the method changes back
        unpatch_result = unpatch_structured_tool()
        self.assertTrue(unpatch_result, "Unpatching should succeed")
        
        # Verify methods are different
        self.assertNotEqual(original_call, StructuredTool.__call__, 
                           "Method should be different after unpatching")
        
        # Check that we logged the patching event
        mock_log_event.assert_any_call(
            name="framework.patch",
            attributes={
                "framework.name": "langchain_structured_tool",
                "patch.type": "method_wrapper",
                "patch.components": ["StructuredTool.__call__"]
            }
        )
    
    def test_patch_twice(self):
        """Test that patching twice works correctly."""
        # Apply patch first time
        result1 = patch_structured_tool()
        self.assertTrue(result1, "First patch should succeed")
        
        # Apply patch second time - should return False
        result2 = patch_structured_tool()
        self.assertFalse(result2, "Second patch should fail")
        
        # Unpatch and verify
        unpatch_result = unpatch_structured_tool()
        self.assertTrue(unpatch_result, "Unpatching should succeed")


if __name__ == "__main__":
    unittest.main() 