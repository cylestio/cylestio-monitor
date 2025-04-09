#!/usr/bin/env python3
"""
Example script to demonstrate the pattern matching functionality of the security scanner.

This script shows how the pattern-based security scanning works for detecting API keys,
PII, and other sensitive data patterns.
"""

import logging
import sys
from pprint import pprint

from cylestio_monitor.security_detection import SecurityScanner
from cylestio_monitor.security_detection.patterns import PatternRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# Create scanner instance
scanner = SecurityScanner.get_instance()

# Get pattern registry instance
pattern_registry = PatternRegistry.get_instance()

def main():
    """Run pattern matching examples."""
    print("\n--- Pattern Matching Examples ---")
    
    # Example 1: OpenAI API Key
    text1 = "My OpenAI API key is sk-abcdefghijklmnopqrstuvwxyz123456"
    print(f"\nExample 1: {text1}")
    
    # Direct pattern matching
    print("\nDirect pattern matching:")
    matches = pattern_registry.scan_text(text1)
    pprint(matches)
    
    # Full security scanning
    print("\nFull security scanning:")
    result = scanner.scan_text(text1)
    pprint(result)
    
    # Example 2: Credit Card Number
    text2 = "My credit card is 4111-1111-1111-1111 and expires 01/25"
    print(f"\nExample 2: {text2}")
    
    # Direct pattern matching
    print("\nDirect pattern matching:")
    matches = pattern_registry.scan_text(text2)
    pprint(matches)
    
    # Full security scanning
    print("\nFull security scanning:")
    result = scanner.scan_text(text2)
    pprint(result)
    
    # Example 3: Email and SSN
    text3 = "Please contact me at user@example.com, my SSN is 123-45-6789"
    print(f"\nExample 3: {text3}")
    
    # Direct pattern matching
    print("\nDirect pattern matching:")
    matches = pattern_registry.scan_text(text3)
    pprint(matches)
    
    # Full security scanning
    print("\nFull security scanning:")
    result = scanner.scan_text(text3)
    pprint(result)
    
    # Example 4: Multiple pattern types
    text4 = """
    Here is my info:
    Email: john.doe@example.com
    Phone: 555-123-4567
    Credit Card: 4111 1111 1111 1111
    SSN: 123-45-6789
    API Key: sk-abcdefghijklmnopqrstuvwxyz123456
    AWS Key: AKIAIOSFODNN7EXAMPLE
    """
    print(f"\nExample 4: Multiple pattern types")
    
    # Direct pattern matching
    print("\nDirect pattern matching:")
    matches = pattern_registry.scan_text(text4)
    pprint(matches)
    
    # Full security scanning
    print("\nFull security scanning:")
    result = scanner.scan_text(text4)
    pprint(result)
    
    # List all available patterns
    print("\nAvailable patterns:")
    for name, pattern_info in pattern_registry._patterns.items():
        print(f"  - {name}: {pattern_info['description']} (severity: {pattern_info['severity']})")

if __name__ == "__main__":
    main() 