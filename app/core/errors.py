"""
Error handlers for the FastAPI application.
"""

from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

templates = Jinja2Templates(directory="templates")


async def not_found_handler(request: Request, exc: HTTPException) -> HTMLResponse:
    """Handle 404 Not Found errors."""
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request, "title": "Page Not Found"},
        status_code=404
    )


async def forbidden_handler(request: Request, exc: HTTPException) -> HTMLResponse:
    """Handle 403 Forbidden errors."""
    return templates.TemplateResponse(
        "errors/403.html",
        {"request": request, "title": "Access Forbidden"},
        status_code=403
    )


async def internal_server_error_handler(request: Request, exc: Exception) -> HTMLResponse:
    """Handle 500 Internal Server errors."""
    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request, "title": "Server Error"},
        status_code=500
    )


async def general_http_exception_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
    """Handle general HTTP exceptions."""
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