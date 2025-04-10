"""
Pattern registry for security detection.

This module provides a thread-safe registry of compiled regex patterns
for security scanning, with patterns compiled once at load time for performance.
"""

import logging
import re
import threading
from typing import Dict, List, Any, Optional, Pattern

from cylestio_monitor.config import ConfigManager

logger = logging.getLogger("CylestioMonitor.Security")


class PatternRegistry:
    """Thread-safe registry of compiled regex patterns for security scanning."""
    
    # Class-level lock for thread safety during initialization
    _init_lock = threading.RLock()
    
    # Singleton instance
    _instance: Optional["PatternRegistry"] = None
    
    # Compiled patterns - immutable after initialization
    _patterns: Dict[str, Dict[str, Any]] = {}
    
    # Flags for initialization state
    _is_initialized = False

    def __new__(cls, config_manager=None):
        """Create or return the singleton instance with thread safety."""
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super(PatternRegistry, cls).__new__(cls)
                cls._instance._initialize(config_manager)
            return cls._instance

    def _initialize(self, config_manager=None):
        """Initialize the pattern registry with thread safety.
        
        Args:
            config_manager: Optional ConfigManager instance
        """
        if self._is_initialized:
            return
            
        with self._init_lock:
            if self._is_initialized:  # Double-check pattern for thread safety
                return
                
            # Use provided config manager or create a new one
            self.config_manager = config_manager or ConfigManager()
            
            # Load patterns from config and compile them
            self._load_and_compile_patterns()
            
            # Mark as initialized
            self._is_initialized = True
            logger.info("Pattern registry initialized with compiled patterns")

    def _load_and_compile_patterns(self):
        """Load patterns from config and compile them once at load time."""
        # First try to load from security.patterns section (new format)
        pattern_configs = self.config_manager.get("security.patterns", {})
        
        # If no patterns found, fall back to data_masking.patterns
        if not pattern_configs:
            logger.warning("No security patterns found, falling back to data_masking patterns")
            pattern_configs = self.config_manager.get("data_masking.patterns", {})
            
        # If still no patterns, use defaults
        if not pattern_configs:
            logger.warning("No patterns found in config, using default patterns")
            pattern_configs = self._get_default_patterns()
        
        # Initialize patterns dictionary
        self._patterns = {}
        
        # Process each pattern
        for name, config in pattern_configs.items():
            try:
                # For list-style config (data_masking format)
                if isinstance(config, dict) and "regex" in config:
                    regex = config["regex"]
                    category = config.get("category", "sensitive_data")
                    severity = config.get("severity", "medium")
                    description = config.get("description", "")
                    mask_method = config.get("mask_method", "default")
                # For simple string config
                elif isinstance(config, str):
                    regex = config
                    category = "sensitive_data"
                    severity = "medium" 
                    description = f"Pattern match: {name}"
                    mask_method = "default"
                else:
                    logger.warning(f"Invalid pattern config for {name}, skipping")
                    continue
                
                # Compile the regex pattern once
                compiled_pattern = re.compile(regex, re.IGNORECASE)
                
                # Store the compiled pattern and metadata
                self._patterns[name] = {
                    "pattern": compiled_pattern,
                    "category": category,
                    "severity": severity,
                    "description": description,
                    "mask_method": mask_method
                }
                logger.debug(f"Compiled pattern '{name}': {regex}")
            except Exception as e:
                # Log error but continue with other patterns
                logger.error(f"Error compiling pattern {name}: {e}")
        
        logger.info(f"Loaded {len(self._patterns)} patterns")

    def _get_default_patterns(self) -> Dict[str, Dict[str, str]]:
        """Return default patterns if none are configured.
        
        Returns:
            Dictionary of default patterns
        """
        return {
            "openai_api_key": {
                "regex": r"(sk-|org-)[a-zA-Z0-9_-]{32,}",
                "category": "sensitive_data",
                "severity": "high",
                "description": "OpenAI API Key",
                "mask_method": "partial"
            },
            "aws_access_key": {
                "regex": r"AKIA[0-9A-Z]{16}",
                "category": "sensitive_data",
                "severity": "high",
                "description": "AWS Access Key ID",
                "mask_method": "partial"
            },
            "anthropic_api_key": {
                "regex": r"sk-ant-[a-zA-Z0-9]{32,}",
                "category": "sensitive_data",
                "severity": "high",
                "description": "Anthropic API Key",
                "mask_method": "partial"
            },
            "credit_card": {
                "regex": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
                "category": "sensitive_data",
                "severity": "high",
                "description": "Credit Card Number",
                "mask_method": "credit_card"
            },
            "email_address": {
                "regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                "category": "sensitive_data",
                "severity": "medium",
                "description": "Email Address",
                "mask_method": "email"
            },
            "phone_number": {
                "regex": r"\b\d{3}[-.\\s]?\d{3}[-.\\s]?\d{4}\b",
                "category": "sensitive_data",
                "severity": "medium",
                "description": "Phone Number",
                "mask_method": "phone"
            },
            "ssn": {
                "regex": r"\b\d{3}-\d{2}-\d{4}\b",
                "category": "sensitive_data",
                "severity": "high",
                "description": "Social Security Number",
                "mask_method": "ssn"
            }
        }

    def _mask_sensitive_value(self, value: str, pattern_name: str, mask_method: str) -> str:
        """Mask sensitive values appropriately for logging.
        
        Args:
            value: Original sensitive value
            pattern_name: Name of the pattern that matched
            mask_method: Method to use for masking (default, partial, full, credit_card, email, etc.)
            
        Returns:
            Masked value safe for logging
        """
        # Skip masking if value is None or empty
        if not value:
            return value
        
        # Handle different masking methods
        if mask_method == "full":
            # Completely mask the value
            return "********"
            
        elif mask_method == "credit_card":
            # Credit card - keep first 4 digits, mask the rest
            digits_only = re.sub(r'[^0-9]', '', value)
            if len(digits_only) >= 12:  # Only mask if it looks like a credit card
                return digits_only[:4] + '-****-****-' + digits_only[-4:]
            else:
                return "****-****-****-****"  # Fallback
                
        elif mask_method == "email":
            # Email - mask username part, keep domain
            parts = value.split('@')
            if len(parts) == 2:
                username, domain = parts
                if len(username) > 2:
                    masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
                else:
                    masked_username = '**'
                return masked_username + '@' + domain
            else:
                return '****@****.***'  # Fallback
                
        elif mask_method == "ssn":
            # SSN - only show last 4 digits
            return "***-**-" + value[-4:]
            
        elif mask_method == "phone":
            # Phone - only show last 4 digits
            digits = re.sub(r'[^0-9]', '', value)
            if len(digits) >= 10:
                return "***-***-" + digits[-4:]
            else:
                return "***-***-****"  # Fallback
            
        elif mask_method == "partial":
            # Show first and last few characters, mask the middle
            if len(value) <= 8:
                return value[:2] + '*' * (len(value) - 4) + value[-2:]
            else:
                return value[:4] + '*' * (len(value) - 8) + value[-4:]
                
        else:  # Default masking
            # Show first 2 chars and replace rest with asterisks
            return value[:2] + '*' * (len(value) - 2)

    def scan_text(self, text: str, mask_values: bool = True) -> List[Dict[str, Any]]:
        """Scan text with all compiled patterns.
        
        Args:
            text: Text to scan
            mask_values: Whether to mask sensitive values (default True)
            
        Returns:
            List of matches with pattern information
        """
        # Scanning is thread-safe - no locks needed here
        # as compiled regex objects are thread-safe for searches
        results = []
        
        # Skip if None or empty
        if not text:
            return results
            
        # Scan with all patterns
        for name, pattern_info in self._patterns.items():
            compiled_pattern = pattern_info["pattern"]
            
            # Find all matches
            for match in compiled_pattern.finditer(text):
                # Extract the matched value
                matched_value = match.group(0)
                
                # Mask the value if required
                masked_value = matched_value
                if mask_values:
                    mask_method = pattern_info.get("mask_method", "default")
                    masked_value = self._mask_sensitive_value(matched_value, name, mask_method)
                
                # Store match information
                results.append({
                    "pattern_name": name,
                    "matched_value": matched_value,
                    "masked_value": masked_value,
                    "position": match.start(),
                    "category": pattern_info["category"],
                    "severity": pattern_info["severity"],
                    "description": pattern_info["description"]
                })
        
        return results
    
    def reload_config(self):
        """Reload patterns from configuration."""
        with self._init_lock:
            self.config_manager.reload()
            self._load_and_compile_patterns()
            logger.info("Patterns reloaded from config")
    
    @staticmethod
    def get_instance(config_manager=None) -> "PatternRegistry":
        """Get or create the singleton instance.
        
        Args:
            config_manager: Optional ConfigManager instance
            
        Returns:
            Singleton PatternRegistry instance
        """
        return PatternRegistry(config_manager)

    def mask_text_in_place(self, text: str) -> str:
        """Mask all sensitive data in a text string.
        
        Unlike scan_text which returns detected matches, this method directly returns
        a masked version of the input text with all sensitive data replaced.
        
        Args:
            text: Text to scan and mask
            
        Returns:
            Text with all sensitive data masked
        """
        # Skip if None or empty
        if not text:
            return text
            
        # First scan for all matches
        matches = self.scan_text(text, mask_values=True)
        
        # If no matches, return original text
        if not matches:
            return text
            
        # Sort matches by position in reverse order to avoid offset issues
        # when replacing substrings
        matches.sort(key=lambda x: x["position"], reverse=True)
        
        # Create a mutable version of the text
        mutable_text = list(text)
        
        # Replace each match with its masked version
        for match in matches:
            start = match["position"]
            end = start + len(match["matched_value"])
            masked_value = match["masked_value"]
            
            # Replace the matched value with the masked version
            mutable_text[start:end] = masked_value
        
        return ''.join(mutable_text) 