"""
Test authentication endpoints.
Created by George Khananaev
https://george.khananaev.com/
"""

import pytest
import time
import random
import asyncio
from httpx import AsyncClient


class TestAuthentication:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        # Add small delay to avoid rate limiting from previous tests
        await asyncio.sleep(0.5)
        
        timestamp = int(time.time() * 1000)
        rand = random.randint(1000, 9999)
        email = f"register_{timestamp}_{rand}@example.com"
        username = f"registeruser_{timestamp}_{rand}"
        
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": "RegisterPass123!",
                "full_name": "Register Test"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert data["username"] == username
        assert data["full_name"] == "Register Test"
        assert "id" in data
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: dict):
        """Test registration with duplicate email."""
        # Add small delay to avoid rate limiting
        await asyncio.sleep(0.5)
        
        timestamp = int(time.time() * 1000)
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user["email"],
                "username": f"anotheruser_{timestamp}",
                "password": "TestPassword123!",
                "full_name": "Another User"
            }
        )
        assert response.status_code in [400, 422]  # Accept either
        # Check for duplicate error in response
        response_text = str(response.json()).lower()
        assert "already" in response_text or "duplicate" in response_text or "exists" in response_text
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user: dict):
        """Test registration with duplicate username."""
        # Add small delay to avoid rate limiting
        await asyncio.sleep(0.5)
        
        timestamp = int(time.time() * 1000)
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"another_{timestamp}@example.com",
                "username": test_user["username"],
                "password": "TestPassword123!",
                "full_name": "Another User"
            }
        )
        assert response.status_code in [400, 422]  # Accept either
        # Check for duplicate error in response
        response_text = str(response.json()).lower()
        assert "already" in response_text or "duplicate" in response_text or "exists" in response_text
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: dict):
        """Test successful login."""
        # Add small delay to avoid rate limiting
        await asyncio.sleep(0.5)
        
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: dict):
        """Test login with wrong password."""
        # Add small delay to avoid rate limiting
        await asyncio.sleep(0.5)
        
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user["username"],
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code in [400, 401]  # Accept either
        assert "incorrect" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        # Add small delay to avoid rate limiting
        await asyncio.sleep(0.5)
        
        timestamp = int(time.time() * 1000)
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": f"nonexistent_{timestamp}",
                "password": "NonExistentPass123!"
            }
        )
        assert response.status_code in [400, 401]  # Accept either
        assert "incorrect" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, superuser_auth_headers: dict):
        """Test login with inactive user."""
        # Add small delay to avoid rate limiting
        await asyncio.sleep(0.5)
        
        # Create a test user first
        timestamp = int(time.time() * 1000)
        rand = random.randint(1000, 9999)
        username = f"inactive_{timestamp}_{rand}"
        email = f"inactive_{timestamp}_{rand}@example.com"
        password = "InactivePass123!"
        
        # Create user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                "full_name": "Inactive User"
            }
        )
        assert response.status_code == 200
        user_data = response.json()
        
        # Deactivate the user as superuser
        response = await client.put(
            f"/api/v1/users/{user_data['id']}",
            headers=superuser_auth_headers,
            json={
                "is_active": False
            }
        )
        assert response.status_code == 200
        
        # Add delay before login attempt
        await asyncio.sleep(0.5)
        
        # Try to login with inactive user
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": username,
                "password": password
            }
        )
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, test_user: dict, auth_headers: dict):
        """Test getting current user info."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user["username"]
        assert data["email"] == test_user["email"]
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]


class TestHealthCheck:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "datetime" in data
        assert "timestamp" in data