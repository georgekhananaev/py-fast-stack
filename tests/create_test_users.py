"""
Create test users to avoid rate limiting during tests.
This script creates a pool of test users that can be reused across tests.
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
TEST_USER_PASSWORD = "TestPassword123!"
NUM_TEST_USERS = 20  # Create a pool of test users


async def create_test_users():
    """Create test users for testing."""
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    # Create async session
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        try:
            created_count = 0
            for i in range(NUM_TEST_USERS):
                username = f"testuser_{i}"
                email = f"testuser_{i}@example.com"
                
                # Check if user already exists
                result = await session.execute(
                    select(User).where(User.username == username)
                )
                existing_user = result.scalar_one_or_none()
                
                if not existing_user:
                    # Create user
                    user = User(
                        username=username,
                        email=email,
                        full_name=f"Test User {i}",
                        hashed_password=await get_password_hash(TEST_USER_PASSWORD),
                        is_active=True,
                        is_superuser=False
                    )
                    session.add(user)
                    created_count += 1
                else:
                    # Update password to ensure it matches
                    existing_user.hashed_password = await get_password_hash(TEST_USER_PASSWORD)
                    existing_user.is_active = True
                
            # Create a superuser for tests
            result = await session.execute(
                select(User).where(User.username == "testsuperuser")
            )
            superuser = result.scalar_one_or_none()
            
            if not superuser:
                superuser = User(
                    username="testsuperuser",
                    email="testsuperuser@example.com",
                    full_name="Test Superuser",
                    hashed_password=await get_password_hash(TEST_USER_PASSWORD),
                    is_active=True,
                    is_superuser=True
                )
                session.add(superuser)
                created_count += 1
            else:
                # Update password to ensure it matches
                superuser.hashed_password = await get_password_hash(TEST_USER_PASSWORD)
                superuser.is_active = True
                superuser.is_superuser = True
                
            await session.commit()
            print(f"Created/updated {created_count} test users")
            print(f"All test users use password: {TEST_USER_PASSWORD}")
                
        except Exception as e:
            print(f"Error creating test users: {e}")
            await session.rollback()
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_users())