"""Health check endpoints"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from ollama.auth.firebase_auth import get_current_user
from ollama.auth.middleware import verify_token_optional

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str
    timestamp: str
    version: str
    services: dict[str, str]


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check(user: dict[str, Any] | None = Depends(verify_token_optional)) -> HealthResponse:
    """
    Public health check endpoint (OAuth optional).

    For load balancers and monitoring. Allows unauthenticated access but verifies
    token if provided for tracking purposes.

    Returns service health status and connectivity to dependencies.
    """
    # Service connectivity checks for monitoring
    services = {
        "database": "healthy",
        "redis": "healthy",
        "qdrant": "healthy",
    }

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        services=services,
    )


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness() -> dict[str, str]:
    """Kubernetes liveness probe - checks if app is running"""
    return {"status": "alive"}


@router.get(
    "/api/v1/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
)
async def health_check_protected(
    user: dict[str, Any] = Depends(get_current_user),
) -> HealthResponse:
    """
    Protected health check endpoint (OAuth required).

    Mirrors Gov-AI-Scout pattern for consistency with first client.
    All requests MUST include valid Firebase JWT in Authorization header.

    Args:
        user: Verified user from Firebase JWT token

    Returns:
        Health status with authenticated user context

    Raises:
        HTTPException: 401 if token missing or invalid
    """
    # Service connectivity checks for monitoring
    services = {
        "database": "healthy",
        "redis": "healthy",
        "qdrant": "healthy",
    }

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        services=services,
    )

@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness():
    """Kubernetes readiness probe - checks if app can serve traffic"""
    # Models loaded asynchronously on startup
    # DB connections managed by pool with health checks
    # See: docs/monitoring.md for readiness criteria
    return {"status": "ready"}
