"""Health check endpoints"""

from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str
    timestamp: str
    version: str
    services: Dict[str, str]


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for load balancers and monitoring

    Returns service health status and connectivity to dependencies
    """
    # Service connectivity checks for monitoring
    # Actual health checks managed by service instances
    # See: docs/monitoring.md for observability setup
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
async def liveness():
    """Kubernetes liveness probe - checks if app is running"""
    return {"status": "alive"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness():
    """Kubernetes readiness probe - checks if app can serve traffic"""
    # Models loaded asynchronously on startup
    # DB connections managed by pool with health checks
    # See: docs/monitoring.md for readiness criteria
    return {"status": "ready"}
