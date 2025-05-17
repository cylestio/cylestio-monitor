"""LLM Output Patcher for Cylestio Monitor.

This module provides patching to monitor LLM output being printed to the console/terminal,
allowing detection and masking of sensitive data that might be missed by other patchers.
"""

import sys
import logging
import builtins
import re
from typing import Any, Dict, List, Optional, Callable

from cylestio_monitor.patchers.base import BasePatcher
from cylestio_monitor.security_detection.scanner import SecurityScanner
from cylestio_monitor.utils.event_logging import log_event, log_warning
from cylestio_monitor.config import ConfigManager

logger = logging.getLogger("CylestioMonitor")

# Store the original print function
_original_print = builtins.print

# Store whether the patcher is active
_print_patched = False

# Store whether to enforce masking
_enforce_masking = False

# ANSI color codes
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"

# Protection messages
PROTECTED_MSG = f"{GREEN}[MASKED AND PROTECTED BY CYLESTIO]{RESET}"
EXPOSED_MSG = f"{RED}[SENSITIVE DATA EXPOSED]{RESET}"


class LLMOutputPatcher(BasePatcher):
    """Patcher for monitoring LLM output printed to terminal."""

    def __init__(self, config_manager: Optional[ConfigManager] = None, enforce_masking: bool = False):
        """Initialize the patcher.

        Args:
            config_manager: Optional ConfigManager instance
            enforce_masking: Whether to mask sensitive data in terminal output
        """
        super().__init__(config_manager)
        self.logger = logging.getLogger("CylestioMonitor.Patchers.LLMOutput")
        self.scanner = SecurityScanner.get_instance(config_manager)
        self.enforce_masking = enforce_masking

        # Compile regex patterns for credit card numbers and SSNs
        self.cc_pattern = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
        self.ssn_pattern = re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b')

        # Sensitive data keywords to check in output
        self.sensitive_keywords = [
            "credit card", "creditcard", "credit-card", "cc number",
            "ssn", "social security", "social-security", "social security number"
        ]

    def _enhance_masking(self, text: str) -> str:
        """Apply enhanced masking with protection message.

        This method:
        1. Fully masks credit card numbers as ****-****-****-****
        2. Adds a protection message after masked content for sensitive data

        Args:
            text: The text that may have been already masked

        Returns:
            Enhanced masked text with protection message
        """
        # Check if the text contains partially masked credit card
        cc_partial_mask = re.compile(r'\b\d{4}-\*{4}-\*{4}-\d{4}\b')
        ssn_mask = re.compile(r'\b\*{3}-\*{2}-\d{4}\b')

        # Replace partially masked credit cards with fully masked ones
        if cc_partial_mask.search(text):
            text = cc_partial_mask.sub("****-****-****-****", text)

        # Replace partially masked SSNs with fully masked ones
        if ssn_mask.search(text):
            text = ssn_mask.sub("***-**-****", text)

        # Check if the text contains masked content (stars)
        contains_masks = "****" in text or "***" in text

        # Always add protection message when there are masks in the text in enforce mode
        if contains_masks and PROTECTED_MSG not in text and _enforce_masking:
            text = f"{text} {PROTECTED_MSG}"

        return text

    def patch(self) -> bool:
        """Apply print function patching to monitor terminal output.

        Returns:
            bool: True if successful, False otherwise
        """
        global _print_patched, _enforce_masking

        if _print_patched:
            self.logger.info("Terminal output monitoring already enabled")
            return True

        try:
            # Store original function
            global _original_print
            _original_print = builtins.print

            # Store masking setting
            _enforce_masking = self.enforce_masking

            # Define our patched print function
            def patched_print(*args, **kwargs):
                """Patched print function that scans output for sensitive data.

                This function will:
                1. Check if the output contains sensitive data like credit cards or SSNs
                2. If enforce_masking is True, mask sensitive data
                3. If enforce_masking is False, alert but don't mask
                4. Log a security event if sensitive data is detected
                5. Pass the output (masked or not) to the original print function
                """
                # Skip empty calls or non-string content
                if not args:
                    return _original_print(*args, **kwargs)

                # Get scanner instance
                scanner = SecurityScanner.get_instance()

                # Process all args
                processed_args = []
                for arg in args:
                    if isinstance(arg, str):
                        # Check for sensitive data patterns in strings
                        original_text = arg

                        # Always check for sensitive data, even if not masking
                        matches = scanner._pattern_registry.scan_text(original_text)

                        # Filter matches to only include sensitive_data category
                        sensitive_matches = [m for m in matches if m.get("category") == "sensitive_data"]

                        # Only process if there are sensitive matches (skip for private data)
                        if sensitive_matches:
                            if _enforce_masking:
                                # Apply masking for sensitive matches when enforcing
                                masked_text = scanner._pattern_registry.mask_text_in_place(original_text)
                                enhanced_masked_text = self._enhance_masking(masked_text)
                                processed_args.append(enhanced_masked_text)

                                # Log MEDIUM severity alert for masked sensitive data
                                for match in sensitive_matches:
                                    log_warning(
                                        name="security.sensitive_data.terminal_output",
                                        attributes={
                                            "security.category": "sensitive_data",
                                            "security.severity": "medium",
                                            "security.pattern_name": match.get("pattern_name", "unknown"),
                                            "security.description": f"Sensitive data ({match.get('pattern_name', 'unknown')}) detected and masked in terminal output"
                                        }
                                    )
                            else:
                                # Don't mask data if not enforced, just add warning message
                                processed_args.append(f"{original_text} {EXPOSED_MSG}")

                                # Log HIGH severity alert for exposed sensitive data
                                for match in sensitive_matches:
                                    log_warning(
                                        name="security.sensitive_data.terminal_output",
                                        attributes={
                                            "security.category": "sensitive_data",
                                            "security.severity": "high",
                                            "security.pattern_name": match.get("pattern_name", "unknown"),
                                            "security.description": f"Sensitive data ({match.get('pattern_name', 'unknown')}) EXPOSED in terminal output"
                                        }
                                    )
                        else:
                            # No sensitive matches found - use original text
                            processed_args.append(arg)
                    elif isinstance(arg, dict):
                        # Handle dictionaries - convert to string, mask if enforced
                        if _enforce_masking:
                            masked_dict = self._mask_dict_values(arg, scanner)
                            processed_args.append(masked_dict)
                        else:
                            # Check for sensitive data in dict without masking
                            has_sensitive = self._check_dict_for_sensitive(arg, scanner)
                            processed_args.append(arg)

                            # Add warning if sensitive data found but not masked
                            if has_sensitive:
                                kwargs.setdefault('end', '\n')
                                _original_print(EXPOSED_MSG, **kwargs)
                    else:
                        processed_args.append(arg)

                # Call the original print with processed args
                return _original_print(*processed_args, **kwargs)

            # Apply the patch
            builtins.print = patched_print
            _print_patched = True

            masking_status = "with masking enabled" if self.enforce_masking else "in detection-only mode"
            self.logger.info(f"Terminal output monitoring enabled {masking_status}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to patch terminal output: {e}")
            return False

    def _check_dict_for_sensitive(self, data: dict, scanner) -> bool:
        """Recursively check if a dictionary contains sensitive values.

        Args:
            data: Dictionary that may contain sensitive values
            scanner: SecurityScanner instance

        Returns:
            True if sensitive data found, False otherwise
        """
        found_sensitive = False
        for key, value in data.items():
            if isinstance(value, str):
                # Check for sensitive data in string values
                matches = scanner._pattern_registry.scan_text(value)

                # Filter to only include sensitive_data category
                sensitive_matches = [m for m in matches if m.get("category") == "sensitive_data"]

                if sensitive_matches:
                    # Log HIGH severity alert for exposed sensitive data
                    for match in sensitive_matches:
                        log_warning(
                            name="security.sensitive_data.terminal_output",
                            attributes={
                                "security.category": "sensitive_data",
                                "security.severity": "high",
                                "security.pattern_name": match.get("pattern_name", "unknown"),
                                "security.description": f"Sensitive data ({match.get('pattern_name', 'unknown')}) EXPOSED in nested data"
                            }
                        )
                    found_sensitive = True
            elif isinstance(value, dict):
                # Recursively check nested dictionaries
                if self._check_dict_for_sensitive(value, scanner):
                    found_sensitive = True
            elif isinstance(value, list):
                # Check lists of values
                for item in value:
                    if isinstance(item, dict) and self._check_dict_for_sensitive(item, scanner):
                        found_sensitive = True
                    elif isinstance(item, str):
                        matches = scanner._pattern_registry.scan_text(item)
                        sensitive_matches = [m for m in matches if m.get("category") == "sensitive_data"]
                        if sensitive_matches:
                            found_sensitive = True
        return found_sensitive

    def _mask_dict_values(self, data: dict, scanner) -> dict:
        """Recursively mask sensitive values in a dictionary.

        Args:
            data: Dictionary that may contain sensitive values
            scanner: SecurityScanner instance

        Returns:
            Dictionary with masked sensitive values
        """
        # Only mask when enforce_masking is True
        if not _enforce_masking:
            # In non-enforce mode, just check for sensitive data but don't mask
            has_sensitive = self._check_dict_for_sensitive(data, scanner)
            return data

        # In enforce mode, mask sensitive data
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Check for sensitive data in string values
                masked_value = scanner._pattern_registry.mask_text_in_place(value)
                if masked_value != value:
                    # Apply enhanced masking
                    masked_value = self._enhance_masking(masked_value)
                    result[key] = masked_value

                    # Only log security events for sensitive_data category
                    matches = scanner._pattern_registry.scan_text(value)
                    sensitive_matches = [m for m in matches if m.get("category") == "sensitive_data"]

                    for match in sensitive_matches:
                        log_warning(
                            name="security.sensitive_data.terminal_output",
                            attributes={
                                "security.category": "sensitive_data",
                                "security.severity": "medium",
                                "security.pattern_name": match.get("pattern_name", "unknown"),
                                "security.description": f"Sensitive data ({match.get('pattern_name', 'unknown')}) detected and masked in nested data"
                            }
                        )
                else:
                    result[key] = value
            elif isinstance(value, dict):
                # Recursively process nested dictionaries
                result[key] = self._mask_dict_values(value, scanner)
            elif isinstance(value, list):
                # Process lists of values
                result[key] = [
                    self._mask_dict_values(item, scanner) if isinstance(item, dict)
                    else scanner._pattern_registry.mask_text_in_place(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def unpatch(self) -> bool:
        """Remove print function patching.

        Returns:
            bool: True if successful, False otherwise
        """
        global _print_patched

        if not _print_patched:
            self.logger.info("Terminal output monitoring not enabled")
            return True

        try:
            # Restore original function
            global _original_print
            builtins.print = _original_print
            _print_patched = False

            self.logger.info("Terminal output monitoring disabled")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unpatch terminal output: {e}")
            return False


def patch_terminal_output(enable_monitoring: bool = True, enforce_masking: bool = False) -> bool:
    """Apply terminal output monitoring.

    Args:
        enable_monitoring: Whether to enable monitoring
        enforce_masking: Whether to mask sensitive data (True) or just alert (False)

    Returns:
        bool: True if successful, False otherwise
    """
    global _print_patched

    if _print_patched:
        logger.info("Terminal output monitoring already enabled")
        return True

    try:
        # Create and apply the patcher
        patcher = LLMOutputPatcher(enforce_masking=enforce_masking)
        success = patcher.patch()

        if success and enable_monitoring:
            masking_status = "with masking enabled" if enforce_masking else "in detection-only mode"
            logger.info(f"Terminal output monitoring enabled {masking_status}")
        return success

    except Exception as e:
        logger.error(f"Failed to patch terminal output: {e}")
        return False


def unpatch_terminal_output() -> bool:
    """Remove terminal output monitoring.

    Returns:
        bool: True if successful, False otherwise
    """
    global _print_patched

    if not _print_patched:
        logger.info("Terminal output monitoring not enabled")
        return True

    try:
        # Create patcher and unpatch
        patcher = LLMOutputPatcher()
        success = patcher.unpatch()

        if success:
            logger.info("Terminal output monitoring disabled")
        return success

    except Exception as e:
        logger.error(f"Failed to unpatch terminal output: {e}")
        return False
