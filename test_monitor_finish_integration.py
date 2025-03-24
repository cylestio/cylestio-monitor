#!/usr/bin/env python3
"""
Test script for monitor_finish event integration
"""

import os
import json
import time
import sys

# Path to src directory
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import from the source directly to test our changes
from cylestio_monitor import enable_monitoring
from cylestio_monitor.monitor import disable_monitoring

def main():
    """Run a simple test of the monitor_finish event"""
    # Create a log file for this test
    log_file = "output/monitor_finish_test.json"
    os.makedirs("output", exist_ok=True)
    
    # Enable monitoring
    print("Enabling monitoring...")
    enable_monitoring(
        agent_id="test-monitor-finish",
        config={
            "log_file": log_file
        }
    )
    
    # Wait a moment
    print("Monitoring enabled, waiting a moment...")
    time.sleep(1)
    
    # Disable monitoring
    print("Disabling monitoring...")
    disable_monitoring()
    
    # Check log file
    try:
        with open(log_file, "r") as f:
            log_lines = f.readlines()
            
        print(f"Log file contains {len(log_lines)} events.")
        print("Event types:")
        
        # Parse JSON and print details
        event_types = []
        for line in log_lines:
            try:
                event = json.loads(line)
                event_type = event.get("event_type", "unknown")
                if event_type not in event_types:
                    event_types.append(event_type)
            except json.JSONDecodeError:
                continue
        
        for i, event_type in enumerate(event_types):
            print(f"  {i+1}. {event_type}")
            
        # Check specifically for monitor_finish
        monitor_finish_count = sum(1 for line in log_lines if '"event_type": "monitor_finish"' in line)
        print(f"\nFound {monitor_finish_count} monitor_finish events.")
        
        if monitor_finish_count == 0:
            print("ERROR: No monitor_finish events found!")
        else:
            print("SUCCESS: monitor_finish event was generated!")
            
    except Exception as e:
        print(f"Error reading log file: {e}")
    
    print("\nTest complete!")

if __name__ == "__main__":
    main() 