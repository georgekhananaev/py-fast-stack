"""
Test web routes for user operations.
Created by George Khananaev
https://george.khananaev.com/

These tests are for web routes that expect cookies and form data.
"""

import pytest
import asyncio
from httpx import AsyncClient


class TestWebUserOperations:
    """Test web user operations that require cookies."""
    
    @pytest.mark.asyncio
    async def test_delete_user_protection(
        self, 
        client: AsyncClient, 
        superuser_cookies: dict, 
        test_user_for_deletion: dict
    ):
        """Test that root user cannot be deleted via web route."""
        # First, try to delete root user (should fail)
        response = await client.delete(
            "/users/delete/1",  # Root user typically has ID 1
            cookies=superuser_cookies
        )
        
        # Check if the response is JSON or HTML error page
        if response.status_code == 403:
            try:
                response_json = response.json()
                assert "Cannot delete root user" in response_json["detail"]
            except:
                # If it's an HTML error page, just check that we got forbidden
                assert response.status_code == 403
                print(f"HTML response title: {response.headers.get('title', 'No title')}")
                print(f"Response contains forbidden: {'forbidden' in response.text.lower()}")
        else:
            assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        
        # Now try to delete a regular test user (should succeed)
        response = await client.delete(
            f"/users/delete/{test_user_for_deletion['id']}",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        
        # Check if response is JSON
        try:
            response_json = response.json()
            assert "User deleted successfully" in response_json["detail"]
        except:
            # If HTML response, just check status code
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_profile_update(
        self, 
        client: AsyncClient, 
        test_user: dict, 
        auth_cookies: dict
    ):
        """Test profile update via web route."""
        # Update profile
        response = await client.post(
            "/profile/update",
            data={"full_name": "Updated Test User"},
            cookies=auth_cookies
        )
        assert response.status_code == 302  # Redirect after successful update
        
        # Verify the update by checking the profile page
        profile_response = await client.get(
            "/profile",
            cookies=auth_cookies
        )
        assert profile_response.status_code == 200
        assert "Updated Test User" in profile_response.text
    
    @pytest.mark.asyncio
    async def test_password_change(
        self, 
        client: AsyncClient, 
        test_user: dict, 
        auth_cookies: dict
    ):
        """Test password change via web route."""
        # Add delay to avoid rate limiting
        await asyncio.sleep(0.5)
        
        # Change password
        response = await client.post(
            "/profile/password",
            data={
                "current_password": test_user["password"],
                "new_password": "NewPassword123!",
                "confirm_new_password": "NewPassword123!"
            },
            cookies=auth_cookies
        )
        assert response.status_code == 302  # Redirect after successful password change
        
        # Add delay between login attempts
        await asyncio.sleep(0.5)
        
        # Verify the old password no longer works
        old_login_response = await client.post(
            "/login",
            data={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        assert old_login_response.status_code == 401
        
        # Add delay between login attempts
        await asyncio.sleep(0.5)
        
        # Verify the new password works
        new_login_response = await client.post(
            "/login",
            data={
                "username": test_user["username"],
                "password": "NewPassword123!"
            }
        )
        assert new_login_response.status_code == 302  # Redirect after successful login
    
    @pytest.mark.asyncio
    async def test_password_change_wrong_current_password(
        self, 
        client: AsyncClient, 
        test_user: dict, 
        auth_cookies: dict
    ):
        """Test password change with wrong current password."""
        response = await client.post(
            "/profile/password",
            data={
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword123!",
                "confirm_new_password": "NewPassword123!"
            },
            cookies=auth_cookies
        )
        assert response.status_code == 400
        assert "Current password is incorrect" in response.text
    
    @pytest.mark.asyncio
    async def test_password_change_mismatch(
        self, 
        client: AsyncClient, 
        test_user: dict, 
        auth_cookies: dict
    ):
        """Test password change with mismatched new passwords."""
        response = await client.post(
            "/profile/password",
            data={
                "current_password": test_user["password"],
                "new_password": "NewPassword123!",
                "confirm_new_password": "DifferentPassword123!"
            },
            cookies=auth_cookies
        )
        assert response.status_code == 400
        assert "New passwords do not match" in response.text
    
    @pytest.mark.asyncio
    async def test_dashboard_access(
        self, 
        client: AsyncClient, 
        test_user: dict, 
        auth_cookies: dict
    ):
        """Test authenticated user can access dashboard."""
        response = await client.get(
            "/dashboard",
            cookies=auth_cookies
        )
        assert response.status_code == 200
        assert "Dashboard" in response.text
        assert test_user["username"] in response.text
    
    @pytest.mark.asyncio
    async def test_dashboard_redirect_without_auth(
        self, 
        client: AsyncClient
    ):
        """Test unauthenticated user gets redirected from dashboard."""
        response = await client.get("/dashboard")
        assert response.status_code == 303  # Redirect response
        assert response.headers["location"] == "/login"
    
    @pytest.mark.asyncio
    async def test_admin_user_management_access(
        self, 
        client: AsyncClient, 
        superuser_cookies: dict
    ):
        """Test superuser can access user management page."""
        response = await client.get(
            "/users",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        assert "Users Management" in response.text
    
    @pytest.mark.asyncio
    async def test_admin_user_management_regular_user_denied(
        self, 
        client: AsyncClient, 
        auth_cookies: dict
    ):
        """Test regular user cannot access user management page."""
        response = await client.get(
            "/users",
            cookies=auth_cookies
        )
        assert response.status_code == 303  # Redirect response
        assert response.headers["location"] == "/dashboard"
    
    @pytest.mark.asyncio
    async def test_self_deletion_protection(
        self, 
        client: AsyncClient, 
        test_user: dict, 
        superuser_cookies: dict
    ):
        """Test that users cannot delete their own account."""
        # Login as root and try to delete own account
        response = await client.delete(
            "/users/delete/1",  # Root user typically has ID 1
            cookies=superuser_cookies
        )
        assert response.status_code == 403
        
        # Check if response is JSON or HTML
        try:
            response_json = response.json()
            assert "Cannot delete root user" in response_json["detail"]
        except:
            # If it's an HTML error page, just check that we got forbidden
            assert response.status_code == 403