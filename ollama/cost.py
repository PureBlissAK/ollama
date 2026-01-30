"""Compatibility shim for `ollama.cost` re-exporting moved package in
`ollama._legacy.cost`.

This allows existing imports like `from ollama.cost import ...` to continue
working while the repository is reorganized.
"""

from ._legacy.cost import *  # noqa: F401,F403

__all__ = getattr(__import__("ollama._legacy.cost", fromlist=["*"]), "__all__", [])
