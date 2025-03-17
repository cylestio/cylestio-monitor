"""Unit tests for the DatabaseManager class.

This module contains tests for the DatabaseManager class, covering initialization
and basic database operations.

Note: Schema verification and modification tests have been removed as these operations
should be handled by proper database migration tools (like Alembic) in production.
"""

import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import Column, Integer, String, create_engine, text, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker, mapped_column, Mapped

from cylestio_monitor.db.database_manager import DatabaseManager


# Test-specific models to avoid dependencies on actual model implementations
class TestBase(DeclarativeBase):
    """Base model class for testing."""
    id: Mapped[int] = mapped_column(primary_key=True)


class TestModel(TestBase):
    """Simple test model."""
    __tablename__ = "testmodel"
    name: Mapped[str] = mapped_column(String(50))


# Mock the get_all_models function
def get_test_models():
    """Get all test models."""
    return [TestModel]


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test database files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def db_manager():
    """Create a DatabaseManager instance without initialization."""
    return DatabaseManager()


@pytest.fixture
def initialized_db_manager(temp_dir):
    """Create an initialized DatabaseManager instance."""
    with patch("cylestio_monitor.db.database_manager.Base", TestBase), \
         patch("cylestio_monitor.db.database_manager.get_all_models", get_test_models):
        manager = DatabaseManager()
        db_path = Path(temp_dir) / "test.db"
        manager.initialize_database(db_path)
        yield manager
        manager.close()


def test_initialization(db_manager, temp_dir):
    """Test database initialization."""
    # Mock the Base class and get_all_models function
    with patch("cylestio_monitor.db.database_manager.Base", TestBase), \
         patch("cylestio_monitor.db.database_manager.get_all_models", get_test_models):
        # Initialize with explicit path
        db_path = Path(temp_dir) / "test.db"
        result = db_manager.initialize_database(db_path)
        
        # Check result
        assert result["success"] is True
        assert result["created"] is True
        assert result["db_path"] == str(db_path)
        assert len(result["tables"]) > 0
        assert "testmodel" in result["tables"]
        assert result["error"] is None
        
        # Check that the file exists
        assert db_path.exists()
        
        # Check internal state
        assert db_manager.is_initialized() is True
        assert db_manager.get_db_path() == db_path
        
        # Check that the table was created correctly
        engine = create_engine(f"sqlite:///{db_path}")
        inspector = inspect(engine)
        
        # Check TestModel table
        assert "testmodel" in inspector.get_table_names()
        columns = {col["name"] for col in inspector.get_columns("testmodel")}
        assert "id" in columns
        assert "name" in columns


def test_initialization_with_platformdirs(db_manager):
    """Test database initialization using platformdirs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock platformdirs.user_data_dir to return our temp dir
        with patch("platformdirs.user_data_dir", return_value=temp_dir), \
             patch("cylestio_monitor.db.database_manager.Base", TestBase), \
             patch("cylestio_monitor.db.database_manager.get_all_models", get_test_models):
            result = db_manager.initialize_database()
            
            # Expected path
            expected_path = Path(temp_dir) / "cylestio_monitor.db"
            
            # Check result
            assert result["success"] is True
            assert result["created"] is True
            assert result["db_path"] == str(expected_path)
            assert len(result["tables"]) > 0
            
            # Check that the file exists
            assert expected_path.exists()


def test_initialization_with_test_env_var(db_manager):
    """Test database initialization using the test environment variable."""
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Set environment variable
            os.environ["CYLESTIO_TEST_DB_DIR"] = temp_dir
            
            # Mock Base and get_all_models
            with patch("cylestio_monitor.db.database_manager.Base", TestBase), \
                 patch("cylestio_monitor.db.database_manager.get_all_models", get_test_models):
                result = db_manager.initialize_database()
                
                # Expected path
                expected_path = Path(temp_dir) / "cylestio_monitor.db"
                
                # Check result
                assert result["success"] is True
                assert result["db_path"] == str(expected_path)
                
                # Check that the file exists
                assert expected_path.exists()
        finally:
            # Clean up environment
            if "CYLESTIO_TEST_DB_DIR" in os.environ:
                del os.environ["CYLESTIO_TEST_DB_DIR"]


def test_initialization_permission_error(db_manager):
    """Test initialization with insufficient permissions."""
    with patch("os.access", return_value=False), \
         patch("cylestio_monitor.db.database_manager.Base", TestBase), \
         patch("cylestio_monitor.db.database_manager.get_all_models", get_test_models):
        result = db_manager.initialize_database()
        
        # Check result
        assert result["success"] is False
        assert "permission" in result["error"].lower()
        assert db_manager.is_initialized() is False


def test_reset_database_not_initialized(db_manager):
    """Test reset_database when database is not initialized."""
    with pytest.raises(RuntimeError, match="not initialized"):
        db_manager.reset_database(force=True)


def test_reset_database_without_force(initialized_db_manager):
    """Test reset_database without force parameter."""
    with pytest.raises(ValueError, match="requires confirmation"):
        initialized_db_manager.reset_database(force=False)


def test_reset_database(initialized_db_manager, temp_dir):
    """Test reset_database with force=True."""
    # Add some data
    with initialized_db_manager.get_session() as session:
        test_obj = TestModel(name="Test Object")
        session.add(test_obj)
        session.commit()
    
    # Reset the database
    result = initialized_db_manager.reset_database(force=True)
    
    # Check result
    assert result["success"] is True
    assert result["backed_up"] is True
    assert result["backup_path"] is not None
    
    # Check that backup file exists
    backup_path = Path(result["backup_path"])
    assert backup_path.exists()
    
    # Check that the database was recreated
    db_path = initialized_db_manager.get_db_path()
    assert db_path.exists()
    
    # Check that the data is gone
    with initialized_db_manager.get_session() as session:
        objects = session.query(TestModel).all()
        assert len(objects) == 0


def test_get_session_not_initialized(db_manager):
    """Test get_session when database is not initialized."""
    with pytest.raises(RuntimeError, match="not initialized"):
        with db_manager.get_session() as session:
            pass


def test_get_session(initialized_db_manager):
    """Test get_session with initialized database."""
    with initialized_db_manager.get_session() as session:
        # Check that session is a proper SQLAlchemy session
        assert hasattr(session, 'query')
        assert callable(session.query)


def test_get_session_exception_handling(initialized_db_manager):
    """Test get_session with exception handling."""
    # Create a spy on session.rollback
    with patch('sqlalchemy.orm.Session.rollback') as mock_rollback:
        try:
            with initialized_db_manager.get_session() as session:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Check that rollback was called
        mock_rollback.assert_called_once()


def test_close(initialized_db_manager):
    """Test close method."""
    # Create a spy on engine.dispose
    with patch.object(initialized_db_manager._engine, 'dispose') as mock_dispose:
        initialized_db_manager.close()
        
        # Check that dispose was called
        mock_dispose.assert_called_once() 