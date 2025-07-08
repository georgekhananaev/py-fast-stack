"""
API v1 routes organization.

Routes are organized by functionality and access level:
- Authentication routes: Mix of public (login/register) and protected (me)
- User management routes: All protected (superuser only)
- Subscription routes: Mix of public (subscribe/unsubscribe) and protected (list)
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, subscriptions, users

api_router = APIRouter()

# ===== PUBLIC AUTHENTICATION =====
# Public endpoints for user authentication
# POST /auth/login - Get access token
# POST /auth/register - Create new account
# GET /auth/me - Get current user (requires auth)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["🔓 Public - Authentication"]
)

# ===== ADMIN - USER MANAGEMENT =====
# Superuser only endpoints for managing users
# GET /users/ - List all users (superuser only)
# GET /users/{id} - Get user details (own profile or superuser)
# PUT /users/{id} - Update user (superuser only)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["🔒 Admin - User Management"]
)

# ===== PUBLIC & ADMIN - NEWSLETTER =====
# Mixed public and admin endpoints for newsletter
# POST /subscribe - Subscribe to newsletter (public)
# DELETE /unsubscribe/{email} - Unsubscribe (public)
# GET /subscriptions - List all subscribers (superuser only)
api_router.include_router(
    subscriptions.router,
    tags=["📧 Newsletter Management"]
)
