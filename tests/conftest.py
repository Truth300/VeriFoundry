"""Pytest configuration and shared fixtures."""
import pytest
from fastapi.testclient import TestClient
from main import create_app


@pytest.fixture
def app():
    """Create a FastAPI app instance for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)
