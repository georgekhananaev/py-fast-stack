# Endpoint Groups Organization

The PyFastStack application endpoints are now organized into clear, descriptive groups that immediately convey their purpose and access requirements.

## API Endpoint Groups (`/api/v1/`)

### 🔓 Public - Authentication
Public endpoints for user authentication and registration.
- `POST /api/v1/auth/login` - Get access token
- `POST /api/v1/auth/register` - Create new account  
- `GET /api/v1/auth/me` - Get current user info (requires auth)

### 🔒 Admin - User Management
Superuser-only endpoints for managing system users.
- `GET /api/v1/users/` - List all users
- `GET /api/v1/users/{id}` - Get user details
- `PUT /api/v1/users/{id}` - Update user

### 📧 Newsletter Management
Mixed public and admin endpoints for newsletter functionality.
- `POST /api/v1/subscribe` - Subscribe to newsletter (public)
- `DELETE /api/v1/unsubscribe/{email}` - Unsubscribe (public)
- `GET /api/v1/subscriptions` - List all subscribers (admin only)

## Web Page Groups

### 🌐 Public Pages
Publicly accessible pages that don't require authentication.
- `GET /` - Home page
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /register` - Registration page
- `POST /register` - Process registration
- `GET /logout` - Logout

### 👤 User Account
Pages for authenticated users to manage their account.
- `GET /dashboard` - User dashboard
- `GET /profile` - Profile page
- `POST /profile/update` - Update profile
- `POST /profile/password` - Change password

### 🛡️ Admin Panel
Administrative pages for superusers only.
- `GET /users` - User management list
- `GET /users/edit/{id}` - Edit user form
- `POST /users/edit/{id}` - Update user
- `DELETE /users/delete/{id}` - Delete user
- `GET /subscribers` - Subscriber list
- `DELETE /subscribers/delete/{id}` - Delete subscriber

## Benefits of This Organization

1. **Visual Clarity**: Icons immediately show the access level
   - 🔓 = Public access
   - 🔒 = Restricted access
   - 👤 = User features
   - 🛡️ = Admin features
   - 📧 = Newsletter features

2. **Better API Documentation**: When viewing `/docs`, endpoints are grouped logically instead of appearing under generic names

3. **Security at a Glance**: Developers and security auditors can immediately identify which endpoints require authentication

4. **Intuitive Navigation**: Related functionality is grouped together

5. **Clear Access Levels**: The naming convention makes it obvious what level of access is required

## Viewing the Groups

Visit these URLs to see the organized endpoint documentation:
- API Documentation: `http://localhost:8000/docs`
- Alternative API Docs: `http://localhost:8000/redoc`

The endpoints will appear organized under their respective group names with clear visual indicators of their purpose and access requirements.