"""
Tests for the pattern matcher module.

These tests verify that the pattern matcher correctly loads and uses
regex patterns for detecting sensitive information.
"""

import re
import pytest
from unittest.mock import MagicMock, patch

from cylestio_monitor.security_detection.patterns import PatternRegistry


class TestPatternRegistry:
    """Test suite for the PatternRegistry."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset the singleton for each test
        PatternRegistry._instance = None
        PatternRegistry._is_initialized = False
        PatternRegistry._patterns = {}
    
    def test_singleton_pattern(self):
        """Test that PatternRegistry implements the singleton pattern correctly."""
        # Create multiple instances
        registry1 = PatternRegistry()
        registry2 = PatternRegistry()
        
        # They should be the same object
        assert registry1 is registry2
        
        # get_instance should return the same object
        registry3 = PatternRegistry.get_instance()
        assert registry1 is registry3
    
    def test_pattern_loading(self):
        """Test that patterns are loaded from config correctly."""
        # Create mock config manager
        mock_manager = MagicMock()
        mock_manager.get.return_value = {
            "test_pattern": {
                "regex": r"test\d+",
                "category": "sensitive_data",
                "severity": "medium",
                "description": "Test Pattern"
            }
        }
        
        # Create registry with mock config
        registry = PatternRegistry(mock_manager)
        
        # Check that pattern was compiled
        assert len(registry._patterns) == 1
        assert "test_pattern" in registry._patterns
        assert isinstance(registry._patterns["test_pattern"]["pattern"], re.Pattern)
    
    def test_default_patterns(self):
        """Test that default patterns are used when none are configured."""
        # Create mock config manager that returns empty config
        mock_manager = MagicMock()
        mock_manager.get.return_value = {}
        
        # Create registry with mock config
        registry = PatternRegistry(mock_manager)
        
        # Check that default patterns were used
        assert len(registry._patterns) > 0
        assert "openai_api_key" in registry._patterns
        assert "credit_card" in registry._patterns
    
    def test_pattern_scanning(self):
        """Test that pattern scanning works correctly."""
        # Create mock config manager
        mock_manager = MagicMock()
        mock_manager.get.return_value = {
            "test_pattern": {
                "regex": r"test\d+",
                "category": "sensitive_data",
                "severity": "medium",
                "description": "Test Pattern"
            },
            "email_pattern": {
                "regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                "category": "sensitive_data",
                "severity": "medium",
                "description": "Email Address"
            }
        }
        
        # Create registry with mock config
        registry = PatternRegistry(mock_manager)
        
        # Test with matching text
        matches = registry.scan_text("This contains test123 and test456")
        assert len(matches) == 2
        assert matches[0]["pattern_name"] == "test_pattern"
        assert matches[0]["matched_value"] == "test123"
        assert matches[1]["matched_value"] == "test456"
        
        # Test with email
        matches = registry.scan_text("Contact us at info@example.com")
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "email_pattern"
        assert matches[0]["matched_value"] == "info@example.com"
        
        # Test with no matches
        matches = registry.scan_text("This text contains no patterns")
        assert len(matches) == 0
        
        # Test with empty text
        matches = registry.scan_text("")
        assert len(matches) == 0
        
        # Test with None
        matches = registry.scan_text(None)
        assert len(matches) == 0
    
    def test_reload_config(self):
        """Test that patterns can be reloaded from config."""
        # Create mock config manager
        mock_manager = MagicMock()
        
        # First load
        mock_manager.get.return_value = {
            "pattern1": {
                "regex": r"pattern1",
                "category": "sensitive_data",
                "severity": "medium",
                "description": "Pattern 1"
            }
        }
        
        # Create registry with mock config
        registry = PatternRegistry(mock_manager)
        assert "pattern1" in registry._patterns
        assert len(registry._patterns) == 1
        
        # Change config
        mock_manager.get.return_value = {
            "pattern1": {
                "regex": r"pattern1",
                "category": "sensitive_data",
                "severity": "medium",
                "description": "Pattern 1"
            },
            "pattern2": {
                "regex": r"pattern2",
                "category": "sensitive_data",
                "severity": "medium",
                "description": "Pattern 2"
            }
        }
        
        # Reload config
        registry.reload_config()
        
        # Check patterns were updated
        assert "pattern1" in registry._patterns
        assert "pattern2" in registry._patterns
        assert len(registry._patterns) == 2

    def test_thread_safety(self):
        """Test thread safety of pattern matching."""
        import threading
        
        # Create mock config manager
        mock_manager = MagicMock()
        mock_manager.get.return_value = {
            "test_pattern": {
                "regex": r"test\d+",
                "category": "sensitive_data",
                "severity": "medium",
                "description": "Test Pattern"
            }
        }
        
        # Create registry with mock config
        registry = PatternRegistry(mock_manager)
        
        # Test data
        text = "This contains test123 and test456"
        
        # Thread function
        def scan_in_thread(results):
            local_matches = registry.scan_text(text)
            results.append(len(local_matches))
        
        # Run multiple threads
        threads = []
        results = []
        for _ in range(10):
            thread = threading.Thread(target=scan_in_thread, args=(results,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All threads should have found 2 matches
        assert all(count == 2 for count in results)
    
    def test_api_key_detection(self):
        """Test detection of API keys."""
        # Use default patterns
        registry = PatternRegistry()
        
        # Test OpenAI API key
        text = "My OpenAI API key is sk-abcdefghijklmnopqrstuvwxyz123456"
        matches = registry.scan_text(text)
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "openai_api_key"
        
        # Test AWS key
        text = "AWS access key: AKIAIOSFODNN7EXAMPLE"
        matches = registry.scan_text(text)
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "aws_access_key"
        
        # Test Anthropic key
        text = "Anthropic key: sk-ant-abcdefghijklmnopqrstuvwxyz123456"
        matches = registry.scan_text(text)
        # Anthropic key matches both OpenAI and Anthropic patterns due to similar format
        assert len(matches) == 2
        # Ensure one of the matches is the anthropic_api_key
        pattern_names = [match["pattern_name"] for match in matches]
        assert "anthropic_api_key" in pattern_names or "api_key" in pattern_names
    
    def test_pii_detection(self):
        """Test detection of PII."""
        # Use default patterns
        registry = PatternRegistry()
        
        # Test credit card
        text = "My credit card is 4111-1111-1111-1111"
        matches = registry.scan_text(text)
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "credit_card"
        
        # Test email
        text = "My email is user@example.com"
        matches = registry.scan_text(text)
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "email_address"
        
        # Test phone number
        text = "My phone is 123-456-7890"
        matches = registry.scan_text(text)
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "phone_number"
        
        # Test SSN
        text = "SSN: 123-45-6789"
        matches = registry.scan_text(text)
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "ssn"
        
    def test_masking_functionality(self):
        """Test masking of sensitive values."""
        # Use default patterns
        registry = PatternRegistry()
        
        # Test credit card masking
        text = "My credit card is 4111-1111-1111-1111"
        matches = registry.scan_text(text, mask_values=True)
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "credit_card"
        assert matches[0]["matched_value"] == "4111-1111-1111-1111"  # Original value
        assert matches[0]["masked_value"] != matches[0]["matched_value"]  # Should be masked
        assert matches[0]["masked_value"].startswith("4111")  # Should keep first 4 digits
        assert matches[0]["masked_value"].endswith("1111")  # Should keep last 4 digits
        assert "****" in matches[0]["masked_value"]  # Should contain asterisks
        
        # Test email masking
        text = "My email is user@example.com"
        matches = registry.scan_text(text, mask_values=True)
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "email_address"
        assert matches[0]["matched_value"] == "user@example.com"  # Original value
        assert matches[0]["masked_value"] != matches[0]["matched_value"]  # Should be masked
        assert matches[0]["masked_value"].endswith("@example.com")  # Should keep domain
        assert "*" in matches[0]["masked_value"]  # Should contain asterisks
        
        # Test SSN masking
        text = "SSN: 123-45-6789"
        matches = registry.scan_text(text, mask_values=True)
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "ssn"
        assert matches[0]["matched_value"] == "123-45-6789"  # Original value
        assert matches[0]["masked_value"] != matches[0]["matched_value"]  # Should be masked
        assert matches[0]["masked_value"].endswith("6789")  # Should keep last 4 digits
        assert matches[0]["masked_value"].startswith("***")  # Should mask first part
        
        # Test API key masking
        text = "API key: sk-abcdefghijklmnopqrstuvwxyz123456"
        matches = registry.scan_text(text, mask_values=True)
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "openai_api_key"
        assert matches[0]["matched_value"] == "sk-abcdefghijklmnopqrstuvwxyz123456"  # Original value
        assert matches[0]["masked_value"] != matches[0]["matched_value"]  # Should be masked
        assert matches[0]["masked_value"].startswith("sk-")  # Should keep prefix
        assert "*" in matches[0]["masked_value"]  # Should contain asterisks
        
        # Test masking disabled
        text = "SSN: 123-45-6789"
        matches = registry.scan_text(text, mask_values=False)
        assert len(matches) == 1
        assert matches[0]["pattern_name"] == "ssn"
        assert matches[0]["matched_value"] == "123-45-6789"  # Original value
        assert matches[0]["masked_value"] == "123-45-6789"  # Should not be masked when disabled 