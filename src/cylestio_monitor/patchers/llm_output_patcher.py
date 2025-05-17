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

# ANSI color codes
GREEN = "\033[32m"
RESET = "\033[0m"

# Protection message
PROTECTION_MSG = f"{GREEN}[MASKED AND PROTECTED BY CYLESTIO]{RESET}"


class LLMOutputPatcher(BasePatcher):
    """Patcher for monitoring LLM output printed to terminal."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the patcher.

        Args:
            config_manager: Optional ConfigManager instance
        """
        super().__init__(config_manager)
        self.logger = logging.getLogger("CylestioMonitor.Patchers.LLMOutput")
        self.scanner = SecurityScanner.get_instance(config_manager)
        
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
        2. Adds a protection message after masked content
        
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
        
        # Always add protection message for any masked content
        if (("****" in text or "***" in text) and PROTECTION_MSG not in text):
            text = f"{text} {PROTECTION_MSG}"
            
        return text

    def patch(self) -> bool:
        """Apply print function patching to monitor terminal output.

        Returns:
            bool: True if successful, False otherwise
        """
        global _print_patched

        if _print_patched:
            self.logger.info("Terminal output monitoring already enabled")
            return True

        try:
            # Store original function
            global _original_print
            _original_print = builtins.print

            # Define our patched print function
            def patched_print(*args, **kwargs):
                """Patched print function that scans output for sensitive data.
                
                This function will:
                1. Check if the output contains sensitive data like credit cards or SSNs
                2. Mask any sensitive data found
                3. Add a protection message after masked content
                4. Log a security event if sensitive data is detected
                5. Pass the masked output to the original print function
                """
                # Skip empty calls or non-string content
                if not args:
                    return _original_print(*args, **kwargs)
                
                # Get scanner instance
                scanner = SecurityScanner.get_instance()
                
                # Process all args
                processed_args = []
                sensitive_data_found = False
                for arg in args:
                    if isinstance(arg, str):
                        # Check for sensitive data patterns in strings
                        original_text = arg
                        masked_text = scanner._pattern_registry.mask_text_in_place(original_text)
                        
                        # If masking changed the text, sensitive data was found
                        if masked_text != original_text:
                            sensitive_data_found = True
                            
                            # Apply enhanced masking and add protection message
                            enhanced_masked_text = self._enhance_masking(masked_text)
                            processed_args.append(enhanced_masked_text)
                            
                            # Log a security event
                            matches = scanner._pattern_registry.scan_text(original_text)
                            for match in matches:
                                log_warning(
                                    name="security.sensitive_data.terminal_output",
                                    attributes={
                                        "security.category": "sensitive_data",
                                        "security.severity": "high",
                                        "security.pattern_name": match.get("pattern_name", "unknown"),
                                        "security.description": f"Sensitive data ({match.get('pattern_name', 'unknown')}) detected in terminal output"
                                    }
                                )
                        else:
                            processed_args.append(arg)
                    elif isinstance(arg, dict):
                        # Handle dictionaries - convert to string, mask, then convert back
                        masked_dict = self._mask_dict_values(arg, scanner)
                        processed_args.append(masked_dict)
                    else:
                        processed_args.append(arg)
                
                # Call the original print with processed args
                return _original_print(*processed_args, **kwargs)

            # Apply the patch
            builtins.print = patched_print
            _print_patched = True
            
            self.logger.info("Terminal output monitoring enabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to patch terminal output: {e}")
            return False

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

    def _mask_dict_values(self, data: dict, scanner) -> dict:
        """Recursively mask sensitive values in a dictionary.
        
        Args:
            data: Dictionary that may contain sensitive values
            scanner: SecurityScanner instance
            
        Returns:
            Dictionary with masked sensitive values
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Check for sensitive data in string values
                masked_value = scanner._pattern_registry.mask_text_in_place(value)
                if masked_value != value:
                    # Apply enhanced masking
                    masked_value = self._enhance_masking(masked_value)
                    result[key] = masked_value
                    
                    # Log a security event
                    matches = scanner._pattern_registry.scan_text(value)
                    for match in matches:
                        log_warning(
                            name="security.sensitive_data.terminal_output",
                            attributes={
                                "security.category": "sensitive_data",
                                "security.severity": "high",
                                "security.pattern_name": match.get("pattern_name", "unknown"),
                                "security.description": f"Sensitive data ({match.get('pattern_name', 'unknown')}) detected in nested data"
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


def patch_terminal_output(enable_monitoring: bool = True) -> bool:
    """Apply terminal output monitoring.

    Args:
        enable_monitoring: Whether to enable monitoring

    Returns:
        bool: True if successful, False otherwise
    """
    global _print_patched

    if _print_patched:
        logger.info("Terminal output monitoring already enabled")
        return True

    try:
        # Create and apply the patcher
        patcher = LLMOutputPatcher()
        success = patcher.patch()
        
        if success and enable_monitoring:
            logger.info("Terminal output monitoring enabled")
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