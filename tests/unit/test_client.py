"""Test suite for Ollama package."""

import pytest
from ollama.client import Client


@pytest.fixture
def client():
    """Fixture providing test client."""
    return Client(base_url="http://localhost:8000")


def test_client_initialization():
    """Test client can be initialized."""
    client = Client()
    assert client.base_url == "http://localhost:8000"
    assert client.client is not None


def test_client_url_normalization():
    """Test client URL normalization."""
    client = Client(base_url="http://localhost:8000/")
    assert client.base_url == "http://localhost:8000"
