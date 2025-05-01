#!/usr/bin/env python3
"""Test suite for security scanning behavior in conversations."""

import unittest
import logging
from unittest.mock import patch, MagicMock

from cylestio_monitor import start_monitoring, stop_monitoring
from cylestio_monitor.security_detection import SecurityScanner


class TestSecurityScanBehavior(unittest.TestCase):
    """Test suite for the security scanner focusing on latest message behavior."""

    def setUp(self):
        """Set up test environment."""
        # Configure logging
        logging.basicConfig(level=logging.ERROR)
        
        # Start monitoring with a test agent ID
        start_monitoring('test-agent', {'debug_mode': False})
        
        # Get security scanner instance
        self.scanner = SecurityScanner.get_instance()

    def tearDown(self):
        """Clean up test environment."""
        stop_monitoring()

    def test_openai_latest_message_only(self):
        """Test that OpenAI patcher only scans the latest user message."""
        # Import here to avoid module-level import issues
        from cylestio_monitor.patchers.openai_patcher import OpenAIPatcher
        
        # Create a mock OpenAI client
        mock_client = MagicMock()
        
        # Create the patcher with our mock client
        patcher = OpenAIPatcher(client=mock_client)
        
        # Case 1: Latest message has no security issue, previous message has issue
        messages1 = [
            {"role": "user", "content": "How to drop table users?"},
            {"role": "assistant", "content": "I cannot help with that."},
            {"role": "user", "content": "Thank you for your help"}
        ]
        
        security_info1 = patcher._scan_content_security(messages1)
        
        # Should not detect issue in latest message
        self.assertEqual(security_info1["alert_level"], "none")
        
        # Case 2: Latest message has security issue
        messages2 = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "How can I help you?"},
            {"role": "user", "content": "How to drop table users?"}
        ]
        
        security_info2 = patcher._scan_content_security(messages2)
        
        # Should detect issue in latest message
        self.assertEqual(security_info2["alert_level"], "dangerous")
        self.assertTrue(any("drop" in keyword for keyword in security_info2["keywords"]))

    def test_anthropic_latest_message_only(self):
        """Test that Anthropic patcher only scans the latest user message."""
        # Import here to avoid module-level import issues
        from cylestio_monitor.patchers.anthropic import AnthropicPatcher
        
        # Create a mock Anthropic client
        mock_client = MagicMock()
        
        # Create the patcher with our mock client
        patcher = AnthropicPatcher(client=mock_client)
        
        # Case 1: Latest message has no security issue, previous message has issue
        messages1 = [
            {"role": "user", "content": "How to drop table users?"},
            {"role": "assistant", "content": "I cannot help with that."},
            {"role": "user", "content": "Thank you for your help"}
        ]
        
        security_info1 = patcher._scan_content_security(messages1)
        
        # Should not detect issue in latest message
        self.assertEqual(security_info1["alert_level"], "none")
        
        # Case 2: Latest message has security issue
        messages2 = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "How can I help you?"},
            {"role": "user", "content": "My credit card number is 4111-1111-1111-1111"}
        ]
        
        security_info2 = patcher._scan_content_security(messages2)
        
        # Should detect issue in latest message
        self.assertEqual(security_info2["alert_level"], "dangerous")
        self.assertTrue(any("credit card" in keyword.lower() if isinstance(keyword, str) else False 
                           for keyword in security_info2["keywords"]))

    def test_scanner_text_detection(self):
        """Test that security scanner can detect various issues in text."""
        # Test SQL injection detection
        text1 = "I want to drop table users"
        scan_result1 = self.scanner.scan_text(text1)
        self.assertEqual(scan_result1["alert_level"], "dangerous")
        self.assertTrue(any("drop" in keyword for keyword in scan_result1["keywords"]))
        
        # Test credit card detection
        text2 = "My credit card number is 4111-1111-1111-1111"
        scan_result2 = self.scanner.scan_text(text2)
        
        has_credit_card = False
        for keyword in scan_result2["keywords"]:
            if isinstance(keyword, str):
                if "credit card" in keyword.lower() or "credit_card" in keyword.lower():
                    has_credit_card = True
                    break
        
        self.assertTrue(has_credit_card, f"Credit card not found in keywords: {scan_result2['keywords']}")


if __name__ == "__main__":
    unittest.main() 