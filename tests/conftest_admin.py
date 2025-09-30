import pytest
import os
from unittest.mock import patch, MagicMock

# Set testing environment before importing app modules
os.environ['TESTING'] = 'true'

from app import create_app

@pytest.fixture(scope="function")
def app():
    """Create and configure a test app for each test function"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'

    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Create a test client using the Flask application configured for testing"""
    return app.test_client()

@pytest.fixture(autouse=True)
def mock_database():
    """Mock database connections for all tests"""
    with patch('app.get_db') as mock_db:
        mock_db.return_value = MagicMock()
        yield mock_db

@pytest.fixture(autouse=True)
def app_context(app):
    """Ensure app context is available for all tests"""
    with app.app_context():
        yield