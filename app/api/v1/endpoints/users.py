from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.crud import user as crud_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserSchema])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=10000),  # Increased max limit to 10000
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve all users - Protected endpoint (Admin only).
    
    Returns a list of all users in the system with pagination.
    
    Authentication required: YES
    Token type: Bearer token (in Authorization header)
    Access level: SUPERUSER ONLY
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (max 10000)
        
    Returns:
        List of User objects
        
    Raises:
        401: Not authenticated
        403: Not a superuser
    """
    users = await crud_user.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserSchema)
async def read_user_by_id(
    user_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific user by id - Protected endpoint.
    
    Returns information about a specific user.
    Regular users can only view their own profile.
    Superusers can view any user's profile.
    
    Authentication required: YES
    Token type: Bearer token (in Authorization header)
    Access level: 
        - Any authenticated user (for own profile)
        - Superuser (for other users' profiles)
    
    Args:
        user_id: The ID of the user to retrieve
        
    Returns:
        User object
        
    Raises:
        401: Not authenticated
        400: Not enough permissions (non-superuser trying to view another user)
        404: User not found
    """
    user = await crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        return user
    if not crud_user.is_superuser(current_user):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a user - Protected endpoint (Admin only).
    
    Updates a user's information. Only superusers can update users.
    
    Authentication required: YES
    Token type: Bearer token (in Authorization header)
    Access level: SUPERUSER ONLY
    
    Args:
        user_id: The ID of the user to update
        user_in: UserUpdate schema with fields to update
        
    Returns:
        Updated User object
        
    Raises:
        401: Not authenticated
        403: Not a superuser
        404: User not found
    """
    user = await crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = await crud_user.update(db, db_obj=user, obj_in=user_in)
    return user