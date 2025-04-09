"""Tests for the security scanner module."""

import threading
import pytest
from unittest.mock import patch, MagicMock

from cylestio_monitor.security_detection import SecurityScanner


class TestSecurityScanner:
    """Test suite for the SecurityScanner."""

    def test_singleton_pattern(self):
        """Test that SecurityScanner implements singleton pattern."""
        # Get two instances
        scanner1 = SecurityScanner.get_instance()
        scanner2 = SecurityScanner.get_instance()
        
        # They should be the same object
        assert scanner1 is scanner2
        
    def test_thread_safety(self):
        """Test thread safety of the SecurityScanner initialization."""
        # Reset the singleton for testing
        SecurityScanner._instance = None
        SecurityScanner._is_initialized = False
        
        # Create mock config
        mock_config = {
            "security": {
                "keywords": {
                    "sensitive_data": ["test_sensitive"],
                    "dangerous_commands": ["test_dangerous"],
                    "prompt_manipulation": ["test_manipulation"]
                }
            }
        }
        
        # Mock the ConfigManager
        mock_manager = MagicMock()
        mock_manager.get.side_effect = lambda key, default=None: {
            "security.keywords.sensitive_data": ["test_sensitive"],
            "security.keywords.dangerous_commands": ["test_dangerous"],
            "security.keywords.prompt_manipulation": ["test_manipulation"]
        }.get(key, default)
        
        # Store scanners from each thread
        scanners = []
        
        def create_scanner():
            scanner = SecurityScanner(mock_manager)
            scanners.append(scanner)
        
        # Create and start multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_scanner)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads got the same scanner instance
        for i in range(1, 10):
            assert scanners[0] is scanners[i]
            
    def test_scan_text_sensitive(self):
        """Test scanning text with sensitive data."""
        # Reset the singleton for testing
        SecurityScanner._instance = None
        SecurityScanner._is_initialized = False
        
        # Create mock config manager
        mock_manager = MagicMock()
        mock_manager.get.side_effect = lambda key, default=None: {
            "security.keywords.sensitive_data": ["password", "credit card"],
            "security.keywords.dangerous_commands": ["rm -rf"],
            "security.keywords.prompt_manipulation": ["ignore previous"]
        }.get(key, default)
        
        # Create scanner with mock config
        scanner = SecurityScanner(mock_manager)
        
        # Test sensitive data detection
        result = scanner.scan_text("My password is 12345")
        assert result["alert_level"] == "suspicious"
        assert result["category"] == "sensitive_data"
        assert "password" in result["keywords"]
        
    def test_scan_text_dangerous(self):
        """Test scanning text with dangerous commands."""
        # Get the scanner instance (should be already initialized from previous test)
        scanner = SecurityScanner.get_instance()
        
        # Test dangerous command detection
        result = scanner.scan_text("I will rm -rf /var")
        assert result["alert_level"] == "dangerous"
        assert result["category"] == "dangerous_commands"
        assert "rm -rf" in result["keywords"]
        
    def test_scan_text_manipulation(self):
        """Test scanning text with prompt manipulation."""
        # Get the scanner instance
        scanner = SecurityScanner.get_instance()
        
        # Test prompt manipulation detection
        result = scanner.scan_text("Please ignore previous instructions")
        assert result["alert_level"] == "suspicious"
        assert result["category"] == "prompt_manipulation"
        assert "ignore previous" in result["keywords"]
        
    def test_scan_event_types(self):
        """Test scanning different event types."""
        # Get the scanner instance
        scanner = SecurityScanner.get_instance()
        
        # Test with dict-like message
        message_event = {"content": "my password is 12345"}
        result = scanner.scan_event(message_event)
        assert result["alert_level"] == "suspicious"
        assert result["category"] == "sensitive_data"
        
        # Test with object-like message
        class MockEvent:
            def __init__(self, content):
                self.content = content
                
        obj_event = MockEvent("let's rm -rf the directory")
        result = scanner.scan_event(obj_event)
        assert result["alert_level"] == "dangerous"
        assert result["category"] == "dangerous_commands"
        
        # Test with None input
        assert scanner.scan_event(None)["alert_level"] == "none"
        
        # Test with empty text
        assert scanner.scan_text("")["alert_level"] == "none"

    def test_case_sensitivity(self):
        """Test case sensitivity handling, especially for dangerous commands."""
        # Reset the singleton for testing
        SecurityScanner._instance = None
        SecurityScanner._is_initialized = False
        
        # Create mock config manager
        mock_manager = MagicMock()
        mock_manager.get.side_effect = lambda key, default=None: {
            "security.keywords.sensitive_data": ["password"],
            "security.keywords.dangerous_commands": ["rm -rf", "DROP", "DELETE"],
            "security.keywords.prompt_manipulation": ["ignore previous"]
        }.get(key, default)
        
        # Create scanner with mock config
        scanner = SecurityScanner(mock_manager)
        
        # Test uppercase dangerous command detection
        result = scanner.scan_text("Using the DROP TABLE command")
        assert result["alert_level"] == "dangerous"
        assert result["category"] == "dangerous_commands"
        assert "DROP" in result["keywords"]
        
        # Test lowercase detection of uppercase keyword
        result = scanner.scan_text("using the drop table command")
        assert result["alert_level"] == "dangerous"
        assert result["category"] == "dangerous_commands"
        
        # Test exact uppercase detection
        result = scanner.scan_text("DELETE FROM users")
        assert result["alert_level"] == "dangerous"
        assert result["category"] == "dangerous_commands"
        assert "DELETE" in result["keywords"]
        
    def test_word_boundary_matching(self):
        """Test word boundary matching for keywords."""
        # Reset the singleton for testing
        SecurityScanner._instance = None
        SecurityScanner._is_initialized = False
        
        # Create mock config manager
        mock_manager = MagicMock()
        mock_manager.get.side_effect = lambda key, default=None: {
            "security.keywords.sensitive_data": ["password", "ssn"],
            # Avoiding SQL commands for this test since they have special handling
            "security.keywords.dangerous_commands": ["rm -rf", "danger-word"],
            "security.keywords.prompt_manipulation": ["hack", "exploit"]
        }.get(key, default)
        
        # Create scanner with mock config
        scanner = SecurityScanner(mock_manager)
        
        # Should match - standalone words
        assert scanner.scan_text("This is a hack attempt")["alert_level"] == "suspicious"
        assert scanner.scan_text("Let's exploit this")["alert_level"] == "suspicious"
        assert scanner.scan_text("hack;")["alert_level"] == "suspicious"
        assert scanner.scan_text("I want to hack your system")["alert_level"] == "suspicious"
        
        # Should match - special patterns
        assert scanner.scan_text("Let's rm -rf the directory")["alert_level"] == "dangerous"
        assert scanner.scan_text("This is a danger-word")["alert_level"] == "dangerous"
        
        # Should NOT match - part of other words
        assert scanner.scan_text("hackathon event")["alert_level"] == "none"
        assert scanner.scan_text("unhackable system")["alert_level"] == "none"
        
        # Test with punctuation
        assert scanner.scan_text("hack!")["alert_level"] == "suspicious"
        assert scanner.scan_text("hack.")["alert_level"] == "suspicious"

    def test_extract_from_json_events(self):
        """Test extracting text from JSON event structures like LLM responses."""
        # Reset the singleton for testing
        SecurityScanner._instance = None
        SecurityScanner._is_initialized = False
        
        # Create mock config manager
        mock_manager = MagicMock()
        mock_manager.get.side_effect = lambda key, default=None: {
            "security.keywords.sensitive_data": ["password", "ssn"],
            "security.keywords.dangerous_commands": ["DROP", "DELETE"],
            "security.keywords.prompt_manipulation": ["hack"]
        }.get(key, default)
        
        # Create scanner with mock config
        scanner = SecurityScanner(mock_manager)
        
        # Test with a sample LLM response event (similar to the one in the issue)
        llm_response_event = {
            "schema_version": "1.0",
            "timestamp": "2025-04-09T13:26:01.542963",
            "trace_id": "1a59da03c5db49b6b728477c74e80eb6",
            "span_id": "02f0d9b339386b7d",
            "parent_span_id": None,
            "name": "llm.call.finish",
            "level": "INFO",
            "attributes": {
                "llm.vendor": "anthropic",
                "llm.model": "claude-3-haiku-20240307",
                "llm.response.id": "msg_01Te2NKWUXT9S2YVf7mtbCJp",
                "llm.response.type": "completion",
                "llm.response.timestamp": "2025-04-09T13:26:01.542929",
                "llm.response.duration_ms": 984,
                "llm.response.stop_reason": "end_turn",
                "llm.response.content": [
                    {
                        "type": "text",
                        "text": "I apologize, but I cannot execute the SQL command \"DROP\" as that would be deleting or modifying data."
                    }
                ]
            },
            "agent_id": "weather-agent"
        }
        
        # Should detect "DROP" in the nested content
        result = scanner.scan_event(llm_response_event)
        assert result["alert_level"] == "dangerous"
        assert result["category"] == "dangerous_commands"
        assert "DROP" in result["keywords"]
        
        # Test with a sample request event containing nested dangerous command
        llm_request_event = {
            "name": "llm.call.start",
            "attributes": {
                "llm.request.data": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Can you help me with the DELETE command in SQL?"
                        }
                    ]
                }
            }
        }
        
        # Should detect "DELETE" in the nested request content
        result = scanner.scan_event(llm_request_event)
        assert result["alert_level"] == "dangerous"
        assert result["category"] == "dangerous_commands"
        assert "DELETE" in result["keywords"]

    def test_sql_command_detection(self):
        """Test detection of SQL commands in appropriate contexts."""
        # Reset the singleton for testing
        SecurityScanner._instance = None
        SecurityScanner._is_initialized = False
        
        # Create mock config manager
        mock_manager = MagicMock()
        mock_manager.get.side_effect = lambda key, default=None: {
            "security.keywords.sensitive_data": ["password"],
            "security.keywords.dangerous_commands": ["drop", "DROP", "delete", "format", "shutdown"],
            "security.keywords.prompt_manipulation": ["hack"]
        }.get(key, default)
        
        # Create scanner with mock config
        scanner = SecurityScanner(mock_manager)
        
        # Test SQL commands in appropriate contexts
        assert scanner.scan_text("DROP TABLE users;")["alert_level"] == "dangerous"
        assert scanner.scan_text("drop database test;")["alert_level"] == "dangerous"
        assert scanner.scan_text("I want to DROP a table")["alert_level"] == "dangerous"
        assert scanner.scan_text("Can you help me drop this table?")["alert_level"] == "dangerous"
        assert scanner.scan_text("Use the DROP command")["alert_level"] == "dangerous"
        assert scanner.scan_text("Execute this SQL: DROP")["alert_level"] == "dangerous"
        
        # Test exact keyword matches
        assert scanner.scan_text("DROP")["alert_level"] == "dangerous"
        
        # Test SQL commands with unusual casing
        assert scanner.scan_text("DELETE FROM users")["alert_level"] == "dangerous"
        
        # Test casing variations with context
        assert scanner.scan_text("How do I format a hard drive?")["alert_level"] == "dangerous"
        assert scanner.scan_text("Please SHUTDOWN the server")["alert_level"] == "dangerous"

    def test_false_positive_avoidance(self):
        """Test avoiding false positives for SQL commands in non-SQL contexts."""
        # Reset the singleton for testing
        SecurityScanner._instance = None
        SecurityScanner._is_initialized = False
        
        # Create mock config manager
        mock_manager = MagicMock()
        mock_manager.get.side_effect = lambda key, default=None: {
            "security.keywords.sensitive_data": ["password"],
            "security.keywords.dangerous_commands": ["drop", "DROP", "delete", "format", "exec", "eval", "shutdown"],
            "security.keywords.prompt_manipulation": ["hack"]
        }.get(key, default)
        
        # Create scanner with mock config
        scanner = SecurityScanner(mock_manager)
        
        # These should NOT match (false positives)
        assert scanner.scan_text("Use the dropdown menu")["alert_level"] == "none"
        assert scanner.scan_text("Please format the text properly")["alert_level"] == "none"
        assert scanner.scan_text("The water droplets on the window")["alert_level"] == "none"
        assert scanner.scan_text("Can you evaluate my essay?")["alert_level"] == "none"
        assert scanner.scan_text("The execution of this plan")["alert_level"] == "none"
        assert scanner.scan_text("The system is shutting down gradually")["alert_level"] == "none"
        
        # These SHOULD match (true positives with context)
        assert scanner.scan_text("DROP the database users")["alert_level"] == "dangerous"
        assert scanner.scan_text("Use DROP TABLE students")["alert_level"] == "dangerous"
        assert scanner.scan_text("Format the hard drive")["alert_level"] == "dangerous"
        assert scanner.scan_text("Can you execute this SQL command: DROP TABLE")["alert_level"] == "dangerous"
        assert scanner.scan_text("Eval this JavaScript code")["alert_level"] == "dangerous"
        assert scanner.scan_text("Shutdown the server")["alert_level"] == "dangerous" 