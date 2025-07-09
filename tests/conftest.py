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
from unittest.mock import Mock, patch

# Base URL for the running server
BASE_URL = "http://localhost:8000"

# Default root password for testing
# In production, this should be set via environment variable
ROOT_PASSWORD = os.environ.get("TEST_ROOT_PASSWORD", "RootPassword123!")

# Track created test users for cleanup
_created_test_users = []

# Flag to control rate limiting in tests
DISABLE_RATE_LIMIT_FOR_TESTS = os.environ.get("DISABLE_RATE_LIMIT_FOR_TESTS", "true").lower() == "true"

# Track used test user indices
_used_test_user_indices = set()
_test_user_lock = asyncio.Lock()
_last_login_time = 0


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
    # Create client with test headers
    headers = {
        "User-Agent": "pytest/test-client",
        "X-Test-Id": f"test_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    }
    async with AsyncClient(base_url=BASE_URL, follow_redirects=False, headers=headers) as test_client:
        yield test_client
        # Cleanup after all tests
        await cleanup_test_users(test_client)


@pytest_asyncio.fixture
async def test_user(client: AsyncClient) -> dict:
    """Get a pre-created test user and return user data."""
    global _used_test_user_indices, _last_login_time
    
    async with _test_user_lock:
        # Add delay between logins to avoid rate limiting
        current_time = time.time()
        time_since_last_login = current_time - _last_login_time
        if time_since_last_login < 0.5:  # Wait at least 0.5 seconds between logins
            await asyncio.sleep(0.5 - time_since_last_login)
        
        # Find an unused test user index
        for i in range(20):  # We created 20 test users
            if i not in _used_test_user_indices:
                _used_test_user_indices.add(i)
                user_index = i
                break
        else:
            # All users are in use, create a new one with timestamp
            timestamp = int(time.time() * 1000)
            rand = random.randint(1000, 9999)
            username = f"testuser_extra_{timestamp}_{rand}"
            email = f"test_extra_{timestamp}_{rand}@example.com"
            password = "TestPassword123!"
            
            # Add delay to avoid rate limiting
            await asyncio.sleep(1)
            
            # Create the user
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "username": username,
                    "password": password,
                    "full_name": "Test User Extra"
                }
            )
            
            if response.status_code != 200:
                print(f"Failed to create extra test user: {response.status_code} - {response.text}")
            
            assert response.status_code == 200, f"Failed to create test user: {response.text}"
            
            user_data = response.json()
            user_data["password"] = password
            _created_test_users.append(user_data["id"])
            
            # Login to get access token
            login_response = await client.post(
                "/api/v1/auth/login",
                data={"username": username, "password": password}
            )
            assert login_response.status_code == 200
            user_data["access_token"] = login_response.json()["access_token"]
            
            return user_data
    
    # Use pre-created test user
    username = f"testuser_{user_index}"
    email = f"testuser_{user_index}@example.com"
    password = "TestPassword123!"
    
    # Login to get user data and access token
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password}
    )
    
    # Update last login time
    _last_login_time = time.time()
    
    if login_response.status_code != 200:
        print(f"Failed to login as {username}: {login_response.status_code} - {login_response.text}")
    
    assert login_response.status_code == 200, f"Failed to login as test user: {login_response.text}"
    
    access_token = login_response.json()["access_token"]
    
    # Get user info
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response.status_code == 200
    
    user_data = me_response.json()
    user_data["password"] = password
    user_data["access_token"] = access_token
    
    return user_data


@pytest_asyncio.fixture
async def test_superuser(client: AsyncClient) -> dict:
    """Use pre-created test superuser for tests."""
    global _last_login_time
    
    # Add delay to avoid rate limiting
    async with _test_user_lock:
        current_time = time.time()
        time_since_last_login = current_time - _last_login_time
        if time_since_last_login < 0.5:
            await asyncio.sleep(0.5 - time_since_last_login)
    
    # Use testsuperuser instead of root to avoid affecting production
    username = "testsuperuser"
    password = "TestPassword123!"
    
    # Login as testsuperuser
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password}
    )
    
    # Update last login time
    _last_login_time = time.time()
    
    if response.status_code == 200:
        # Get user info
        token = response.json()["access_token"]
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        user_data = me_response.json()
        user_data["password"] = password
        user_data["access_token"] = token
        return user_data
    
    # If testsuperuser login failed, try root as fallback
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
        user_data["access_token"] = token
        return user_data
    
    # If both failed, skip tests
    pytest.skip(f"Superuser login failed: {response.text}")


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
    """Get authentication headers for a superuser."""
    global _last_login_time
    
    # Add delay to avoid rate limiting
    async with _test_user_lock:
        current_time = time.time()
        time_since_last_login = current_time - _last_login_time
        if time_since_last_login < 0.5:
            await asyncio.sleep(0.5 - time_since_last_login)
    
    # Use testsuperuser first
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testsuperuser", "password": "TestPassword123!"}
    )
    
    # Update last login time
    _last_login_time = time.time()
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    # Fallback to root if testsuperuser fails
    if not ROOT_PASSWORD:
        pytest.skip("Superuser login failed and root password not available")
    
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "root", "password": ROOT_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Superuser login failed: {response.text}")
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_cookies(client: AsyncClient, test_user: dict) -> dict:
    """Get authentication cookies for web route testing."""
    # Add delay to avoid rate limiting
    await asyncio.sleep(0.5)
    
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
    # Try testsuperuser first
    response = await client.post(
        "/login",
        data={
            "username": "testsuperuser",
            "password": "TestPassword123!"
        }
    )
    
    if response.status_code == 302:
        # Extract the access token from cookies
        cookies = response.cookies
        access_token = cookies.get("access_token")
        assert access_token is not None, "No access token in cookies"
        return {"access_token": access_token}
    
    # Fallback to root
    if not ROOT_PASSWORD:
        pytest.skip("Superuser login failed and root password not available")
    
    response = await client.post(
        "/login",
        data={
            "username": "root",
            "password": ROOT_PASSWORD
        }
    )
    if response.status_code != 302:
        pytest.skip(f"Superuser login failed: {response.text}")
    
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
    password = "DeletePass123!"
    
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