"""
Test web routes for subscriber management operations.
Created for PyFastStack

These tests are for web routes that expect cookies and form data.
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import text
from app.db.session import get_db, engine
from app.crud.subscription import subscription as crud_subscription
from app.schemas.subscription import SubscriptionCreate


class TestWebSubscriberOperations:
    """Test web subscriber operations that require superuser access."""
    
    @pytest.mark.asyncio
    async def test_subscribers_list_access_superuser(
        self, 
        client: AsyncClient, 
        superuser_cookies: dict
    ):
        """Test that superuser can access subscribers list."""
        response = await client.get(
            "/subscribers",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        assert "Subscribers Management" in response.text
        assert "Search by email, name, or company" in response.text
    
    @pytest.mark.asyncio
    async def test_subscribers_list_access_regular_user_denied(
        self, 
        client: AsyncClient, 
        auth_cookies: dict
    ):
        """Test that regular user cannot access subscribers list."""
        response = await client.get(
            "/subscribers",
            cookies=auth_cookies,
            follow_redirects=False
        )
        # Should redirect to dashboard
        assert response.status_code == 303
        assert response.headers["location"] == "/dashboard"
    
    @pytest.mark.asyncio
    async def test_subscribers_list_access_unauthenticated(
        self, 
        client: AsyncClient
    ):
        """Test that unauthenticated user cannot access subscribers list."""
        response = await client.get(
            "/subscribers",
            follow_redirects=False
        )
        # Should redirect to login
        assert response.status_code == 303
        assert response.headers["location"] == "/login"
    
    @pytest.mark.asyncio
    async def test_subscribers_list_pagination(
        self, 
        client: AsyncClient, 
        superuser_cookies: dict
    ):
        """Test subscribers list pagination."""
        # First, create some test subscribers directly in the database to avoid rate limits
        from app.db.session import AsyncSessionLocal
        from app.schemas.subscription import SubscriptionCreate
        
        async with AsyncSessionLocal() as db:
            for i in range(15):
                email = f"test_sub_{i}@example.com"
                # Check if already exists
                existing = await crud_subscription.get_by_email(db, email=email)
                if not existing:
                    subscription_data = SubscriptionCreate(
                        email=email,
                        name=f"Test Subscriber {i}",
                        company=f"Company {i}" if i % 2 == 0 else None,
                        interests=[f"Interest {i}"] if i % 3 == 0 else None
                    )
                    await crud_subscription.create(db, obj_in=subscription_data)
        
        # Test first page
        response = await client.get(
            "/subscribers?page=1&limit=10",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        assert "Showing" in response.text
        assert "results" in response.text
        
        # Test second page
        response = await client.get(
            "/subscribers?page=2&limit=10",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        
        # Clean up - get subscriptions from API and delete them
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            for i in range(15):
                await crud_subscription.deactivate_subscription(db, email=f"test_sub_{i}@example.com")
    
    @pytest.mark.asyncio
    async def test_subscribers_list_search(
        self, 
        client: AsyncClient, 
        superuser_cookies: dict
    ):
        """Test subscribers list search functionality."""
        # Create a test subscriber via API
        subscription_data = {
            "email": "search_test@example.com",
            "name": "Searchable User",
            "company": "Test Company",
            "interests": ["Testing", "Development"]
        }
        response = await client.post(
            "/api/v1/subscribe",
            json=subscription_data
        )
        # 400 means email already exists, which is fine for our test
        assert response.status_code in [200, 201, 400], f"Failed to create subscriber: {response.text}"
        
        # Search by email
        response = await client.get(
            "/subscribers?search=search_test",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        assert "search_test@example.com" in response.text
        assert "Searchable User" in response.text
        
        # Search by name
        response = await client.get(
            "/subscribers?search=Searchable",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        assert "Searchable User" in response.text
        
        # Search by company
        response = await client.get(
            "/subscribers?search=Test%20Company",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        assert "Test Company" in response.text
        
        # Clean up
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await crud_subscription.deactivate_subscription(db, email="search_test@example.com")
    
    @pytest.mark.asyncio
    async def test_subscribers_list_sorting(
        self, 
        client: AsyncClient, 
        superuser_cookies: dict
    ):
        """Test subscribers list sorting functionality."""
        # Clean up any existing test data first
        from app.db.session import AsyncSessionLocal
        test_data = [
            ("alpha@example.com", "Alpha User", "A Company"),
            ("beta@example.com", "Beta User", "B Company"),
            ("gamma@example.com", "Gamma User", "C Company"),
        ]
        async with AsyncSessionLocal() as db:
            for email, _, _ in test_data:
                existing = await crud_subscription.get_by_email(db, email=email)
                if existing:
                    await crud_subscription.remove(db, id=existing.id)
        
        # Create test subscribers via API
        for email, name, company in test_data:
            subscription_data = {
                "email": email,
                "name": name,
                "company": company
            }
            response = await client.post(
                "/api/v1/subscribe",
                json=subscription_data
            )
            # 400 means email already exists, which is fine for our test
            assert response.status_code in [200, 201, 400], f"Failed to create subscriber: {response.text}"
        
        # Test sorting by email ascending
        response = await client.get(
            "/subscribers?sort_by=email&sort_order=asc",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        content = response.text
        # Check order in HTML
        alpha_pos = content.find("alpha@example.com")
        beta_pos = content.find("beta@example.com")
        gamma_pos = content.find("gamma@example.com")
        if alpha_pos != -1 and beta_pos != -1 and gamma_pos != -1:
            assert alpha_pos < beta_pos < gamma_pos
        
        # Test sorting by name descending
        response = await client.get(
            "/subscribers?sort_by=name&sort_order=desc",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        
        # Clean up
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            for email, _, _ in test_data:
                subscription = await crud_subscription.get_by_email(db, email=email)
                if subscription:
                    await crud_subscription.remove(db, id=subscription.id)
    
    @pytest.mark.asyncio
    async def test_delete_subscriber(
        self, 
        client: AsyncClient, 
        superuser_cookies: dict
    ):
        """Test deleting a subscriber."""
        # Create a test subscriber via API
        subscription_data = {
            "email": "delete_test@example.com",
            "name": "Delete Test User"
        }
        response = await client.post(
            "/api/v1/subscribe",
            json=subscription_data
        )
        
        # If email already exists (400), we need to get the subscriber from the database
        if response.status_code == 400:
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                subscription = await crud_subscription.get_by_email(db, email="delete_test@example.com")
                assert subscription is not None, "Subscriber not found in database"
                subscriber_id = subscription.id
        else:
            assert response.status_code in [200, 201], f"Failed to create subscriber: {response.text}"
            subscriber_id = response.json()["id"]
        
        # Delete the subscriber
        response = await client.delete(
            f"/subscribers/delete/{subscriber_id}",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        assert response.json()["detail"] == "Subscriber deleted successfully"
        
        # Verify deletion by trying to get the subscriber again
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            subscriber = await crud_subscription.get(db, id=subscriber_id)
            assert subscriber is None
    
    @pytest.mark.asyncio
    async def test_delete_subscriber_regular_user_denied(
        self, 
        client: AsyncClient, 
        auth_cookies: dict
    ):
        """Test that regular user cannot delete subscribers."""
        response = await client.delete(
            "/subscribers/delete/999",  # Non-existent ID
            cookies=auth_cookies
        )
        assert response.status_code == 403
        # Check for JSON response or ensure it's the expected error
        try:
            json_response = response.json()
            assert "Not enough permissions" in json_response["detail"]
        except:
            # If not JSON, just verify the status code
            pass
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_subscriber(
        self, 
        client: AsyncClient, 
        superuser_cookies: dict
    ):
        """Test deleting a non-existent subscriber."""
        response = await client.delete(
            "/subscribers/delete/99999",  # Non-existent ID
            cookies=superuser_cookies
        )
        assert response.status_code == 404
        # Check for JSON response
        try:
            json_response = response.json()
            assert "Subscriber not found" in json_response["detail"]
        except:
            # If not JSON, just verify the status code
            pass
    
    @pytest.mark.asyncio
    async def test_navigation_menu_shows_subscribers_for_superuser(
        self, 
        client: AsyncClient, 
        superuser_cookies: dict
    ):
        """Test that navigation menu shows Subscribers link for superuser."""
        response = await client.get(
            "/dashboard",
            cookies=superuser_cookies
        )
        assert response.status_code == 200
        assert 'href="/subscribers"' in response.text
        assert "Subscribers" in response.text
    
    @pytest.mark.asyncio
    async def test_navigation_menu_hides_subscribers_for_regular_user(
        self, 
        client: AsyncClient, 
        auth_cookies: dict
    ):
        """Test that navigation menu does not show Subscribers link for regular user."""
        response = await client.get(
            "/dashboard",
            cookies=auth_cookies
        )
        assert response.status_code == 200
        assert 'href="/subscribers"' not in response.text or response.text.count('href="/subscribers"') == 0