"""
PyFastStack - A modern Python web application template
Created by George Khananaev
https://george.khananaev.com/
"""

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware
from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.middleware import RequestSizeLimitMiddleware, PerformanceMiddleware
from app.db.session import engine
from app.db.base import Base
from app.web import web_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    # Increase limits for file uploads and request body size
    max_request_size=100 * 1024 * 1024,  # 100 MB
)

# Add middlewares in reverse order (last added is executed first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add request size limit middleware
app.add_middleware(RequestSizeLimitMiddleware, max_size=100 * 1024 * 1024)  # 100MB

# Add performance tracking middleware
app.add_middleware(PerformanceMiddleware)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Configure this for production
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(web_router)




@app.get("/health")
async def health():
    """Health check endpoint optimized for benchmarking.
    
    Returns minimal JSON with server status and current datetime.
    This endpoint is designed to have minimal overhead for accurate benchmarking.
    """
    return {
        "status": "healthy",
        "datetime": datetime.utcnow().isoformat(),
        "timestamp": datetime.utcnow().timestamp()
    }