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
from ..utils.event_utils import format_timestamp
from ..utils.trace_context import TraceContext
from .base import BasePatcher

# Import security scanner
from ..security_detection import SecurityScanner

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
        
        # Initialize security scanner
        try:
            self.security_scanner = SecurityScanner.get_instance()
        except Exception as e:
            self.logger.warning(f"Failed to initialize security scanner: {e}")
            self.security_scanner = None

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
                    stream = kwargs.get("stream", False)

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
                    if stream:
                        request_data["stream"] = True

                    # Security content scanning
                    security_info = self._scan_content_security(messages)

                    # Prepare attributes for the request event
                    request_attributes = {
                        "llm.vendor": "openai",
                        "llm.model": model,
                        "llm.request.type": "chat_completion",
                        "llm.request.data": request_data,
                        "llm.request.timestamp": format_timestamp(),
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
                        channel="OPENAI",
                    )

                except Exception as e:
                    # If logging fails, log the error but don't disrupt the actual API call
                    self.logger.error(f"Error logging request: {e}")
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")

                # Call the original function and get the result
                try:
                    result = original_create(*args, **kwargs)

                    # Handle streaming response
                    if stream:
                        return self._wrap_streaming_response(result, span_id, trace_id, model, start_time)

                    # Calculate duration
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Log the response safely
                    try:
                        # Extract structured data from the response
                        response_data = self._extract_chat_response_data(result)

                        # Debug log to check if the usage information is present in the raw response
                        if self.debug_mode:
                            if hasattr(result, "usage"):
                                self.logger.debug(f"Raw OpenAI usage data found: {result.usage}")
                            else:
                                self.logger.debug("No usage data found in OpenAI response")
                            
                            if "usage" in response_data:
                                self.logger.debug(f"Extracted usage data: {response_data['usage']}")
                            else:
                                self.logger.debug("No usage data in extracted response_data")

                        # Extract model and token usage if available
                        usage = response_data.get("usage", {})

                        # Get model from response or fallback to the model from the request
                        response_model = response_data.get("model")
                        if response_model == "unknown" or response_model is None:
                            response_model = model

                        # Prepare attributes for the response event
                        response_attributes = {
                            "llm.vendor": "openai",
                            "llm.model": response_model,
                            "llm.response.id": response_data.get("id", ""),
                            "llm.response.type": "chat_completion",
                            "llm.response.timestamp": format_timestamp(),
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
                        # If no usage data is available, estimate based on model and content length
                        else:
                            # Estimate based on content length for basic tracking
                            content_length = 0
                            if "llm.response.content" in response_attributes:
                                content = response_attributes["llm.response.content"]
                                if isinstance(content, dict) and "content" in content:
                                    content_length = len(content["content"])
                                elif isinstance(content, str):
                                    content_length = len(content)
                            
                            # Use tiktoken if available for more accurate estimation
                            try:
                                import tiktoken
                                enc = tiktoken.encoding_for_model(model)
                                prompt_text = "".join(m["content"] for m in messages if isinstance(m, dict) and "content" in m)
                                input_tokens = len(enc.encode(prompt_text))
                                completion_text = first_choice.get("message", {}).get("content", "") if choices else ""
                                output_tokens = len(enc.encode(completion_text))
                                response_attributes["llm.usage.input_tokens"] = input_tokens
                                response_attributes["llm.usage.output_tokens"] = output_tokens
                                response_attributes["llm.usage.total_tokens"] = input_tokens + output_tokens
                            except ImportError:
                                # Fall back to simple estimation
                                response_attributes["llm.usage.input_tokens"] = int(content_length / 4)
                                response_attributes["llm.usage.output_tokens"] = int(content_length / 4)
                                response_attributes["llm.usage.total_tokens"] = int(content_length / 2)

                        # Log the response event
                        log_event(
                            name="llm.call.end",
                            attributes=response_attributes,
                            level="INFO",
                            span_id=span_id,
                            trace_id=trace_id,
                            channel="OPENAI",
                        )

                    except Exception as e:
                        self.logger.error(f"Error logging response: {e}")
                        if self.debug_mode:
                            self.logger.error(f"Traceback: {traceback.format_exc()}")

                    return result

                except Exception as e:
                    # Log error but don't disrupt the actual API call
                    self.logger.error(f"Error in patched create method: {e}")
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")
                    raise

            # Replace the original method with our wrapper
            self.client.chat.completions.create = wrapped_chat_create

        # Patch Completions create method
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
                    stream = kwargs.get("stream", False)

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
                    if stream:
                        request_data["stream"] = True

                    # Security content scanning
                    security_info = self._scan_content_security([{"content": prompt}])

                    # Prepare attributes for the request event
                    request_attributes = {
                        "llm.vendor": "openai",
                        "llm.model": model,
                        "llm.request.type": "completion",
                        "llm.request.data": request_data,
                        "llm.request.timestamp": format_timestamp(),
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
                        request_attributes["security.alert_level"] = security_info["alert_level"]
                        request_attributes["security.keywords"] = security_info["keywords"]

                        # Log security event separately
                        self._log_security_event(security_info, request_data)

                    # Log the request with debug mode info if enabled
                    if self.debug_mode:
                        self.logger.debug(f"Request data: {json.dumps(request_data)[:500]}...")

                    # Log the request event
                    log_event(
                        name="llm.call.start",
                        attributes=request_attributes,
                        level="INFO",
                        span_id=span_id,
                        trace_id=trace_id,
                        channel="OPENAI",
                    )

                except Exception as e:
                    # If logging fails, log the error but don't disrupt the actual API call
                    self.logger.error(f"Error logging request: {e}")
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")

                # Call the original function and get the result
                try:
                    result = original_completion_create(*args, **kwargs)

                    # Handle streaming response
                    if stream:
                        return self._wrap_streaming_response(result, span_id, trace_id, model, start_time)

                    # Calculate duration
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Log the response safely
                    try:
                        # Extract structured data from the response
                        response_data = self._extract_completion_response_data(result)

                        # Debug log to check if the usage information is present in the raw response
                        if self.debug_mode:
                            if hasattr(result, "usage"):
                                self.logger.debug(f"Raw OpenAI usage data found: {result.usage}")
                            else:
                                self.logger.debug("No usage data found in OpenAI response")
                            
                            if "usage" in response_data:
                                self.logger.debug(f"Extracted usage data: {response_data['usage']}")
                            else:
                                self.logger.debug("No usage data in extracted response_data")

                        # Extract model and token usage if available
                        usage = response_data.get("usage", {})

                        # Get model from response or fallback to the model from the request
                        response_model = response_data.get("model")
                        if response_model == "unknown" or response_model is None:
                            response_model = model

                        # Prepare attributes for the response event
                        response_attributes = {
                            "llm.vendor": "openai",
                            "llm.model": response_model,
                            "llm.response.id": response_data.get("id", ""),
                            "llm.response.type": "completion",
                            "llm.response.timestamp": format_timestamp(),
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
                        # If no usage data is available, estimate based on model and content length
                        else:
                            # Estimate based on content length for basic tracking
                            content_length = 0
                            if "llm.response.content" in response_attributes:
                                content = response_attributes["llm.response.content"]
                                if isinstance(content, str):
                                    content_length = len(content)
                            
                            # Use tiktoken if available for more accurate estimation
                            try:
                                import tiktoken
                                enc = tiktoken.encoding_for_model(model)
                                input_tokens = len(enc.encode(prompt))
                                completion_text = first_choice.get("text", "") if choices else ""
                                output_tokens = len(enc.encode(completion_text))
                                response_attributes["llm.usage.input_tokens"] = input_tokens
                                response_attributes["llm.usage.output_tokens"] = output_tokens
                                response_attributes["llm.usage.total_tokens"] = input_tokens + output_tokens
                            except ImportError:
                                # Fall back to simple estimation
                                response_attributes["llm.usage.input_tokens"] = int(content_length / 4)
                                response_attributes["llm.usage.output_tokens"] = int(content_length / 4)
                                response_attributes["llm.usage.total_tokens"] = int(content_length / 2)

                        # Log the response event
                        log_event(
                            name="llm.call.end",
                            attributes=response_attributes,
                            level="INFO",
                            span_id=span_id,
                            trace_id=trace_id,
                            channel="OPENAI",
                        )

                    except Exception as e:
                        self.logger.error(f"Error logging response: {e}")
                        if self.debug_mode:
                            self.logger.error(f"Traceback: {traceback.format_exc()}")

                    return result

                except Exception as e:
                    # Log error but don't disrupt the actual API call
                    self.logger.error(f"Error in patched create method: {e}")
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")
                    raise

            # Replace the original method with our wrapper
            self.client.completions.create = wrapped_completion_create

        # Patch async methods
        if hasattr(self.client.chat.completions, "acreate"):
            self.logger.debug("Found chat.completions.acreate method to patch")
            original_async_create = self.client.chat.completions.acreate
            self.original_funcs["chat.completions.acreate"] = original_async_create

            async def wrapped_async_chat_create(*args, **kwargs):
                """Async wrapper for OpenAI chat.completions.acreate that logs but doesn't modify behavior."""
                self.logger.debug("Patched chat.completions.acreate method called!")

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
                    stream = kwargs.get("stream", False)

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
                    if stream:
                        request_data["stream"] = True

                    # Security content scanning
                    security_info = self._scan_content_security(messages)

                    # Prepare attributes for the request event
                    request_attributes = {
                        "llm.vendor": "openai",
                        "llm.model": model,
                        "llm.request.type": "chat_completion",
                        "llm.request.data": request_data,
                        "llm.request.timestamp": format_timestamp(),
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
                        channel="OPENAI",
                    )

                except Exception as e:
                    # If logging fails, log the error but don't disrupt the actual API call
                    self.logger.error(f"Error logging request: {e}")
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")

                # Call the original function and get the result
                try:
                    result = await original_async_create(*args, **kwargs)

                    # Handle streaming response
                    if stream:
                        return self._wrap_streaming_response(result, span_id, trace_id, model, start_time)

                    # Calculate duration
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Log the response safely
                    try:
                        # Extract structured data from the response
                        response_data = self._extract_chat_response_data(result)

                        # Debug log to check if the usage information is present in the raw response
                        if self.debug_mode:
                            if hasattr(result, "usage"):
                                self.logger.debug(f"Raw OpenAI usage data found: {result.usage}")
                            else:
                                self.logger.debug("No usage data found in OpenAI response")
                            
                            if "usage" in response_data:
                                self.logger.debug(f"Extracted usage data: {response_data['usage']}")
                            else:
                                self.logger.debug("No usage data in extracted response_data")

                        # Extract model and token usage if available
                        usage = response_data.get("usage", {})

                        # Get model from response or fallback to the model from the request
                        response_model = response_data.get("model")
                        if response_model == "unknown" or response_model is None:
                            response_model = model

                        # Prepare attributes for the response event
                        response_attributes = {
                            "llm.vendor": "openai",
                            "llm.model": response_model,
                            "llm.response.id": response_data.get("id", ""),
                            "llm.response.type": "chat_completion",
                            "llm.response.timestamp": format_timestamp(),
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
                        # If no usage data is available, estimate based on model and content length
                        else:
                            # Estimate based on content length for basic tracking
                            content_length = 0
                            if "llm.response.content" in response_attributes:
                                content = response_attributes["llm.response.content"]
                                if isinstance(content, dict) and "content" in content:
                                    content_length = len(content["content"])
                                elif isinstance(content, str):
                                    content_length = len(content)
                            
                            # Use tiktoken if available for more accurate estimation
                            try:
                                import tiktoken
                                enc = tiktoken.encoding_for_model(model)
                                prompt_text = "".join(m["content"] for m in messages if isinstance(m, dict) and "content" in m)
                                input_tokens = len(enc.encode(prompt_text))
                                completion_text = first_choice.get("message", {}).get("content", "") if choices else ""
                                output_tokens = len(enc.encode(completion_text))
                                response_attributes["llm.usage.input_tokens"] = input_tokens
                                response_attributes["llm.usage.output_tokens"] = output_tokens
                                response_attributes["llm.usage.total_tokens"] = input_tokens + output_tokens
                            except ImportError:
                                # Fall back to simple estimation
                                response_attributes["llm.usage.input_tokens"] = int(content_length / 4)
                                response_attributes["llm.usage.output_tokens"] = int(content_length / 4)
                                response_attributes["llm.usage.total_tokens"] = int(content_length / 2)

                        # Log the response event
                        log_event(
                            name="llm.call.end",
                            attributes=response_attributes,
                            level="INFO",
                            span_id=span_id,
                            trace_id=trace_id,
                            channel="OPENAI",
                        )

                    except Exception as e:
                        self.logger.error(f"Error logging response: {e}")
                        if self.debug_mode:
                            self.logger.error(f"Traceback: {traceback.format_exc()}")

                    return result

                except Exception as e:
                    # Log error but don't disrupt the actual API call
                    self.logger.error(f"Error in patched create method: {e}")
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")
                    raise

            # Replace the original method with our wrapper
            self.client.chat.completions.acreate = wrapped_async_chat_create

        # Patch async completions
        if hasattr(self.client.completions, "acreate"):
            self.logger.debug("Found completions.acreate method to patch")
            original_async_completion_create = self.client.completions.acreate
            self.original_funcs["completions.acreate"] = original_async_completion_create

            async def wrapped_async_completion_create(*args, **kwargs):
                """Async wrapper for OpenAI completions.acreate that logs but doesn't modify behavior."""
                self.logger.debug("Patched completions.acreate method called!")

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
                    stream = kwargs.get("stream", False)

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
                    if stream:
                        request_data["stream"] = True

                    # Security content scanning
                    security_info = self._scan_content_security([{"content": prompt}])

                    # Prepare attributes for the request event
                    request_attributes = {
                        "llm.vendor": "openai",
                        "llm.model": model,
                        "llm.request.type": "completion",
                        "llm.request.data": request_data,
                        "llm.request.timestamp": format_timestamp(),
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
                        channel="OPENAI",
                    )

                except Exception as e:
                    # If logging fails, log the error but don't disrupt the actual API call
                    self.logger.error(f"Error logging request: {e}")
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")

                # Call the original function and get the result
                try:
                    result = await original_async_completion_create(*args, **kwargs)

                    # Handle streaming response
                    if stream:
                        return self._wrap_streaming_response(result, span_id, trace_id, model, start_time)

                    # Calculate duration
                    duration_ms = int((time.time() - start_time) * 1000)

                    # Log the response safely
                    try:
                        # Extract structured data from the response
                        response_data = self._extract_completion_response_data(result)

                        # Debug log to check if the usage information is present in the raw response
                        if self.debug_mode:
                            if hasattr(result, "usage"):
                                self.logger.debug(f"Raw OpenAI usage data found: {result.usage}")
                            else:
                                self.logger.debug("No usage data found in OpenAI response")
                            
                            if "usage" in response_data:
                                self.logger.debug(f"Extracted usage data: {response_data['usage']}")
                            else:
                                self.logger.debug("No usage data in extracted response_data")

                        # Extract model and token usage if available
                        usage = response_data.get("usage", {})

                        # Get model from response or fallback to the model from the request
                        response_model = response_data.get("model")
                        if response_model == "unknown" or response_model is None:
                            response_model = model

                        # Prepare attributes for the response event
                        response_attributes = {
                            "llm.vendor": "openai",
                            "llm.model": response_model,
                            "llm.response.id": response_data.get("id", ""),
                            "llm.response.type": "completion",
                            "llm.response.timestamp": format_timestamp(),
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
                        # If no usage data is available, estimate based on model and content length
                        else:
                            # Estimate based on content length for basic tracking
                            content_length = 0
                            if "llm.response.content" in response_attributes:
                                content = response_attributes["llm.response.content"]
                                if isinstance(content, str):
                                    content_length = len(content)
                            
                            # Use tiktoken if available for more accurate estimation
                            try:
                                import tiktoken
                                enc = tiktoken.encoding_for_model(model)
                                input_tokens = len(enc.encode(prompt))
                                completion_text = first_choice.get("text", "") if choices else ""
                                output_tokens = len(enc.encode(completion_text))
                                response_attributes["llm.usage.input_tokens"] = input_tokens
                                response_attributes["llm.usage.output_tokens"] = output_tokens
                                response_attributes["llm.usage.total_tokens"] = input_tokens + output_tokens
                            except ImportError:
                                # Fall back to simple estimation
                                response_attributes["llm.usage.input_tokens"] = int(content_length / 4)
                                response_attributes["llm.usage.output_tokens"] = int(content_length / 4)
                                response_attributes["llm.usage.total_tokens"] = int(content_length / 2)

                        # Log the response event
                        log_event(
                            name="llm.call.end",
                            attributes=response_attributes,
                            level="INFO",
                            span_id=span_id,
                            trace_id=trace_id,
                            channel="OPENAI",
                        )

                    except Exception as e:
                        self.logger.error(f"Error logging response: {e}")
                        if self.debug_mode:
                            self.logger.error(f"Traceback: {traceback.format_exc()}")

                    return result

                except Exception as e:
                    # Log error but don't disrupt the actual API call
                    self.logger.error(f"Error in patched create method: {e}")
                    if self.debug_mode:
                        self.logger.error(f"Traceback: {traceback.format_exc()}")
                    raise

            # Replace the original method with our wrapper
            self.client.completions.acreate = wrapped_async_completion_create

        # Mark client as patched
        _patched_clients.add(client_id)
        self.is_patched = True
        self.logger.debug("Successfully patched OpenAI client")

    def _wrap_streaming_response(self, response, span_id, trace_id, model, start_time):
        """Wrap a streaming response to accumulate token counts and log final totals.

        Args:
            response: The streaming response from OpenAI
            span_id: The span ID for this operation
            trace_id: The trace ID for this operation
            model: The model used for the request
            start_time: The start time of the request

        Returns:
            A context manager that yields a wrapped streaming response
        """
        class StreamingResponseWrapper:
            def __init__(self, response, span_id, trace_id, model, start_time):
                self.response = response
                self.span_id = span_id
                self.trace_id = trace_id
                self.model = model
                self.start_time = start_time
                self.accumulated_content = ""
                self.accumulated_tokens = 0

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                duration_ms = int((time.time() - self.start_time) * 1000)
                log_event(
                    name="llm.call.end",
                    attributes={
                        "llm.vendor": "openai",
                        "llm.model": self.model,
                        "llm.response.type": "streaming_completion",
                        "llm.response.timestamp": format_timestamp(),
                        "llm.response.duration_ms": duration_ms,
                        "llm.response.content": self.accumulated_content,
                        "llm.usage.output_tokens": self.accumulated_tokens,
                        "llm.usage.input_tokens": len(self.accumulated_content) // 4,
                        "llm.usage.total_tokens": self.accumulated_tokens + (len(self.accumulated_content) // 4),
                    },
                    level="INFO",
                    span_id=self.span_id,
                    trace_id=self.trace_id,
                    channel="OPENAI",
                )

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                duration_ms = int((time.time() - self.start_time) * 1000)
                log_event(
                    name="llm.call.end",
                    attributes={
                        "llm.vendor": "openai",
                        "llm.model": self.model,
                        "llm.response.type": "streaming_completion",
                        "llm.response.timestamp": format_timestamp(),
                        "llm.response.duration_ms": duration_ms,
                        "llm.response.content": self.accumulated_content,
                        "llm.usage.output_tokens": self.accumulated_tokens,
                        "llm.usage.input_tokens": len(self.accumulated_content) // 4,
                        "llm.usage.total_tokens": self.accumulated_tokens + (len(self.accumulated_content) // 4),
                    },
                    level="INFO",
                    span_id=self.span_id,
                    trace_id=self.trace_id,
                    channel="OPENAI",
                )

            async def __aiter__(self):
                async for chunk in self.response:
                    if hasattr(chunk, "choices") and chunk.choices:
                        for choice in chunk.choices:
                            if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                                content = choice.delta.content
                                if content:
                                    self.accumulated_content += content
                                    self.accumulated_tokens += len(content) // 4
                    yield chunk

            def __iter__(self):
                for chunk in self.response:
                    if hasattr(chunk, "choices") and chunk.choices:
                        for choice in chunk.choices:
                            if hasattr(choice, "delta") and hasattr(choice.delta, "content"):
                                content = choice.delta.content
                                if content:
                                    self.accumulated_content += content
                                    self.accumulated_tokens += len(content) // 4
                    yield chunk

        return StreamingResponseWrapper(response, span_id, trace_id, model, start_time)

    def _safe_serialize(self, obj: Any, depth: int = 0, max_depth: int = 10) -> Any:
        """Safely serialize an object to a JSON-compatible format.

        Args:
            obj: Object to serialize
            depth: Current recursion depth
            max_depth: Maximum recursion depth

        Returns:
            JSON-compatible object
        """
        if depth > max_depth:
            return "[Max depth exceeded]"

        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            return {k: self._safe_serialize(v, depth + 1, max_depth) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._safe_serialize(item, depth + 1, max_depth) for item in obj]
        elif hasattr(obj, "model_dump"):
                return self._safe_serialize(obj.model_dump(), depth + 1, max_depth)
        elif hasattr(obj, "to_dict"):
            return self._safe_serialize(obj.to_dict(), depth + 1, max_depth)
        else:
            return str(obj)

    def _scan_content_security(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Scan content for security issues.

        Args:
            messages: List of messages to scan

        Returns:
            Dict with security scan results
        """
        try:
            if not self.security_scanner:
                return {"alert_level": "none", "keywords": []}

            # Find the latest user message to scan - avoid rescanning history
            latest_message = None
            if isinstance(messages, list) and messages:
                # For single prompt input (common in completions API)
                if len(messages) == 1 and not isinstance(messages[0], dict):
                    latest_message = {"content": messages[0]}
                # For chat completions, get the last user message
                else:
                    for message in reversed(messages):
                        if isinstance(message, dict) and message.get("role") == "user":
                            latest_message = message
                            break

            # If we found a message to scan
            if latest_message:
                if isinstance(latest_message, dict):
                    content = latest_message.get("content", "")
                else:
                    content = getattr(latest_message, "content", "")

                if content:
                    # Scan just the latest message
                    scan_result = self.security_scanner.scan_text(content)
                    if scan_result["alert_level"] != "none":
                        return scan_result

            return {"alert_level": "none", "keywords": []}
        except Exception as e:
            self.logger.error(f"Error scanning content security: {e}")
            if self.debug_mode:
                self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {"alert_level": "none", "keywords": []}

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
        scanner = SecurityScanner.get_instance()
        masked_content_sample = scanner._pattern_registry.mask_text_in_place(content_sample)
        
        # Create more specific event name based on severity
        event_name = f"security.content.{security_info['alert_level']}"
        
        # Use SECURITY_ALERT level for dangerous content, WARNING for suspicious
        event_level = (
            "SECURITY_ALERT" if security_info["alert_level"] == "dangerous" else "WARNING"
        )

        # Generate a unique timestamp for this alert
        detection_timestamp = format_timestamp()
        
        # Generate a unique message ID based on timestamp and keywords
        import hashlib
        alert_hash = hashlib.md5(f"{detection_timestamp}-{'-'.join(security_info['keywords'])}".encode()).hexdigest()[:8]
        message_id = f"security-{alert_hash}"

        # Create security attributes
        security_attributes = {
            "security.alert_level": security_info["alert_level"],
            "security.keywords": security_info["keywords"],
            "security.content_sample": masked_content_sample,
            "security.detection_time": detection_timestamp,
            "security.message_id": message_id,
            "llm.vendor": "openai",
            "llm.model": sanitized_data.get("model"),
            "llm.request.timestamp": format_timestamp(),
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
            f"SECURITY ALERT {message_id}: {security_info['alert_level'].upper()} content detected: {security_info['keywords']}"
        )

    def _extract_chat_response_data(self, response):
        """Extract relevant data from a chat completion response.

        Args:
            response: The response from OpenAI

        Returns:
            Dict: Extracted response data
        """
        try:
            if not response:
                return {}

            data = {
                "model": getattr(response, "model", None),
                "created": getattr(response, "created", None),
                "usage": getattr(response, "usage", {}),
                "choices": [],
            }

            if hasattr(response, "choices"):
                for choice in response.choices:
                    choice_data = {
                        "index": getattr(choice, "index", None),
                        "finish_reason": getattr(choice, "finish_reason", None),
                        "message": {},
                    }

                    if hasattr(choice, "message"):
                        message = choice.message
                        choice_data["message"] = {
                            "role": getattr(message, "role", None),
                            "content": getattr(message, "content", None),
                            "function_call": getattr(message, "function_call", None),
                        }

                    data["choices"].append(choice_data)

            return data
        except Exception as e:
            self.logger.error(f"Error extracting chat response data: {e}")
            if self.debug_mode:
                self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {}

    def _extract_completion_response_data(self, response):
        """Extract structured data from OpenAI completion response.

        Args:
            response: OpenAI response object

        Returns:
            Dict: Structured response data
        """
        try:
            # Convert OpenAIObject to dict if needed
            if hasattr(response, "model_dump"):
                data = response.model_dump()
            elif hasattr(response, "to_dict"):
                data = response.to_dict()
            else:
                data = response

            # Extract usage data - try both attribute and dict access
            usage = {}
            if hasattr(response, "usage"):
                usage = response.usage
            elif "usage" in data:
                usage = data["usage"]
            elif hasattr(response, "usage") and hasattr(response.usage, "model_dump"):
                usage = response.usage.model_dump()
            elif hasattr(response, "usage") and hasattr(response.usage, "to_dict"):
                usage = response.usage.to_dict()

            # Extract choices data
            choices = []
            if hasattr(response, "choices"):
                choices = response.choices
            elif "choices" in data:
                choices = data["choices"]

            # Extract model
            model = getattr(response, "model", None) or data.get("model", "unknown")

            # Extract id
            response_id = getattr(response, "id", None) or data.get("id", "")

            return {
                "id": response_id,
                "model": model,
                "choices": choices,
                "usage": usage,
            }

        except Exception as e:
            self.logger.error(f"Error extracting completion response data: {e}")
            if self.debug_mode:
                self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "id": "",
                "model": "unknown",
                "choices": [],
                "usage": {},
            }

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
