"""Compatibility shim for `ollama.training` re-exporting moved package in
`ollama._legacy.training`.
"""

from ._legacy.training import *  # noqa: F401,F403

__all__ = getattr(__import__("ollama._legacy.training", fromlist=["*"]), "__all__", [])
