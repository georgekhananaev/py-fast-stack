"""
Test user CRUD operations.
Created by George Khananaev
https://george.khananaev.com/
"""

import pytest
import time
import random
from httpx import AsyncClient


class TestUserOperations:
    """Test user CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_list_users_as_superuser(
        self, client: AsyncClient, test_user: dict, superuser_auth_headers: dict
    ):
        """Test listing users as superuser."""
        response = await client.get(
            "/api/v1/users/",
            headers=superuser_auth_headers
        )
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 1  # At least root user
        usernames = [user["username"] for user in users]
        assert "root" in usernames
    
    @pytest.mark.asyncio
    async def test_list_users_as_regular_user(
        self, client: AsyncClient, test_user: dict, auth_headers: dict
    ):
        """Test listing users as regular user (should fail)."""
        response = await client.get(
            "/api/v1/users/",
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(
        self, client: AsyncClient, test_user: dict, auth_headers: dict
    ):
        """Test getting user by ID."""
        response = await client.get(
            f"/api/v1/users/{test_user['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user["id"]
        assert data["username"] == test_user["username"]
        assert data["email"] == test_user["email"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_user(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent user."""
        response = await client.get(
            "/api/v1/users/99999",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_user_as_superuser(
        self, client: AsyncClient, test_user: dict, superuser_auth_headers: dict
    ):
        """Test updating user as superuser."""
        timestamp = int(time.time() * 1000)
        new_email = f"updated_{timestamp}@example.com"
        response = await client.put(
            f"/api/v1/users/{test_user['id']}",
            headers=superuser_auth_headers,
            json={
                "email": new_email,
                "full_name": "Updated Name",
                "is_active": True,
                "is_superuser": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_email
        assert data["full_name"] == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_update_user_as_regular_user(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating another user as regular user (should fail)."""
        # Try to update root user
        response = await client.put(
            f"/api/v1/users/1",
            headers=auth_headers,
            json={
                "email": "hacker@example.com"
            }
        )
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    # Skipping delete tests as they are web routes that require cookies
    
    


# Profile tests removed as they are web routes that require cookies
# See test_users_web.py for web route tests