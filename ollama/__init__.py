#!/usr/bin/env python
"""Ollama package initialization."""

__version__ = "1.0.0"
__author__ = "kushin77"
__description__ = "Elite local AI development platform for LLM inference"

from ollama.client import Client

__all__ = ["Client"]
