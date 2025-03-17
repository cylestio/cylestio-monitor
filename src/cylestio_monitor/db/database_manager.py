"""Database initialization and management module for Cylestio Monitor.

This module provides a comprehensive database management system for Cylestio Monitor,
handling initialization, verification, updates, and reset operations. It's designed
to ensure a robust and reliable database state while providing detailed reporting
on any issues encountered.
"""

import logging
import os
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

import platformdirs
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from cylestio_monitor.db.models import Base, get_all_models

logger = logging.getLogger("CylestioMonitor")


class DatabaseManager:
    """
    Manages database initialization, verification, and updates.
    
    This class provides comprehensive database management functionality,
    allowing for initialization, verification, updates, and reset operations.
    It ensures the database schema matches the SQLAlchemy model definitions
    and provides detailed reporting on any discrepancies.
    """

    def __init__(self):
        """Initialize the DatabaseManager (without connecting to a database)."""
        self._engine = None
        self._Session = None
        self._lock = threading.Lock()
        self._initialized = False
        self._db_path = None
        self._data_dir = None
        self._sql_logger = logging.getLogger("sqlalchemy.engine")
    
    def initialize_database(self, db_path: Optional[Path] = None, enable_sql_logging: bool = False) -> Dict[str, Any]:
        """
        Initialize the database with the schema defined by SQLAlchemy models.
        
        Args:
            db_path: Optional explicit path to the database file.
                    If not provided, uses platformdirs to determine the location.
            enable_sql_logging: Whether to enable SQLAlchemy query logging (for development)
        
        Returns:
            Dict containing initialization status and details:
                - success: Whether initialization was successful
                - db_path: Path to the database file
                - created: Whether a new database was created
                - error: Error message if initialization failed
                - tables: List of created tables
        
        Raises:
            PermissionError: If the process lacks permission to create/write to the database
            OSError: If there is an OS-level error creating the database
        """
        with self._lock:
            # Set up the result dictionary
            result = {
                "success": False,
                "db_path": None,
                "created": False,
                "error": None,
                "tables": [],
            }
            
            try:
                # Determine database path
                if db_path is not None:
                    self._db_path = db_path
                    self._data_dir = db_path.parent
                else:
                    # Check if we're in test mode
                    test_db_dir = os.environ.get("CYLESTIO_TEST_DB_DIR")
                    if test_db_dir:
                        self._data_dir = Path(test_db_dir)
                    else:
                        self._data_dir = Path(platformdirs.user_data_dir(
                            appname="cylestio-monitor",
                            appauthor="cylestio"
                        ))
                    self._db_path = self._data_dir / "cylestio_monitor.db"
                
                # Create directory if it doesn't exist
                os.makedirs(self._data_dir, exist_ok=True)
                
                # Check directory permissions
                if not os.access(self._data_dir, os.W_OK):
                    error_msg = f"Insufficient permissions to write to directory: {self._data_dir}"
                    logger.error(error_msg)
                    result["error"] = error_msg
                    return result
                
                # Check if database already exists
                newly_created = not self._db_path.exists()
                result["created"] = newly_created
                
                # Set up SQL logging if requested or in development mode
                development_mode = os.environ.get("CYLESTIO_DEVELOPMENT_MODE", "0").lower() in ("1", "true", "yes")
                if enable_sql_logging or development_mode:
                    self._sql_logger.setLevel(logging.DEBUG)
                    # Add a handler if none exists
                    if not self._sql_logger.handlers:
                        console_handler = logging.StreamHandler()
                        console_handler.setFormatter(logging.Formatter(
                            "SQLAlchemy: %(message)s"
                        ))
                        self._sql_logger.addHandler(console_handler)
                        logger.info("SQLAlchemy query logging enabled")
                else:
                    self._sql_logger.setLevel(logging.WARNING)
                
                # Create the SQLAlchemy engine
                sqlite_url = f"sqlite:///{self._db_path}"
                self._engine = create_engine(
                    sqlite_url,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    connect_args={"check_same_thread": False},
                    echo=enable_sql_logging or development_mode
                )
                
                # Create session factory
                self._Session = sessionmaker(bind=self._engine)
                
                # If newly created or if tables don't exist, create them
                if newly_created or not self._tables_exist():
                    Base.metadata.create_all(self._engine)
                    logger.info("Database tables created")
                else:
                    # Check for schema updates using migration support
                    self._check_for_schema_updates()
                
                # Get list of created tables
                inspector = inspect(self._engine)
                result["tables"] = inspector.get_table_names()
                
                self._initialized = True
                result["success"] = True
                result["db_path"] = str(self._db_path)
                
                logger.info(f"Database {'created' if newly_created else 'connected'} at {self._db_path}")
                
            except PermissionError as e:
                error_msg = f"Permission error: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg
                
            except SQLAlchemyError as e:
                error_msg = f"Database error: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg
                
            except OSError as e:
                error_msg = f"OS error: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg
                
            return result
    
    def _tables_exist(self) -> bool:
        """
        Check if the tables exist in the database.
        
        Returns:
            bool: True if all required tables exist, False otherwise
        """
        if not self._engine:
            return False
        
        inspector = inspect(self._engine)
        existing_tables = set(inspector.get_table_names())
        
        # Get table names from our models
        model_tables = {model.__tablename__ for model in get_all_models()}
        
        # Check if all model tables exist in the database
        return model_tables.issubset(existing_tables)
    
    def _check_for_schema_updates(self) -> None:
        """
        Check for schema updates and apply migrations if needed.
        
        This implements basic migration support by comparing the existing schema
        with the model definitions and adding missing columns or tables.
        """
        if not self._engine:
            return
        
        try:
            inspector = inspect(self._engine)
            existing_tables = set(inspector.get_table_names())
            
            # Get all model tables
            metadata = Base.metadata
            model_tables = {table.name: table for table in metadata.tables.values()}
            
            # Check for missing tables and create them
            missing_tables = set(model_tables.keys()) - existing_tables
            if missing_tables:
                logger.info(f"Creating missing tables: {', '.join(missing_tables)}")
                # Create only the missing tables
                missing_metadata = MetaData()
                for table_name in missing_tables:
                    model_tables[table_name].tometadata(missing_metadata)
                missing_metadata.create_all(self._engine)
            
            # Check for missing columns in existing tables
            for table_name in existing_tables:
                if table_name in model_tables:
                    model_table = model_tables[table_name]
                    
                    # Get existing columns
                    existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
                    
                    # Get model columns
                    model_columns = {col.name for col in model_table.columns}
                    
                    # Find missing columns
                    missing_columns = model_columns - existing_columns
                    if missing_columns:
                        logger.info(f"Table '{table_name}' missing columns: {', '.join(missing_columns)}")
                        logger.info("Migration support will add these columns in a future version")
                        # In a real migration system, we would alter the table here
                        # For now, we just log the issue
            
            logger.info("Schema update check completed")
            
        except Exception as e:
            logger.error(f"Error checking for schema updates: {e}")
    
    def verify_schema(self) -> Dict[str, Any]:
        """
        Verify that the database schema matches the SQLAlchemy model definitions.
        
        Returns:
            Dict containing verification results:
                - success: Whether verification was successful
                - matches: Whether schema matches models
                - missing_tables: List of tables defined in models but missing from DB
                - missing_columns: Dict of columns missing from tables
                - extra_tables: List of tables in DB but not in models
                - extra_columns: Dict of columns in DB but not in models
                - error: Error message if verification failed
        
        Raises:
            RuntimeError: If database is not initialized
        """
        if not self._initialized or not self._engine:
            raise RuntimeError("Database not initialized. Call initialize_database() first.")
        
        with self._lock:
            result = {
                "success": False,
                "matches": False,
                "missing_tables": [],
                "missing_columns": {},
                "extra_tables": [],
                "extra_columns": {},
                "error": None
            }
            
            try:
                # Get inspector for schema introspection
                inspector = inspect(self._engine)
                
                # Get actual tables in the database
                db_tables = set(inspector.get_table_names())
                
                # Get expected tables from models
                model_tables = {model.__tablename__ for model in get_all_models()}
                model_tables.add("sqlite_sequence")  # SQLite internal table
                
                # Check for missing and extra tables
                missing_tables = model_tables - db_tables
                extra_tables = db_tables - model_tables
                
                result["missing_tables"] = list(missing_tables)
                result["extra_tables"] = list(extra_tables)
                
                # Check columns for each table in the models
                missing_columns = {}
                extra_columns = {}
                
                for model in get_all_models():
                    table_name = model.__tablename__
                    
                    if table_name in db_tables:
                        # Get columns from the database
                        db_columns = {col["name"] for col in inspector.get_columns(table_name)}
                        
                        # Get columns from the model
                        model_columns = {column.key for column in model.__table__.columns}
                        
                        # Check for missing and extra columns
                        missing = model_columns - db_columns
                        extra = db_columns - model_columns
                        
                        if missing:
                            missing_columns[table_name] = list(missing)
                        
                        if extra:
                            extra_columns[table_name] = list(extra)
                
                result["missing_columns"] = missing_columns
                result["extra_columns"] = extra_columns
                
                # Determine if schema matches
                result["matches"] = (
                    not missing_tables and 
                    not missing_columns and 
                    not extra_tables and 
                    not extra_columns
                )
                
                result["success"] = True
                
                if result["matches"]:
                    logger.info("Database schema verification successful: Schema matches models")
                else:
                    logger.warning("Database schema verification found discrepancies")
                    
                    if missing_tables:
                        logger.warning(f"Missing tables: {', '.join(missing_tables)}")
                    
                    if missing_columns:
                        for table, columns in missing_columns.items():
                            logger.warning(f"Table '{table}' missing columns: {', '.join(columns)}")
                    
                    if extra_tables:
                        logger.warning(f"Extra tables: {', '.join(extra_tables)}")
                    
                    if extra_columns:
                        for table, columns in extra_columns.items():
                            logger.warning(f"Table '{table}' has extra columns: {', '.join(columns)}")
                
            except SQLAlchemyError as e:
                error_msg = f"Schema verification error: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg
                
            except Exception as e:
                error_msg = f"Unexpected error during schema verification: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg
                
            return result
    
    def update_schema(self) -> Dict[str, Any]:
        """
        Update the database schema to match the SQLAlchemy model definitions.
        
        This method will add missing tables and columns but will NOT modify or remove
        existing tables or columns to prevent data loss.
        
        Returns:
            Dict containing update results:
                - success: Whether update was successful
                - tables_added: List of tables added
                - tables_modified: List of tables modified
                - error: Error message if update failed
        
        Raises:
            RuntimeError: If database is not initialized
        """
        if not self._initialized or not self._engine:
            raise RuntimeError("Database not initialized. Call initialize_database() first.")
        
        with self._lock:
            result = {
                "success": False,
                "tables_added": [],
                "tables_modified": [],
                "error": None
            }
            
            try:
                # First verify the schema to identify issues
                verification = self.verify_schema()
                
                if not verification["success"]:
                    result["error"] = "Schema verification failed"
                    return result
                
                # If schema already matches, nothing to do
                if verification["matches"]:
                    logger.info("Schema already up to date, no changes needed")
                    result["success"] = True
                    return result
                
                # Add missing tables
                if verification["missing_tables"]:
                    # Create metadata for just the missing tables
                    missing_tables_metadata = MetaData()
                    
                    for model in get_all_models():
                        if model.__tablename__ in verification["missing_tables"]:
                            # Copy table definition to our metadata
                            Table(model.__tablename__, missing_tables_metadata, *[
                                c.copy() for c in model.__table__.columns
                            ])
                    
                    # Create missing tables
                    missing_tables_metadata.create_all(self._engine)
                    result["tables_added"] = verification["missing_tables"]
                    logger.info(f"Added missing tables: {', '.join(verification['missing_tables'])}")
                
                # Add missing columns (complex operation, requires raw SQL)
                if verification["missing_columns"]:
                    # Start a transaction
                    with self._engine.begin() as conn:
                        for table_name, missing_cols in verification["missing_columns"].items():
                            # Find the model for this table
                            model = next((m for m in get_all_models() if m.__tablename__ == table_name), None)
                            
                            if model:
                                modified = False
                                
                                for col_name in missing_cols:
                                    # Find the column in the model
                                    col = getattr(model.__table__.c, col_name, None)
                                    
                                    if col:
                                        # Create an ADD COLUMN statement
                                        # SQLite has limitations on ALTER TABLE
                                        col_type = col.type.compile(dialect=self._engine.dialect)
                                        nullable = "" if col.nullable else " NOT NULL"
                                        default = f" DEFAULT {col.default.arg}" if col.default and not callable(col.default.arg) else ""
                                        
                                        alter_stmt = text(
                                            f"ALTER TABLE {table_name} "
                                            f"ADD COLUMN {col_name} {col_type}{nullable}{default}"
                                        )
                                        
                                        # Execute the ALTER TABLE statement
                                        conn.execute(alter_stmt)
                                        modified = True
                                        logger.info(f"Added column '{col_name}' to table '{table_name}'")
                                
                                if modified:
                                    result["tables_modified"].append(table_name)
                
                # We don't remove extra tables or columns to prevent data loss
                if verification["extra_tables"]:
                    logger.warning(f"Extra tables exist but won't be removed: {', '.join(verification['extra_tables'])}")
                
                if verification["extra_columns"]:
                    for table, columns in verification["extra_columns"].items():
                        logger.warning(f"Table '{table}' has extra columns that won't be removed: {', '.join(columns)}")
                
                result["success"] = True
                logger.info("Schema update completed successfully")
                
            except SQLAlchemyError as e:
                error_msg = f"Schema update error: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg
                
            except Exception as e:
                error_msg = f"Unexpected error during schema update: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg
                
            return result
    
    def reset_database(self, force: bool = False) -> Dict[str, Any]:
        """
        Reset the database by dropping all tables and recreating the schema.
        
        This is a destructive operation that will delete all data. By default, it
        requires confirmation via the force parameter.
        
        Args:
            force: If True, bypass confirmation and perform reset
        
        Returns:
            Dict containing reset results:
                - success: Whether reset was successful
                - backed_up: Whether a backup was created
                - backup_path: Path to the backup file if created
                - error: Error message if reset failed
        
        Raises:
            RuntimeError: If database is not initialized
            ValueError: If force is False (confirmation required)
        """
        if not self._initialized or not self._engine or not self._db_path:
            raise RuntimeError("Database not initialized. Call initialize_database() first.")
        
        if not force:
            raise ValueError("Database reset requires confirmation. Set force=True to confirm.")
        
        with self._lock:
            result = {
                "success": False,
                "backed_up": False,
                "backup_path": None,
                "error": None
            }
            
            try:
                # Create a backup before resetting
                backup_path = self._db_path.with_name(
                    f"{self._db_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                )
                
                # Check if the database file exists before backing up
                if self._db_path.exists():
                    shutil.copy2(self._db_path, backup_path)
                    result["backed_up"] = True
                    result["backup_path"] = str(backup_path)
                    logger.info(f"Created database backup at {backup_path}")
                
                # Close existing connections
                if hasattr(self, '_engine') and self._engine:
                    self._engine.dispose()
                
                # Delete the database file if it exists
                if self._db_path.exists():
                    self._db_path.unlink()
                
                # Reinitialize the database
                init_result = self.initialize_database(self._db_path)
                
                if not init_result["success"]:
                    result["error"] = f"Failed to reinitialize database: {init_result['error']}"
                    return result
                
                result["success"] = True
                logger.info("Database reset successfully")
                
            except SQLAlchemyError as e:
                error_msg = f"Database reset error: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg
                
            except OSError as e:
                error_msg = f"OS error during database reset: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg
                
            except Exception as e:
                error_msg = f"Unexpected error during database reset: {str(e)}"
                logger.error(error_msg)
                result["error"] = error_msg
                
            return result
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Get a SQLAlchemy session with proper transaction management.
        
        This context manager ensures proper transaction handling:
        - Automatically commits the transaction on successful completion
        - Automatically rolls back on exception
        - Always closes the session at the end
        
        Yields:
            SQLAlchemy Session object
            
        Raises:
            SQLAlchemyError: If there is a database error
        """
        if not self._initialized:
            self.initialize_database()
        
        if not self._Session:
            raise RuntimeError("Database not initialized. Call initialize_database() first.")
        
        session = self._Session()
        try:
            yield session
            # If we get here, no exception was raised, so commit
            session.commit()
        except Exception as e:
            # An exception occurred, roll back the transaction
            session.rollback()
            logger.error(f"Database error, transaction rolled back: {e}")
            # Re-raise the exception
            raise
        finally:
            # Always close the session
            session.close()
    
    def close(self) -> None:
        """Close all database connections in the pool."""
        if hasattr(self, '_engine') and self._engine:
            self._engine.dispose()
    
    def get_db_path(self) -> Optional[Path]:
        """
        Get the path to the database file.
        
        Returns:
            Path to the database file, or None if not initialized
        """
        return self._db_path
    
    def is_initialized(self) -> bool:
        """
        Check if the database has been initialized.
        
        Returns:
            True if the database is initialized, False otherwise
        """
        return self._initialized 