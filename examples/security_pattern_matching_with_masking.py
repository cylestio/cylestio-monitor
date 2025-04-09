#!/usr/bin/env python3
"""
Example script to demonstrate the pattern matching with masking functionality.

This script shows how sensitive data is masked when detected, allowing
for secure logging of security alerts without exposing the actual sensitive data.
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
    """Run pattern matching examples with masking."""
    print("\n--- Pattern Matching with Masking Examples ---")
    
    # Example: Credit Card
    text = "My credit card is 5482-4252-5231-5242 and expires 01/25"
    print(f"\nInput Text: {text}")
    
    # Direct pattern matching with masking
    print("\nDirect pattern matching with masking:")
    matches = pattern_registry.scan_text(text, mask_values=True)
    
    for match in matches:
        print(f"\nPattern: {match['pattern_name']}")
        print(f"Original value: {match['matched_value']}")
        print(f"Masked value:   {match['masked_value']}")
    
    # Full security scanning (which includes masking)
    print("\nFull security scanning (with automatic masking):")
    result = scanner.scan_text(text)
    
    # Show the masked values in scan results
    print("\nMasked keywords in scan results:")
    for keyword in result["keywords"]:
        print(f"  - {keyword}")
    
    print("\nMasked pattern matches in scan results:")
    for match in result.get("pattern_matches", []):
        print(f"  - {match['pattern_name']}: {match['matched_value']}")
    
    # Example: Multiple sensitive data types
    print("\n\n--- Example with Multiple Sensitive Data Types ---")
    text = """
    Here is my personal information:
    Credit Card: 4111-2222-3333-4444
    SSN: 123-45-6789
    Email: john.doe@example.com
    Phone: 555-123-4567
    API Key: sk-abcdefghijklmnopqrstuvwxyz123456
    AWS Key: AKIAIOSFODNN7EXAMPLE
    """
    print(f"Input text contains multiple types of sensitive data")
    
    # Security scan result
    result = scanner.scan_text(text)
    
    print(f"\nAlert level: {result['alert_level']}")
    print(f"Category: {result['category']}")
    print(f"Severity: {result['severity']}")
    
    print("\nMasked keywords in scan results:")
    for keyword in result["keywords"]:
        print(f"  - {keyword}")
    
    print("\nPattern matches (with masked values):")
    for match in result.get("pattern_matches", []):
        print(f"  - {match['pattern_name']}: {match['matched_value']}")
    
    # Demonstrate difference between masked and unmasked
    print("\n\n--- Comparing Masked vs. Unmasked Output ---")
    text = "SSN: 123-45-6789"
    
    # Unmasked pattern matching (should NOT be used in production)
    print("\nUNMASKED pattern matching (UNSAFE for logs):")
    unmasked_matches = pattern_registry.scan_text(text, mask_values=False)
    for match in unmasked_matches:
        print(f"Pattern: {match['pattern_name']}")
        print(f"Value:   {match['matched_value']}")
    
    # Masked pattern matching (SAFE for logs)
    print("\nMASKED pattern matching (SAFE for logs):")
    masked_matches = pattern_registry.scan_text(text, mask_values=True)
    for match in masked_matches:
        print(f"Pattern: {match['pattern_name']}")
        print(f"Value:   {match['masked_value']}")

if __name__ == "__main__":
    main() 