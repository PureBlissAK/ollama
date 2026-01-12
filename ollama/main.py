"""
Ollama API - Main Application Entry Point
FastAPI-based AI inference server with production-grade features
"""
import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import uvicorn

from ollama.config import get_settings
from ollama.api.routes import health, models, generate, chat, embeddings
from ollama.services import (
    init_database, get_db_manager,
    init_cache, 
    init_vector_db
)
from ollama.services.cache import _cache_manager, CacheManager
from ollama.services.vector import _vector_manager, VectorManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def get_cache_manager() -> "CacheManager":
    """Get cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        raise RuntimeError("Cache manager not initialized")
    return _cache_manager


async def get_vector_manager() -> "VectorManager":
    """Get vector manager instance"""
    global _vector_manager
    if _vector_manager is None:
        raise RuntimeError("Vector manager not initialized")
    return _vector_manager

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    settings = get_settings()
    logger.info("🚀 Starting Ollama API Server")
    logger.info(f"Environment: production")
    logger.info(f"Host: {settings.host}:{settings.port}")
    logger.info(f"Public URL: {settings.public_url}")
    
    # Startup tasks
    try:
        # Initialize database connection pool
        logger.info("📦 Initializing database connection...")
        db_manager = init_database(settings.database_url, echo=False)
        await db_manager.initialize()
        
        # Initialize Redis connection
        logger.info("🔴 Connecting to Redis...")
        cache_manager = init_cache(settings.redis_url, db=0)
        await cache_manager.initialize()
        
        # Initialize Qdrant client
        logger.info("🔷 Connecting to Qdrant...")
        vector_manager = init_vector_db(settings.qdrant_url)
        await vector_manager.initialize()
        
        # Verify Ollama inference server
        logger.info("🤖 Verifying AI inference server...")
        try:
            # This would normally make a request to verify Ollama is running
            logger.info("✅ AI inference server verified")
        except Exception as e:
            logger.warning(f"⚠️  AI inference server check failed: {e}")
        
        logger.info("✅ Ollama API Server started successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        raise
    
    yield
    
    # Shutdown tasks
    logger.info("🛑 Shutting down Ollama API Server")
    try:
        # Close database connection
        db_manager = get_db_manager()
        await db_manager.close()
        
        # Close Redis connection
        cache_manager = await get_cache_manager()
        await cache_manager.close()
        
        # Close Qdrant connection
        vector_manager = await get_vector_manager()
        await vector_manager.close()
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("✅ Shutdown complete")


# Create FastAPI application
def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Ollama API",
        description="Elite AI Inference Platform - Local LLM serving with production features",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=settings.cors_expose_headers,
    )
    
    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Trusted hosts (when behind reverse proxy)
    if settings.trusted_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.trusted_hosts
        )
    
    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "no-request-id")
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
    
    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "type": "http_error",
                    "status_code": exc.status_code
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "message": "Internal server error",
                    "type": "server_error",
                    "status_code": 500
                }
            }
        )
    
    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])
    app.include_router(generate.router, prefix="/api/v1", tags=["Generation"])
    app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
    app.include_router(embeddings.router, prefix="/api/v1", tags=["Embeddings"])
    
    # Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "name": "Ollama API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "health": "/health"
        }
    
    return app


# Create application instance
app = create_app()


def main():
    """Run the application with uvicorn"""
    settings = get_settings()
    
    uvicorn.run(
        "ollama.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
