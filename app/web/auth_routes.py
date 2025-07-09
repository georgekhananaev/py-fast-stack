"""
Authenticated user routes - Requires login.

These routes are accessible to any authenticated user (regular users).
"""
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth_dependencies import get_current_user_from_cookie
from app.core.rate_limiter import limiter
from app.core.security import verify_password
from app.crud import user as crud_user
from app.db.session import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.user import UserUpdate
from app.api.v1.endpoints.server_stats import get_server_stats, format_bytes, format_uptime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Add built-in functions to Jinja2 globals
templates.env.globals.update({
    'min': min,
    'max': max,
    'range': range
})


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

    # Get quick stats if user is superuser
    user_stats = None
    subscriber_stats = None
    
    if current_user.is_superuser:
        # Get user counts
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0
        
        active_users_result = await db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_users_result.scalar() or 0
        
        # Get subscriber counts
        total_subscribers_result = await db.execute(select(func.count(Subscription.id)))
        total_subscribers = total_subscribers_result.scalar() or 0
        
        active_subscribers_result = await db.execute(
            select(func.count(Subscription.id)).where(Subscription.is_active == True)
        )
        active_subscribers = active_subscribers_result.scalar() or 0
        
        user_stats = {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users
        }
        
        subscriber_stats = {
            "total": total_subscribers,
            "active": active_subscribers,
            "inactive": total_subscribers - active_subscribers
        }

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Dashboard",
            "user": current_user,
            "user_stats": user_stats,
            "subscriber_stats": subscriber_stats
        }
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
@limiter.limit("3/minute")
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


@router.get("/server-stats", response_class=HTMLResponse)
async def server_stats(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Server statistics page - Protected endpoint.
    
    Displays server resource usage and system information.
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: Any authenticated user
    
    Returns:
        - If authenticated: Server statistics page
        - If not authenticated: Redirect to login
    """
    # Manual authentication check
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    # Get server statistics
    stats = get_server_stats()
    
    # Add formatted values for template
    stats_formatted = {
        **stats,
        "memory_total_formatted": format_bytes(stats["memory_total"]),
        "memory_used_formatted": format_bytes(stats["memory_used"]),
        "memory_available_formatted": format_bytes(stats["memory_available"]),
        "disk_total_formatted": format_bytes(stats["disk_total"]),
        "disk_used_formatted": format_bytes(stats["disk_used"]),
        "disk_free_formatted": format_bytes(stats["disk_free"]),
        "uptime_formatted": format_uptime(stats["app_uptime_seconds"]),
        "process_memory_rss_formatted": format_bytes(stats["process_memory_rss"]),
        "process_memory_vms_formatted": format_bytes(stats["process_memory_vms"]),
    }

    return templates.TemplateResponse(
        "server_stats.html",
        {
            "request": request, 
            "title": "Server Statistics", 
            "user": current_user,
            "stats": stats_formatted
        }
    )


@router.get("/server-stats/cards", response_class=HTMLResponse)
async def server_stats_cards(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Server statistics cards partial - Protected endpoint.
    
    Returns only the stats cards for HTMX updates.
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: Any authenticated user
    
    Returns:
        - If authenticated: Server statistics cards HTML partial
        - If not authenticated: Empty response (for HTMX requests)
    """
    # Manual authentication check
    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return HTMLResponse("")  # Return empty for HTMX requests
    
    # Get server statistics
    stats = get_server_stats()
    
    # Add formatted values for template
    stats_formatted = {
        **stats,
        "memory_total_formatted": format_bytes(stats["memory_total"]),
        "memory_used_formatted": format_bytes(stats["memory_used"]),
        "memory_available_formatted": format_bytes(stats["memory_available"]),
        "disk_total_formatted": format_bytes(stats["disk_total"]),
        "disk_used_formatted": format_bytes(stats["disk_used"]),
        "disk_free_formatted": format_bytes(stats["disk_free"]),
        "uptime_formatted": format_uptime(stats["app_uptime_seconds"]),
        "process_memory_rss_formatted": format_bytes(stats["process_memory_rss"]),
        "process_memory_vms_formatted": format_bytes(stats["process_memory_vms"]),
    }
    
    return templates.TemplateResponse(
        "server_stats_cards.html",
        {
            "request": request,
            "stats": stats_formatted
        }
    )
