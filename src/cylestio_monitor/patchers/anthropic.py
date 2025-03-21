"""Anthropic patcher for monitoring Anthropic API calls."""

import functools
import inspect
import logging
import traceback
import json
from typing import Any, Dict, Optional

from anthropic import Anthropic

from ..events_processor import log_event
from .base import BasePatcher

# Track patched clients to prevent duplicate patching
_patched_clients = set()

class AnthropicPatcher(BasePatcher):
    """Patcher for monitoring Anthropic API calls."""

    def __init__(self, client: Optional[Anthropic] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize Anthropic patcher.

        Args:
            client: Optional Anthropic client instance to patch
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.client = client
        self.original_funcs = {}
        self.logger = logging.getLogger("CylestioMonitor.Anthropic")

    def patch(self) -> None:
        """Apply monitoring patches to Anthropic client."""
        if not self.client:
            self.logger.warning("No Anthropic client provided, skipping patch")
            return

        # Check if this client is already patched
        client_id = id(self.client)
        if client_id in _patched_clients:
            self.logger.warning("Anthropic client already patched, skipping")
            return

        if self.is_patched:
            return

        self.logger.debug("Starting to patch Anthropic client...")
        
        # Get the underlying create method (accessing the wrapped method if possible)
        if hasattr(self.client.messages, "create"):
            self.logger.debug("Found messages.create method to patch")
            original_create = self.client.messages.create
            # Store the original for unpatch
            self.original_funcs["messages.create"] = original_create
            
            # Get signature of the original function to ensure compatibility
            sig = inspect.signature(original_create)
            
            def wrapped_create(*args, **kwargs):
                """Wrapper for Anthropic messages.create that logs but doesn't modify behavior."""
                self.logger.debug("Patched messages.create method called!")
                
                # Extract the prompt for logging, with error handling
                try:
                    prompt_data = kwargs.get("messages", args[0] if args else "")
                    # Make it serializable if possible
                    try:
                        json.dumps(prompt_data)
                    except (TypeError, OverflowError):
                        # Fall back to string representation
                        prompt_data = str(prompt_data)
                    
                    # Log the request
                    self.logger.debug("About to log LLM_call_start event")
                    log_event(
                        "LLM_call_start",
                        {
                            "method": "messages.create",
                            "prompt": prompt_data,
                            "alert": "none"  # Could add content filtering here
                        },
                        "LLM"
                    )
                except Exception as e:
                    # If logging fails, just log the error and continue
                    self.logger.error(f"Error logging request: {e}")
                
                # Call the original function and get the result
                try:
                    self.logger.debug("Calling original messages.create method")
                    result = original_create(*args, **kwargs)
                    self.logger.debug("Original messages.create method returned")
                    
                    # Log the response safely
                    try:
                        # Prepare response data without modifying the result
                        response_data = self._extract_response_data(result)
                        self.logger.debug("About to log LLM_call_finish event")
                        log_event(
                            "LLM_call_finish",  # Changed from LLM_call_end to LLM_call_finish
                            {
                                "method": "messages.create",
                                "response": response_data
                            },
                            "LLM"
                        )
                    except Exception as e:
                        # If response logging fails, just log the error and continue
                        self.logger.error(f"Error logging response: {e}")
                    
                    # Important: Return the original result unchanged
                    return result
                except Exception as e:
                    # If the API call fails, log the error
                    try:
                        error_message = f"{type(e).__name__}: {str(e)}"
                        self.logger.debug("About to log LLM_call_blocked event")
                        log_event(
                            "LLM_call_blocked",  # Changed from LLM_call_error to LLM_call_blocked
                            {
                                "method": "messages.create",
                                "error": error_message,
                                "error_type": type(e).__name__
                            },
                            "LLM",
                            level="error"
                        )
                    except Exception as log_error:
                        # If error logging fails, log the error and continue
                        self.logger.error(f"Error logging blocked call: {log_error}")
                    
                    # Re-raise the original exception
                    raise
            
            # Apply signature from original function (helps with IDE hints/autocomplete)
            wrapped_create.__signature__ = sig
            wrapped_create.__doc__ = original_create.__doc__
            wrapped_create.__name__ = original_create.__name__
            
            # Replace the method
            self.logger.debug("Replacing original messages.create with wrapped version")
            self.client.messages.create = wrapped_create
            self.is_patched = True
            
            # Add client to patched clients set
            _patched_clients.add(client_id)
            
            self.logger.info("Applied Anthropic monitoring patches")
        else:
            self.logger.warning("Could not find messages.create method to patch")

    def _extract_response_data(self, result):
        """Safely extract data from response without modifying the original."""
        # First, just try to get a basic representation that won't affect the original
        if hasattr(result, "model_dump"):
            try:
                # For Pydantic models (newer Anthropic client) - create a copy
                return result.model_dump()
            except Exception as e:
                self.logger.debug(f"Could not use model_dump: {e}")
        
        if hasattr(result, "dict"):
            try:
                # For objects with dict method
                return result.dict()
            except Exception as e:
                self.logger.debug(f"Could not use dict method: {e}")
        
        if hasattr(result, "__dict__"):
            try:
                # For objects with __dict__ attribute
                return {k: v for k, v in result.__dict__.items() if not k.startswith("_")}
            except Exception as e:
                self.logger.debug(f"Could not use __dict__: {e}")
                
        if isinstance(result, dict):
            # For dictionary responses
            return dict(result)
        
        # Fallback: convert to string for logging
        try:
            return {"text": str(result)}
        except Exception as e:
            self.logger.error(f"Could not convert response to string: {e}")
            return {"text": "Unable to extract response data"}

    def unpatch(self) -> None:
        """Remove monitoring patches from Anthropic client."""
        if not self.is_patched:
            return

        # Restore original functions
        if "messages.create" in self.original_funcs:
            self.client.messages.create = self.original_funcs["messages.create"]
            del self.original_funcs["messages.create"]

        self.is_patched = False
        
        # Remove client from patched clients set
        if self.client:
            _patched_clients.discard(id(self.client))

        self.logger.info("Removed Anthropic monitoring patches")
