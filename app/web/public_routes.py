"""
Public web routes - No authentication required.

These routes are accessible to everyone without any authentication.
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.db.session import get_db
from app.schemas.user import UserCreate

router = APIRouter()
templates = Jinja2Templates(directory="templates")
settings = get_settings()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Home page - Public endpoint.
    
    This is the landing page of the application.
    
    Authentication required: NO
    Token type: None
    
    Returns:
        HTMLResponse: The home page template
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Home"}
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Login page - Public endpoint.
    
    Displays the login form for users to authenticate.
    
    Authentication required: NO
    Token type: None
    
    Returns:
        HTMLResponse: The login page template
    """
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
    """
    Login form submission - Public endpoint.
    
    Authenticates user credentials and creates a session.
    Sets an httpOnly cookie with the access token on successful login.
    
    Authentication required: NO (this IS the authentication endpoint)
    Token type: None (creates cookie on success)
    
    Args:
        username: The username from the login form
        password: The password from the login form
        
    Returns:
        - On success: Redirect to dashboard with auth cookie
        - On failure: Login page with error message
    """
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
    """
    Registration page - Public endpoint.
    
    Displays the registration form for new users.
    
    Authentication required: NO
    Token type: None
    
    Returns:
        HTMLResponse: The registration page template
    """
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
    """
    Registration form submission - Public endpoint.
    
    Creates a new user account and automatically logs them in.
    Sets an httpOnly cookie with the access token after successful registration.
    
    Authentication required: NO
    Token type: None
    
    Args:
        email: User's email address
        username: Desired username (must be unique)
        password: User's password (will be hashed)
        full_name: User's full name (optional)
        
    Returns:
        - On success: Redirect to dashboard with auth cookie
        - On failure: Registration page with error message
    """
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


@router.get("/logout")
async def logout(request: Request):
    """
    Logout - Public endpoint.
    
    Logs out the current user by deleting the authentication cookie.
    
    Authentication required: NO (but only useful if logged in)
    Token type: None
    
    Returns:
        Redirect to home page with auth cookie deleted
    """
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response
