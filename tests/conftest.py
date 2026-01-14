"""Pytest configuration and fixtures for Ollama test suite.

This module provides shared fixtures used across all test modules.
It is automatically discovered and loaded by pytest.
"""

from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture()
def auth_manager() -> Mock:
    """Provide a mocked AuthManager for testing.

    Returns:
        Mocked AuthManager instance with password hashing support
    """
    manager = Mock()

    # Mock hash_password to return a realistic hash
    hashes: dict[str, str] = {}

    def mock_hash(pwd: str) -> str:
        """Hash a password and store it."""
        hashed = f"$2b$12$mocked_hash_of_{pwd}"
        hashes[pwd] = hashed
        return hashed

    def mock_verify(pwd: str, hashed: str) -> bool:
        """Verify password matches hash."""
        expected = f"$2b$12$mocked_hash_of_{pwd}"
        return hashed == expected

    manager.hash_password = Mock(side_effect=mock_hash)
    manager.verify_password = Mock(side_effect=mock_verify)
    return manager


@pytest.fixture()
def mock_request() -> Mock:
    """Provide a mock FastAPI Request object.

    Returns:
        Mock request with common attributes
    """
    request = Mock()
    request.headers = {}
    return request


@pytest.fixture()
def mock_settings() -> Mock:
    """Provide mock application settings.

    Returns:
        Mock settings object with common config values
    """
    settings = Mock()
    settings.firebase_enabled = True
    settings.api_key_auth_enabled = True
    settings.cors_origins = ["*"]
    settings.cors_allow_credentials = True
    settings.cors_expose_headers = ["X-Request-ID"]
    settings.host = "127.0.0.1"  # Use localhost for tests
    settings.port = 8000
    settings.workers = 1
    settings.log_level = "info"
    settings.public_url = "http://localhost:8000"
    return settings


@pytest.fixture()
def mock_firebase_user() -> Mock:
    """Provide a mock Firebase user object.

    Returns:
        Mock Firebase user with standard attributes
    """
    user = Mock()
    user.uid = "test-uid-123"
    user.email = "test@example.com"
    user.display_name = "Test User"
    user.email_verified = True
    user.custom_claims = {"role": "user"}
    return user


@pytest.fixture()
def mock_firebase_auth() -> MagicMock:
    """Provide a mocked Firebase authentication module.

    Returns:
        Mock firebase_auth module with common methods
    """
    auth = MagicMock()
    auth.verify_id_token = Mock(return_value={"sub": "test-user", "email": "test@example.com"})
    auth.get_user = Mock(return_value=Mock(uid="test-uid", email="test@example.com"))
    auth.get_user_by_email = Mock(
        return_value=Mock(uid="test-uid", email="test@example.com")
    )
    auth.create_user = Mock(
        return_value=Mock(uid="new-uid", email="new@example.com")
    )
    auth.UserNotFoundError = Exception
    auth.ExpiredSignInError = Exception
    auth.RevokedSignInError = Exception
    auth.InvalidIdTokenError = Exception
    return auth
