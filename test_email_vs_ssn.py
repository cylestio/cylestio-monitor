#!/usr/bin/env python
"""Test script to verify email detection changes."""

import sys
import os
from cylestio_monitor.monitor import start_monitoring, stop_monitoring

def test_detection_mode(enforce_mode: bool):
    """Test terminal output in different modes.

    Args:
        enforce_mode: Whether to enforce masking
    """
    mode_title = "ENFORCE-MASKING MODE" if enforce_mode else "DETECTION-ONLY MODE"
    print(f"\n=== TESTING SENSITIVE VS PRIVATE DATA IN {mode_title} ===")

    # Start monitoring with debug mode
    start_monitoring(
        agent_id=f"test-{'enforce' if enforce_mode else 'detect'}-mode",
        config={
            "debug_mode": True,
            "enforce": enforce_mode,
            "debug_level": "DEBUG"
        }
    )

    # Print data to terminal
    print("\nPrinting sensitive and private data to terminal:")
    print("Email: user@example.com")
    print("SSN: 123-45-6789")
    print("Credit card: 4111-1111-1111-1111")

    # Stop monitoring
    stop_monitoring()
    print(f"\n{mode_title} test completed")

def main():
    """Run the tests in both modes."""
    # Test in detection-only mode first
    test_detection_mode(enforce_mode=False)

    # Test in enforce-masking mode
    test_detection_mode(enforce_mode=True)


if __name__ == "__main__":
    main()
