"""
Custom middleware for request handling.
Created by George Khananaev
https://george.khananaev.com/
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to handle large request bodies."""

    def __init__(self, app, max_size: int = 100 * 1024 * 1024):  # 100MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        # Set max request body size
        request._max_request_body_size = self.max_size

        response = await call_next(request)
        return response


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track request performance."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        return response
