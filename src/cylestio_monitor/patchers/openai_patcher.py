"""OpenAI patcher for monitoring OpenAI API calls."""

import functools
import json
import logging
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

# Try to import OpenAI but don't fail if not available
try:
    import openai
    from openai import AsyncOpenAI, OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from ..utils.event_logging import log_event
from ..utils.trace_context import TraceContext
from .base import BasePatcher

# Track patched clients to prevent duplicate patching
_patched_clients = set()
_is_module_patched = False

# Store original methods for restoration
_original_methods = {}


class OpenAIPatcher(BasePatcher):
    """Patcher for monitoring OpenAI API calls."""

    def __init__(
        self, client: Optional[Any] = None, config: Optional[Dict[str, Any]] = None
    ):
        """Initialize OpenAI patcher.

        Args:
            client: Optional OpenAI client instance to patch
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.client = client
        self.original_funcs = {}
        self.logger = logging.getLogger("CylestioMonitor.OpenAI")
        self.debug_mode = config.get("debug", False) if config else False

    def patch(self) -> None:
        """Apply monitoring patches to OpenAI client."""
        if not self.client:
            self.logger.warning("No OpenAI client provided, skipping instance patch")
            return

        # Check if this client is already patched
        client_id = id(self.client)
        if client_id in _patched_clients:
            self.logger.warning("OpenAI client already patched, skipping")
            return

        if self.is_patched:
            return

        self.logger.debug("Starting to patch OpenAI client...")

        # Patch ChatCompletions create method
        if hasattr(self.client.chat.completions, "create"):
            self.logger.debug("Found chat.completions.create method to patch")
            original_create = self.client.chat.completions.create
            self.original_funcs["chat.completions.create"] = original_create

            def wrapped_chat_create(*args, **kwargs):
                """Wrapper for OpenAI chat.completions.create that logs but doesn't modify behavior."""
                self.logger.debug("Patched chat.completions.create method called!")

                # Generate a unique span ID for this operation
                span_id = TraceContext.start_span("llm.call")["span_id"]
                trace_id = TraceContext.get_current_context().get("trace_id")

                # Record start time for performance measurement
                start_time = time.time()

                # Extract request details
                try:
                    model = kwargs.get("model", "unknown")
                    messages = kwargs.get("messages", [])
                    temperature = kwargs.get("temperature")
                    max_tokens = kwargs.get("max_tokens")
                    top_p = kwargs.get("top_p")
                    frequency_penalty = kwargs.get("frequency_penalty")
                    presence_penalty = kwargs.get("presence_penalty")
                    stop = kwargs.get("stop")

                    # Prepare complete request data
                    request_data = {
                        "messages": self._safe_serialize(messages),
                        "model": model,
                    }

                    # Add optional parameters if present
                    if temperature is not None:
                        request_data["temperature"] = temperature
                    if max_tokens is not None:
                        request_data["max_tokens"] = max_tokens
                    if top_p is not None:
                        request_data["top_p"] = top_p
                    if frequency_penalty is not None:
                        request_data["frequency_penalty"] = frequency_penalty
                    if presence_penalty is not None:
                        request_data["presence_penalty"] = presence_penalty
                    if stop is not None:
                        request_data["stop"] = stop

                    # Security content scanning
                    security_info = self._scan_content_security(messages)

                    # Prepare attributes for the request event
                    request_attributes = {
                        "llm.vendor": "openai",
                        "llm.model": model,
                        "llm.request.type": "chat_completion",
                        "llm.request.data": request_data,
                        "llm.request.timestamp": datetime.now().isoformat(),
                    }

                    # Add model configuration
                    if temperature is not None:
                        request_attributes["llm.request.temperature"] = temperature
                    if max_tokens is not None:
                        request_attributes["llm.request.max_tokens"] = max_tokens
                    if top_p is not None:
                        request_attributes["llm.request.top_p"] = top_p

                    # Add security details if something was detected
                    if security_info["alert_level"] != "none":
                        request_attributes["security.alert_level"] = security_info[
                            "alert_level"
                        ]
                        request_attributes["security.keywords"] = security_info[
                            "keywords"
                        ]

                        # Log security event separately
                        self._log_security_event(security_info, request_data)

                    # Log the request with debug mode info if enabled
                    if self.debug_mode:
                        self.logger.debug(
                            f"Request data: {json.dumps(request_data)[:500]}..."
                        )

                    # Log the request event
                    log_event(
                        name="llm.call.start",
                        attributes=request_attributes,
                        level="INFO",
                        span_id=span_id,
                        trace_id=trace_id,
                    )

                except Exception as e:
                    # If logging fails, log the error but don't disrupt the actual API call
                    self.logger.error(f"Error logging request: {e}")
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")

                # Call the original function and get the result
                try:
                    result = original_create(*args, **kwargs)

                    # Calculate duration
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Log the response safely
                    try:
                        # Extract structured data from the response
                        response_data = self._extract_chat_response_data(result)

                        # Extract model and token usage if available
                        usage = response_data.get("usage", {})

                        # Prepare attributes for the response event
                        response_attributes = {
                            "llm.vendor": "openai",
                            "llm.model": response_data.get("model", model),
                            "llm.response.id": response_data.get("id", ""),
                            "llm.response.type": "chat_completion",
                            "llm.response.timestamp": datetime.now().isoformat(),
                            "llm.response.duration_ms": duration_ms,
                        }

                        # Add content data from response choices
                        choices = response_data.get("choices", [])
                        if choices:
                            first_choice = choices[0]
                            if "message" in first_choice:
                                response_attributes[
                                    "llm.response.content"
                                ] = self._safe_serialize(first_choice["message"])
                            if "finish_reason" in first_choice:
                                response_attributes[
                                    "llm.response.stop_reason"
                                ] = first_choice["finish_reason"]

                        # Add usage statistics if available
                        if usage:
                            if "prompt_tokens" in usage:
                                response_attributes["llm.usage.input_tokens"] = usage[
                                    "prompt_tokens"
                                ]
                            if "completion_tokens" in usage:
                                response_attributes["llm.usage.output_tokens"] = usage[
                                    "completion_tokens"
                                ]
                            if "total_tokens" in usage:
                                response_attributes["llm.usage.total_tokens"] = usage[
                                    "total_tokens"
                                ]
                                
                        # Extract response content for security scanning
                        response_content = ""
                        if "llm.response.content" in response_attributes:
                            content_data = response_attributes["llm.response.content"]
                            if isinstance(content_data, dict) and "content" in content_data:
                                response_content = content_data["content"]
                            elif isinstance(content_data, str):
                                response_content = content_data
                                
                        # If no content was found but we have choices
                        if not response_content and choices:
                            first_choice = choices[0]
                            if isinstance(first_choice, dict):
                                if "message" in first_choice and isinstance(first_choice["message"], dict):
                                    response_content = first_choice["message"].get("content", "")
                                elif "text" in first_choice:
                                    response_content = first_choice["text"]
                                    
                        # Scan response content for security concerns
                        if response_content:
                            # Security scanning for response content
                            from cylestio_monitor.security_detection import SecurityScanner
                            scanner = SecurityScanner.get_instance()
                            security_info = scanner.scan_text(response_content)
                            
                            # If security issues found, add to attributes and log a separate event
                            if security_info["alert_level"] != "none":
                                response_attributes["security.alert_level"] = security_info["alert_level"]
                                response_attributes["security.keywords"] = security_info["keywords"]
                                response_attributes["security.category"] = security_info["category"]
                                response_attributes["security.severity"] = security_info["severity"]
                                response_attributes["security.description"] = security_info["description"]
                                
                                # Log security event for response content
                                self._log_security_event(security_info, {"content": response_content[:100] + "..."})
                                
                                # Log warning
                                self.logger.warning(
                                    f"SECURITY ALERT in LLM RESPONSE: {security_info['alert_level'].upper()} content "
                                    f"detected: {security_info['keywords']}"
                                )

                        # Debug logging
                        if self.debug_mode:
                            self.logger.debug(
                                f"Response attributes: {json.dumps(response_attributes)[:500]}..."
                            )

                        # Log the completion of the operation
                        log_event(
                            name="llm.call.finish",
                            attributes=response_attributes,
                            level="INFO",
                            span_id=span_id,
                            trace_id=trace_id,
                        )
                    except Exception as e:
                        # If response logging fails, log the error but don't disrupt the response
                        error_msg = f"Error logging response: {e}"
                        self.logger.error(error_msg)
                        if self.debug_mode:
                            self.logger.error(f"Traceback: {traceback.format_exc()}")

                        # Log a simplified response event to ensure the span is completed
                        log_event(
                            name="llm.call.finish",
                            attributes={
                                "llm.vendor": "openai",
                                "llm.model": model,
                                "llm.response.duration_ms": duration_ms,
                                "error": error_msg,
                            },
                            level="INFO",
                            span_id=span_id,
                            trace_id=trace_id,
                        )

                    # End the span
                    TraceContext.end_span()

                    # Return the original result unchanged
                    return result

                except Exception as e:
                    # Calculate duration up to the error
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Log the error
                    error_msg = f"Error during OpenAI chat completion call: {str(e)}"
                    self.logger.error(error_msg)
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")

                    # Log the error event
                    log_event(
                        name="llm.call.error",
                        attributes={
                            "llm.vendor": "openai",
                            "llm.model": model,
                            "llm.response.duration_ms": duration_ms,
                            "error.message": str(e),
                            "error.type": e.__class__.__name__,
                        },
                        level="ERROR",
                        span_id=span_id,
                        trace_id=trace_id,
                    )

                    # End the span
                    TraceContext.end_span()

                    # Re-raise the original exception
                    raise

            # Apply the patch
            self.client.chat.completions.create = wrapped_chat_create

        # Patch Completions create method (legacy API)
        if hasattr(self.client.completions, "create"):
            self.logger.debug("Found completions.create method to patch")
            original_completion_create = self.client.completions.create
            self.original_funcs["completions.create"] = original_completion_create

            def wrapped_completion_create(*args, **kwargs):
                """Wrapper for OpenAI completions.create that logs but doesn't modify behavior."""
                self.logger.debug("Patched completions.create method called!")

                # Generate a unique span ID for this operation
                span_id = TraceContext.start_span("llm.call")["span_id"]
                trace_id = TraceContext.get_current_context().get("trace_id")

                # Record start time for performance measurement
                start_time = time.time()

                # Extract request details
                try:
                    model = kwargs.get("model", "unknown")
                    prompt = kwargs.get("prompt", "")
                    temperature = kwargs.get("temperature")
                    max_tokens = kwargs.get("max_tokens")
                    top_p = kwargs.get("top_p")
                    frequency_penalty = kwargs.get("frequency_penalty")
                    presence_penalty = kwargs.get("presence_penalty")
                    stop = kwargs.get("stop")

                    # Prepare complete request data
                    request_data = {
                        "prompt": self._safe_serialize(prompt),
                        "model": model,
                    }

                    # Add optional parameters if present
                    if temperature is not None:
                        request_data["temperature"] = temperature
                    if max_tokens is not None:
                        request_data["max_tokens"] = max_tokens
                    if top_p is not None:
                        request_data["top_p"] = top_p
                    if frequency_penalty is not None:
                        request_data["frequency_penalty"] = frequency_penalty
                    if presence_penalty is not None:
                        request_data["presence_penalty"] = presence_penalty
                    if stop is not None:
                        request_data["stop"] = stop

                    # Security content scanning - format the prompt appropriately
                    prompts = (
                        [{"role": "user", "content": prompt}]
                        if isinstance(prompt, str)
                        else [{"role": "user", "content": p} for p in prompt]
                    )
                    security_info = self._scan_content_security(prompts)

                    # Prepare attributes for the request event
                    request_attributes = {
                        "llm.vendor": "openai",
                        "llm.model": model,
                        "llm.request.type": "completion",
                        "llm.request.data": request_data,
                        "llm.request.timestamp": datetime.now().isoformat(),
                    }

                    # Add model configuration
                    if temperature is not None:
                        request_attributes["llm.request.temperature"] = temperature
                    if max_tokens is not None:
                        request_attributes["llm.request.max_tokens"] = max_tokens
                    if top_p is not None:
                        request_attributes["llm.request.top_p"] = top_p

                    # Add security details if something was detected
                    if security_info["alert_level"] != "none":
                        request_attributes["security.alert_level"] = security_info[
                            "alert_level"
                        ]
                        request_attributes["security.keywords"] = security_info[
                            "keywords"
                        ]

                        # Log security event separately
                        self._log_security_event(security_info, request_data)

                    # Log the request with debug mode info if enabled
                    if self.debug_mode:
                        self.logger.debug(
                            f"Request data: {json.dumps(request_data)[:500]}..."
                        )

                    # Log the request event
                    log_event(
                        name="llm.call.start",
                        attributes=request_attributes,
                        level="INFO",
                        span_id=span_id,
                        trace_id=trace_id,
                    )

                except Exception as e:
                    # If logging fails, log the error but don't disrupt the actual API call
                    self.logger.error(f"Error logging request: {e}")
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")

                # Call the original function and get the result
                try:
                    result = original_completion_create(*args, **kwargs)

                    # Calculate duration
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Log the response safely
                    try:
                        # Extract structured data from the response
                        response_data = self._extract_completion_response_data(result)

                        # Extract model and token usage if available
                        usage = response_data.get("usage", {})

                        # Prepare attributes for the response event
                        response_attributes = {
                            "llm.vendor": "openai",
                            "llm.model": response_data.get("model", model),
                            "llm.response.id": response_data.get("id", ""),
                            "llm.response.type": "completion",
                            "llm.response.timestamp": datetime.now().isoformat(),
                            "llm.response.duration_ms": duration_ms,
                        }

                        # Add content data from response choices
                        choices = response_data.get("choices", [])
                        if choices:
                            first_choice = choices[0]
                            if "text" in first_choice:
                                response_attributes[
                                    "llm.response.content"
                                ] = self._safe_serialize(first_choice["text"])
                            if "finish_reason" in first_choice:
                                response_attributes[
                                    "llm.response.stop_reason"
                                ] = first_choice["finish_reason"]

                        # Add usage statistics if available
                        if usage:
                            if "prompt_tokens" in usage:
                                response_attributes["llm.usage.input_tokens"] = usage[
                                    "prompt_tokens"
                                ]
                            if "completion_tokens" in usage:
                                response_attributes["llm.usage.output_tokens"] = usage[
                                    "completion_tokens"
                                ]
                            if "total_tokens" in usage:
                                response_attributes["llm.usage.total_tokens"] = usage[
                                    "total_tokens"
                                ]
                                
                        # Extract response content for security scanning
                        response_content = ""
                        if "llm.response.content" in response_attributes:
                            content_data = response_attributes["llm.response.content"]
                            if isinstance(content_data, dict) and "content" in content_data:
                                response_content = content_data["content"]
                            elif isinstance(content_data, str):
                                response_content = content_data
                                
                        # If no content was found but we have choices
                        if not response_content and choices:
                            first_choice = choices[0]
                            if isinstance(first_choice, dict):
                                if "text" in first_choice:
                                    response_content = first_choice["text"]
                                    
                        # Scan response content for security concerns
                        if response_content:
                            # Security scanning for response content
                            from cylestio_monitor.security_detection import SecurityScanner
                            scanner = SecurityScanner.get_instance()
                            security_info = scanner.scan_text(response_content)
                            
                            # If security issues found, add to attributes and log a separate event
                            if security_info["alert_level"] != "none":
                                response_attributes["security.alert_level"] = security_info["alert_level"]
                                response_attributes["security.keywords"] = security_info["keywords"]
                                response_attributes["security.category"] = security_info["category"]
                                response_attributes["security.severity"] = security_info["severity"]
                                response_attributes["security.description"] = security_info["description"]
                                
                                # Log security event for response content
                                self._log_security_event(security_info, {"content": response_content[:100] + "..."})
                                
                                # Log warning
                                self.logger.warning(
                                    f"SECURITY ALERT in LLM RESPONSE: {security_info['alert_level'].upper()} content "
                                    f"detected: {security_info['keywords']}"
                                )

                        # Debug logging
                        if self.debug_mode:
                            self.logger.debug(
                                f"Response attributes: {json.dumps(response_attributes)[:500]}..."
                            )

                        # Log the completion of the operation
                        log_event(
                            name="llm.call.finish",
                            attributes=response_attributes,
                            level="INFO",
                            span_id=span_id,
                            trace_id=trace_id,
                        )
                    except Exception as e:
                        # If response logging fails, log the error but don't disrupt the response
                        error_msg = f"Error logging response: {e}"
                        self.logger.error(error_msg)
                        if self.debug_mode:
                            self.logger.error(f"Traceback: {traceback.format_exc()}")

                        # Log a simplified response event to ensure the span is completed
                        log_event(
                            name="llm.call.finish",
                            attributes={
                                "llm.vendor": "openai",
                                "llm.model": model,
                                "llm.response.duration_ms": duration_ms,
                                "error": error_msg,
                            },
                            level="INFO",
                            span_id=span_id,
                            trace_id=trace_id,
                        )

                    # End the span
                    TraceContext.end_span()

                    # Return the original result unchanged
                    return result

                except Exception as e:
                    # Calculate duration up to the error
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Log the error
                    error_msg = f"Error during OpenAI completion call: {str(e)}"
                    self.logger.error(error_msg)
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")

                    # Log the error event
                    log_event(
                        name="llm.call.error",
                        attributes={
                            "llm.vendor": "openai",
                            "llm.model": model,
                            "llm.response.duration_ms": duration_ms,
                            "error.message": str(e),
                            "error.type": e.__class__.__name__,
                        },
                        level="ERROR",
                        span_id=span_id,
                        trace_id=trace_id,
                    )

                    # End the span
                    TraceContext.end_span()

                    # Re-raise the original exception
                    raise

            # Apply the patch
            self.client.completions.create = wrapped_completion_create

        # Mark client as patched
        _patched_clients.add(client_id)
        self.is_patched = True
        self.logger.info("OpenAI client successfully patched")

    def _safe_serialize(self, obj: Any, depth: int = 0, max_depth: int = 10) -> Any:
        """Safely serialize objects to JSON-compatible format, handling recursion and non-serializable types.

        Args:
            obj: The object to serialize
            depth: Current recursion depth
            max_depth: Maximum recursion depth

        Returns:
            A JSON-serializable representation of the object
        """
        if depth > max_depth:
            return "[MAX_DEPTH_EXCEEDED]"

        if obj is None:
            return None

        # Handle basic types
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # Handle lists
        if isinstance(obj, list):
            return [self._safe_serialize(item, depth + 1, max_depth) for item in obj]

        # Handle dictionaries
        if isinstance(obj, dict):
            return {
                str(k): self._safe_serialize(v, depth + 1, max_depth)
                for k, v in obj.items()
            }

        # Handle objects with a to_dict method
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            try:
                return self._safe_serialize(obj.to_dict(), depth + 1, max_depth)
            except Exception:
                pass

        # Handle model objects with a model_dump method (typical for Pydantic v2)
        if hasattr(obj, "model_dump") and callable(obj.model_dump):
            try:
                return self._safe_serialize(obj.model_dump(), depth + 1, max_depth)
            except Exception:
                pass

        # Handle model objects with a dict method (typical for Pydantic v1)
        if hasattr(obj, "dict") and callable(obj.dict):
            try:
                return self._safe_serialize(obj.dict(), depth + 1, max_depth)
            except Exception:
                pass

        # For all other types, convert to string
        try:
            return str(obj)
        except Exception:
            return "[UNSERIALIZABLE]"

    def _scan_content_security(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Scan message content for potential security issues.

        Args:
            messages: List of message objects

        Returns:
            Dictionary with alert level and details
        """
        from cylestio_monitor.security_detection import SecurityScanner
        
        # Get the scanner instance
        scanner = SecurityScanner.get_instance()
        
        # Find the last user message in the conversation
        last_user_message = None
        if isinstance(messages, list):
            for message in reversed(messages):
                if isinstance(message, dict) and message.get("role") == "user":
                    last_user_message = message
                    break
        
        # If we found a last user message, only scan that
        if last_user_message:
            scan_result = scanner.scan_text(last_user_message.get("content", ""))
        else:
            # Fallback to scanning the entire conversation if we can't identify the last user message
            scan_result = scanner.scan_event(messages)
        
        # Map the scanner result to the expected format
        result = {
            "alert_level": scan_result["alert_level"],
            "keywords": scan_result.get("keywords", []),
            "category": scan_result.get("category"),
            "severity": scan_result.get("severity"),
            "description": scan_result.get("description")
        }
        
        # Log the result if it's not "none"
        if result["alert_level"] != "none":
            self.logger.warning(
                f"Security scan detected {result['alert_level']} content: "
                f"category={result['category']}, severity={result['severity']}, "
                f"description='{result['description']}', keywords={result['keywords']}"
            )
            
        return result

    def _log_security_event(
        self, security_info: Dict[str, Any], request_data: Dict[str, Any]
    ) -> None:
        """Log a security event when potentially sensitive content is detected.

        Args:
            security_info: Security scan results
            request_data: The request data being sent
        """
        # Only log if there's something to report
        if security_info["alert_level"] == "none" or not security_info["keywords"]:
            return

        # Create a sanitized version of the request data
        sanitized_data = {"model": request_data.get("model", "unknown")}
        
        # Extract a sample of content for logging
        content_sample = (
            str(request_data)[:100] + "..."
            if len(str(request_data)) > 100
            else str(request_data)
        )
        
        # Mask sensitive data in the content sample
        from cylestio_monitor.security_detection import SecurityScanner
        scanner = SecurityScanner.get_instance()
        masked_content_sample = scanner._pattern_registry.mask_text_in_place(content_sample)
        
        # Create more specific event name based on severity
        event_name = f"security.content.{security_info['alert_level']}"
        
        # Use SECURITY_ALERT level for dangerous content, WARNING for suspicious
        event_level = (
            "SECURITY_ALERT" if security_info["alert_level"] == "dangerous" else "WARNING"
        )

        # Create security attributes
        security_attributes = {
            "security.alert_level": security_info["alert_level"],
            "security.keywords": security_info["keywords"],
            "security.content_sample": masked_content_sample,
            "security.detection_time": datetime.now().isoformat(),
            "llm.vendor": "openai",
            "llm.model": sanitized_data.get("model"),
            "llm.request.timestamp": datetime.now().isoformat(),
        }
        
        # Add new security attributes if available
        if "category" in security_info and security_info["category"]:
            security_attributes["security.category"] = security_info["category"]
        
        if "severity" in security_info and security_info["severity"]:
            security_attributes["security.severity"] = security_info["severity"]
            
        if "description" in security_info and security_info["description"]:
            security_attributes["security.description"] = security_info["description"]

        # Log the security event
        log_event(
            name=event_name,
            attributes=security_attributes,
            level=event_level,
        )

        self.logger.warning(
            f"SECURITY ALERT: {security_info['alert_level'].upper()} content detected: {security_info['keywords']}"
        )

    def _extract_chat_response_data(self, result: Any) -> Dict[str, Any]:
        """Extract structured data from chat completion response.

        Args:
            result: The OpenAI API response

        Returns:
            A dictionary of extracted data
        """
        response_data = {}

        try:
            # Handle different response formats
            if hasattr(result, "model_dump"):
                # Handle Pydantic v2 objects
                raw_data = result.model_dump()
                response_data = self._safe_serialize(raw_data)
            elif hasattr(result, "dict"):
                # Handle Pydantic v1 objects
                raw_data = result.dict()
                response_data = self._safe_serialize(raw_data)
            elif hasattr(result, "to_dict"):
                # Handle objects with to_dict method
                raw_data = result.to_dict()
                response_data = self._safe_serialize(raw_data)
            elif isinstance(result, dict):
                # Handle plain dictionaries
                response_data = self._safe_serialize(result)
            else:
                # Handle objects without standard serialization
                response_data = {
                    "id": getattr(result, "id", "unknown"),
                    "model": getattr(result, "model", "unknown"),
                    "choices": [],
                }

                # Extract choices if available
                if hasattr(result, "choices"):
                    choices = []
                    for choice in result.choices:
                        choice_data = {}

                        # Extract message if available
                        if hasattr(choice, "message"):
                            message = choice.message
                            message_data = {}

                            if hasattr(message, "role"):
                                message_data["role"] = message.role
                            if hasattr(message, "content"):
                                message_data["content"] = message.content

                            choice_data["message"] = message_data

                        # Extract finish reason if available
                        if hasattr(choice, "finish_reason"):
                            choice_data["finish_reason"] = choice.finish_reason

                        choices.append(choice_data)

                    response_data["choices"] = choices

                # Extract usage if available
                if hasattr(result, "usage"):
                    usage = {}
                    if hasattr(result.usage, "prompt_tokens"):
                        usage["prompt_tokens"] = result.usage.prompt_tokens
                    if hasattr(result.usage, "completion_tokens"):
                        usage["completion_tokens"] = result.usage.completion_tokens
                    if hasattr(result.usage, "total_tokens"):
                        usage["total_tokens"] = result.usage.total_tokens

                    response_data["usage"] = usage
        except Exception as e:
            self.logger.error(f"Error extracting response data: {e}")
            # Return minimal data in case of error
            response_data = {
                "id": (
                    getattr(result, "id", "unknown")
                    if hasattr(result, "id")
                    else "unknown"
                ),
                "model": (
                    getattr(result, "model", "unknown")
                    if hasattr(result, "model")
                    else "unknown"
                ),
            }

        return response_data

    def _extract_completion_response_data(self, result: Any) -> Dict[str, Any]:
        """Extract structured data from completion response.

        Args:
            result: The OpenAI API response

        Returns:
            A dictionary of extracted data
        """
        response_data = {}

        try:
            # Handle different response formats
            if hasattr(result, "model_dump"):
                # Handle Pydantic v2 objects
                raw_data = result.model_dump()
                response_data = self._safe_serialize(raw_data)
            elif hasattr(result, "dict"):
                # Handle Pydantic v1 objects
                raw_data = result.dict()
                response_data = self._safe_serialize(raw_data)
            elif hasattr(result, "to_dict"):
                # Handle objects with to_dict method
                raw_data = result.to_dict()
                response_data = self._safe_serialize(raw_data)
            elif isinstance(result, dict):
                # Handle plain dictionaries
                response_data = self._safe_serialize(result)
            else:
                # Handle objects without standard serialization
                response_data = {
                    "id": getattr(result, "id", "unknown"),
                    "model": getattr(result, "model", "unknown"),
                    "choices": [],
                }

                # Extract choices if available
                if hasattr(result, "choices"):
                    choices = []
                    for choice in result.choices:
                        choice_data = {}

                        # Extract text if available
                        if hasattr(choice, "text"):
                            choice_data["text"] = choice.text

                        # Extract finish reason if available
                        if hasattr(choice, "finish_reason"):
                            choice_data["finish_reason"] = choice.finish_reason

                        choices.append(choice_data)

                    response_data["choices"] = choices

                # Extract usage if available
                if hasattr(result, "usage"):
                    usage = {}
                    if hasattr(result.usage, "prompt_tokens"):
                        usage["prompt_tokens"] = result.usage.prompt_tokens
                    if hasattr(result.usage, "completion_tokens"):
                        usage["completion_tokens"] = result.usage.completion_tokens
                    if hasattr(result.usage, "total_tokens"):
                        usage["total_tokens"] = result.usage.total_tokens

                    response_data["usage"] = usage
        except Exception as e:
            self.logger.error(f"Error extracting response data: {e}")
            # Return minimal data in case of error
            response_data = {
                "id": (
                    getattr(result, "id", "unknown")
                    if hasattr(result, "id")
                    else "unknown"
                ),
                "model": (
                    getattr(result, "model", "unknown")
                    if hasattr(result, "model")
                    else "unknown"
                ),
            }

        return response_data

    def unpatch(self) -> None:
        """Remove monitoring patches from OpenAI client."""
        if not self.is_patched:
            return

        # Unpatch chat completions create
        if "chat.completions.create" in self.original_funcs:
            self.client.chat.completions.create = self.original_funcs[
                "chat.completions.create"
            ]

        # Unpatch completions create
        if "completions.create" in self.original_funcs:
            self.client.completions.create = self.original_funcs["completions.create"]

        # Remove from patched clients set
        client_id = id(self.client)
        if client_id in _patched_clients:
            _patched_clients.remove(client_id)

        self.is_patched = False
        self.logger.info("OpenAI client successfully unpatched")

    @classmethod
    def patch_module(cls) -> None:
        """Apply global patches to OpenAI module.

        This method patches the constructor of OpenAI client classes to automatically
        intercept all instances created, without requiring explicit patching.
        """
        global _is_module_patched

        if _is_module_patched:
            return

        logger = logging.getLogger("CylestioMonitor.OpenAI")
        logger.debug("Starting OpenAI module-level patch")

        # Ensure OpenAI is available
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI module not available, skipping module-level patch")
            return

        try:
            # Patch regular OpenAI client
            original_init = OpenAI.__init__
            _original_methods["OpenAI.__init__"] = original_init

            @functools.wraps(original_init)
            def patched_init(self, *args, **kwargs):
                # Call original init
                original_init(self, *args, **kwargs)

                # Automatically patch this instance
                patcher = cls(client=self)
                patcher.patch()

            # Apply the patch
            OpenAI.__init__ = patched_init

            # Patch AsyncOpenAI client if it exists
            if "AsyncOpenAI" in globals():
                async_original_init = AsyncOpenAI.__init__
                _original_methods["AsyncOpenAI.__init__"] = async_original_init

                @functools.wraps(async_original_init)
                def patched_async_init(self, *args, **kwargs):
                    # Call original init
                    async_original_init(self, *args, **kwargs)

                    # Automatically patch this instance
                    patcher = cls(client=self)
                    patcher.patch()

                # Apply the patch
                AsyncOpenAI.__init__ = patched_async_init

            _is_module_patched = True
            logger.info("OpenAI module successfully patched")

        except Exception as e:
            logger.error(f"Error patching OpenAI module: {e}")
            logger.debug(f"Stack trace: {traceback.format_exc()}")

    @classmethod
    def unpatch_module(cls) -> None:
        """Remove global patches from OpenAI module."""
        global _is_module_patched

        if not _is_module_patched:
            return

        logger = logging.getLogger("CylestioMonitor.OpenAI")
        logger.debug("Starting OpenAI module-level unpatch")

        # Ensure OpenAI is available
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI module not available, skipping module-level unpatch")
            return

        try:
            # Restore original OpenAI constructor
            if "OpenAI.__init__" in _original_methods:
                OpenAI.__init__ = _original_methods["OpenAI.__init__"]

            # Restore original AsyncOpenAI constructor
            if (
                "AsyncOpenAI.__init__" in _original_methods
                and "AsyncOpenAI" in globals()
            ):
                AsyncOpenAI.__init__ = _original_methods["AsyncOpenAI.__init__"]

            _is_module_patched = False
            logger.info("OpenAI module successfully unpatched")

        except Exception as e:
            logger.error(f"Error unpatching OpenAI module: {e}")


# Convenience functions for module-level patching/unpatching
def patch_openai_module():
    """Apply patches to OpenAI module."""
    OpenAIPatcher.patch_module()


def unpatch_openai_module():
    """Remove patches from OpenAI module."""
    OpenAIPatcher.unpatch_module()
