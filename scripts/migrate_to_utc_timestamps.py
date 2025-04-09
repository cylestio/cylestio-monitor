#!/usr/bin/env python3
"""
Migration script for standardizing event timestamps.

This script scans Python files in the cylestio_monitor package to find and replace
direct datetime.now().isoformat() calls with format_timestamp().
"""

import os
import re
import sys
from pathlib import Path

# Regular expressions for finding patterns
DATETIME_NOW_ISOFORMAT = r'datetime\.now\(\)\.isoformat\(\)'
NAIVE_TIMESTAMP_ASSIGNMENT = r'("timestamp"\s*:\s*)datetime\.now\(\)\.isoformat\(\)'
LLM_TIMESTAMP_ASSIGNMENT = r'("llm\.[^"]+?\.timestamp"\s*:\s*)datetime\.now\(\)\.isoformat\(\)'
TOOL_TIMESTAMP_ASSIGNMENT = r'("tool\.[^"]+?\.timestamp"\s*:\s*)datetime\.now\(\)\.isoformat\(\)'
SYSTEM_TIMESTAMP_ASSIGNMENT = r'("[^"]*?_time"\s*:\s*)datetime\.now\(\)\.isoformat\(\)'

# Replacement patterns
FORMAT_TIMESTAMP_IMPORT = 'from cylestio_monitor.utils.event_utils import format_timestamp'
EVENT_FACTORIES_IMPORT = 'from cylestio_monitor.events.factories import create_system_event, create_llm_request_event, create_llm_response_event, create_tool_call_event, create_tool_result_event'


def should_process_file(file_path):
    """Determine if a file should be processed."""
    # Skip migration script itself
    if "migrate_to_utc_timestamps.py" in str(file_path):
        return False
    
    # Skip test files except for actual application tests
    if "test_" in str(file_path) and "tests/utils/test_event_utils.py" not in str(file_path):
        return False
    
    # Skip documentation files
    if "docs/" in str(file_path) or file_path.suffix in (".md", ".rst"):
        return False
    
    # Only process Python files
    return file_path.suffix == ".py"


def add_import_if_missing(content, import_statement):
    """Add import statement if not already present."""
    if import_statement not in content:
        # Find the last import statement
        import_lines = re.findall(r'^import .*$|^from .* import .*$', content, re.MULTILINE)
        if import_lines:
            last_import_pos = content.rindex(import_lines[-1]) + len(import_lines[-1])
            return content[:last_import_pos] + '\n' + import_statement + content[last_import_pos:]
    return content


def replace_timestamp_patterns(content):
    """Replace timestamp patterns with format_timestamp()."""
    # Replace basic datetime.now().isoformat()
    content = re.sub(DATETIME_NOW_ISOFORMAT, 'format_timestamp()', content)
    
    # Replace timestamp assignments in dictionaries
    content = re.sub(NAIVE_TIMESTAMP_ASSIGNMENT, r'\1format_timestamp()', content)
    content = re.sub(LLM_TIMESTAMP_ASSIGNMENT, r'\1format_timestamp()', content)
    content = re.sub(TOOL_TIMESTAMP_ASSIGNMENT, r'\1format_timestamp()', content)
    content = re.sub(SYSTEM_TIMESTAMP_ASSIGNMENT, r'\1format_timestamp()', content)
    
    return content


def process_file(file_path):
    """Process a single file to replace timestamp patterns."""
    print(f"Processing {file_path}...")
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Make a copy of original content
    original_content = content
    
    # Add import if needed and datetime.now() is used
    if re.search(DATETIME_NOW_ISOFORMAT, content):
        content = add_import_if_missing(content, FORMAT_TIMESTAMP_IMPORT)
    
    # Replace timestamp patterns
    content = replace_timestamp_patterns(content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
    else:
        print(f"No changes needed in {file_path}")


def main():
    """Main function to process files and replace timestamp patterns."""
    # Get the root directory (assuming script is in scripts/)
    root_dir = Path(__file__).parent.parent
    src_dir = root_dir / "src" / "cylestio_monitor"
    
    # Find all Python files
    python_files = list(src_dir.glob("**/*.py"))
    
    # Add examples directory if it exists
    examples_dir = root_dir / "examples"
    if examples_dir.exists():
        python_files.extend(examples_dir.glob("**/*.py"))
    
    # Filter files
    python_files = [f for f in python_files if should_process_file(f)]
    
    # Process each file
    for file_path in python_files:
        process_file(file_path)
    
    print(f"Processed {len(python_files)} files")


if __name__ == "__main__":
    main() 