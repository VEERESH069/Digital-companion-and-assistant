"""
Pytest configuration and fixtures for API tests
"""

import os
import pytest
import tempfile
from pathlib import Path

from database import Database
from api import app, llm_engine


@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup after tests
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def db(test_db_path):
    """Initialize test database"""
    database_url = f"sqlite:///{test_db_path}"
    db = Database(database_url)
    return db


@pytest.fixture
def client(db):
    """Create Flask test client"""
    app.config['TESTING'] = True
    
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def sample_session(db):
    """Create a sample session for testing"""
    session = db.create_session(
        patient_id="P_TEST_001",
        language="en"
    )
    return session


@pytest.fixture
def sample_patient_id():
    """Sample patient ID"""
    return "P_TEST_002"
