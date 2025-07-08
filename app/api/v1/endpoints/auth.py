from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.config import get_settings
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.db.session import get_db
from app.schemas.token import Token
from app.schemas.user import User, UserCreate

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login - Public endpoint.
    
    Authenticates user and returns an access token for API requests.
    
    Authentication required: NO (this IS the authentication endpoint)
    Token type: None (returns Bearer token on success)
    
    Args:
        form_data: OAuth2 form with username and password
        
    Returns:
        Token object with access_token and token_type
        
    Raises:
        401: Incorrect username or password
        400: Inactive user account
    """
    user = await crud_user.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not crud_user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=User)
async def register(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Register a new user - Public endpoint.
    
    Creates a new user account via API.
    
    Authentication required: NO
    Token type: None
    
    Args:
        user_in: UserCreate schema with email, username, password, full_name
        
    Returns:
        Created User object
        
    Raises:
        400: A user with this email already exists
        400: A user with this username already exists
    """
    user = await crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )

    user = await crud_user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this username already exists.",
        )

    user = await crud_user.create(db, obj_in=user_in)
    return user


@router.get("/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user - Protected endpoint.
    
    Returns information about the currently authenticated user.
    
    Authentication required: YES
    Token type: Bearer token (in Authorization header)
    Access level: Any authenticated active user
    
    Returns:
        Current User object
        
    Raises:
        401: Not authenticated
        401: Could not validate credentials
        400: Inactive user
    """
    return current_user
