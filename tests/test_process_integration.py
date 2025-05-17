"""
Integration test for process execution monitoring.
"""
import os
import subprocess
import unittest

from cylestio_monitor import start_monitoring, stop_monitoring


class TestProcessIntegration(unittest.TestCase):
    """Integration test for process execution monitoring."""

    def test_process_monitoring(self):
        """Test that process monitoring works when enabled through start_monitoring."""
        # Start monitoring
        start_monitoring(agent_id="test-process-agent")

        # Execute a process
        subprocess.run(["echo", "test"], check=True)

        # Execute a system command
        os.system("echo test")

        # Stop monitoring
        stop_monitoring()

        # No assertions needed - we're just checking that it runs without errors


if __name__ == "__main__":
    unittest.main()
