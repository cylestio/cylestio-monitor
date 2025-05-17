#!/usr/bin/env python
"""
Test script for terminal output monitoring of sensitive data.
"""
import time
import sys
import os

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)

# Import Cylestio Monitor
from cylestio_monitor.monitor import start_monitoring, stop_monitoring
from cylestio_monitor.patchers.llm_output_patcher import patch_terminal_output

def main():
    """Test terminal output monitoring."""
    print("Starting terminal output monitoring test...")
    
    # Start monitoring with debug mode
    start_monitoring(
        agent_id="terminal-test-agent",
        config={
            "debug_mode": True,
            "events_output_file": os.path.join(script_dir, "output", "terminal_monitoring.json"),
            "debug_level": "DEBUG",
        }
    )
    
    # Wait a moment for monitoring to initialize
    time.sleep(1)
    
    print("\n=== Testing output with sensitive data ===")
    
    # Test with credit card
    print("Customer credit card: 4111-1111-1111-1111")
    
    # Test with SSN
    print("Social Security Number: 123-45-6789")
    
    # Test with multiple sensitive data in one string
    print("Multiple patterns in one message - CC: 4111-1111-1111-1111 and SSN: 123-45-6789")
    
    # Test with sensitive data in non-string type
    print("Complex data:", {
        "customer": {
            "name": "Test User",
            "credit_card": "4111-1111-1111-1111"
        }
    })
    
    # Test plain message without sensitive data
    print("This is a normal message with no sensitive data")
    
    print("\n=== Test completed ===")
    
    # Stop monitoring
    stop_monitoring()
    print("Monitoring stopped")

if __name__ == "__main__":
    main() 