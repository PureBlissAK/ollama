"""
Authentication and Authorization Module
Provides JWT token management, API key validation, and user authentication
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from ollama.config import get_settings
from ollama.services import get_db
from ollama.repositories.factory import RepositoryFactory

logger = logging.getLogger(__name__)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthenticationError(Exception):
    """Custom authentication error"""
    pass


class AuthManager:
    """
    Authentication and authorization manager
    
    Handles:
    - Password hashing and verification
    - JWT token generation and validation
    - API key validation
    - User session management
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize auth manager
        
        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT algorithm (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_access_token(
        self,
        user_id: UUID,
        username: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token
        
        Args:
            user_id: User UUID
            username: Username
            expires_delta: Token expiration time
            
        Returns:
            Encoded JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=1)
        
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload = {
            "sub": str(user_id),
            "username": username,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def create_refresh_token(
        self,
        user_id: UUID,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token
        
        Args:
            user_id: User UUID
            expires_delta: Token expiration time
            
        Returns:
            Encoded JWT refresh token
        """
        if expires_delta is None:
            expires_delta = timedelta(days=7)
        
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def decode_token(self, token: str) -> dict:
        """
        Decode and validate JWT token
        
        Args:
            token: Encoded JWT token
            
        Returns:
            Token payload
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    def hash_api_key(self, api_key: str) -> str:
        """
        Hash an API key
        
        Args:
            api_key: Plain API key
            
        Returns:
            Hashed API key
        """
        return self.hash_password(api_key)
    
    def verify_api_key(self, api_key: str, hashed: str) -> bool:
        """
        Verify an API key against its hash
        
        Args:
            api_key: Plain API key
            hashed: Hashed API key
            
        Returns:
            True if API key matches
        """
        return self.verify_password(api_key, hashed)


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """
    Get global auth manager instance
    
    Returns:
        AuthManager instance
    """
    global _auth_manager
    if _auth_manager is None:
        settings = get_settings()
        jwt_secret = getattr(settings, 'jwt_secret', 'development-secret-change-me')
        _auth_manager = AuthManager(secret_key=jwt_secret)
    return _auth_manager


# FastAPI Dependencies
async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user from JWT token
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        auth_manager = get_auth_manager()
        payload = auth_manager.decode_token(credentials.credentials)
        
        user_id = UUID(payload.get("sub"))
        
        # Get user from database
        repo_factory = RepositoryFactory(db)
        user_repo = repo_factory.get_user_repository()
        user = await user_repo.get_by_id(user_id)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_user_from_api_key(
    api_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user from API key
    
    Args:
        api_key: API key from X-API-Key header
        db: Database session
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If authentication fails
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    try:
        # Get API key from database
        repo_factory = RepositoryFactory(db)
        api_key_repo = repo_factory.get_api_key_repository()
        
        # Verify and get user from API key
        key_record = await api_key_repo.verify_and_get_user(api_key)
        
        if key_record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Mark API key as used
        await api_key_repo.mark_used(key_record.id)
        
        # Get user
        user_repo = repo_factory.get_user_repository()
        user = await user_repo.get_by_id(key_record.user_id)
        
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"API key authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )


async def get_current_user(
    bearer_user = Depends(get_current_user_from_token),
    api_key_user = Depends(get_current_user_from_api_key)
):
    """
    Get current user from either JWT token or API key
    
    Tries bearer token first, falls back to API key
    
    Returns:
        User model instance
    """
    # This will never actually be called because the dependencies
    # will handle the authentication. This is just a marker.
    return bearer_user or api_key_user


def require_admin(
    current_user = Depends(get_current_user_from_token)
):
    """
    Require admin privileges
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# Optional authentication (doesn't fail if not authenticated)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user if authenticated, None otherwise
    
    Useful for endpoints that work both authenticated and unauthenticated
    
    Returns:
        User model instance or None
    """
    try:
        if credentials:
            return await get_current_user_from_token(credentials, db)
        elif api_key:
            return await get_current_user_from_api_key(api_key, db)
    except HTTPException:
        pass
    
    return None
