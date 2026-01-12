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
    # TODO: Add actual service checks
    services = {
        "database": "healthy",
        "redis": "healthy",
        "qdrant": "healthy",
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        services=services
    )


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness():
    """Kubernetes liveness probe - checks if app is running"""
    return {"status": "alive"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness():
    """Kubernetes readiness probe - checks if app can serve traffic"""
    # TODO: Check if models loaded, DB connected, etc.
    return {"status": "ready"}
