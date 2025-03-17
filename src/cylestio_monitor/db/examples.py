"""Examples demonstrating usage of the DatabaseManager class.

This module contains examples showing how to use the DatabaseManager class for
database initialization, verification, updates, and reset operations.
"""

import logging
from pathlib import Path

from cylestio_monitor.db.database_manager import DatabaseManager


def initialize_database_example():
    """Example of initializing a database."""
    # Create a DatabaseManager instance
    db_manager = DatabaseManager()
    
    # Initialize the database with default location
    result = db_manager.initialize_database()
    
    if result["success"]:
        print(f"Database successfully initialized at: {result['db_path']}")
        print(f"Tables created: {', '.join(result['tables'])}")
    else:
        print(f"Database initialization failed: {result['error']}")
    
    # Don't forget to close when done
    db_manager.close()


def custom_location_example(db_path: Path):
    """Example of initializing a database at a custom location."""
    db_manager = DatabaseManager()
    
    # Initialize with explicit path
    result = db_manager.initialize_database(db_path)
    
    if result["success"]:
        print(f"Database successfully initialized at custom location: {result['db_path']}")
    else:
        print(f"Database initialization failed: {result['error']}")
    
    db_manager.close()


def verify_schema_example():
    """Example of verifying database schema."""
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    # Verify the schema
    verification = db_manager.verify_schema()
    
    if verification["success"]:
        if verification["matches"]:
            print("Database schema matches model definitions.")
        else:
            print("Database schema has discrepancies:")
            
            if verification["missing_tables"]:
                print(f"Missing tables: {', '.join(verification['missing_tables'])}")
            
            if verification["missing_columns"]:
                for table, columns in verification["missing_columns"].items():
                    print(f"Table '{table}' missing columns: {', '.join(columns)}")
            
            if verification["extra_tables"]:
                print(f"Extra tables: {', '.join(verification['extra_tables'])}")
            
            if verification["extra_columns"]:
                for table, columns in verification["extra_columns"].items():
                    print(f"Table '{table}' has extra columns: {', '.join(columns)}")
    else:
        print(f"Schema verification failed: {verification['error']}")
    
    db_manager.close()


def update_schema_example():
    """Example of updating database schema."""
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    # Verify the schema first
    verification = db_manager.verify_schema()
    
    if verification["success"] and not verification["matches"]:
        print("Schema discrepancies found. Updating schema...")
        
        # Update the schema
        update_result = db_manager.update_schema()
        
        if update_result["success"]:
            print("Schema update successful!")
            
            if update_result["tables_added"]:
                print(f"Tables added: {', '.join(update_result['tables_added'])}")
            
            if update_result["tables_modified"]:
                print(f"Tables modified: {', '.join(update_result['tables_modified'])}")
        else:
            print(f"Schema update failed: {update_result['error']}")
    else:
        print("Schema is already up to date or verification failed.")
    
    db_manager.close()


def reset_database_example():
    """Example of resetting a database (with confirmation)."""
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    # This would normally be a user prompt
    confirm = input("Are you sure you want to reset the database? All data will be lost. (y/n): ")
    
    if confirm.lower() == 'y':
        try:
            result = db_manager.reset_database(force=True)
            
            if result["success"]:
                print("Database reset successful!")
                
                if result["backed_up"]:
                    print(f"Backup created at: {result['backup_path']}")
            else:
                print(f"Database reset failed: {result['error']}")
        except ValueError as e:
            print(f"Error: {str(e)}")
    else:
        print("Database reset cancelled.")
    
    db_manager.close()


def integration_with_existing_code_example():
    """Example showing integration with existing DBManager code."""
    # First initialize the database with DatabaseManager
    db_manager = DatabaseManager()
    init_result = db_manager.initialize_database()
    
    if init_result["success"]:
        print(f"Database initialized at: {init_result['db_path']}")
        
        # Verify and update if needed
        verification = db_manager.verify_schema()
        if not verification["matches"]:
            print("Updating schema...")
            db_manager.update_schema()
        
        # Now we can use the existing DBManager for database operations
        from cylestio_monitor.db.db_manager import DBManager
        
        # Get the DBManager singleton instance
        # It will use the same database we just initialized
        db_ops = DBManager()
        
        # Use DBManager for regular operations
        agent_id = db_ops.get_or_create_agent("example_agent")
        print(f"Got agent ID: {agent_id}")
        
        # Both managers should be closed when done
        db_ops.close()
        db_manager.close()
    else:
        print(f"Database initialization failed: {init_result['error']}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the examples
    print("=== Basic Initialization Example ===")
    initialize_database_example()
    
    print("\n=== Custom Location Example ===")
    custom_path = Path("./custom_database.db")
    custom_location_example(custom_path)
    
    print("\n=== Schema Verification Example ===")
    verify_schema_example()
    
    print("\n=== Schema Update Example ===")
    update_schema_example()
    
    print("\n=== Integration Example ===")
    integration_with_existing_code_example()
    
    # Reset example requires user input, so run it last
    print("\n=== Reset Database Example ===")
    reset_database_example() 