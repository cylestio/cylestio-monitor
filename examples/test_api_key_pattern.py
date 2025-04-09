#!/usr/bin/env python3
"""
Test script for OpenAI API key detection.

This script verifies that various OpenAI API key formats are properly detected.
"""

import logging
import sys

from cylestio_monitor.security_detection import SecurityScanner
from cylestio_monitor.security_detection.patterns import PatternRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# Get pattern registry instance
pattern_registry = PatternRegistry.get_instance()

def main():
    """Test various OpenAI API key formats."""
    # Reset the pattern registry to ensure we have the latest patterns
    PatternRegistry._instance = None
    PatternRegistry._is_initialized = False
    pattern_registry = PatternRegistry.get_instance()
    
    print("\n--- Testing OpenAI API Key Pattern Detection ---")
    
    test_keys = [
        # Standard format
        "sk-abcdefghijklmnopqrstuvwxyz123456",
        # With underscores
        "sk-abcdef_ghijklmnop_qrstuvwxyz123456",
        # With hyphens
        "sk-abcdef-ghijklmnop-qrstuvwxyz123456",
        # Organization keys
        "org-abcdefghijklmnopqrstuvwxyz123456",
        # Longer keys
        "sk-abcdefghijklmnopqrstuvwxyz1234567890abcdef",
        # Enter your actual key format here (masked)
        # "your-key-format-masked-for-testing"
    ]
    
    print(f"OpenAI API key regex pattern: {pattern_registry._patterns['openai_api_key']['pattern'].pattern}")
    print("\nTesting key detection:")
    
    for i, key in enumerate(test_keys):
        print(f"\nTest key #{i+1}: {key[:5]}...{key[-4:]}")
        
        # Check if key is detected by the pattern
        matches = pattern_registry.scan_text(f"API key: {key}", mask_values=True)
        
        if matches and any(m["pattern_name"] == "openai_api_key" for m in matches):
            match = next(m for m in matches if m["pattern_name"] == "openai_api_key")
            print(f"✅ DETECTED as OpenAI API key")
            print(f"   Masked value: {match['masked_value']}")
        else:
            print(f"❌ NOT DETECTED as OpenAI API key")

if __name__ == "__main__":
    main() 