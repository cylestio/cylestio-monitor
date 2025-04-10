# Event Timestamp Migration Scripts

This directory contains scripts for standardizing event timestamp formatting across the codebase to ensure all timestamps are consistently in UTC format with the "Z" suffix.

## Available Scripts

1. **migrate_to_utc_timestamps.py**: Automatically finds and updates code that creates timestamps without proper UTC formatting
2. **verify_utc_timestamps.py**: Validates event log files to ensure all timestamps follow the required format

## Why Standardize Timestamps?

- **Consistency**: All event timestamps should follow the same format (UTC with "Z" suffix)
- **Clarity**: UTC timezone with Z suffix is ISO 8601 compliant and unambiguous
- **Interoperability**: Standard formats make integration with external systems easier
- **Analysis**: Consistent timestamps simplify data analysis across events

## How to Use

### Migrate Code

To automatically migrate timestamp creation code to use the new utilities:

```bash
# Run the migration script (from project root)
python scripts/migrate_to_utc_timestamps.py
```

This script will:
1. Scan Python files in the codebase
2. Find instances of `datetime.now().isoformat()`
3. Replace them with `format_timestamp()` from our utilities
4. Add the necessary import statements

### Verify Log Files

To verify that timestamps in your event log files are properly formatted:

```bash
# Verify timestamps in a specific log file
python scripts/verify_utc_timestamps.py path/to/log_file.json

# Use wildcards to check multiple files
python scripts/verify_utc_timestamps.py "logs/*.json"
```

This script will:
1. Parse each event in the log files
2. Check that all timestamp fields follow the UTC format with Z suffix
3. Report any non-compliant timestamps

## Manual Migration

For more complex cases, you should manually migrate to the new event utilities:

1. Use `format_timestamp()` for any basic timestamp generation
2. Use domain-specific factories for creating different types of events:
   - `create_llm_request_event()` and `create_llm_response_event()` for LLM events
   - `create_tool_call_event()` and `create_tool_result_event()` for tool events
   - `create_system_event()` for system events

## Troubleshooting

- If the migration script doesn't update a particular file, check if it has unusual patterns of creating timestamps
- For custom timestamp formats, you may need to manually refactor the code
- If verification fails, examine the specific fields that have incorrect formatting 