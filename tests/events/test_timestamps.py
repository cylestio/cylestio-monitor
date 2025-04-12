"""
Comprehensive tests for timestamp handling across Cylestio Monitor.

This module tests timestamp formatting and consistency across:
1. StandardizedEvent class
2. Event factory functions
3. Event attributes
"""

import datetime
from datetime import timezone, timedelta
import pytest
import types

from cylestio_monitor.events.schema import StandardizedEvent
from cylestio_monitor.events.factories import (
    create_llm_request_event,
    create_llm_response_event,
    create_tool_call_event,
    create_system_event
)
from cylestio_monitor.utils.event_utils import (
    get_utc_timestamp, 
    format_timestamp, 
    parse_timestamp
)
from tests.utils.timestamp_validation import (
    validate_timestamp_format,
    check_event_timestamps,
    check_events_list_timestamps
)

try:
    # Import patchers if available
    from cylestio_monitor.patchers.openai_patcher import OpenAIPatcher
except ImportError:
    # Mock for testing without patchers
    OpenAIPatcher = None


class TestTimestampConsistency:
    """Tests for timestamp consistency across the system."""

    def test_standardized_event_timestamp_str(self):
        """Test StandardizedEvent handles string timestamps correctly."""
        test_cases = [
            "2023-09-15T14:30:45.123Z",         # Z suffix
            "2023-09-15T14:30:45.123+00:00",    # +00:00 offset
            "2023-09-15T14:30:45.123-00:00",    # -00:00 offset
            "2023-09-15T10:30:45.123-04:00",    # Non-UTC timezone
            "2023-09-15T14:30:45",              # No timezone (assume UTC)
        ]
        
        for ts in test_cases:
            event = StandardizedEvent(
                timestamp=ts,
                level="INFO",
                agent_id="test-agent",
                name="test.event"
            )
            
            # Check main timestamp field
            assert validate_timestamp_format(event.timestamp)
            
            # Convert back to dictionary and check
            event_dict = event.to_dict()
            assert validate_timestamp_format(event_dict["timestamp"])

    def test_standardized_event_timestamp_datetime(self):
        """Test StandardizedEvent handles datetime timestamps correctly."""
        test_cases = [
            datetime.datetime(2023, 9, 15, 14, 30, 45, 123456, tzinfo=timezone.utc),  # UTC
            datetime.datetime(2023, 9, 15, 14, 30, 45, 123456),  # Naive
            datetime.datetime(2023, 9, 15, 10, 30, 45, 123456, 
                              tzinfo=timezone(timedelta(hours=-4))),  # Non-UTC
        ]
        
        for dt in test_cases:
            event = StandardizedEvent(
                timestamp=dt,
                level="INFO",
                agent_id="test-agent",
                name="test.event"
            )
            
            # Check main timestamp field
            assert validate_timestamp_format(event.timestamp)
            
            # Convert back to dictionary and check
            event_dict = event.to_dict()
            assert validate_timestamp_format(event_dict["timestamp"])
            
            # Check if non-UTC timestamps are properly converted
            if dt.tzinfo and dt.tzinfo != timezone.utc:
                utc_dt = dt.astimezone(timezone.utc)
                # Extract hour from formatted timestamp
                hour_in_timestamp = int(event.timestamp.split("T")[1].split(":")[0])
                assert hour_in_timestamp == utc_dt.hour

    def test_event_factories_timestamp_consistency(self):
        """Test that all event factory functions format timestamps consistently."""
        # Test datetime input
        test_dt = datetime.datetime(2023, 9, 15, 14, 30, 45, 123456, tzinfo=timezone.utc)
        
        # Create different types of events with the same timestamp
        llm_request = create_llm_request_event(
            agent_id="test-agent",
            provider="test",
            model="test-model",
            prompt="test",
            timestamp=test_dt
        )
        
        llm_response = create_llm_response_event(
            agent_id="test-agent",
            provider="test",
            model="test-model",
            response="test",
            timestamp=test_dt
        )
        
        tool_call = create_tool_call_event(
            agent_id="test-agent",
            tool_name="test-tool",
            inputs={"param": "value"},
            timestamp=test_dt
        )
        
        system_event = create_system_event(
            agent_id="test-agent",
            event_type="test",
            data={"test": "data"},
            timestamp=test_dt
        )
        
        # Check all events using the helper function
        assert check_event_timestamps(llm_request)
        assert check_event_timestamps(llm_response)
        assert check_event_timestamps(tool_call)
        assert check_event_timestamps(system_event)
        
        # Verify consistency in timestamps
        timestamps = [
            llm_request["timestamp"],
            llm_response["timestamp"],
            tool_call["timestamp"],
            system_event["timestamp"]
        ]
        
        # All timestamps should be identical since they came from the same input
        assert all(ts == timestamps[0] for ts in timestamps)

    def test_nested_event_timestamps(self):
        """Test timestamps in nested event attributes."""
        # Create an event with nested timestamps in attributes
        event = create_llm_request_event(
            agent_id="test-agent",
            provider="test",
            model="test-model",
            prompt="test",
            request_timestamp="2023-09-15T10:30:45-04:00",  # Non-UTC
            timestamp="2023-09-15T14:30:45Z"  # UTC
        )
        
        # Verify using helper function
        assert check_event_timestamps(event)
        
        # The timestamps should both be in UTC format with Z suffix
        # But they might have different values due to timezone conversion
        main_ts = event["timestamp"]
        nested_ts = event["attributes"]["llm.request.request_timestamp"]
        
        # Parse both timestamps to compare
        main_dt = datetime.datetime.fromisoformat(main_ts.replace("Z", "+00:00"))
        nested_dt = datetime.datetime.fromisoformat(nested_ts.replace("Z", "+00:00"))
        
        # Both should be in UTC
        assert main_dt.tzinfo == timezone.utc
        assert nested_dt.tzinfo == timezone.utc


@pytest.mark.skipif(OpenAIPatcher is None, reason="OpenAI patcher not available")
class TestTimestampValidationUtils:
    """Tests for the timestamp validation utilities."""
    
    def test_validate_timestamp_format(self):
        """Test that validate_timestamp_format correctly identifies valid and invalid timestamps."""
        # Valid formats should return True
        valid_timestamps = [
            "2023-09-15T14:30:45Z",
            "2023-09-15T14:30:45.123Z",
            "2023-09-15T14:30:45.123456Z",
            "2023-01-01T00:00:00.000000Z",
            "2050-12-31T23:59:59.999999Z"
        ]
        
        for ts in valid_timestamps:
            assert validate_timestamp_format(ts), f"Should be valid: {ts}"
        
        # Invalid formats should return False
        invalid_timestamps = [
            "2023-09-15T14:30:45",  # Missing Z
            "2023-09-15T14:30:45+00:00",  # Wrong timezone format
            "2023-09-15 14:30:45Z",  # Missing T
            "2023/09/15T14:30:45Z",  # Wrong date format
            "not a timestamp"
        ]
        
        for ts in invalid_timestamps:
            assert not validate_timestamp_format(ts), f"Should be invalid: {ts}"
    
    def test_check_event_timestamps(self):
        """Test that check_event_timestamps correctly validates event dictionaries."""
        # Event with all valid timestamps
        valid_event = {
            "timestamp": "2023-09-15T14:30:45Z",
            "attributes": {
                "request.timestamp": "2023-09-15T14:30:45.123Z",
                "response.timestamp": "2023-09-15T14:35:45.123Z"
            }
        }
        assert check_event_timestamps(valid_event)
        
        # Event with invalid main timestamp
        invalid_main_ts = {
            "timestamp": "2023-09-15T14:30:45",  # Missing Z
            "attributes": {
                "request.timestamp": "2023-09-15T14:30:45.123Z"
            }
        }
        assert not check_event_timestamps(invalid_main_ts)
        
        # Event with invalid attribute timestamp
        invalid_attr_ts = {
            "timestamp": "2023-09-15T14:30:45Z",
            "attributes": {
                "request.timestamp": "2023-09-15T14:30:45"  # Missing Z
            }
        }
        assert not check_event_timestamps(invalid_attr_ts)
        
        # Event with no timestamps (should pass as there's nothing to validate)
        no_ts = {
            "name": "test",
            "attributes": {
                "foo": "bar"
            }
        }
        assert check_event_timestamps(no_ts)
    
    def test_check_events_list_timestamps(self):
        """Test that check_events_list_timestamps correctly validates event lists."""
        # List with all valid events
        valid_events = [
            {"timestamp": "2023-09-15T14:30:45Z"},
            {"timestamp": "2023-09-15T14:35:45Z"}
        ]
        assert check_events_list_timestamps(valid_events)
        
        # List with one invalid event
        mixed_events = [
            {"timestamp": "2023-09-15T14:30:45Z"},  # Valid
            {"timestamp": "2023-09-15T14:35:45"}    # Invalid (missing Z)
        ]
        assert not check_events_list_timestamps(mixed_events) 