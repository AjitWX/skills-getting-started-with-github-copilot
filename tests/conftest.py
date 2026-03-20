"""
Pytest configuration and fixtures for FastAPI tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app
import copy


@pytest.fixture
def client():
    """
    Provide a FastAPI TestClient instance for testing.
    """
    return TestClient(app)


@pytest.fixture
def reset_activities(monkeypatch):
    """
    Reset the activities database to a known state before each test.
    This ensures test isolation and prevents state pollution between tests.
    """
    # Import the activities dict from the app module
    from src import app as app_module
    
    # Store the original activities state
    original_activities = copy.deepcopy(app_module.activities)
    
    # Reset activities to the original state for this test
    app_module.activities.clear()
    app_module.activities.update(original_activities)
    
    yield
    
    # Restore original state after test completes
    app_module.activities.clear()
    app_module.activities.update(original_activities)
