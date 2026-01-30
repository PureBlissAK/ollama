"""Compatibility shim for `ollama.monitoring` re-exporting moved package in
`ollama._legacy.monitoring`.

This keeps imports working during repository reorganization.
"""

from ._legacy.monitoring import *  # noqa: F401,F403

__all__ = getattr(__import__("ollama._legacy.monitoring", fromlist=["*"]), "__all__", [])
