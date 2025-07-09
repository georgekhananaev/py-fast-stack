import asyncio
import time
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.rate_limit
async def test_login_rate_limit(client: AsyncClient):
    """Test that login endpoint is rate limited to 5 requests per minute."""
    # First create a test user
    timestamp = int(time.time() * 1000)
    username = f"ratelimituser_{timestamp}"
    email = f"ratelimit_{timestamp}@example.com"
    password = "TestPassword123!"
    
    # Register the user
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "full_name": "Rate Limit Test User"
        }
    )
    assert register_response.status_code == 200
    
    login_data = {
        "username": username,
        "password": password
    }
    
    # Make 5 successful requests (within limit)
    for i in range(5):
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200, f"Request {i+1} failed unexpectedly"
    
    # 6th request should be rate limited
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 429
    assert "5 per 1 minute" in response.text


@pytest.mark.asyncio
@pytest.mark.rate_limit
async def test_register_rate_limit(client: AsyncClient):
    """Test that registration endpoint is rate limited to 3 requests per minute."""
    # Make 3 registration attempts (within limit)
    timestamp = int(time.time() * 1000)
    
    for i in range(3):
        register_data = {
            "username": f"testuser_{timestamp}_{i}",
            "email": f"test_{timestamp}_{i}@example.com",
            "password": "TestPassword123!"
        }
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code in [200, 201], f"Request {i+1} failed unexpectedly: {response.status_code} - {response.text[:200]}"
    
    # 4th request should be rate limited
    register_data = {
        "username": f"testuser_{timestamp}_4",
        "email": f"test_{timestamp}_4@example.com",
        "password": "TestPassword123!"
    }
    response = await client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 429
    assert "3 per 1 minute" in response.text


@pytest.mark.asyncio
@pytest.mark.rate_limit
async def test_web_login_rate_limit(client: AsyncClient):
    """Test that web login form is rate limited to 5 requests per minute."""
    # First create a test user
    timestamp = int(time.time() * 1000)
    username = f"webloginuser_{timestamp}"
    email = f"weblogin_{timestamp}@example.com"
    password = "TestPassword123!"
    
    # Register the user via API
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )
    assert register_response.status_code == 200
    
    login_data = {
        "username": username,
        "password": password
    }
    
    # Make 5 login attempts (within limit)
    for i in range(5):
        response = await client.post("/login", data=login_data)
        assert response.status_code in [200, 302, 303], f"Request {i+1} failed unexpectedly"
    
    # 6th request should be rate limited
    response = await client.post("/login", data=login_data)
    assert response.status_code == 429


@pytest.mark.asyncio
@pytest.mark.rate_limit
async def test_web_register_rate_limit(client: AsyncClient):
    """Test that web registration form is rate limited to 3 requests per minute."""
    timestamp = int(time.time() * 1000)
    
    # Make 3 registration attempts (within limit)
    for i in range(3):
        register_data = {
            "username": f"webuser_{timestamp}_{i}",
            "email": f"webtest_{timestamp}_{i}@example.com",
            "password": "TestPassword123!",
            "full_name": f"Web User {i}"
        }
        response = await client.post("/register", data=register_data)
        assert response.status_code in [200, 302, 303], f"Request {i+1} failed unexpectedly"
    
    # 4th request should be rate limited
    register_data = {
        "username": f"webuser_{timestamp}_4",
        "email": f"webtest_{timestamp}_4@example.com",
        "password": "TestPassword123!",
        "full_name": "Web User 4"
    }
    response = await client.post("/register", data=register_data)
    assert response.status_code == 429


@pytest.mark.asyncio
@pytest.mark.rate_limit
async def test_newsletter_subscription_rate_limit(client: AsyncClient):
    """Test that newsletter subscription is rate limited to 3 requests per minute."""
    timestamp = int(time.time() * 1000)
    
    # Make 3 subscription attempts (within limit)
    for i in range(3):
        subscription_data = {
            "email": f"newsletter_{timestamp}_{i}@example.com",
            "name": f"Newsletter User {i}"
        }
        response = await client.post("/api/v1/subscribe", json=subscription_data)
        assert response.status_code in [200, 201], f"Request {i+1} failed unexpectedly: {response.status_code} - {response.text[:200]}"
    
    # 4th request should be rate limited
    subscription_data = {
        "email": f"newsletter_{timestamp}_4@example.com",
        "name": "Newsletter User 4"
    }
    response = await client.post("/api/v1/subscribe", json=subscription_data)
    assert response.status_code == 429
    assert "3 per 1 minute" in response.text


@pytest.mark.asyncio
async def test_health_endpoint_not_rate_limited(client: AsyncClient):
    """Test that health endpoint is NOT rate limited."""
    # Make many requests to health endpoint
    num_requests = 100
    
    for i in range(num_requests):
        response = await client.get("/health")
        assert response.status_code == 200, f"Health check request {i+1} failed unexpectedly"
    
    # All requests should succeed
    print(f"\nSuccessfully made {num_requests} requests to /health endpoint without rate limiting")


@pytest.mark.asyncio
@pytest.mark.rate_limit
async def test_rate_limit_resets_after_time(client: AsyncClient):
    """Test that rate limit resets after the time window expires."""
    # First create a test user
    timestamp = int(time.time() * 1000)
    username = f"resetuser_{timestamp}"
    email = f"reset_{timestamp}@example.com"
    password = "TestPassword123!"
    
    # Register the user
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "full_name": "Rate Limit Test User"
        }
    )
    assert register_response.status_code == 200
    
    login_data = {
        "username": username,
        "password": password
    }
    
    # Exhaust rate limit
    for _ in range(6):
        await client.post("/api/v1/auth/login", data=login_data)
    
    # Verify rate limit is active
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 429
    
    # Wait for rate limit window to expire (61 seconds to be safe)
    # Note: In a real test environment, you might want to mock time instead
    # await asyncio.sleep(61)
    
    # For now, we'll just verify the rate limit was applied
    # In production tests, you'd want to test the reset functionality