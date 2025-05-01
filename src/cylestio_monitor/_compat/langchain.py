"""LangChain compatibility layer.

This module provides compatibility shims for different versions of LangChain,
ensuring that cylestio-monitor can work with various LangChain versions without
crashing the host application.
"""

import logging
import sys
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union, cast

from cylestio_monitor._compat.utils import filter_kwargs_for_callable, safe_call, create_safe_wrapper

logger = logging.getLogger("CylestioMonitor")

# Keep track of functions we've already patched
_PATCHED_FUNCTIONS: Set[str] = set()

def _patch_function_in_module(
    module_name: str, 
    function_name: str, 
    wrapper_factory: Callable[[Callable], Callable]
) -> bool:
    """Patch a function in a module with a wrapper.
    
    Args:
        module_name: Name of the module containing the function
        function_name: Name of the function to patch
        wrapper_factory: Function that takes the original and returns a wrapped version
        
    Returns:
        True if patching succeeded, False otherwise
    """
    # Generate a unique ID for this patch to avoid double-patching
    patch_id = f"{module_name}.{function_name}"
    if patch_id in _PATCHED_FUNCTIONS:
        return True  # Already patched
    
    try:
        # Check if module is loaded
        if module_name not in sys.modules:
            return False
        
        module = sys.modules[module_name]
        
        # Check if function exists in module
        if not hasattr(module, function_name):
            return False
            
        original_func = getattr(module, function_name)
        
        # Skip if already patched (redundant check but useful for safety)
        if hasattr(original_func, "_cy_patched"):
            return True
            
        # Create wrapped version
        wrapped_func = wrapper_factory(original_func)
        
        # Mark as patched
        wrapped_func._cy_patched = True  # type: ignore
        
        # Replace original with wrapped version
        setattr(module, function_name, wrapped_func)
        
        # Record that we've patched this function
        _PATCHED_FUNCTIONS.add(patch_id)
        
        logger.debug(f"Successfully patched {patch_id}")
        return True
        
    except Exception as e:
        logger.warning(f"Failed to patch {patch_id}: {e}")
        return False


def patch_convert_to_openai_function() -> bool:
    """Patch the convert_to_openai_function in langchain_core.
    
    This addresses the specific issue with the 'strict' kwarg being added in newer
    versions of langchain-openai but not supported in older langchain-core versions.
    
    Returns:
        True if patching succeeded, False otherwise
    """
    def create_wrapper(original: Callable) -> Callable:
        @functools.wraps(original)
        def wrapped_convert_to_openai_function(tool: Any, **kwargs: Any) -> Any:
            try:
                # Filter kwargs to only include those accepted by the original function
                filtered_kwargs = filter_kwargs_for_callable(original, kwargs)
                return original(tool, **filtered_kwargs)
            except Exception as e:
                # Log the error once
                logger.warning(
                    f"Error in convert_to_openai_function, returning original tool: {e}"
                )
                # Return the unmodified object to fail softly
                return tool
        
        return wrapped_convert_to_openai_function
    
    # Try to patch in both potential locations
    success1 = _patch_function_in_module(
        "langchain_core.utils.function_calling", 
        "convert_to_openai_function",
        create_wrapper
    )
    
    success2 = _patch_function_in_module(
        "langchain.tools.convert_to_openai_function",
        "convert_to_openai_function",
        create_wrapper
    )
    
    # Also try under langchain_core.tools
    success3 = _patch_function_in_module(
        "langchain_core.tools",
        "convert_to_openai_function",
        create_wrapper
    )
    
    return success1 or success2 or success3


def apply_patches() -> None:
    """Apply all compatibility patches for LangChain.
    
    This function is designed to be idempotent - it's safe to call multiple times.
    """
    try:
        patch_convert_to_openai_function()
        
        # Add additional patches here as needed
        # patch_another_function()
        # etc.
        
    except Exception as e:
        logger.warning(f"Error applying LangChain compatibility patches: {e}")
        # Continue execution - we should never take down the host application 