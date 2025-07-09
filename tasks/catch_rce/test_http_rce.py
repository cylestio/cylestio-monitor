#!/usr/bin/env python
"""
Test script for HTTP-based RCE detection in Cylestio Monitor.
This script sends HTTP requests with SQL queries containing shell commands.
"""

import os
import sys
import time
import subprocess
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_http_rce")

def setup_monitor():
    """Import and initialize Cylestio Monitor."""
    try:
        # Add the project root to the Python path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        sys.path.insert(0, project_root)

        # Import Cylestio Monitor modules
        from cylestio_monitor.patchers.http_patcher import patch_http_monitoring
        from cylestio_monitor.patchers.process_patcher import patch_process_monitoring

        # Initialize the monitoring components
        logger.info("Initializing HTTP monitoring...")
        http_result = patch_http_monitoring()
        logger.info(f"HTTP monitoring initialized: {http_result}")

        logger.info("Initializing process monitoring...")
        process_result = patch_process_monitoring(enable_detection=True)
        logger.info(f"Process monitoring initialized: {process_result}")

        return http_result and process_result
    except Exception as e:
        logger.error(f"Error setting up monitor: {e}")
        return False

def test_http_sql_shell_command():
    """Test HTTP request with SQL query containing shell command."""
    try:
        # Use localhost to avoid actual network requests
        url = "http://localhost:12345"  # Non-existent service, just for testing

        # Test with different SQL patterns containing shell commands
        test_patterns = [
            # Simple shell command in WHERE clause
            {"query": "SELECT * FROM users WHERE name = 'ls -la'"},

            # Command with path
            {"query": "SELECT * FROM data WHERE path = '/bin/cat /etc/passwd'"},

            # Context switching pattern
            {"query": "SELECT * FROM system WHERE mode = 'enable-shell'"},

            # Multiple commands
            {"query": "SELECT * FROM files WHERE filename = 'file.txt'; cat /etc/passwd"}
        ]

        for i, payload in enumerate(test_patterns):
            logger.info(f"Sending test request {i+1} with payload: {payload}")

            try:
                # Send the request - will fail to connect but the HTTP patcher should still detect it
                requests.post(url, json=payload, timeout=1)
            except requests.exceptions.RequestException:
                # Expected to fail - service doesn't exist
                pass

            # Add a small delay to let the detection process work
            time.sleep(1)

            # After HTTP request, execute a shell command to test correlation
            logger.info("Executing shell command to test HTTP-to-shell correlation")
            try:
                subprocess.run(["ls", "-la"], capture_output=True, check=True)
            except subprocess.SubprocessError:
                pass

            # Wait for correlation to complete
            time.sleep(2)
    except Exception as e:
        logger.error(f"Error in HTTP RCE test: {e}")

def main():
    """Main test function."""
    logger.info("Starting HTTP-based RCE detection test")

    if not setup_monitor():
        logger.error("Failed to set up monitoring. Exiting.")
        return 1

    # Run the tests
    test_http_sql_shell_command()

    logger.info("HTTP-based RCE detection test completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
