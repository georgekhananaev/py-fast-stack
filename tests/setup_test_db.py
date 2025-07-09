"""
Setup test database with test root user.
This script creates a test root user for running tests without affecting production data.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.user import User
from app.core.security import get_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./pyfaststack.db")
TEST_ROOT_PASSWORD = os.getenv("TEST_ROOT_PASSWORD", "RootPassword123!")


async def create_test_root_user():
    """Create or update test root user for testing."""
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    # Create async session
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        try:
            # Check if root user exists
            result = await session.execute(
                select(User).where(User.username == "root")
            )
            root_user = result.scalar_one_or_none()
            
            if root_user:
                print("Root user already exists")
                # Update password to ensure it matches test password
                root_user.hashed_password = await get_password_hash(TEST_ROOT_PASSWORD)
                root_user.is_active = True
                root_user.is_superuser = True
                await session.commit()
                print(f"Updated root user password")
            else:
                # Create root user
                root_user = User(
                    username="root",
                    email="root@example.com",
                    full_name="Root User",
                    hashed_password=await get_password_hash(TEST_ROOT_PASSWORD),
                    is_active=True,
                    is_superuser=True
                )
                session.add(root_user)
                await session.commit()
                print("Created root user")
                
            print(f"Root user is ready for testing with password: {TEST_ROOT_PASSWORD}")
            
        except Exception as e:
            print(f"Error setting up test root user: {e}")
            await session.rollback()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_root_user())