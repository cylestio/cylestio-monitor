"""Anthropic patcher for monitoring Anthropic API calls."""

import functools
import inspect
import logging
import traceback
import json
import sys
from typing import Any, Dict, Optional
from datetime import datetime

# Try to import Anthropic but don't fail if not available
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from ..utils.trace_context import TraceContext
from ..utils.event_logging import log_event
from .base import BasePatcher

# Track patched clients to prevent duplicate patching
_patched_clients = set()
_is_module_patched = False

# Store original methods for restoration
_original_methods = {}

class AnthropicPatcher(BasePatcher):
    """Patcher for monitoring Anthropic API calls."""

    def __init__(self, client: Optional[Any] = None, config: Optional[Dict[str, Any]] = None):
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
            self.logger.warning("No Anthropic client provided, skipping instance patch")
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
                    
                    # Check for suspicious or dangerous content
                    alert_level = "none"
                    suspicious_keywords = ["hack", "exploit", "bomb", "terrorist", "illegal", "attack", "drop", "destroy", "delete", "backdoor", "exploit", "virus", "malware"]
                    dangerous_keywords = ["how to make a bomb", "how to steal", "how to hack", "assassinate", "kill", "build a bomb", "drop a bomb"]
                    
                    # Convert prompt to string for checking keywords
                    prompt_str = str(prompt_data).lower()
                    
                    # Check for dangerous content first (more severe)
                    for keyword in dangerous_keywords:
                        if keyword in prompt_str:
                            alert_level = "dangerous"
                            self.logger.warning(f"SECURITY ALERT: Dangerous content detected in LLM request: '{keyword}'")
                            # Log as a dedicated security event too
                            log_event(
                                name="security.content.dangerous",
                                attributes={
                                    "method": "messages.create",
                                    "keyword": keyword,
                                    "content_sample": prompt_str[:100] + "..." if len(prompt_str) > 100 else prompt_str
                                },
                                level="ERROR"
                            )
                            break
                            
                    # If not dangerous, check if suspicious
                    if alert_level == "none":
                        for keyword in suspicious_keywords:
                            if keyword in prompt_str:
                                alert_level = "suspicious"
                                self.logger.warning(f"SECURITY WARNING: Suspicious content detected in LLM request: '{keyword}'")
                                # Log as a dedicated security event too
                                log_event(
                                    name="security.content.suspicious",
                                    attributes={
                                        "method": "messages.create",
                                        "keyword": keyword,
                                        "content_sample": prompt_str[:100] + "..." if len(prompt_str) > 100 else prompt_str
                                    },
                                    level="WARNING"
                                )
                                break
                    
                    # Extract model information if available
                    model = kwargs.get("model", "unknown")
                    
                    # Prepare attributes for the request event
                    request_attributes = {
                        "method": "messages.create",
                        "llm.vendor": "anthropic",
                        "llm.model": model,
                        "llm.request.type": "completion",
                        "llm.request.prompt": prompt_data,
                        "security.alert": alert_level,
                    }
                    
                    # Add security details if there's an alert
                    if alert_level != "none":
                        request_attributes["security.detection_time"] = datetime.now().isoformat()
                    
                    # Log the request
                    self.logger.debug("About to log llm.call.start event")
                    log_event(
                        name="llm.call.start",
                        attributes=request_attributes,
                        level="INFO"
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
                        
                        # Extract model and token usage if available
                        model = response_data.get("model", model if "model" in locals() else "unknown")
                        usage = response_data.get("usage", {})
                        
                        # Prepare attributes for the response event
                        response_attributes = {
                            "method": "messages.create",
                            "response": response_data  # Store the entire response data
                        }
                        
                        # Add usage statistics if available
                        if usage:
                            if "input_tokens" in usage:
                                response_attributes["llm.usage.input_tokens"] = usage["input_tokens"]
                            if "output_tokens" in usage:
                                response_attributes["llm.usage.output_tokens"] = usage["output_tokens"]
                        
                        # Add a debug statement to check serializability
                        try:
                            json.dumps(response_attributes)
                            self.logger.debug("Response data is JSON serializable")
                        except (TypeError, ValueError) as e:
                            self.logger.error(f"Response data is not JSON serializable: {e}")
                            # Fallback to a more basic representation
                            response_attributes = {
                                "method": "messages.create",
                                "response": {
                                    "id": response_data.get("id", ""),
                                    "model": model,
                                    "role": "assistant",
                                    "text_content": str(result)
                                }
                            }
                        
                        self.logger.debug("About to log llm.call.finish event")
                        log_event(
                            name="llm.call.finish",
                            attributes=response_attributes,
                            level="INFO"
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
                        
                        # Prepare attributes for the error event
                        error_attributes = {
                            "method": "messages.create",
                            "llm.vendor": "anthropic",
                            "llm.model": model if "model" in locals() else "unknown",
                            "error.type": type(e).__name__,
                            "error.message": error_message
                        }
                        
                        self.logger.debug("About to log llm.error event")
                        log_event(
                            name="llm.call.error",
                            attributes=error_attributes,
                            level="ERROR"
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
            
            # Mark as patched
            self.is_patched = True
            _patched_clients.add(client_id)
            self.logger.info("Successfully patched Anthropic client")
        else:
            self.logger.warning("Anthropic client doesn't have messages.create method, skipping patch")

    def _extract_response_data(self, result):
        """Extract relevant response data for logging.
        
        Args:
            result: Result from the API call
            
        Returns:
            Dict with extracted data
        """
        try:
            # Check if the result is a message object
            if hasattr(result, "model"):
                # It's probably a Message object, extract attributes
                data = {
                    "id": getattr(result, "id", ""),
                    "model": getattr(result, "model", "unknown"),
                    "role": getattr(result, "role", "assistant"),
                    "stop_reason": getattr(result, "stop_reason", None),
                }
                
                # Handle content specially to make it JSON serializable
                content = getattr(result, "content", [])
                if content:
                    # Convert content objects to dictionaries
                    serializable_content = []
                    for item in content:
                        if hasattr(item, "__dict__"):
                            # Convert object to dict, excluding special attributes
                            item_dict = {k: v for k, v in item.__dict__.items() 
                                        if not k.startswith("_")}
                            serializable_content.append(item_dict)
                        elif hasattr(item, "to_dict"):
                            # Use to_dict method if available
                            serializable_content.append(item.to_dict())
                        elif isinstance(item, dict):
                            serializable_content.append(item)
                        else:
                            # Fallback to string representation
                            serializable_content.append({"type": "text", "text": str(item)})
                    data["content"] = serializable_content
                
                # Extract usage if available
                if hasattr(result, "usage"):
                    usage = result.usage
                    data["usage"] = {
                        "input_tokens": getattr(usage, "input_tokens", 0),
                        "output_tokens": getattr(usage, "output_tokens", 0)
                    }
                
                return data
            elif isinstance(result, dict):
                # It's already a dict, just return it
                return result
            else:
                # Convert to string representation as fallback
                return {"content": str(result)}
        except Exception as e:
            self.logger.error(f"Error extracting response data: {e}")
            return {"content": str(result)}

    def unpatch(self) -> None:
        """Restore original methods."""
        if not self.is_patched:
            return

        self.logger.debug("Unpatching Anthropic client...")
        
        # Restore original methods
        for name, original_func in self.original_funcs.items():
            if name == "messages.create" and hasattr(self.client.messages, "create"):
                self.client.messages.create = original_func
        
        # Clear stored functions
        self.original_funcs = {}
        
        # Remove from patched clients
        client_id = id(self.client)
        if client_id in _patched_clients:
            _patched_clients.remove(client_id)
        
        self.is_patched = False
        self.logger.info("Successfully unpatched Anthropic client")

    @classmethod
    def patch_module(cls) -> None:
        """Patch the Anthropic module to intercept client creation."""
        global _is_module_patched
        
        if not ANTHROPIC_AVAILABLE:
            return
            
        if _is_module_patched:
            return
            
        # Get the original __init__ method
        original_init = Anthropic.__init__
        
        # Store the original for unpatch
        _original_methods["Anthropic.__init__"] = original_init
        
        @functools.wraps(original_init)
        def patched_init(self, *args, **kwargs):
            # Call original init
            original_init(self, *args, **kwargs)
            
            # Log the initialization as a framework initialization event
            log_event(
                name="framework.initialization",
                attributes={
                    "framework.name": "anthropic",
                    "framework.type": "llm_provider",
                    "api_key_present": bool(kwargs.get("api_key") or hasattr(self, "api_key")),
                    "auth_present": bool(kwargs.get("auth_token") or hasattr(self, "auth_token")),
                },
                level="info"
            )
            
            # Patch the new instance
            patcher = cls(self)
            patcher.patch()
        
        # Replace the method
        Anthropic.__init__ = patched_init
        
        _is_module_patched = True
        logger = logging.getLogger("CylestioMonitor.Anthropic")
        logger.info("Patched Anthropic module")

    @classmethod
    def unpatch_module(cls) -> None:
        """Restore original Anthropic module methods."""
        global _is_module_patched
        
        if not ANTHROPIC_AVAILABLE or not _is_module_patched:
            return
            
        # Restore the original __init__ method
        if "Anthropic.__init__" in _original_methods:
            Anthropic.__init__ = _original_methods["Anthropic.__init__"]
            del _original_methods["Anthropic.__init__"]
        
        _is_module_patched = False
        logger = logging.getLogger("CylestioMonitor.Anthropic")
        logger.info("Unpatched Anthropic module")


def patch_anthropic_module():
    """Patch the Anthropic module."""
    AnthropicPatcher.patch_module()

def unpatch_anthropic_module():
    """Unpatch the Anthropic module."""
    AnthropicPatcher.unpatch_module()
