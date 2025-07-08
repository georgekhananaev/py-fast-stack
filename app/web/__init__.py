from app.web.public_routes import router as public_router
from app.web.auth_routes import router as auth_router
from app.web.admin_routes import router as admin_router

__all__ = ["public_router", "auth_router", "admin_router"]