"""Test for BaseTool patching functionality."""

import os
import unittest
from typing import Any, Optional, Dict
from unittest.mock import patch, MagicMock, ANY

try:
    from langchain_core.tools import BaseTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.tools import BaseTool
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
    

from cylestio_monitor.patchers.base_tool_patcher import (
    patch_base_tool,
    unpatch_base_tool,
)


@unittest.skipIf(not LANGCHAIN_AVAILABLE, "LangChain not available")
class BaseToolPatcherTest(unittest.TestCase):
    """Test suite for BaseToolPatcher."""

    def setUp(self):
        """Set up test environment."""
        # Enable development mode for easier testing
        os.environ["CYLESTIO_DEVELOPMENT_MODE"] = "1"
        # Reset patching state before each test
        try:
            unpatch_base_tool()
        except:
            pass  # Ignore errors on initial unpatching

    def tearDown(self):
        """Clean up after tests."""
        # Ensure patching is reset after each test
        try:
            unpatch_base_tool()
        except:
            pass  # Ignore errors on final unpatching
            
        if "CYLESTIO_DEVELOPMENT_MODE" in os.environ:
            del os.environ["CYLESTIO_DEVELOPMENT_MODE"]

    @patch("cylestio_monitor.patchers.base_tool_patcher.log_event")
    def test_base_tool_patching(self, mock_log_event):
        """Test that BaseTool patching works correctly."""
        # First, verify we can patch the BaseTool
        result = patch_base_tool()
        self.assertTrue(result, "BaseTool patching should succeed")
        
        # Store original method for comparison
        original_invoke = BaseTool.invoke
        
        # Unpatch and verify the method changes back
        unpatch_result = unpatch_base_tool()
        self.assertTrue(unpatch_result, "Unpatching should succeed")
        
        # Verify methods are different
        self.assertNotEqual(original_invoke, BaseTool.invoke, 
                           "Method should be different after unpatching")
        
        # Check that we logged the patching event
        mock_log_event.assert_any_call(
            name="framework.patch",
            attributes={
                "framework.name": "langchain_base_tool",
                "patch.type": "method_wrapper",
                "patch.components": ["BaseTool.invoke", "BaseTool.ainvoke"]
            }
        )
    
    def test_patch_twice(self):
        """Test that patching twice works correctly."""
        # Apply patch first time
        result1 = patch_base_tool()
        self.assertTrue(result1, "First patch should succeed")
        
        # Apply patch second time - should return False
        result2 = patch_base_tool()
        self.assertFalse(result2, "Second patch should fail")
        
        # Unpatch and verify
        unpatch_result = unpatch_base_tool()
        self.assertTrue(unpatch_result, "Unpatching should succeed")


if __name__ == "__main__":
    unittest.main() 