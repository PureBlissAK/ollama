"""Compatibility shim for ZeroTrustManager.

This module re-exports the production implementation in
`zero_trust_impl.py` to keep imports stable while the implementation
lives in a separate file.
"""

from __future__ import annotations

from .zero_trust_impl import ZeroTrustConfig, ZeroTrustManager

__all__ = ["ZeroTrustConfig", "ZeroTrustManager"]
