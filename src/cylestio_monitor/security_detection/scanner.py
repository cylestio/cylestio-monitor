"""
Security scanner for monitoring LLM events in Cylestio Monitor.

This module provides a unified, thread-safe interface for security scanning
across all event types. It implements a singleton pattern to ensure
consistent access to security keywords from a central source.
"""

import logging
import re
import threading
from typing import Any, Dict, List, Set, Optional, Tuple

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.security_detection.patterns import PatternRegistry

logger = logging.getLogger("CylestioMonitor.Security")


class SecurityScanner:
    """Thread-safe security scanner for all event types."""

    # Class-level lock for thread safety during initialization
    _init_lock = threading.RLock()
    
    # Singleton instance
    _instance: Optional["SecurityScanner"] = None
    
    # Keyword sets - immutable after initialization
    _sensitive_data_keywords: Set[str] = set()
    _dangerous_commands_keywords: Set[str] = set()
    _prompt_manipulation_keywords: Set[str] = set()
    
    # Category configuration - immutable after initialization
    _categories: Dict[str, Dict[str, Any]] = {}
    
    # Pattern registry for regex pattern matching
    _pattern_registry: Optional[PatternRegistry] = None
    
    # Flags for initialization state
    _is_initialized = False

    def __new__(cls, config_manager=None):
        """Create or return the singleton instance with thread safety."""
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super(SecurityScanner, cls).__new__(cls)
                cls._instance._initialize(config_manager)
            return cls._instance

    def _initialize(self, config_manager=None):
        """Initialize the scanner with thread safety.
        
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
            
            # Load all keywords from the config
            self._load_keywords()
            
            # Initialize pattern registry
            self._pattern_registry = PatternRegistry.get_instance(self.config_manager)
            
            # Mark as initialized
            self._is_initialized = True
            logger.info("Security scanner initialized with keywords and patterns")

    def _load_keywords(self):
        """Load keywords and categories from configuration with fallbacks."""
        # Load categories from new format
        try:
            categories = self.config_manager.get("security.alert_categories", {})
            if categories:
                self._categories = categories
                
                # Load keywords from category structure
                for category, config in categories.items():
                    if not config.get("enabled", True):
                        logger.info(f"Category {category} is disabled, skipping")
                        continue
                        
                    keywords = config.get("keywords", [])
                    if category == "sensitive_data":
                        self._sensitive_data_keywords = set(k.lower() for k in keywords)
                    elif category == "dangerous_commands":
                        # Store dangerous commands preserving original case and adding lowercase versions
                        self._dangerous_commands_keywords = set()
                        # Add all SQL and database commands that should be detected without case sensitivity
                        sql_commands = ["drop", "delete", "truncate", "alter", "create", "insert", 
                                      "update", "select", "exec", "shutdown", "format", "eval"]
                                      
                        # Make sure all basic SQL commands are included even if not in config
                        for cmd in sql_commands:
                            self._dangerous_commands_keywords.add(cmd)
                            self._dangerous_commands_keywords.add(cmd.upper())
                            
                        # Now add all commands from config
                        for cmd in keywords:
                            # Add original case
                            self._dangerous_commands_keywords.add(cmd)
                            # Add lowercase
                            if cmd != cmd.lower():
                                self._dangerous_commands_keywords.add(cmd.lower())
                            # Add uppercase
                            if cmd != cmd.upper():
                                self._dangerous_commands_keywords.add(cmd.upper())
                    elif category == "prompt_manipulation":
                        # For prompt manipulation, we need to preserve case for some keywords
                        # but also support case-insensitive matching
                        self._prompt_manipulation_keywords = set()
                        for keyword in keywords:
                            # Add original case
                            self._prompt_manipulation_keywords.add(keyword)
                            # Add lowercase if different
                            if keyword != keyword.lower():
                                self._prompt_manipulation_keywords.add(keyword.lower())
                
                logger.info(f"Loaded keywords from alert_categories config with {len(categories)} categories")
                return
        except Exception as e:
            logger.warning(f"Error loading from alert_categories: {str(e)}")
                
        # Fallback to legacy format if needed
        logger.warning("Falling back to legacy keywords format")
        
        # Sensitive data keywords
        sensitive_data = self.config_manager.get("security.keywords.sensitive_data", [])
        if not sensitive_data:
            logger.warning("No sensitive data keywords found in config, using defaults")
            sensitive_data = [
                "password", "api_key", "token", "secret", "ssn", "credit card"
            ]
        self._sensitive_data_keywords = set(k.lower() for k in sensitive_data)
        
        # Dangerous commands keywords
        dangerous_commands = self.config_manager.get(
            "security.keywords.dangerous_commands", []
        )
        if not dangerous_commands:
            logger.warning("No dangerous commands keywords found in config, using defaults")
            dangerous_commands = [
                "drop table", "delete from", "rm -rf", "exec(", "system(", "eval("
            ]
        
        # Store dangerous commands preserving original case and adding lowercase versions
        self._dangerous_commands_keywords = set()
        # Add all SQL and database commands that should be detected without case sensitivity
        sql_commands = ["drop", "delete", "truncate", "alter", "create", "insert", 
                      "update", "select", "exec", "shutdown", "format", "eval"]
                      
        # Make sure all basic SQL commands are included even if not in config
        for cmd in sql_commands:
            self._dangerous_commands_keywords.add(cmd)
            self._dangerous_commands_keywords.add(cmd.upper())
            
        # Now add all commands from config
        for cmd in dangerous_commands:
            # Add original case
            self._dangerous_commands_keywords.add(cmd)
            # Add lowercase
            if cmd != cmd.lower():
                self._dangerous_commands_keywords.add(cmd.lower())
            # Add uppercase
            if cmd != cmd.upper():
                self._dangerous_commands_keywords.add(cmd.upper())
        
        # Prompt manipulation keywords
        prompt_manipulation = self.config_manager.get(
            "security.keywords.prompt_manipulation", []
        )
        if not prompt_manipulation:
            logger.warning("No prompt manipulation keywords found in config, using defaults")
            prompt_manipulation = [
                "ignore previous", "disregard", "bypass", "jailbreak", "hack", "exploit"
            ]
        self._prompt_manipulation_keywords = set(k.lower() for k in prompt_manipulation)
        
        # Create default categories since we're in fallback mode
        self._categories = {
            "sensitive_data": {
                "enabled": True,
                "severity": "medium",
                "description": "Sensitive information like PII, credentials, and other confidential data"
            },
            "dangerous_commands": {
                "enabled": True,
                "severity": "high",
                "description": "System commands, SQL injections, and other potentially harmful operations"
            },
            "prompt_manipulation": {
                "enabled": True,
                "severity": "medium",
                "description": "Attempts to manipulate LLM behavior or bypass security constraints"
            }
        }
        
        # Log keyword counts
        logger.debug(f"Loaded dangerous commands: {sorted(list(self._dangerous_commands_keywords))}")
        logger.info(
            f"Loaded keywords - Sensitive: {len(self._sensitive_data_keywords)}, "
            f"Dangerous: {len(self._dangerous_commands_keywords)}, "
            f"Manipulation: {len(self._prompt_manipulation_keywords)}"
        )

    def reload_config(self):
        """Reload keywords from configuration."""
        with self._init_lock:
            self.config_manager.reload()
            self._load_keywords()
            # Reload pattern registry
            if self._pattern_registry:
                self._pattern_registry.reload_config()
            logger.info("Security keywords and patterns reloaded from config")

    def scan_event(self, event: Any) -> Dict[str, Any]:
        """Scan any event type for security concerns.
        
        Args:
            event: Any event type to scan
            
        Returns:
            Dict with scan results including alert level, category, severity, description, and keywords
        """
        # Skip if None
        if event is None:
            return {"alert_level": "none", "category": None, "severity": None, "description": None, "keywords": []}
            
        # Extract text based on event type
        text = self._extract_text_from_event(event)
        
        # Scan the text
        return self.scan_text(text)
    
    def _extract_text_from_event(self, event: Any) -> str:
        """Extract text content from different event types.
        
        Args:
            event: Event object of any type
            
        Returns:
            Text content for scanning
        """
        # Skip if None
        if event is None:
            return ""
            
        # Handle different event types
        if hasattr(event, "content"):  # LLM message
            return str(event.content)
        elif hasattr(event, "prompt"):  # LLM prompt
            return str(event.prompt)
        elif hasattr(event, "command"):  # Tool call
            return str(event.command)
        elif hasattr(event, "request"):  # API request
            if hasattr(event.request, "body"):
                return str(event.request.body)
            return str(event.request)
        elif hasattr(event, "args"):  # Function call
            return str(event.args)
        # Handle dict-like objects with message content
        elif isinstance(event, dict):
            # Try to extract content from common dict formats
            if "content" in event:
                return str(event["content"])
            elif "messages" in event:
                return str(event["messages"])
            elif "prompt" in event:
                return str(event["prompt"])
            # Handle event with attributes that has llm.response.content
            elif "attributes" in event and isinstance(event["attributes"], dict):
                attributes = event["attributes"]
                
                # Handle LangGraph node events
                if "node.result" in attributes and isinstance(attributes["node.result"], dict):
                    node_result = attributes["node.result"]
                    
                    # Handle messages array in node result (common LangGraph pattern)
                    if "messages" in node_result and isinstance(node_result["messages"], list):
                        extracted_text = ""
                        for msg in node_result["messages"]:
                            if isinstance(msg, dict) and "content" in msg:
                                extracted_text += str(msg["content"]) + " "
                        if extracted_text:
                            return extracted_text.strip()
                    
                    # If node result contains content directly
                    if "content" in node_result:
                        return str(node_result["content"])
                        
                    # If no messages or couldn't extract from messages, return the whole node result
                    return str(node_result)
                
                # Handle LangGraph node.state (for langgraph.node.start events)
                elif "node.state" in attributes and isinstance(attributes["node.state"], dict):
                    node_state = attributes["node.state"]
                    
                    # Handle messages array in node state
                    if "messages" in node_state and isinstance(node_state["messages"], list):
                        extracted_text = ""
                        for msg in node_state["messages"]:
                            if isinstance(msg, dict) and "content" in msg:
                                extracted_text += str(msg["content"]) + " "
                        if extracted_text:
                            return extracted_text.strip()
                            
                        # If node state contains content directly
                        if "content" in node_state:
                            return str(node_state["content"])
                            
                        # If no messages or couldn't extract from messages, return the whole node state
                        return str(node_state)
                
                # Handle LangGraph state_transition events
                elif "state" in attributes and isinstance(attributes["state"], dict):
                    state = attributes["state"]
                    
                    # Handle messages array in state
                    if "messages" in state and isinstance(state["messages"], list):
                        extracted_text = ""
                        for msg in state["messages"]:
                            if isinstance(msg, dict) and "content" in msg:
                                extracted_text += str(msg["content"]) + " "
                        if extracted_text:
                            return extracted_text.strip()
                            
                        # If state contains content directly
                        if "content" in state:
                            return str(state["content"])
                            
                        # If no messages or couldn't extract from messages, return the whole state
                        return str(state)
                
                # LLM response content
                if "llm.response.content" in attributes:
                    content = attributes["llm.response.content"]
                    # Handle array of content blocks
                    if isinstance(content, list):
                        extracted_text = ""
                        for item in content:
                            if isinstance(item, dict) and "text" in item:
                                extracted_text += item["text"] + " "
                        return extracted_text.strip()
                    return str(content)
                # Input content
                elif "llm.request.data" in attributes and isinstance(attributes["llm.request.data"], dict):
                    request_data = attributes["llm.request.data"]
                    if "messages" in request_data:
                        return str(request_data["messages"])
                    elif "prompt" in request_data:
                        return str(request_data["prompt"])
                # Generic attributes extraction as fallback
                return str(attributes)
        
        # Fallback - convert entire event to string
        return str(event)
    
    def scan_text(self, text: str) -> Dict[str, Any]:
        """Scan text for security concerns.
        
        Args:
            text: Text to scan
            
        Returns:
            Dict with scan results including alert level, category, severity, and found keywords
        """
        # Skip if None or empty
        if not text:
            return {"alert_level": "none", "category": None, "severity": None, "description": None, "keywords": []}
        
        # Original text for exact case matching
        original = text
        
        # Normalize text to lowercase for case-insensitive matching
        normalized = text.lower()
        
        # Collect ALL matches first, then prioritize
        matches = {
            "dangerous_commands": [],
            "prompt_manipulation": [],
            "sensitive_data": []
        }
        
        # Check ALL dangerous commands and collect matches
        for keyword in self._dangerous_commands_keywords:
            if self._simple_text_match(keyword, original) or self._simple_text_match(keyword, normalized):
                matches["dangerous_commands"].append(keyword)
                
        # Check ALL prompt manipulation keywords and collect matches
        for keyword in self._prompt_manipulation_keywords:
            # For multi-word prompt manipulation phrases, use simple contains on either original or lowercase
            if " " in keyword:
                if keyword in original or (keyword.lower() in normalized and keyword.lower() == keyword):
                    matches["prompt_manipulation"].append(keyword)
            # For uppercase keywords (like "REMOVE"), check in original case
            elif keyword.isupper() and keyword in original:
                matches["prompt_manipulation"].append(keyword)
            # For single words, use word boundary match to avoid false positives
            elif self._word_boundary_match(keyword, normalized):
                matches["prompt_manipulation"].append(keyword)
                
        # Check ALL sensitive data keywords and collect matches
        for keyword in self._sensitive_data_keywords:
            if self._word_boundary_match(keyword, normalized):
                matches["sensitive_data"].append(keyword)
        
        # Check patterns with pattern registry
        pattern_matches = []
        masked_pattern_refs = []
        if self._pattern_registry:
            pattern_matches = self._pattern_registry.scan_text(original, mask_values=True)
            
            # Add pattern matches to the appropriate categories using masked values
            for match in pattern_matches:
                category = match.get("category", "sensitive_data")
                if category in matches:
                    masked_value = match.get("masked_value", match.get("matched_value", ""))
                    pattern_ref = f"{match['pattern_name']}:{masked_value}"
                    matches[category].append(pattern_ref)
                    masked_pattern_refs.append(pattern_ref)
                
        # Determine category, severity, and alert level
        category, severity, alert_level, description, found_keywords = self._determine_category_and_severity(matches, pattern_matches)
        
        # Return detailed result with pattern matches
        result = {
            "alert_level": alert_level,
            "category": category,
            "severity": severity,
            "description": description,
            "keywords": found_keywords
        }
        
        # Add pattern_matches if any were found, but ensure sensitive data is masked
        if pattern_matches:
            # Create a list of matches with masked values
            masked_matches = []
            for match in pattern_matches:
                # Create a copy of the match with masked value replacing the actual value
                masked_match = match.copy()
                if "matched_value" in masked_match and "masked_value" in masked_match:
                    # Replace the actual matched value with the masked one for logging
                    masked_match["matched_value"] = masked_match["masked_value"]
                    # Remove the redundant masked_value field
                    del masked_match["masked_value"]
                masked_matches.append(masked_match)
                
            result["pattern_matches"] = masked_matches
            
        return result
    
    def _determine_category_and_severity(self, matches: Dict[str, List[str]], pattern_matches: List[Dict[str, Any]] = None) -> Tuple[Optional[str], Optional[str], str, Optional[str], List[str]]:
        """Determine the most severe category and appropriate severity based on matches.
        
        Args:
            matches: Dictionary of matches by category
            pattern_matches: List of pattern matches with severity information
            
        Returns:
            Tuple of (category, severity, alert_level, description, keywords)
        """
        # No matches at all
        if not any(matches.values()) and not pattern_matches:
            return None, None, "none", None, []
        
        # Initialize highest severity based on patterns
        highest_pattern_severity = None
        highest_pattern_category = None
        highest_pattern_description = None
        
        # Check if we have any high severity pattern matches
        if pattern_matches:
            for match in pattern_matches:
                pattern_severity = match.get("severity", "medium")
                if pattern_severity == "high" or (highest_pattern_severity is None and pattern_severity == "medium"):
                    highest_pattern_severity = pattern_severity
                    highest_pattern_category = match.get("category", "sensitive_data")
                    highest_pattern_description = match.get("description", f"Pattern match: {match.get('pattern_name', 'unknown')}")
                    # Break early if we found a high severity match
                    if pattern_severity == "high":
                        break
            
        # Priority order of categories (dangerous_commands takes precedence over others)
        priority_order = ["dangerous_commands", "prompt_manipulation", "sensitive_data"]
        
        # Find the highest priority category that has matches
        for category in priority_order:
            if matches[category] and category in self._categories:
                # Get category config
                category_config = self._categories[category]
                
                # Skip if disabled
                if not category_config.get("enabled", True):
                    continue
                
                # Get severity from category config
                severity = category_config.get("severity", "medium")
                
                # Get description from category config
                description = category_config.get("description", f"{category} detection")
                
                # Map severity to alert level
                alert_level = {
                    "low": "suspicious",
                    "medium": "suspicious",
                    "high": "dangerous"
                }.get(severity, "suspicious")
                
                # If we have a high severity pattern match, use it for dangerous commands and sensitive_data
                if highest_pattern_severity == "high" and (category == "sensitive_data" or not matches["dangerous_commands"]):
                    return highest_pattern_category, "high", "dangerous", highest_pattern_description, matches[highest_pattern_category]
                
                return category, severity, alert_level, description, matches[category]
        
        # If we get here and have a pattern match, use it
        if highest_pattern_severity:
            alert_level = "suspicious"
            if highest_pattern_severity == "high":
                alert_level = "dangerous"
            return highest_pattern_category, highest_pattern_severity, alert_level, highest_pattern_description, matches.get(highest_pattern_category, [])
        
        # Fallback if we have matches but no category in priority order matched
        for category, keywords in matches.items():
            if keywords and category in self._categories:
                # Get category config
                category_config = self._categories[category]
                
                # Skip if disabled
                if not category_config.get("enabled", True):
                    continue
                    
                severity = category_config.get("severity", "medium")
                description = category_config.get("description", f"{category} detection")
                alert_level = "suspicious"
                if severity == "high":
                    alert_level = "dangerous"
                return category, severity, alert_level, description, keywords
        
        # Ultimate fallback (should never happen)
        return None, None, "none", None, []
                
    def _simple_text_match(self, keyword: str, text: str) -> bool:
        """Simple substring match that can be used for commands or phrases.
        
        Args:
            keyword: Keyword to search for
            text: Text to search in
            
        Returns:
            True if keyword is found
        """
        # Skip if either is None
        if not keyword or not text:
            return False
            
        # For multi-word phrases or special characters, use simple substring match
        if " " in keyword or "(" in keyword or "-" in keyword:
            return keyword in text
            
        # For single words that are SQL commands, use word boundary matching to avoid false positives
        # List of SQL commands and dangerous commands that need context-aware matching
        sql_commands = {"drop", "delete", "truncate", "alter", "create", "insert", 
                      "update", "select", "exec", "shutdown", "format", "eval"}
                      
        if keyword.lower() in sql_commands:
            # If it's an exact match (the whole text is just the command), it's a match
            if text.strip().lower() == keyword.lower():
                return True
                
            # Check for word boundaries
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if not re.search(pattern, text):
                return False
                
            # For potentially ambiguous keywords, we need to check for usage context
            if keyword.lower() in {"drop", "format", "eval", "delete", "exec", "shutdown"}:
                # First check if it's used in a technical/programming context
                text_lower = text.lower()
                
                # For "format", only match if it's about formatting storage, not text/documents
                if keyword.lower() == "format":
                    # Check for "format" + storage-related terms
                    storage_terms = {"hard", "drive", "disk", "partition", "memory", "usb", "flash", "sd card"}
                    
                    has_storage_context = any(term in text_lower for term in storage_terms)
                    has_text_context = any(term in text_lower for term in 
                                           {"text", "document", "properly", "paragraph", "string"})
                    
                    # Only match if clear storage context, but not text context
                    if not has_storage_context and has_text_context:
                        return False
                
                # For "eval", only match if it's about code evaluation
                if keyword.lower() == "eval":
                    # Only match if seems to be about code evaluation
                    if "evaluate" in text_lower and not any(term in text_lower for term in 
                                                         {"code", "script", "javascript", "function"}):
                        return False
                
                # For "drop", look for database context
                if keyword.lower() == "drop":
                    # Common false positives for "drop"
                    false_positive_terms = {"dropdown", "drop-down", "droplet", "dropping"}
                    
                    # Check false positives first
                    for term in false_positive_terms:
                        if term in text_lower:
                            return False
                    
                    # No need to check for database context - that's handled by word boundary check
            
            # If uppercase, it's likely a SQL statement
            if keyword.isupper():
                return True
            
            # Default to matching SQL commands if they pass word boundary check
            return True
            
        # For all other keywords, use simple substring match
        return keyword in text

    def _word_boundary_match(self, keyword: str, text: str) -> bool:
        """Match keywords at word boundaries to avoid false positives.
        
        Args:
            keyword: Keyword to search for
            text: Text to search in
            
        Returns:
            True if keyword is found at word boundaries
        """
        # Skip if either is None
        if not keyword or not text:
            return False
            
        # For multi-word keywords, do simple contains
        if " " in keyword:
            return keyword in text
            
        # For single words, check word boundaries
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text))
    
    @staticmethod
    def get_instance(config_manager=None) -> "SecurityScanner":
        """Get the singleton instance of the security scanner.
        
        Args:
            config_manager: Optional ConfigManager instance
            
        Returns:
            SecurityScanner instance
        """
        return SecurityScanner(config_manager)

    def mask_event(self, event: Any) -> Any:
        """Mask sensitive data in any event type.
        
        This method extracts text from the event, masks sensitive data,
        and updates the event with the masked text.
        
        Args:
            event: Event to mask
            
        Returns:
            Event with sensitive data masked
        """
        # Skip if None
        if event is None:
            return None
            
        # Extract text from event based on type
        text = self._extract_text_from_event(event)
        if not text:
            return event
            
        # Mask the text
        masked_text = self._pattern_registry.mask_text_in_place(text)
        
        # If no masking occurred, return original event
        if masked_text == text:
            return event
            
        # Create a shallow copy of the event and update with masked text
        return self._update_event_with_masked_text(event, masked_text)
        
    def _update_event_with_masked_text(self, event: Any, masked_text: str) -> Any:
        """Update event with masked text in the appropriate field.
        
        Args:
            event: Original event
            masked_text: Masked text to update in the event
            
        Returns:
            Updated event with masked text
        """
        import copy
        
        # Create a shallow copy to avoid modifying the original
        # (unless the event is a primitive type)
        if isinstance(event, (str, int, float, bool, type(None))):
            return masked_text if isinstance(event, str) else event
            
        masked_event = copy.copy(event)
        
        # Update appropriate field based on event type
        if hasattr(masked_event, "content"):  # LLM message
            masked_event.content = masked_text
        elif hasattr(masked_event, "prompt"):  # LLM prompt
            masked_event.prompt = masked_text
        elif hasattr(masked_event, "command"):  # Tool call
            masked_event.command = masked_text
        elif hasattr(masked_event, "request") and hasattr(masked_event.request, "body"):  # API request
            masked_event.request.body = masked_text
        elif hasattr(masked_event, "args"):  # Function call
            masked_event.args = masked_text
        # Handle dict-like objects
        elif isinstance(masked_event, dict):
            if "content" in masked_event:
                masked_event["content"] = masked_text
            elif "messages" in masked_event:
                masked_event["messages"] = masked_text
            elif "prompt" in masked_event:
                masked_event["prompt"] = masked_text
            # Handle event with attributes that has llm.response.content
            elif "attributes" in masked_event and isinstance(masked_event["attributes"], dict):
                attributes = masked_event["attributes"]
                
                # Handle LangGraph node events
                if "node.result" in attributes and isinstance(attributes["node.result"], dict):
                    node_result = attributes["node.result"]
                    
                    # Handle messages array in node result
                    if "messages" in node_result and isinstance(node_result["messages"], list):
                        # We need to scan each message individually and only mask those with sensitive data
                        for i, msg in enumerate(node_result["messages"]):
                            if isinstance(msg, dict) and "content" in msg:
                                # Extract the original content
                                original_content = str(msg["content"])
                                
                                # Check if this specific message contains sensitive data
                                # by scanning it with the pattern registry
                                matches = self._pattern_registry.scan_text(original_content)
                                
                                # Only mask if sensitive data was found in this message
                                if matches:
                                    # Mask just this message's content
                                    msg_masked_text = self._pattern_registry.mask_text_in_place(original_content)
                                    node_result["messages"][i]["content"] = msg_masked_text
                    
                    # If content field exists directly in node result
                    elif "content" in node_result:
                        node_result["content"] = masked_text
                
                # Handle LangGraph node.state (for langgraph.node.start events)
                elif "node.state" in attributes and isinstance(attributes["node.state"], dict):
                    node_state = attributes["node.state"]
                    
                    # Handle messages array in node state
                    if "messages" in node_state and isinstance(node_state["messages"], list):
                        # We need to scan each message individually and only mask those with sensitive data
                        for i, msg in enumerate(node_state["messages"]):
                            if isinstance(msg, dict) and "content" in msg:
                                # Extract the original content
                                original_content = str(msg["content"])
                                
                                # Check if this specific message contains sensitive data
                                # by scanning it with the pattern registry
                                matches = self._pattern_registry.scan_text(original_content)
                                
                                # Only mask if sensitive data was found in this message
                                if matches:
                                    # Mask just this message's content
                                    msg_masked_text = self._pattern_registry.mask_text_in_place(original_content)
                                    node_state["messages"][i]["content"] = msg_masked_text
                    
                    # If content field exists directly in node state
                    elif "content" in node_state:
                        node_state["content"] = masked_text
                
                # Handle LangGraph state_transition events
                elif "state" in attributes and isinstance(attributes["state"], dict):
                    state = attributes["state"]
                    
                    # Handle messages array in state
                    if "messages" in state and isinstance(state["messages"], list):
                        # We need to scan each message individually and only mask those with sensitive data
                        for i, msg in enumerate(state["messages"]):
                            if isinstance(msg, dict) and "content" in msg:
                                # Extract the original content
                                original_content = str(msg["content"])
                                
                                # Check if this specific message contains sensitive data
                                # by scanning it with the pattern registry
                                matches = self._pattern_registry.scan_text(original_content)
                                
                                # Only mask if sensitive data was found in this message
                                if matches:
                                    # Mask just this message's content
                                    msg_masked_text = self._pattern_registry.mask_text_in_place(original_content)
                                    state["messages"][i]["content"] = msg_masked_text
                    
                    # If content field exists directly in state
                    elif "content" in state:
                        state["content"] = masked_text
                
                # LLM response content
                elif "llm.response.content" in attributes:
                    content = attributes["llm.response.content"]
                    if isinstance(content, list):
                        # Handle array of content blocks
                        for i, item in enumerate(content):
                            if isinstance(item, dict) and "text" in item:
                                # Create masked version of content blocks
                                item_text = self._pattern_registry.mask_text_in_place(item["text"])
                                content[i]["text"] = item_text
                    else:
                        attributes["llm.response.content"] = masked_text
                # Input content
                elif "llm.request.data" in attributes and isinstance(attributes["llm.request.data"], dict):
                    request_data = attributes["llm.request.data"]
                    if "messages" in request_data:
                        request_data["messages"] = masked_text
                    elif "prompt" in request_data:
                        request_data["prompt"] = masked_text
        
        return masked_event 