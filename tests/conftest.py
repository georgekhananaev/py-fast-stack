"""
Test configuration and fixtures.
Created by George Khananaev
https://george.khananaev.com/
"""

import asyncio
import pytest
import pytest_asyncio
import os
import re
import time
import random
from typing import AsyncGenerator, Generator, Dict, Any
from httpx import AsyncClient, Response

# Base URL for the running server
BASE_URL = "http://localhost:8000"

# Default root password for testing
# In production, this should be set via environment variable
ROOT_PASSWORD = os.environ.get("TEST_ROOT_PASSWORD", "RootPassword123!")

# Track created test users for cleanup
_created_test_users = []


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


async def cleanup_test_users(client: AsyncClient):
    """Clean up test users created during tests."""
    if not _created_test_users:
        return
    
    # Get superuser token for cleanup
    try:
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "root", "password": ROOT_PASSWORD}
        )
        if response.status_code != 200:
            print(f"Failed to login as root for cleanup: {response.text}")
            return
        
        token = response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # Delete test users
        for user_id in _created_test_users:
            try:
                delete_response = await client.delete(
                    f"/users/delete/{user_id}",
                    headers={"Cookie": f"access_token={token}"}
                )
                if delete_response.status_code == 200:
                    print(f"Cleaned up test user {user_id}")
                else:
                    print(f"Failed to clean up test user {user_id}: {delete_response.text}")
            except Exception as e:
                print(f"Error cleaning up test user {user_id}: {e}")
    except Exception as e:
        print(f"Error during user cleanup: {e}")
    finally:
        _created_test_users.clear()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create a test client that connects to the running server."""
    async with AsyncClient(base_url=BASE_URL, follow_redirects=False) as test_client:
        yield test_client
        # Cleanup after all tests
        await cleanup_test_users(test_client)


@pytest_asyncio.fixture
async def test_user(client: AsyncClient) -> dict:
    """Create a test user via API and return user data."""
    # Use unique username and email for each test run
    timestamp = int(time.time() * 1000)
    rand = random.randint(1000, 9999)
    username = f"testuser_{timestamp}_{rand}"
    email = f"test_{timestamp}_{rand}@example.com"
    password = "TestPassword123!"
    
    # Create the user
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": "Test User"
        }
    )
    
    if response.status_code != 200:
        # If registration failed, try to get error details
        print(f"Failed to create test user: {response.status_code} - {response.text}")
    
    assert response.status_code == 200, f"Failed to create test user: {response.text}"
    
    # Add password to the response for use in tests
    user_data = response.json()
    user_data["password"] = password
    
    # Track for cleanup
    _created_test_users.append(user_data["id"])
    
    # Login to get access token
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password}
    )
    assert login_response.status_code == 200
    user_data["access_token"] = login_response.json()["access_token"]
    
    return user_data


@pytest_asyncio.fixture
async def test_superuser(client: AsyncClient) -> dict:
    """Use root user as superuser for tests."""
    # Login as root
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "root", "password": ROOT_PASSWORD}
    )
    
    if response.status_code == 200:
        # Get user info
        token = response.json()["access_token"]
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        user_data = me_response.json()
        user_data["password"] = ROOT_PASSWORD
        return user_data
    
    # If root login failed, skip tests
    pytest.skip(f"Root login failed: {response.text}")


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: dict) -> dict:
    """Get authentication headers for a regular user."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def superuser_auth_headers(client: AsyncClient) -> dict:
    """Get authentication headers for a superuser (root user)."""
    if not ROOT_PASSWORD:
        pytest.skip("Root password not available, skipping superuser tests")
    
    # Use the root user credentials
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "root", "password": ROOT_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Root login failed: {response.text}")
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_cookies(client: AsyncClient, test_user: dict) -> dict:
    """Get authentication cookies for web route testing."""
    # Login via web form to get cookie
    response = await client.post(
        "/login",
        data={
            "username": test_user["username"],
            "password": test_user["password"]
        }
    )
    
    # Check if login failed
    if response.status_code != 302:
        print(f"Login failed with status {response.status_code}")
        print(f"Response text: {response.text}")
        print(f"User data: {test_user}")
        
    assert response.status_code == 302, f"Expected 302 redirect, got {response.status_code}. Response: {response.text}"
    
    # Extract the access token from cookies
    cookies = response.cookies
    access_token = cookies.get("access_token")
    assert access_token is not None, "No access token in cookies"
    
    return {"access_token": access_token}


@pytest_asyncio.fixture
async def superuser_cookies(client: AsyncClient) -> dict:
    """Get authentication cookies for superuser web route testing."""
    if not ROOT_PASSWORD:
        pytest.skip("Root password not available, skipping superuser tests")
    
    # Login as root via web form
    response = await client.post(
        "/login",
        data={
            "username": "root",
            "password": ROOT_PASSWORD
        }
    )
    if response.status_code != 302:
        pytest.skip(f"Root login failed: {response.text}")
    
    # Extract the access token from cookies
    cookies = response.cookies
    access_token = cookies.get("access_token")
    assert access_token is not None, "No access token in cookies"
    
    return {"access_token": access_token}


@pytest_asyncio.fixture
async def test_user_for_deletion(client: AsyncClient) -> dict:
    """Create a test user specifically for deletion tests."""
    timestamp = int(time.time() * 1000)
    rand = random.randint(1000, 9999)
    username = f"deleteme_{timestamp}_{rand}"
    email = f"deleteme_{timestamp}_{rand}@example.com"
    password = "deletepass123"
    
    # Create the user
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": "Delete Me User"
        }
    )
    
    assert response.status_code == 200, f"Failed to create test user: {response.text}"
    
    user_data = response.json()
    user_data["password"] = password
    
    # Don't track for cleanup since it will be deleted during tests
    
    return user_data


@pytest.fixture
def test_user_data() -> dict:
    """Sample user data for testing."""
    timestamp = int(time.time() * 1000)
    rand = random.randint(1000, 9999)
    return {
        "email": f"newuser_{timestamp}_{rand}@example.com",
        "username": f"newuser_{timestamp}_{rand}",
        "password": "newpass123",
        "full_name": "New User"
    }