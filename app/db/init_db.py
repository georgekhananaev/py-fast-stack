"""Database initialization with root user creation."""

import secrets
import string

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.user import User


def generate_secure_password(length: int = 16) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


async def init_db() -> dict:
    """Initialize database and create root user."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Check if root user exists
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.username == "root")
        )
        existing_root = result.scalar_one_or_none()

        if not existing_root:
            # Generate credentials
            root_password = generate_secure_password()

            # Create root user
            root_user = User(
                email="root@example.com",
                username="root",
                hashed_password=await get_password_hash(root_password),
                full_name="Root Administrator",
                is_active=True,
                is_superuser=True
            )

            session.add(root_user)
            await session.commit()

            return {
                "created": True,
                "username": "root",
                "password": root_password,
                "email": "root@localhost"
            }
        else:
            return {
                "created": False,
                "message": "Root user already exists"
            }


async def run_init():
    """Run database initialization."""
    return await init_db()
