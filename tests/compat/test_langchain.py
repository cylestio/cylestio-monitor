"""Tests for LangChain compatibility layer."""

import inspect
import unittest
import functools
from unittest.mock import MagicMock, patch

import pytest

from cylestio_monitor._compat.utils import filter_kwargs_for_callable, safe_call
from cylestio_monitor._compat.langchain import _patch_function_in_module, patch_convert_to_openai_function


class TestKwargsFiltering(unittest.TestCase):
    """Test the kwargs filtering utilities."""
    
    def test_filter_kwargs_keeps_supported_kwargs(self):
        """Test that filter_kwargs_for_callable keeps supported kwargs."""
        def func(a, b, c=None):
            return a, b, c
        
        kwargs = {"a": 1, "b": 2, "c": 3, "d": 4}
        filtered = filter_kwargs_for_callable(func, kwargs)
        
        self.assertEqual(filtered, {"a": 1, "b": 2, "c": 3})
        self.assertNotIn("d", filtered)
    
    def test_filter_kwargs_with_var_keywords(self):
        """Test that filter_kwargs_for_callable keeps all kwargs for **kwargs functions."""
        def func(a, b, **kwargs):
            return a, b, kwargs
        
        kwargs = {"a": 1, "b": 2, "c": 3, "d": 4}
        filtered = filter_kwargs_for_callable(func, kwargs)
        
        self.assertEqual(filtered, kwargs)
    
    def test_safe_call_with_extra_kwargs(self):
        """Test that safe_call correctly calls a function with filtered kwargs."""
        def func(a, b, c=None):
            return a, b, c
        
        result = safe_call(func, a=1, b=2, c=3, d=4)
        self.assertEqual(result, (1, 2, 3))


class TestLangChainPatching(unittest.TestCase):
    """Test the LangChain patching functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock module
        self.mock_module = MagicMock()
        
        # Create a function to be patched
        def original_func(arg1, strict=False):
            return f"Original: {arg1}, strict={strict}"
        
        self.mock_module.original_func = original_func
        
        # Add to sys.modules
        self.sys_modules_patch = patch("sys.modules", {"test_module": self.mock_module})
        self.mock_sys_modules = self.sys_modules_patch.start()
    
    def tearDown(self):
        """Clean up test environment."""
        self.sys_modules_patch.stop()
    
    def test_patching_function(self):
        """Test that _patch_function_in_module correctly patches a function."""
        def wrapper_factory(original):
            def wrapped(arg1, **kwargs):
                kwargs = filter_kwargs_for_callable(original, kwargs)
                return f"Wrapped: {original(arg1, **kwargs)}"
            return wrapped
        
        # Patch the function
        success = _patch_function_in_module("test_module", "original_func", wrapper_factory)
        
        # Check patching succeeded
        self.assertTrue(success)
        
        # Test calling the patched function
        result = self.mock_module.original_func("test", strict=True)
        self.assertEqual(result, "Wrapped: Original: test, strict=True")
        
        # Verify the function is marked as patched
        self.assertTrue(hasattr(self.mock_module.original_func, "_cy_patched"))
        
        # Test patching is idempotent
        success = _patch_function_in_module("test_module", "original_func", wrapper_factory)
        self.assertTrue(success)
    
    def test_patching_nonexistent_module(self):
        """Test that patching a nonexistent module fails gracefully."""
        success = _patch_function_in_module("nonexistent_module", "func", lambda x: x)
        self.assertFalse(success)
    
    def test_patching_nonexistent_function(self):
        """Test that patching a nonexistent function fails gracefully."""
        # Ensure the function doesn't exist in the module
        if hasattr(self.mock_module, "nonexistent_func"):
            delattr(self.mock_module, "nonexistent_func")
            
        success = _patch_function_in_module("test_module", "nonexistent_func", lambda x: x)
        self.assertFalse(success)


class TestConvertToOpenAIFunctionPatching(unittest.TestCase):
    """Test patching for convert_to_openai_function."""
    
    def setUp(self):
        """Set up test variables."""
        # Mock tool
        self.mock_tool = MagicMock()
        self.mock_tool.name = "test_tool"
    
    @patch('cylestio_monitor._compat.langchain._patch_function_in_module')
    def test_patch_convert_to_openai_function(self, mock_patch_function):
        """Test patching convert_to_openai_function."""
        # Setup the mock patch function to return True
        mock_patch_function.return_value = True
        
        # Call the function
        success = patch_convert_to_openai_function()
        
        # Should return True since all the patching functions returned True
        self.assertTrue(success)
        
        # Verify the right modules were patched
        calls = mock_patch_function.call_args_list
        self.assertEqual(len(calls), 3)
        
        # Verify correct module paths
        self.assertEqual(calls[0][0][0], "langchain_core.utils.function_calling")
        self.assertEqual(calls[1][0][0], "langchain.tools.convert_to_openai_function")
        self.assertEqual(calls[2][0][0], "langchain_core.tools")
        
        # All should patch the same function name
        for call in calls:
            self.assertEqual(call[0][1], "convert_to_openai_function")
    
    def test_wrapped_function_filters_kwargs(self):
        """Test that wrapped functions properly filter kwargs."""
        # Create a function that only accepts specific kwargs
        def original_function(tool):
            """Function without strict param."""
            return {"function": {"name": tool.name}}
        
        # Create the wrapper directly to test filtering
        def create_wrapper(original):
            @functools.wraps(original)
            def wrapped(tool, **kwargs):
                try:
                    # Filter kwargs to only include those accepted by original
                    filtered_kwargs = filter_kwargs_for_callable(original, kwargs)
                    return original(tool, **filtered_kwargs)
                except Exception as e:
                    return tool
            return wrapped
        
        wrapped_function = create_wrapper(original_function)
        
        # Test calling with an unsupported kwarg
        result = wrapped_function(self.mock_tool, strict=True)
        
        # Should work by filtering out the unsupported kwarg
        self.assertEqual(result["function"]["name"], "test_tool")
        self.assertNotIn("strict", result["function"])
    
    def test_wrapped_function_handles_errors(self):
        """Test that wrapped functions handle errors gracefully."""
        # Create a function that raises an exception
        def error_function(tool, **kwargs):
            """Function that raises an exception."""
            raise ValueError("Test error")
        
        # Create the wrapper
        def create_wrapper(original):
            @functools.wraps(original)
            def wrapped(tool, **kwargs):
                try:
                    return original(tool, **kwargs)
                except Exception:
                    return tool
            return wrapped
        
        wrapped_function = create_wrapper(error_function)
        
        # Test calling the wrapped function
        result = wrapped_function(self.mock_tool, strict=True)
        
        # Should return the original tool without error
        self.assertEqual(result, self.mock_tool)


if __name__ == "__main__":
    unittest.main() 