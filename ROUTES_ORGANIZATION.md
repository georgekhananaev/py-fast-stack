# Routes Organization

## Overview

The PyFastStack application routes are organized into logical groups based on access levels and functionality. This makes the security model clearer and the codebase more maintainable.

## Web Routes Structure

Web routes are split into three files based on access level:

### 1. **Public Routes** (`app/web/public_routes.py`)
No authentication required. Accessible to everyone.

- `GET /` - Home page
- `GET /login` - Login page
- `POST /login` - Login form submission (creates auth cookie)
- `GET /register` - Registration page
- `POST /register` - Registration form submission
- `GET /logout` - Logout (clears auth cookie)

### 2. **Authenticated Routes** (`app/web/auth_routes.py`)
Requires valid authentication cookie. Accessible to any logged-in user.

- `GET /dashboard` - User dashboard
- `GET /profile` - User profile page
- `POST /profile/update` - Update own profile
- `POST /profile/password` - Change own password

### 3. **Admin Routes** (`app/web/admin_routes.py`)
Requires superuser privileges. Only accessible to administrators.

- `GET /users` - Users management list
- `GET /users/edit/{user_id}` - Edit user form
- `POST /users/edit/{user_id}` - Update user
- `DELETE /users/delete/{user_id}` - Delete user
- `GET /subscribers` - Newsletter subscribers list
- `DELETE /subscribers/delete/{subscriber_id}` - Delete subscriber

## API Routes Structure

API routes remain in their original structure but are clearly documented in `app/api/v1/api.py`:

### Authentication Endpoints (`/api/v1/auth/`)
- `POST /auth/login` - **Public** - Get access token
- `POST /auth/register` - **Public** - Create new account
- `GET /auth/me` - **Protected** - Get current user info

### User Management Endpoints (`/api/v1/users/`)
- `GET /users/` - **Protected (Superuser)** - List all users
- `GET /users/{id}` - **Protected** - Get user (own profile or superuser)
- `PUT /users/{id}` - **Protected (Superuser)** - Update user

### Subscription Endpoints (`/api/v1/`)
- `POST /subscribe` - **Public** - Subscribe to newsletter
- `DELETE /unsubscribe/{email}` - **Public** - Unsubscribe
- `GET /subscriptions` - **Protected (Superuser)** - List subscribers

## Authentication Methods

### Web Routes
- Use **cookie-based authentication** with httpOnly cookies
- Token stored in `access_token` cookie
- Automatic redirects to login page when not authenticated

### API Routes
- Use **Bearer token authentication** via Authorization header
- Token obtained from `/api/v1/auth/login` endpoint
- Returns 401 status codes when not authenticated

## Security Benefits

1. **Clear Access Control**: Routes are physically separated by access level
2. **Easier Maintenance**: Related routes are grouped together
3. **Better Security Review**: Easy to audit which endpoints require what permissions
4. **Consistent Patterns**: Each router file uses the same authentication patterns
5. **Reduced Code Duplication**: Shared authentication logic within each router

## File Structure

```
app/
├── web/
│   ├── __init__.py           # Exports all three routers
│   ├── public_routes.py      # No auth required
│   ├── auth_routes.py        # Login required
│   └── admin_routes.py       # Superuser required
├── api/
│   └── v1/
│       ├── api.py           # Main API router with documentation
│       └── endpoints/
│           ├── auth.py      # Mixed public/protected
│           ├── users.py     # All protected
│           └── subscriptions.py  # Mixed public/protected
└── main.py                  # Includes all routers
```

## Usage in main.py

```python
# Web routers - grouped by access level
app.include_router(public_router)     # Public routes (no auth required)
app.include_router(auth_router)       # Authenticated user routes
app.include_router(admin_router)      # Admin/superuser only routes
```

This organization makes it immediately clear which routes require authentication and what level of access is needed.