#!/usr/bin/env python3
"""
Verification script for event timestamp formatting.

This script monitors events generated by the system and verifies that
all timestamps follow the UTC format with "Z" suffix.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Regex pattern for valid ISO 8601 UTC timestamp with Z suffix
VALID_TIMESTAMP_PATTERN = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z'


def is_valid_timestamp(timestamp):
    """Check if a timestamp follows the UTC format with Z suffix."""
    return bool(re.match(VALID_TIMESTAMP_PATTERN, timestamp))


def validate_event_file(file_path):
    """Validate timestamps in an event log file."""
    print(f"Validating timestamps in {file_path}...")
    valid_count = 0
    invalid_count = 0
    invalid_lines = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                # Parse JSON event
                event = json.loads(line.strip())
                
                # Check primary timestamp
                if "timestamp" in event:
                    timestamp = event["timestamp"]
                    if not is_valid_timestamp(timestamp):
                        invalid_lines.append((line_num, "timestamp", timestamp))
                        invalid_count += 1
                    else:
                        valid_count += 1
                
                # Check nested timestamps in attributes
                if "attributes" in event and isinstance(event["attributes"], dict):
                    for key, value in event["attributes"].items():
                        if "timestamp" in key.lower() and isinstance(value, str):
                            if not is_valid_timestamp(value):
                                invalid_lines.append((line_num, key, value))
                                invalid_count += 1
                            else:
                                valid_count += 1
            except json.JSONDecodeError:
                print(f"Warning: Line {line_num} is not valid JSON")
    
    # Print results
    print(f"Found {valid_count} valid timestamps and {invalid_count} invalid timestamps")
    
    if invalid_lines:
        print("\nInvalid timestamps:")
        for line_num, key, value in invalid_lines:
            print(f"Line {line_num}, {key}: {value}")
        return False
    
    return True


def main():
    """Main function to validate event log files."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Validate event timestamp formatting")
    parser.add_argument("files", nargs="+", help="Event log files to validate")
    args = parser.parse_args()
    
    # Validate each file
    all_valid = True
    for file_pattern in args.files:
        # Expand wildcards
        for file_path in Path().glob(file_pattern):
            if not validate_event_file(file_path):
                all_valid = False
    
    # Return appropriate exit code
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main() 