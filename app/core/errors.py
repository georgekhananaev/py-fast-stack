"""
Error handlers for the FastAPI application.
"""


from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

templates = Jinja2Templates(directory="templates")


def _create_error_response(
    request: Request,
    status_code: int,
    detail: str,
    template_name: str,
    template_title: str
) -> JSONResponse | HTMLResponse:
    """Create error response based on request type (API or web)."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail}
        )

    return templates.TemplateResponse(
        template_name,
        {"request": request, "title": template_title},
        status_code=status_code
    )


async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 Not Found errors."""
    detail = exc.detail if hasattr(exc, 'detail') else "Not Found"
    return _create_error_response(
        request, 404, detail, "errors/404.html", "Page Not Found"
    )


async def forbidden_handler(request: Request, exc: HTTPException):
    """Handle 403 Forbidden errors."""
    detail = exc.detail if hasattr(exc, 'detail') else "Forbidden"
    return _create_error_response(
        request, 403, detail, "errors/403.html", "Access Forbidden"
    )


async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server errors."""
    return _create_error_response(
        request, 500, "Internal Server Error", "errors/500.html", "Server Error"
    )


async def general_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle general HTTP exceptions."""
    # For specific status codes, use dedicated handlers
    if exc.status_code == 404:
        return await not_found_handler(request, exc)
    elif exc.status_code == 403:
        return await forbidden_handler(request, exc)
    elif exc.status_code >= 500:
        return await internal_server_error_handler(request, exc)

    # For other status codes, create appropriate response
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    # For web routes, use a generic error page
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
