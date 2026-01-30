"""Compatibility shim for `ollama.repositories` re-exporting moved package
into `ollama.services.repositories`.

This keeps `from ollama.repositories import X` working while the package
layout is cleaned up for Landing Zone compliance.
"""

from .services.repositories import *  # noqa: F401,F403

__all__ = getattr(__import__("ollama.services.repositories", fromlist=["*"]), "__all__", [])
