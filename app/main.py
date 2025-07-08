"""
PyFastStack - A modern Python web application template
Created by George Khananaev
https://george.khananaev.com/
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.errors import (
    forbidden_handler,
    general_http_exception_handler,
    internal_server_error_handler,
    not_found_handler,
)
from app.core.middleware import PerformanceMiddleware, RequestSizeLimitMiddleware
from app.db.base import Base
from app.db.session import engine
from app.web import admin_router, auth_router, public_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application lifespan events."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="""
    ## PyFastStack API
    
    A modern Python web application with organized endpoints:
    
    - **🔓 Public - Authentication**: Login and registration endpoints
    - **🔒 Admin - User Management**: User CRUD operations (superuser only)
    - **📧 Newsletter Management**: Subscribe/unsubscribe and admin list view
    - **🌐 Public Pages**: Home, login, register pages
    - **👤 User Account**: Dashboard, profile management 
    - **🛡️ Admin Panel**: User and subscriber management
    
    ### Authentication
    - API endpoints use Bearer token authentication
    - Web pages use cookie-based authentication
    """,
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

# Include routers - order matters!
# API router first (with prefix) to avoid web routes catching API requests
app.include_router(api_router, prefix="/api/v1")

# Web routers - grouped by access level
app.include_router(public_router, tags=["🌐 Public Pages"])
app.include_router(auth_router, tags=["👤 User Account"])
app.include_router(admin_router, tags=["🛡️ Admin Panel"])

# Add error handlers - they will check request path and handle accordingly
app.add_exception_handler(StarletteHTTPException, general_http_exception_handler)
app.add_exception_handler(404, not_found_handler)
app.add_exception_handler(403, forbidden_handler)
app.add_exception_handler(500, internal_server_error_handler)
app.add_exception_handler(Exception, internal_server_error_handler)


@app.get("/health")
async def health():
    """
    Health check endpoint - Public endpoint.
    
    Returns minimal JSON with server status and current datetime.
    This endpoint is designed to have minimal overhead for accurate benchmarking.
    
    Authentication required: NO
    Token type: None
    
    Returns:
        JSON with status, datetime, and timestamp
    """
    return {
        "status": "healthy",
        "datetime": datetime.now(timezone.utc).isoformat(),
        "timestamp": datetime.now(timezone.utc).timestamp()
    }
