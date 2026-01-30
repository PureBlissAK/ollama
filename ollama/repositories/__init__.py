"""Compatibility package for `ollama.repositories` re-exporting the
implementation now located under `ollama.services.repositories`.
"""

from .services.repositories import *  # noqa: F401,F403

__all__ = getattr(__import__("ollama.services.repositories", fromlist=["*"]), "__all__", [])
