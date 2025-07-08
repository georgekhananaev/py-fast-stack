"""
Admin routes - Requires superuser privileges.

These routes are only accessible to users with superuser/admin status.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token
from app.crud import subscription as crud_subscription
from app.crud import user as crud_user
from app.db.session import get_db
from app.schemas.user import UserUpdate

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# Import auth dependencies from core module instead of defining them here
# This avoids duplication and ensures consistent behavior


@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit: int = 10,
    search: str = "",
    sort_by: str = "id",
    sort_order: str = "asc"
):
    """
    Users management list - Protected endpoint (Admin only).
    
    Displays a paginated list of all users with search and sorting capabilities.
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: SUPERUSER ONLY
    
    Args:
        page: Page number for pagination
        limit: Number of users per page
        search: Search term for filtering users
        sort_by: Column to sort by
        sort_order: Sort order (asc/desc)
        
    Returns:
        - If superuser: Users list page
        - If authenticated but not superuser: Redirect to dashboard
        - If not authenticated: Redirect to login
    """
    # Manual authentication check
    from app.core.auth_dependencies import get_current_user_from_cookie

    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    if not current_user.is_superuser:
        return RedirectResponse(url="/dashboard", status_code=303)

    # Calculate skip
    skip = (page - 1) * limit

    # Get users with pagination
    users, total = await crud_user.get_multi_with_pagination(
        db,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Calculate pagination info
    total_pages = (total + limit - 1) // limit

    # Helper functions for template
    def sort_url(column: str) -> str:
        """Generate URL for sorting by a column."""
        new_order = "desc" if sort_by == column and sort_order == "asc" else "asc"
        params = []
        if search:
            params.append(f"search={search}")
        params.append(f"sort_by={column}")
        params.append(f"sort_order={new_order}")
        params.append("page=1")  # Reset to first page when sorting
        return f"/users?{'&'.join(params)}"

    def pagination_url(page_num: int) -> str:
        """Generate URL for a specific page."""
        params = []
        if search:
            params.append(f"search={search}")
        if sort_by != "id":
            params.append(f"sort_by={sort_by}")
        if sort_order != "asc":
            params.append(f"sort_order={sort_order}")
        params.append(f"page={page_num}")
        return f"/users?{'&'.join(params)}"

    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "title": "Users Management",
            "user": current_user,
            "users": users,
            "current_page": page,
            "total_pages": total_pages,
            "total_users": total,
            "limit": limit,
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "sort_url": sort_url,
            "pagination_url": pagination_url,
            "min": min,
            "max": max,
            "range": range
        }
    )


@router.get("/users/edit/{user_id}", response_class=HTMLResponse)
async def edit_user_form(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    success: str = None,
    error: str = None
):
    """
    User edit form - Protected endpoint (Admin only).
    
    Displays a form to edit a specific user's information.
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: SUPERUSER ONLY
    
    Args:
        user_id: ID of the user to edit
        success: Success message to display
        error: Error message to display
        
    Returns:
        - If superuser: User edit form
        - If authenticated but not superuser: Redirect to dashboard
        - If not authenticated: Redirect to login
        - If user not found: Redirect to users list
    """
    # Manual authentication check
    from app.core.auth_dependencies import get_current_user_from_cookie

    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    if not current_user.is_superuser:
        return RedirectResponse(url="/dashboard", status_code=303)

    # Get user to edit
    edit_user = await crud_user.get(db, id=user_id)
    if not edit_user:
        return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        "user_edit.html",
        {
            "request": request,
            "title": f"Edit User - {edit_user.username}",
            "user": current_user,
            "edit_user": edit_user,
            "success": success,
            "error": error
        }
    )


@router.post("/users/edit/{user_id}")
async def update_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Update user - Protected endpoint (Admin only).
    
    Updates a user's information. Special restrictions:
    - Cannot change root user's username
    - Root user must remain superuser
    - Username must be unique
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: SUPERUSER ONLY
    
    Args:
        user_id: ID of the user to update
        Form data: username, email, full_name, new_password, is_active, is_superuser
        
    Returns:
        - If successful: Redirect to edit form with success message
        - If username exists: Redirect with error message
        - If not superuser: Redirect to dashboard
        - If not authenticated: Redirect to login
    """
    # Manual authentication check
    from app.core.auth_dependencies import get_current_user_from_cookie

    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    if not current_user.is_superuser:
        return RedirectResponse(url="/dashboard", status_code=303)

    # Get form data
    form_data = await request.form()
    username = form_data.get("username")
    email = form_data.get("email")
    full_name = form_data.get("full_name")
    new_password = form_data.get("new_password")
    is_active = "is_active" in form_data
    is_superuser = "is_superuser" in form_data

    # Get user to update
    user_to_update = await crud_user.get(db, id=user_id)
    if not user_to_update:
        return RedirectResponse(url="/users", status_code=status.HTTP_302_FOUND)

    # Prepare update data
    update_data = UserUpdate(
        email=email,
        full_name=full_name,
        is_active=is_active
    )

    # Handle username change (except for root)
    if user_to_update.username != "root" and username != user_to_update.username:
        # Check if new username is already taken
        existing_user = await crud_user.get_by_username(db, username=username)
        if existing_user and existing_user.id != user_id:
            return RedirectResponse(
                url=f"/users/edit/{user_id}?error=Username already exists",
                status_code=status.HTTP_302_FOUND
            )
        update_data.username = username

    # Handle password change
    if new_password:
        update_data.password = new_password

    # Handle superuser status (root must remain superuser)
    if user_to_update.username != "root":
        update_data.is_superuser = is_superuser

    # Update the user
    await crud_user.update(db, db_obj=user_to_update, obj_in=update_data)

    return RedirectResponse(
        url=f"/users/edit/{user_id}?success=User updated successfully",
        status_code=status.HTTP_302_FOUND
    )


@router.delete("/users/delete/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user - Protected endpoint (Admin only).
    
    Permanently deletes a user account. Special restrictions:
    - Cannot delete root user
    - Cannot delete your own account
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: SUPERUSER ONLY
    HTTP Method: DELETE (called via AJAX)
    
    Args:
        user_id: ID of the user to delete
        
    Returns:
        - 200: {"detail": "User deleted successfully"}
        - 401: Not authenticated
        - 403: Not enough permissions / Cannot delete root / Cannot delete self
        - 404: User not found
    """
    # Manual auth check for API-style endpoint
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    current_user = await crud_user.get_by_username(db, username=username)
    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=401, detail="User not active")

    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Get user to delete
    user_to_delete = await crud_user.get(db, id=user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent deletion of root user
    if user_to_delete.username == "root":
        raise HTTPException(status_code=403, detail="Cannot delete root user")

    # Prevent self-deletion
    if user_to_delete.id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete your own account")

    # Delete the user
    await crud_user.remove(db, id=user_id)

    return {"detail": "User deleted successfully"}


@router.get("/subscribers", response_class=HTMLResponse)
async def subscribers_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit: int = 10,
    search: str = "",
    sort_by: str = "id",
    sort_order: str = "asc"
):
    """
    Newsletter subscribers list - Protected endpoint (Admin only).
    
    Displays a paginated list of newsletter subscribers with search and sorting.
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: SUPERUSER ONLY
    
    Args:
        page: Page number for pagination
        limit: Number of subscribers per page
        search: Search term for filtering subscribers
        sort_by: Column to sort by
        sort_order: Sort order (asc/desc)
        
    Returns:
        - If superuser: Subscribers list page
        - If authenticated but not superuser: Redirect to dashboard
        - If not authenticated: Redirect to login
    """
    # Manual authentication check
    from app.core.auth_dependencies import get_current_user_from_cookie

    current_user = await get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    if not current_user.is_superuser:
        return RedirectResponse(url="/dashboard", status_code=303)

    # Calculate skip
    skip = (page - 1) * limit

    # Get subscribers with pagination
    subscribers, total = await crud_subscription.get_multi_with_pagination(
        db,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Calculate pagination info
    total_pages = (total + limit - 1) // limit

    # Helper functions for template
    def sort_url(column: str) -> str:
        """Generate URL for sorting by a column."""
        new_order = "desc" if sort_by == column and sort_order == "asc" else "asc"
        params = []
        if search:
            params.append(f"search={search}")
        params.append(f"sort_by={column}")
        params.append(f"sort_order={new_order}")
        params.append("page=1")  # Reset to first page when sorting
        return f"/subscribers?{'&'.join(params)}"

    def pagination_url(page_num: int) -> str:
        """Generate URL for a specific page."""
        params = []
        if search:
            params.append(f"search={search}")
        if sort_by != "id":
            params.append(f"sort_by={sort_by}")
        if sort_order != "asc":
            params.append(f"sort_order={sort_order}")
        params.append(f"page={page_num}")
        return f"/subscribers?{'&'.join(params)}"

    return templates.TemplateResponse(
        "subscribers.html",
        {
            "request": request,
            "title": "Subscribers Management",
            "user": current_user,
            "subscribers": subscribers,
            "current_page": page,
            "total_pages": total_pages,
            "total_subscribers": total,
            "limit": limit,
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "sort_url": sort_url,
            "pagination_url": pagination_url,
            "min": min,
            "max": max,
            "range": range
        }
    )


@router.delete("/subscribers/delete/{subscriber_id}")
async def delete_subscriber(
    subscriber_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete newsletter subscriber - Protected endpoint (Admin only).
    
    Permanently removes a subscriber from the newsletter list.
    
    Authentication required: YES
    Token type: Cookie-based (access_token)
    Access level: SUPERUSER ONLY
    HTTP Method: DELETE (called via AJAX)
    
    Args:
        subscriber_id: ID of the subscriber to delete
        
    Returns:
        - 200: {"detail": "Subscriber deleted successfully"}
        - 401: Not authenticated
        - 403: Not enough permissions
        - 404: Subscriber not found
    """
    # Manual auth check for API-style endpoint
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    current_user = await crud_user.get_by_username(db, username=username)
    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=401, detail="User not active")

    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Get subscriber to delete
    subscriber = await crud_subscription.subscription.get(db, id=subscriber_id)
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    # Delete the subscriber
    await crud_subscription.subscription.remove(db, id=subscriber_id)

    return {"detail": "Subscriber deleted successfully"}
