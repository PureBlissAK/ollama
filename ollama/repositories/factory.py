"""
Repository Factory - Creates repository instances with dependency injection.
Provides a clean interface for accessing repositories in FastAPI endpoints.
"""

from collections.abc import AsyncGenerator
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from .api_key_repository import APIKeyRepository
from .conversation_repository import ConversationRepository
from .document_repository import DocumentRepository
from .message_repository import MessageRepository
from .usage_repository import UsageRepository
from .user_repository import UserRepository


class RepositoryFactory:
    """Factory for creating repository instances."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize factory with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self._repositories: dict[str, Any] = {}

    def get_user_repository(self) -> UserRepository:
        """Get or create UserRepository instance."""
        if "user" not in self._repositories:
            self._repositories["user"] = UserRepository(self.session)
        return cast(UserRepository, self._repositories["user"])

    def get_api_key_repository(self) -> APIKeyRepository:
        """Get or create APIKeyRepository instance."""
        if "api_key" not in self._repositories:
            self._repositories["api_key"] = APIKeyRepository(self.session)
        return cast(APIKeyRepository, self._repositories["api_key"])

    def get_conversation_repository(self) -> ConversationRepository:
        """Get or create ConversationRepository instance."""
        if "conversation" not in self._repositories:
            self._repositories["conversation"] = ConversationRepository(self.session)
        return cast(ConversationRepository, self._repositories["conversation"])

    def get_message_repository(self) -> MessageRepository:
        """Get or create MessageRepository instance."""
        if "message" not in self._repositories:
            self._repositories["message"] = MessageRepository(self.session)
        return cast(MessageRepository, self._repositories["message"])

    def get_document_repository(self) -> DocumentRepository:
        """Get or create DocumentRepository instance."""
        if "document" not in self._repositories:
            self._repositories["document"] = DocumentRepository(self.session)
        return cast(DocumentRepository, self._repositories["document"])

    def get_usage_repository(self) -> UsageRepository:
        """Get or create UsageRepository instance."""
        if "usage" not in self._repositories:
            self._repositories["usage"] = UsageRepository(self.session)
        return cast(UsageRepository, self._repositories["usage"])

    async def close(self) -> None:
        """Close all repository sessions."""
        # All repositories share the same session, just close once
        await self.session.close()


async def get_repositories() -> AsyncGenerator[RepositoryFactory, None]:
    """FastAPI dependency for repository factory.

    Creates a RepositoryFactory instance with a new session from the database manager.

    Usage in endpoints:
        @app.get("/api/v1/conversations")
        async def list_conversations(
            user_id: uuid.UUID,
            repos: RepositoryFactory = Depends(get_repositories)
        ):
            conv_repo = repos.get_conversation_repository()
            conversations = await conv_repo.get_by_user_id(user_id)
            return conversations

    Yields:
        RepositoryFactory instance
    """
    # Get session from database manager
    from ollama.services import get_db_manager

    manager = get_db_manager()
    async for session in manager.get_session():
        factory = RepositoryFactory(session)
        yield factory
