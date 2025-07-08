"""
Error handlers for the FastAPI application.
"""

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

templates = Jinja2Templates(directory="templates")


async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 Not Found errors."""
    # Check if this is an API request
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"detail": exc.detail if hasattr(exc, 'detail') else "Not Found"}
        )
    
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request, "title": "Page Not Found"},
        status_code=404
    )


async def forbidden_handler(request: Request, exc: HTTPException):
    """Handle 403 Forbidden errors."""
    # Check if this is an API request
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=403,
            content={"detail": exc.detail if hasattr(exc, 'detail') else "Forbidden"}
        )
    
    return templates.TemplateResponse(
        "errors/403.html",
        {"request": request, "title": "Access Forbidden"},
        status_code=403
    )


async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server errors."""
    # Check if this is an API request
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )
    
    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request, "title": "Server Error"},
        status_code=500
    )


async def general_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle general HTTP exceptions."""
    # Check if this is an API request
    if request.url.path.startswith("/api/"):
        # Return JSON response for API endpoints
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    # For web routes, return HTML pages
    # Map status codes to appropriate error pages
    if exc.status_code == 404:
        return await not_found_handler(request, exc)
    elif exc.status_code == 403:
        return await forbidden_handler(request, exc)
    elif exc.status_code >= 500:
        return await internal_server_error_handler(request, exc)
    else:
        # For other status codes, use a generic error page
        return templates.TemplateResponse(
            "errors/500.html",
            {
                "request": request, 
                "title": f"Error {exc.status_code}",
                "error_code": exc.status_code,
                "error_detail": exc.detail
            },
            status_code=exc.status_code
        )