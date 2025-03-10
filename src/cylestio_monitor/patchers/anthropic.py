"""Anthropic patcher for monitoring Anthropic API calls."""

import functools
import logging
from typing import Any, Dict, Optional

from anthropic import Anthropic

from ..events_processor import log_event
from .base import BasePatcher


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

        if self.is_patched:
            return

        # Patch messages.create
        original_create = self.client.messages.create
        self.original_funcs["messages.create"] = original_create

        @functools.wraps(original_create)
        def wrapped_create(*args, **kwargs):
            # Log request
            log_event(
                "anthropic_request",
                {
                    "method": "messages.create",
                    "args": str(args),
                    "kwargs": {k: v for k, v in kwargs.items() if k != "api_key"},
                },
                "ANTHROPIC",
            )

            try:
                # Call original function
                result = original_create(*args, **kwargs)

                # Log response
                log_event(
                    "anthropic_response",
                    {"method": "messages.create", "response": result.model_dump()},
                    "ANTHROPIC",
                )

                return result

            except Exception as e:
                # Log error
                log_event(
                    "anthropic_error",
                    {"method": "messages.create", "error": str(e)},
                    "ANTHROPIC",
                    level="error",
                )
                raise

        self.client.messages.create = wrapped_create
        self.is_patched = True

        self.logger.info("Applied Anthropic monitoring patches")

    def unpatch(self) -> None:
        """Remove monitoring patches from Anthropic client."""
        if not self.is_patched:
            return

        # Restore original functions
        if "messages.create" in self.original_funcs:
            self.client.messages.create = self.original_funcs["messages.create"]
            del self.original_funcs["messages.create"]

        self.is_patched = False

        self.logger.info("Removed Anthropic monitoring patches")
