"""
Tests for the process execution monitoring sensor.
"""
import os
import subprocess
import unittest
from unittest.mock import patch

from cylestio_monitor._sensors.process import _span_popen, _span_system, initialize
from cylestio_monitor.patchers.process_patcher import (patch_process_monitoring,
                                                      unpatch_process_monitoring)


class TestProcessSensor(unittest.TestCase):
    """Test cases for process execution monitoring."""

    def setUp(self):
        """Set up test fixtures, patch event logging."""
        # Save original functions
        self.orig_popen = subprocess.Popen
        self.orig_system = os.system

        # Patch event logging
        self.log_event_patcher = patch('cylestio_monitor._sensors.process.log_event')
        self.mock_log_event = self.log_event_patcher.start()

    def tearDown(self):
        """Tear down test fixtures."""
        # Restore original functions
        subprocess.Popen = self.orig_popen
        os.system = self.orig_system

        # Stop patchers
        self.log_event_patcher.stop()

    def test_initialize(self):
        """Test initialization of the process monitoring sensor."""
        # Initialize the sensor
        initialize()

        # Verify that Popen and system are patched
        self.assertEqual(subprocess.Popen, _span_popen)
        self.assertEqual(os.system, _span_system)

    def test_span_popen(self):
        """Test the span_popen function."""
        # Initialize the sensor
        initialize()

        # Call subprocess.Popen to trigger our patched version
        process = subprocess.Popen(["echo", "test"], stdout=subprocess.PIPE)
        process.wait()

        # Verify that log_event was called twice
        # Once for the process.exec event, once for process.started
        self.assertEqual(self.mock_log_event.call_count, 2)

        # Check the first call arguments (process.exec)
        args, kwargs = self.mock_log_event.call_args_list[0]
        self.assertEqual(args[0], "process.exec")
        self.assertEqual(kwargs["level"], "WARNING")
        self.assertIn("proc.path", kwargs["attributes"])
        self.assertIn("proc.args", kwargs["attributes"])
        self.assertIn("proc.shell", kwargs["attributes"])
        self.assertIn("proc.parent_id", kwargs["attributes"])
        self.assertIn("session.id", kwargs["attributes"])

        # Check the second call arguments (process.started)
        args, kwargs = self.mock_log_event.call_args_list[1]
        self.assertEqual(args[0], "process.started")
        self.assertEqual(kwargs["level"], "INFO")
        self.assertIn("proc.child_id", kwargs["attributes"])
        self.assertIn("proc.path", kwargs["attributes"])
        self.assertIn("session.id", kwargs["attributes"])

    def test_span_system(self):
        """Test the span_system function."""
        # Initialize the sensor
        initialize()

        # Call os.system to trigger our patched version
        os.system("echo test")

        # Verify that log_event was called once
        self.assertEqual(self.mock_log_event.call_count, 1)

        # Check the call arguments
        args, kwargs = self.mock_log_event.call_args
        self.assertEqual(args[0], "process.exec")
        self.assertEqual(kwargs["level"], "WARNING")
        self.assertIn("proc.path", kwargs["attributes"])
        self.assertIn("proc.args", kwargs["attributes"])
        self.assertIn("proc.shell", kwargs["attributes"])
        self.assertEqual(kwargs["attributes"]["proc.shell"], True)
        self.assertIn("proc.parent_id", kwargs["attributes"])
        self.assertIn("session.id", kwargs["attributes"])

    def test_patcher_functions(self):
        """Test the patch_process_monitoring and unpatch_process_monitoring functions."""
        # Patch process monitoring
        result = patch_process_monitoring()
        self.assertTrue(result)

        # Verify that Popen and system are patched
        self.assertEqual(subprocess.Popen, _span_popen)
        self.assertEqual(os.system, _span_system)

        # Unpatch process monitoring
        result = unpatch_process_monitoring()
        self.assertTrue(result)

        # Verify that Popen and system are restored
        self.assertEqual(subprocess.Popen, self.orig_popen)
        self.assertEqual(os.system, self.orig_system)


if __name__ == '__main__':
    unittest.main()
