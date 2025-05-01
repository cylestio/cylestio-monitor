"""Utilities for compatibility handling."""

import inspect
import logging
import functools
from typing import Any, Callable, Dict, Optional, TypeVar, cast

logger = logging.getLogger("CylestioMonitor")

F = TypeVar('F', bound=Callable[..., Any])

def filter_kwargs_for_callable(func: Callable, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Filter kwargs to only include those accepted by the callable.
    
    Args:
        func: The callable to inspect
        kwargs: The keyword arguments to filter
        
    Returns:
        Dict with only the kwargs that are accepted by the callable
    """
    try:
        sig = inspect.signature(func)
        parameters = sig.parameters
        
        # Check for **kwargs parameter which accepts any keyword arguments
        has_kwargs_param = any(
            p.kind == inspect.Parameter.VAR_KEYWORD 
            for p in parameters.values()
        )
        
        if has_kwargs_param:
            # If function accepts **kwargs, allow all provided kwargs
            return kwargs
        
        # Filter to only include params the function accepts
        supported_kwargs = {
            k: v for k, v in kwargs.items() 
            if k in parameters
        }
        
        # Log removed kwargs only once per function
        removed_keys = set(kwargs.keys()) - set(supported_kwargs.keys())
        if removed_keys:
            func_id = f"{func.__module__}.{func.__qualname__}"
            if not hasattr(filter_kwargs_for_callable, "_warned_funcs"):
                filter_kwargs_for_callable._warned_funcs = set()
            
            if func_id not in filter_kwargs_for_callable._warned_funcs:
                filter_kwargs_for_callable._warned_funcs.add(func_id)
                logger.warning(
                    f"Removed unsupported kwargs {removed_keys} for {func_id}"
                )
        
        return supported_kwargs
    except Exception as e:
        # If inspection fails, return all kwargs and log a warning
        logger.warning(f"Failed to inspect function signature: {e}. Using all kwargs.")
        return kwargs


def safe_call(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Call a function with only the kwargs it accepts, dropping others.
    
    Args:
        func: The callable to call safely
        *args: Positional arguments to pass
        **kwargs: Keyword arguments to filter and pass
        
    Returns:
        The result of calling the function with filtered kwargs
    """
    supported_kwargs = filter_kwargs_for_callable(func, kwargs)
    return func(*args, **supported_kwargs)


def create_safe_wrapper(original_func: F) -> F:
    """Create a wrapper that calls the original function with only supported kwargs.
    
    Args:
        original_func: The function to wrap
        
    Returns:
        A wrapped function that filters kwargs before calling the original
    """
    @functools.wraps(original_func)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        return safe_call(original_func, *args, **kwargs)
    
    return cast(F, wrapped) 