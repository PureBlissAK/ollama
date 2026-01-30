"""Compatibility shim for `ollama.federation` re-exporting moved package in
`ollama._legacy.federation`.
"""

from ._legacy.federation import *  # noqa: F401,F403

__all__ = getattr(__import__("ollama._legacy.federation", fromlist=["*"]), "__all__", [])
