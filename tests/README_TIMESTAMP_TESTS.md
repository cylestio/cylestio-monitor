# Timestamp Tests Overview

This document describes the timestamp tests implemented as part of the UTC Timestamp Standardization project.

## Purpose

These tests ensure that all timestamps in the Cylestio Monitor system are consistently formatted as UTC timestamps with the "Z" suffix in ISO8601 format. Proper timestamp formatting is critical for:

1. Accurate chronological sorting of events
2. Consistent event processing across timezones
3. Reliable interoperability with external systems
4. Accurate time-based analytics

## Test Structure

The timestamp tests are organized into several modules:

### 1. Timestamp Validation Utilities (`tests/utils/timestamp_validation.py`)

Contains reusable functions for validating timestamp formats:

- `validate_timestamp_format()`: Checks if a string is a valid ISO8601 UTC timestamp with Z suffix
- `check_event_timestamps()`: Recursively checks all timestamps in an event dictionary
- `check_events_list_timestamps()`: Validates timestamps in a list of events

### 2. Core Timestamp Utilities Tests (`tests/utils/test_event_utils.py`)

Tests the core timestamp utility functions:

- `get_utc_timestamp()`
- `format_timestamp()`
- `parse_timestamp()`
- `validate_iso8601()`

Also includes tests for edge cases and validation.

### 3. Event Timestamp Consistency Tests (`tests/events/test_timestamps.py`)

Tests timestamp formatting across different components:

- StandardizedEvent class
- Event factory functions
- Nested timestamps in event attributes

### 4. Patcher Timestamp Tests (`tests/patchers/test_patcher_timestamps.py`)

Tests that patchers correctly format timestamps:

- OpenAI patcher
- Langchain patcher
- Tool decorator patcher

## Running the Tests

Run all timestamp tests:

```
pytest tests/utils/test_event_utils.py tests/events/test_timestamps.py tests/patchers/test_patcher_timestamps.py -v
```

Or run individual test modules:

```
pytest tests/events/test_timestamps.py -v
```

## Test Markers

Some tests use the `skipif` marker to handle cases where certain patchers are not available:

```python
@pytest.mark.skipif(OpenAIPatcher is None, reason="OpenAI patcher not available")
```

## Expected Results

All timestamp-related tests should pass after implementing Tasks 1-6 of the UTC Timestamp Standardization project. If any tests fail, check that:

1. The timestamp utilities in `utils/event_utils.py` are properly implemented
2. The StandardizedEvent class correctly normalizes timestamps
3. Factory functions use the standardized timestamp utilities
4. Patchers correctly format timestamps in events they generate 