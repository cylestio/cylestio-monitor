"""
Security scanner for monitoring LLM events in Cylestio Monitor.

This module provides a unified, thread-safe interface for security scanning
across all event types. It implements a singleton pattern to ensure
consistent access to security keywords from a central source.
"""

import logging
import re
import threading
from typing import Any, Dict, List, Set, Optional

from cylestio_monitor.config import ConfigManager

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
            
            # Mark as initialized
            self._is_initialized = True
            logger.info("Security scanner initialized with keywords")

    def _load_keywords(self):
        """Load keywords from configuration with fallbacks."""
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
            logger.info("Security keywords reloaded from config")

    def scan_event(self, event: Any) -> Dict[str, Any]:
        """Scan any event type for security concerns.
        
        Args:
            event: Any event type to scan
            
        Returns:
            Dict with scan results including alert level and category
        """
        # Skip if None
        if event is None:
            return {"alert_level": "none", "category": None, "keywords": []}
            
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
            Dict with scan results including alert level and category
        """
        # Skip if None or empty
        if not text:
            return {"alert_level": "none", "category": None, "keywords": []}
        
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
            if self._word_boundary_match(keyword, normalized):
                matches["prompt_manipulation"].append(keyword)
                
        # Check ALL sensitive data keywords and collect matches
        for keyword in self._sensitive_data_keywords:
            if self._word_boundary_match(keyword, normalized):
                matches["sensitive_data"].append(keyword)
        
        # Determine the result based on matches - prioritizing dangerous > manipulation > sensitive
        if matches["dangerous_commands"]:
            return {
                "alert_level": "dangerous",
                "category": "dangerous_commands",
                "keywords": matches["dangerous_commands"]
            }
        elif matches["prompt_manipulation"]:
            return {
                "alert_level": "suspicious",
                "category": "prompt_manipulation",
                "keywords": matches["prompt_manipulation"]
            }
        elif matches["sensitive_data"]:
            return {
                "alert_level": "suspicious",
                "category": "sensitive_data",
                "keywords": matches["sensitive_data"]
            }
        else:
            return {"alert_level": "none", "category": None, "keywords": []}
        
    def _simple_text_match(self, keyword: str, text: str) -> bool:
        """Smart substring match with context awareness for SQL commands.
        
        Args:
            keyword: Keyword to search for
            text: Text to search in
            
        Returns:
            True if keyword is found in text
        """
        # For multi-word phrases, use simple substring match
        if " " in keyword or "(" in keyword or "-" in keyword:
            return keyword in text
            
        # List of SQL commands that need context-aware matching
        sql_commands = {"drop", "delete", "truncate", "alter", "create", "insert", 
                       "update", "select", "exec", "shutdown", "format", "eval"}
                       
        # For SQL commands, use more sophisticated matching to avoid false positives
        if keyword.lower() in sql_commands:
            # If it's an exact match (the whole text is just the command), it's a match
            if text.strip().lower() == keyword.lower():
                return True
                
            # Check for SQL context with word boundaries
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                # Check for SQL context
                sql_context_terms = [
                    "table", "database", "schema", "column", "index", "view", "function", 
                    "procedure", "trigger", "sql", "query", "db", "command", "statement"
                ]
                
                text_lower = text.lower()
                
                # If it appears with SQL context terms, it's likely a SQL command
                for term in sql_context_terms:
                    if term in text_lower:
                        return True
                        
                # If it's near specific SQL syntax, it's likely a SQL command
                sql_syntax = ["select", "from", "where", "alter", "create", "insert", 
                             "update", "delete", ";", "--", "/*", "*/"]
                             
                for syntax in sql_syntax:
                    if syntax in text_lower:
                        return True
                        
                # For standalone commands, check if they're being used as commands
                command_indicators = ["command", "run", "execute", "shell", "terminal", 
                                     "bash", "cmd", "powershell", "executing"]
                                     
                for indicator in command_indicators:
                    if indicator in text_lower:
                        return True
                
                # Special cases for specific commands
                if keyword.lower() == "drop":
                    # "drop" in database/programming context
                    if any(x in text_lower for x in ["table", "database", "db", "index", "column"]):
                        return True
                    # Standalone "drop" with clear intent  
                    if re.search(r'\bdrop\b.*\btable\b', text_lower) or re.search(r'\bdrop\b.*\bdatabase\b', text_lower):
                        return True
                
                elif keyword.lower() == "format":
                    # "format" in dangerous context
                    if any(x in text_lower for x in ["disk", "drive", "hard", "partition", "memory"]):
                        return True
                
                elif keyword.lower() in ["exec", "eval"]:
                    # "exec"/"eval" in code execution context
                    if any(x in text_lower for x in ["code", "script", "function", "command"]):
                        return True
                
                elif keyword.lower() == "shutdown":
                    # "shutdown" in system context
                    if any(x in text_lower for x in ["server", "system", "computer", "machine"]):
                        return True
                
                # If no context suggests it's a SQL command, check if used as a verb
                # This helps avoid triggering on phrases like "dropdown menu"
                return False
                
            # Simple substring match as fallback for exact casing like "DROP"
            # but not for lowercase to avoid false positives 
            if keyword.isupper() and keyword in text:
                return True
                
            return False
            
        # For all other dangerous commands, use simple substring match
        return keyword in text
        
    def _word_boundary_match(self, keyword: str, text: str) -> bool:
        """Match a keyword in text using word boundaries.
        
        Args:
            keyword: Keyword to search for
            text: Text to search in
            
        Returns:
            True if keyword is found in text
        """
        # For multi-word phrases, use simple substring match
        if " " in keyword:
            return keyword in text
            
        # For single-word keywords, use word boundary matching
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text))

    # Static accessor for convenience
    @staticmethod
    def get_instance(config_manager=None) -> "SecurityScanner":
        """Get or create the scanner instance.
        
        Args:
            config_manager: Optional config manager to use
            
        Returns:
            SecurityScanner instance
        """
        return SecurityScanner(config_manager) 