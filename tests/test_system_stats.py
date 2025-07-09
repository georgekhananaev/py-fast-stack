"""
Test system statistics endpoints.
Created for PyFastStack

Tests the system monitoring API endpoints.
"""

import pytest
from httpx import AsyncClient


class TestSystemStats:
    """Test system statistics endpoints."""
    
    @pytest.mark.asyncio
    async def test_system_stats_requires_superuser(
        self, 
        client: AsyncClient, 
        auth_headers: dict
    ):
        """Test that system stats endpoint requires superuser access."""
        # Regular user should get 403
        response = await client.get(
            "/api/v1/system/stats",
            headers=auth_headers
        )
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_system_stats_superuser_access(
        self, 
        client: AsyncClient, 
        superuser_auth_headers: dict
    ):
        """Test that superuser can access system stats."""
        response = await client.get(
            "/api/v1/system/stats",
            headers=superuser_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Check users data
        assert "users" in data
        assert "total" in data["users"]
        assert "active" in data["users"]
        assert "inactive" in data["users"]
        assert isinstance(data["users"]["total"], int)
        assert isinstance(data["users"]["active"], int)
        assert isinstance(data["users"]["inactive"], int)
        
        # Check subscribers data
        assert "subscribers" in data
        assert "total" in data["subscribers"]
        assert "active" in data["subscribers"]
        assert "inactive" in data["subscribers"]
        assert isinstance(data["subscribers"]["total"], int)
        assert isinstance(data["subscribers"]["active"], int)
        assert isinstance(data["subscribers"]["inactive"], int)
        
        # Check server data
        assert "server" in data
        assert "cpu_usage_percent" in data["server"]
        assert "memory" in data["server"]
        assert "disk" in data["server"]
        assert "uptime" in data["server"]
        assert "timestamp" in data["server"]
        
        # Check memory details
        assert "total_gb" in data["server"]["memory"]
        assert "used_gb" in data["server"]["memory"]
        assert "available_gb" in data["server"]["memory"]
        assert "percent" in data["server"]["memory"]
        
        # Check disk details
        assert "total_gb" in data["server"]["disk"]
        assert "used_gb" in data["server"]["disk"]
        assert "free_gb" in data["server"]["disk"]
        assert "percent" in data["server"]["disk"]
        
        # Validate data types and ranges
        assert isinstance(data["server"]["cpu_usage_percent"], (int, float))
        assert 0 <= data["server"]["cpu_usage_percent"] <= 100
        assert isinstance(data["server"]["memory"]["percent"], (int, float))
        assert 0 <= data["server"]["memory"]["percent"] <= 100
        assert isinstance(data["server"]["disk"]["percent"], (int, float))
        assert 0 <= data["server"]["disk"]["percent"] <= 100
        
        # Check uptime format
        assert isinstance(data["server"]["uptime"], str)
        assert "d" in data["server"]["uptime"]
        assert "h" in data["server"]["uptime"]
        assert "m" in data["server"]["uptime"]
        assert "s" in data["server"]["uptime"]
    
    @pytest.mark.asyncio
    async def test_system_stats_unauthenticated(
        self, 
        client: AsyncClient
    ):
        """Test that unauthenticated users cannot access system stats."""
        response = await client.get("/api/v1/system/stats")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_system_stats_data_consistency(
        self, 
        client: AsyncClient, 
        superuser_auth_headers: dict
    ):
        """Test that system stats data is consistent."""
        response = await client.get(
            "/api/v1/system/stats",
            headers=superuser_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Check that inactive counts are correct
        assert data["users"]["inactive"] == data["users"]["total"] - data["users"]["active"]
        assert data["subscribers"]["inactive"] == data["subscribers"]["total"] - data["subscribers"]["active"]
        
        # Check that memory values are consistent
        memory = data["server"]["memory"]
        assert memory["used_gb"] <= memory["total_gb"]
        assert memory["available_gb"] <= memory["total_gb"]
        
        # Check that disk values are consistent
        disk = data["server"]["disk"]
        assert disk["used_gb"] <= disk["total_gb"]
        assert disk["free_gb"] <= disk["total_gb"]
        # Note: used + free may not equal total due to reserved space