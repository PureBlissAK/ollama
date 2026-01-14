"""Schema: APIKeyList for authentication endpoints."""

from pydantic import BaseModel

from ollama.api.schemas.auth_api_key_response import APIKeyResponse


class APIKeyList(BaseModel):
    """Schema for list of API keys"""

    keys: list[APIKeyResponse]
    total: int
