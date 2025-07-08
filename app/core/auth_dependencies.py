"""
Authentication dependencies for web routes.

These dependencies handle authentication and authorization for web routes,
including proper redirects when authentication fails.
"""

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token
from app.crud import user as crud_user
from app.db.session import get_db
from app.models.user import User


class AuthRedirectException(Exception):
    """Custom exception for authentication redirects."""
    def __init__(self, redirect_url: str):
        self.redirect_url = redirect_url
        super().__init__(f"Redirecting to {redirect_url}")


async def get_current_user_from_cookie(request: Request, db: AsyncSession) -> User | None:
    """Get current user from access token in cookie."""
    token = request.cookies.get("access_token")
    if not token:
        return None

    username = verify_token(token)
    if not username:
        return None

    user = await crud_user.get_by_username(db, username=username)
    if not user or not user.is_active:
        return None

    return user


async def get_optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User | None:
    """Get current user if authenticated, otherwise None."""
    return await get_current_user_from_cookie(request, db)


async def get_current_user_or_redirect(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User | RedirectResponse:
    """Get current user or return redirect response."""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return user


async def get_current_superuser_or_redirect(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User | RedirectResponse:
    """Get current superuser or return redirect response."""
    user = await get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if not user.is_superuser:
        return RedirectResponse(url="/dashboard", status_code=303)
    return user
