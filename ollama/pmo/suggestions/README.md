# Smart Suggestions

This package provides a `SmartSuggestionsEngine` prototype that ranks
candidate suggestions using a simple token-overlap heuristic. Replace the
internal `_embed` and similarity functions with real embedding models for
production-quality suggestions.

Usage:

>>> from ollama.pmo.suggestions import SmartSuggestionsEngine
>>> engine = SmartSuggestionsEngine()
>>> engine.suggest("optimize cost", ["reduce cost", "increase throughput"]) 
