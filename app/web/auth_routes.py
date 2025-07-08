"""
Authenticated user routes - Requires login.

These routes are accessible to any authenticated user (regular users).
"""
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud import user as crud_user
from app.schemas.user import UserUpdate
from app.core.security import verify_token, verify_password
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def get_current_user_from_cookie(request: Request, db: AsyncSession):
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


# Authentication is handled manually in each endpoint to properly handle redirects


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    User dashboard - Protected endpoint.
    
    Displays the user's personal dashboard.
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: Any authenticated user
    
    Returns:
        - If authenticated: Dashboard page
        - If not authenticated: Redirect to login
    """
    # Manual authentication check
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Dashboard", "user": current_user}
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    success: str = None,
    error: str = None
):
    """
    User profile page - Protected endpoint.
    
    Displays the user's profile information and settings.
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: Any authenticated user
    
    Args:
        success: Success message to display (from query params)
        error: Error message to display (from query params)
        
    Returns:
        - If authenticated: Profile page
        - If not authenticated: Redirect to login
    """
    # Manual authentication check
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request, 
            "title": "Profile", 
            "user": current_user,
            "success": success,
            "error": error
        }
    )


@router.post("/profile/update")
async def update_profile(
    request: Request,
    full_name: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user profile - Protected endpoint.
    
    Updates the authenticated user's profile information.
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: Any authenticated user (can only update own profile)
    
    Args:
        full_name: Updated full name
        
    Returns:
        - If authenticated: Redirect to profile with success message
        - If not authenticated: Redirect to login
    """
    # Manual authentication check
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Update user
    user_update = UserUpdate(full_name=full_name)
    await crud_user.update(db, db_obj=current_user, obj_in=user_update)
    
    # Redirect back to profile with success message
    return RedirectResponse(
        url="/profile?success=Profile updated successfully",
        status_code=status.HTTP_302_FOUND
    )


@router.post("/profile/password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_new_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Change user password - Protected endpoint.
    
    Allows authenticated users to change their password.
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: Any authenticated user (can only change own password)
    
    Args:
        current_password: Current password for verification
        new_password: New password
        confirm_new_password: New password confirmation
        
    Returns:
        - If authenticated and passwords valid: Redirect to profile with success
        - If not authenticated: Redirect to login
        - If passwords invalid: Profile page with error
    """
    # Manual authentication check
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Verify current password
    if not await verify_password(current_password, current_user.hashed_password):
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "title": "Profile", "user": current_user, "error": "Current password is incorrect"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if passwords match
    if new_password != confirm_new_password:
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "title": "Profile", "user": current_user, "error": "New passwords do not match"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Update password
    user_update = UserUpdate(password=new_password)
    await crud_user.update(db, db_obj=current_user, obj_in=user_update)
    
    # Redirect back to profile with success message
    return RedirectResponse(
        url="/profile?success=Password changed successfully",
        status_code=status.HTTP_302_FOUND
    )