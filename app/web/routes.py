from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.crud import user as crud_user
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import create_access_token, verify_token, verify_password
from datetime import timedelta
from app.core.config import get_settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")
settings = get_settings()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Home"}
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "title": "Login"}
    )


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle login form submission."""
    user = await crud_user.authenticate(db, username=username, password=password)
    
    if not user:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "title": "Login", "error": "Invalid username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "title": "Login", "error": "Inactive account"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Redirect to dashboard with token in cookie
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax"
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page."""
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "title": "Register"}
    )


@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle registration form submission."""
    # Check if user exists
    existing_user = await crud_user.get_by_email(db, email=email)
    if existing_user:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "title": "Register", "error": "Email already registered"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    existing_user = await crud_user.get_by_username(db, username=username)
    if existing_user:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "title": "Register", "error": "Username already taken"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Create new user
    user_in = UserCreate(
        email=email,
        username=username,
        password=password,
        full_name=full_name
    )
    
    user = await crud_user.create(db, obj_in=user_in)
    
    # Auto-login after registration
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax"
    )
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """User dashboard."""
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify token and get user
    username = verify_token(token)
    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    user = await crud_user.get_by_username(db, username=username)
    if not user or not user.is_active:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Dashboard", "user": user}
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    success: str = None,
    error: str = None
):
    """User profile page."""
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify token and get user
    username = verify_token(token)
    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    user = await crud_user.get_by_username(db, username=username)
    if not user or not user.is_active:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request, 
            "title": "Profile", 
            "user": user,
            "success": success,
            "error": error
        }
    )


@router.post("/profile/update")
async def update_profile(
    request: Request,
    full_name: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile."""
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify token and get user
    username = verify_token(token)
    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    user = await crud_user.get_by_username(db, username=username)
    if not user or not user.is_active:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Update user
    user_update = UserUpdate(full_name=full_name)
    await crud_user.update(db, db_obj=user, obj_in=user_update)
    
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
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify token and get user
    username = verify_token(token)
    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    user = await crud_user.get_by_username(db, username=username)
    if not user or not user.is_active:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify current password
    if not await verify_password(current_password, user.hashed_password):
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "title": "Profile", "user": user, "error": "Current password is incorrect"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if passwords match
    if new_password != confirm_new_password:
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "title": "Profile", "user": user, "error": "New passwords do not match"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Update password
    user_update = UserUpdate(password=new_password)
    await crud_user.update(db, db_obj=user, obj_in=user_update)
    
    # Redirect back to profile with success message
    return RedirectResponse(
        url="/profile?success=Password changed successfully",
        status_code=status.HTTP_302_FOUND
    )


@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Display users list (superuser only)."""
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify token and get user
    username = verify_token(token)
    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    user = await crud_user.get_by_username(db, username=username)
    if not user or not user.is_active:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Check if user is superuser
    if not user.is_superuser:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    # Get all users
    users = await crud_user.get_multi(db, skip=skip, limit=limit)
    
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "title": "Users Management",
            "user": user,
            "users": users
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
    """Display user edit form (superuser only)."""
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify token and get current user
    username = verify_token(token)
    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    current_user = await crud_user.get_by_username(db, username=username)
    if not current_user or not current_user.is_active:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Check if current user is superuser
    if not current_user.is_superuser:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
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
    """Update user (superuser only)."""
    # Get form data
    form_data = await request.form()
    username = form_data.get("username")
    email = form_data.get("email")
    full_name = form_data.get("full_name")
    new_password = form_data.get("new_password")
    is_active = "is_active" in form_data
    is_superuser = "is_superuser" in form_data
    
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Verify token and get current user
    current_username = verify_token(token)
    if not current_username:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    current_user = await crud_user.get_by_username(db, username=current_username)
    if not current_user or not current_user.is_active:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Check if current user is superuser
    if not current_user.is_superuser:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
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
    """Delete a user (superuser only, cannot delete root)."""
    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify token and get current user
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    current_user = await crud_user.get_by_username(db, username=username)
    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=401, detail="User not active")
    
    # Check if current user is superuser
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


@router.get("/logout")
async def logout(request: Request):
    """Logout user."""
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response