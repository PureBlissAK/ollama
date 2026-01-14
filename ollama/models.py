"""Ollama Database Models (backward compatibility re-exports).

This module re-exports ORM models split into individual modules. New code should
import models directly from their dedicated modules under `ollama.models`.

Legacy imports (deprecated):
    >>> from ollama.models import Base, User, APIKey

Preferred imports:
    >>> from ollama.models.base import Base
    >>> from ollama.models.user import User
    >>> from ollama.models.api_key import APIKey
    >>> from ollama.models.conversation import Conversation
    >>> from ollama.models.message import Message
    >>> from ollama.models.document import Document
    >>> from ollama.models.usage import Usage
"""

from ollama.models.api_key import APIKey
from ollama.models.base import Base
from ollama.models.conversation import Conversation
from ollama.models.document import Document
from ollama.models.message import Message
from ollama.models.usage import Usage
from ollama.models.user import User

__all__ = ["APIKey", "Base", "Conversation", "Document", "Message", "Usage", "User"]
