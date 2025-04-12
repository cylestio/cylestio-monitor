#!/usr/bin/env python3
"""
Migration script for standardizing event timestamps.

This script scans Python files in the cylestio_monitor package to find and replace
various timestamp generation patterns with the standardized timestamp utilities.
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Regular expressions for finding patterns
DATETIME_NOW_ISOFORMAT = r'datetime\.now\(\)\.isoformat\(\)'
NAIVE_TIMESTAMP_ASSIGNMENT = r'("timestamp"\s*:\s*)datetime\.now\(\)\.isoformat\(\)'
LLM_TIMESTAMP_ASSIGNMENT = r'("llm\.[^"]+?\.timestamp"\s*:\s*)datetime\.now\(\)\.isoformat\(\)'
TOOL_TIMESTAMP_ASSIGNMENT = r'("tool\.[^"]+?\.timestamp"\s*:\s*)datetime\.now\(\)\.isoformat\(\)'
SYSTEM_TIMESTAMP_ASSIGNMENT = r'("[^"]*?_time"\s*:\s*)datetime\.now\(\)\.isoformat\(\)'

# Additional regex patterns for timestamp generation
DATETIME_NOW = r'datetime\.now\(\)(?!\.isoformat\(\)|\.strftime|\(timezone\.utc\))'
DATETIME_NOW_WITH_STRFTIME = r'datetime\.now\(\)\.strftime\([\'"]([^\'"]+)[\'"]\)'
TIMESTAMP_ASSIGNMENT = r'([\'"]timestamp[\'"]\s*:\s*)datetime\.now\(\)'
IF_TIMESTAMP_NONE = r'if\s+timestamp\s*(?:is|==)\s*None\s*:\s*timestamp\s*=\s*datetime\.now\(\)'
TIMESTAMP_VARIABLE_ASSIGN = r'(\w+)(?:\s*=\s*)datetime\.now\(\)(?!\(timezone\.utc\))(?!\s*\.\s*replace\s*\(\s*tzinfo\s*=\s*timezone\.utc\s*\))'
DATETIME_UTC_NOW = r'datetime\.utcnow\(\)'
TIMESTAMP_ARG_DEFAULT = r'(timestamp\s*=\s*)datetime\.now\(\)'
CLASS_INIT_TIMESTAMP = r'(self\.[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*)datetime\.now\(\)'

# Replacement patterns
FORMAT_TIMESTAMP_IMPORT = 'from cylestio_monitor.utils.event_utils import format_timestamp'
GET_UTC_TIMESTAMP_IMPORT = 'from cylestio_monitor.utils.event_utils import get_utc_timestamp'
BOTH_IMPORTS = 'from cylestio_monitor.utils.event_utils import format_timestamp, get_utc_timestamp'
EVENT_FACTORIES_IMPORT = 'from cylestio_monitor.events.factories import create_system_event, create_llm_request_event, create_llm_response_event, create_tool_call_event, create_tool_result_event'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("timestamp_migration")


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


def add_import_if_missing(content, import_statements):
    """
    Add import statements if not already present.
    
    Args:
        content: File content
        import_statements: List of import statements to add
        
    Returns:
        str: Content with imports added if needed
    """
    if not isinstance(import_statements, list):
        import_statements = [import_statements]
    
    modified_content = content
    
    for import_statement in import_statements:
        if import_statement not in modified_content:
            # Find the last import statement
            import_lines = re.findall(r'^import .*$|^from .* import .*$', modified_content, re.MULTILINE)
            if import_lines:
                last_import_pos = modified_content.rindex(import_lines[-1]) + len(import_lines[-1])
                modified_content = modified_content[:last_import_pos] + '\n' + import_statement + modified_content[last_import_pos:]
            else:
                # No imports found, add at the beginning after any module docstring
                docstring_match = re.match(r'(^""".*?"""\s*\n)', modified_content, re.DOTALL)
                if docstring_match:
                    end_pos = docstring_match.end()
                    modified_content = modified_content[:end_pos] + '\n' + import_statement + '\n' + modified_content[end_pos:]
                else:
                    # No docstring, add at the beginning
                    modified_content = import_statement + '\n' + modified_content
    
    return modified_content


def handle_strftime_replacement(format_str):
    """
    Handle various strftime format patterns.
    
    Args:
        format_str: The strftime format string
        
    Returns:
        str: Replacement code using UTC timestamp
    """
    # If it's a simple date or datetime format, use the format_timestamp function
    # with appropriate post-processing
    if re.match(r'%Y-%m-%d %H:%M:%S', format_str):
        return "format_timestamp().replace('T', ' ').replace('Z', '')"
    elif re.match(r'%Y%m%d-%H%M%S', format_str):
        return "get_utc_timestamp().strftime('%Y%m%d-%H%M%S')"
    elif re.match(r'%Y-%m-%d', format_str):
        return "get_utc_timestamp().strftime('%Y-%m-%d')"
    elif re.match(r'%H:%M:%S', format_str):
        return "get_utc_timestamp().strftime('%H:%M:%S')"
    else:
        # For more complex formats, keep the original strftime but use UTC timestamp
        return f"get_utc_timestamp().strftime('{format_str}')"


def replace_timestamp_patterns(content):
    """
    Replace timestamp patterns with standardized UTC timestamp utilities.
    
    Args:
        content: File content to process
        
    Returns:
        Tuple[str, int]: Modified content and count of patterns replaced
    """
    original_content = content
    patterns_replaced = 0
    
    # Replace patterns for direct datetime.now() usage
    new_content, replaced = re.subn(
        DATETIME_NOW, 
        'get_utc_timestamp()', 
        content
    )
    patterns_replaced += replaced
    content = new_content
    
    # Replace datetime.utcnow() patterns
    new_content, replaced = re.subn(
        DATETIME_UTC_NOW,
        'get_utc_timestamp()',
        content
    )
    patterns_replaced += replaced
    content = new_content
    
    # Replace datetime.now().strftime() patterns
    new_content, replaced = re.subn(
        DATETIME_NOW_WITH_STRFTIME,
        lambda m: handle_strftime_replacement(m.group(1)),
        content
    )
    patterns_replaced += replaced
    content = new_content
    
    # Replace timestamp variable assignments
    new_content, replaced = re.subn(
        TIMESTAMP_VARIABLE_ASSIGN,
        r'\1 = get_utc_timestamp()',
        content
    )
    patterns_replaced += replaced
    content = new_content
    
    # Replace "if timestamp is None" patterns
    new_content, replaced = re.subn(
        IF_TIMESTAMP_NONE,
        'if timestamp is None: timestamp = get_utc_timestamp()',
        content
    )
    patterns_replaced += replaced
    content = new_content
    
    # Replace timestamp argument default patterns
    new_content, replaced = re.subn(
        TIMESTAMP_ARG_DEFAULT,
        r'\1get_utc_timestamp()',
        content
    )
    patterns_replaced += replaced
    content = new_content
    
    # Replace class init timestamp assignment
    new_content, replaced = re.subn(
        CLASS_INIT_TIMESTAMP,
        r'\1get_utc_timestamp()',
        content
    )
    patterns_replaced += replaced
    content = new_content
    
    # Replace timestamp assignments in dictionaries
    new_content, replaced = re.subn(
        TIMESTAMP_ASSIGNMENT,
        r'\1get_utc_timestamp()',
        content
    )
    patterns_replaced += replaced
    content = new_content
    
    # Original patterns from current implementation
    new_content, replaced = re.subn(DATETIME_NOW_ISOFORMAT, 'format_timestamp()', content)
    patterns_replaced += replaced
    content = new_content
    
    new_content, replaced = re.subn(NAIVE_TIMESTAMP_ASSIGNMENT, r'\1format_timestamp()', content)
    patterns_replaced += replaced
    content = new_content
    
    new_content, replaced = re.subn(LLM_TIMESTAMP_ASSIGNMENT, r'\1format_timestamp()', content)
    patterns_replaced += replaced
    content = new_content
    
    new_content, replaced = re.subn(TOOL_TIMESTAMP_ASSIGNMENT, r'\1format_timestamp()', content)
    patterns_replaced += replaced
    content = new_content
    
    new_content, replaced = re.subn(SYSTEM_TIMESTAMP_ASSIGNMENT, r'\1format_timestamp()', content)
    patterns_replaced += replaced
    content = new_content
    
    return content, patterns_replaced


def process_file(file_path, dry_run=False):
    """
    Process a single file to replace timestamp patterns.
    
    Args:
        file_path: Path to the file to process
        dry_run: If True, do not modify files
        
    Returns:
        Dict: Statistics about the file processing
    """
    file_stats = {
        'updated': False,
        'patterns_replaced': 0
    }
    
    logger.info(f"Processing {file_path}...")
    
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Make a copy of original content
        original_content = content
        
        # Determine which imports are needed based on patterns in the file
        imports_needed = []
        
        if re.search(DATETIME_NOW_ISOFORMAT, content) or re.search(NAIVE_TIMESTAMP_ASSIGNMENT, content):
            imports_needed.append(FORMAT_TIMESTAMP_IMPORT)
            
        if (re.search(DATETIME_NOW, content) or re.search(DATETIME_NOW_WITH_STRFTIME, content) or 
            re.search(TIMESTAMP_VARIABLE_ASSIGN, content) or re.search(DATETIME_UTC_NOW, content)):
            imports_needed.append(GET_UTC_TIMESTAMP_IMPORT)
        
        # If both imports are needed, use the combined import instead
        if FORMAT_TIMESTAMP_IMPORT in imports_needed and GET_UTC_TIMESTAMP_IMPORT in imports_needed:
            imports_needed = [item for item in imports_needed if item not in (FORMAT_TIMESTAMP_IMPORT, GET_UTC_TIMESTAMP_IMPORT)]
            imports_needed.append(BOTH_IMPORTS)
        
        # Add necessary imports
        if imports_needed:
            content = add_import_if_missing(content, imports_needed)
        
        # Replace timestamp patterns
        content, patterns_replaced = replace_timestamp_patterns(content)
        file_stats['patterns_replaced'] = patterns_replaced
        
        # Write back if changed and not in dry run mode
        if content != original_content:
            file_stats['updated'] = True
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Updated {file_path} - Replaced {patterns_replaced} patterns")
            else:
                logger.info(f"Would update {file_path} - Found {patterns_replaced} patterns (dry run)")
        else:
            logger.info(f"No changes needed in {file_path}")
    
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        file_stats['error'] = str(e)
    
    return file_stats


def main():
    """Main function to process files and replace timestamp patterns."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Migrate timestamp patterns to UTC format')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying files')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--path', type=str, help='Specific directory or file to process')
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Starting UTC timestamp migration {'(dry run)' if args.dry_run else ''}")
    
    # Get the root directory (assuming script is in scripts/)
    root_dir = Path(__file__).parent.parent
    
    # Determine paths to scan
    if args.path:
        target_path = Path(args.path)
        if not target_path.exists():
            logger.error(f"Path not found: {args.path}")
            sys.exit(1)
        
        if target_path.is_file():
            python_files = [target_path] if target_path.suffix == ".py" else []
        else:
            python_files = list(target_path.glob("**/*.py"))
    else:
        # Default behavior: scan all project files
        src_dir = root_dir / "src" / "cylestio_monitor"
        python_files = list(src_dir.glob("**/*.py"))
        
        # Add examples directory if it exists
        examples_dir = root_dir / "examples"
        if examples_dir.exists():
            python_files.extend(examples_dir.glob("**/*.py"))
    
    # Filter files
    python_files = [f for f in python_files if should_process_file(f)]
    
    # Track statistics
    stats = {
        'files_processed': 0,
        'files_updated': 0,
        'patterns_replaced': 0,
        'errors': 0
    }
    
    # Process each file
    for file_path in python_files:
        # Process the file and collect statistics
        file_stats = process_file(file_path, dry_run=args.dry_run)
        
        # Update overall statistics
        stats['files_processed'] += 1
        stats['files_updated'] += 1 if file_stats['updated'] else 0
        stats['patterns_replaced'] += file_stats['patterns_replaced']
        stats['errors'] += 1 if 'error' in file_stats else 0
    
    # Print summary
    logger.info(f"\nMigration Summary:")
    logger.info(f"Files processed: {stats['files_processed']}")
    logger.info(f"Files updated: {stats['files_updated']}")
    logger.info(f"Patterns replaced: {stats['patterns_replaced']}")
    if stats['errors'] > 0:
        logger.info(f"Errors encountered: {stats['errors']}")
    
    if args.dry_run:
        logger.info("\nThis was a dry run. No files were modified.")


if __name__ == "__main__":
    main() 