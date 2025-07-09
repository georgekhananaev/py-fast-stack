"""
Tests for server statistics endpoints and functionality.
"""
import pytest
from httpx import AsyncClient
from fastapi import status


class TestServerStatsAPI:
    """Test server statistics API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_server_stats_requires_auth(self, client: AsyncClient):
        """Test that server stats endpoint requires authentication."""
        response = await client.get("/api/v1/server-stats/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"
    
    @pytest.mark.asyncio
    async def test_get_server_stats_authenticated(self, client: AsyncClient, auth_headers: dict):
        """Test getting server stats with authentication."""
        response = await client.get("/api/v1/server-stats/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Check system info
        assert "hostname" in data
        assert "platform" in data
        assert "platform_version" in data
        assert "architecture" in data
        assert "python_version" in data
        
        # Check CPU info
        assert "cpu_count" in data
        assert "cpu_percent" in data
        assert isinstance(data["cpu_count"], int)
        assert isinstance(data["cpu_percent"], float)
        assert data["cpu_count"] > 0
        assert 0 <= data["cpu_percent"] <= 100
        
        # Check memory info
        assert "memory_total" in data
        assert "memory_used" in data
        assert "memory_available" in data
        assert "memory_percent" in data
        assert isinstance(data["memory_total"], int)
        assert isinstance(data["memory_percent"], float)
        assert data["memory_total"] > 0
        assert 0 <= data["memory_percent"] <= 100
        
        # Check disk info
        assert "disk_total" in data
        assert "disk_used" in data
        assert "disk_free" in data
        assert "disk_percent" in data
        assert isinstance(data["disk_total"], int)
        assert isinstance(data["disk_percent"], float)
        assert data["disk_total"] > 0
        assert 0 <= data["disk_percent"] <= 100
        
        # Check application info
        assert "app_uptime_seconds" in data
        assert "app_start_time" in data
        assert "current_time" in data
        assert isinstance(data["app_uptime_seconds"], float)
        assert data["app_uptime_seconds"] >= 0
        
        # Check process info
        assert "process_id" in data
        assert "process_memory_rss" in data
        assert "process_memory_vms" in data
        assert "process_threads" in data
        assert isinstance(data["process_id"], int)
        assert isinstance(data["process_threads"], int)
        assert data["process_id"] > 0
        assert data["process_threads"] > 0
    
    @pytest.mark.asyncio
    async def test_get_server_stats_formatted(self, client: AsyncClient, auth_headers: dict):
        """Test getting formatted server stats with authentication."""
        response = await client.get("/api/v1/server-stats/formatted", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Check all regular fields are present
        assert "cpu_percent" in data
        assert "memory_total" in data
        
        # Check formatted fields
        assert "memory_total_formatted" in data
        assert "memory_used_formatted" in data
        assert "memory_available_formatted" in data
        assert "disk_total_formatted" in data
        assert "disk_used_formatted" in data
        assert "disk_free_formatted" in data
        assert "uptime_formatted" in data
        assert "process_memory_rss_formatted" in data
        assert "process_memory_vms_formatted" in data
        
        # Check format contains units
        assert any(unit in data["memory_total_formatted"] for unit in ["B", "KB", "MB", "GB", "TB"])
        assert any(unit in data["disk_total_formatted"] for unit in ["B", "KB", "MB", "GB", "TB"])
        
        # Check uptime format
        uptime = data["uptime_formatted"]
        assert any(unit in uptime for unit in ["s", "m", "h", "d"]) or uptime == "0s"
    
    @pytest.mark.asyncio
    async def test_server_stats_rate_limiting(self, client: AsyncClient, auth_headers: dict):
        """Test that server stats endpoint has rate limiting."""
        # Make 11 requests (limit is 10/minute)
        for i in range(11):
            response = await client.get("/api/v1/server-stats/", headers=auth_headers)
            if i < 10:
                assert response.status_code == status.HTTP_200_OK
            else:
                # 11th request should be rate limited
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                assert "Rate limit exceeded" in response.json()["detail"]


class TestServerStatsWeb:
    """Test server statistics web routes."""
    
    @pytest.mark.asyncio
    async def test_server_stats_page_requires_auth(self, client: AsyncClient):
        """Test that server stats page requires authentication."""
        response = await client.get("/server-stats", follow_redirects=False)
        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["location"] == "/login"
    
    @pytest.mark.asyncio
    async def test_server_stats_page_authenticated(self, client: AsyncClient, auth_cookies: dict):
        """Test accessing server stats page with authentication."""
        response = await client.get("/server-stats", cookies=auth_cookies)
        assert response.status_code == status.HTTP_200_OK
        assert "Server Statistics" in response.text
        assert "System Information" in response.text
        assert "CPU Usage" in response.text
        assert "Memory Usage" in response.text
        assert "Disk Usage" in response.text
        assert "Process Information" in response.text
    
    @pytest.mark.asyncio
    async def test_dashboard_has_server_stats_link(self, client: AsyncClient, auth_cookies: dict):
        """Test that dashboard contains link to server statistics."""
        response = await client.get("/dashboard", cookies=auth_cookies)
        assert response.status_code == status.HTTP_200_OK
        assert "/server-stats" in response.text
        assert "Server Statistics" in response.text
        assert "Monitor server resources" in response.text
    
    @pytest.mark.asyncio
    async def test_server_stats_cards_endpoint(self, client: AsyncClient, auth_cookies: dict):
        """Test the HTMX cards endpoint for real-time updates."""
        response = await client.get("/server-stats/cards", cookies=auth_cookies)
        assert response.status_code == status.HTTP_200_OK
        # Check that the response contains stats cards
        assert "System Information" in response.text
        assert "CPU Usage" in response.text
        assert "Memory Usage" in response.text
        assert "Disk Usage" in response.text
        assert "Process Information" in response.text
        # Check that it's a partial template (no base template elements)
        assert "<!DOCTYPE html>" not in response.text
        assert "<body" not in response.text
    
    @pytest.mark.asyncio
    async def test_server_stats_cards_requires_auth(self, client: AsyncClient):
        """Test that cards endpoint returns empty for unauthenticated requests."""
        response = await client.get("/server-stats/cards")
        assert response.status_code == status.HTTP_200_OK
        assert response.text == ""  # Empty response for HTMX


class TestServerStatsHelpers:
    """Test helper functions for server statistics."""
    
    def test_format_bytes(self):
        """Test bytes formatting function."""
        from app.api.v1.endpoints.server_stats import format_bytes
        
        assert format_bytes(0) == "0.00 B"
        assert format_bytes(1023) == "1023.00 B"
        assert format_bytes(1024) == "1.00 KB"
        assert format_bytes(1024 * 1024) == "1.00 MB"
        assert format_bytes(1024 * 1024 * 1024) == "1.00 GB"
        assert format_bytes(1024 * 1024 * 1024 * 1024) == "1.00 TB"
        assert format_bytes(1024 * 1024 * 1024 * 1024 * 1024) == "1.00 PB"
    
    def test_format_uptime(self):
        """Test uptime formatting function."""
        from app.api.v1.endpoints.server_stats import format_uptime
        
        assert format_uptime(0) == "0s"
        assert format_uptime(30) == "30s"
        assert format_uptime(60) == "1m"
        assert format_uptime(90) == "1m 30s"
        assert format_uptime(3600) == "1h"
        assert format_uptime(3661) == "1h 1m 1s"
        assert format_uptime(86400) == "1d"
        assert format_uptime(90061) == "1d 1h 1m 1s"
    
    def test_get_server_stats_structure(self):
        """Test that get_server_stats returns expected structure."""
        from app.api.v1.endpoints.server_stats import get_server_stats
        
        stats = get_server_stats()
        
        # Check all required fields are present
        required_fields = [
            "hostname", "platform", "platform_version", "architecture", "python_version",
            "cpu_count", "cpu_percent",
            "memory_total", "memory_used", "memory_available", "memory_percent",
            "disk_total", "disk_used", "disk_free", "disk_percent",
            "app_uptime_seconds", "app_start_time", "current_time",
            "process_id", "process_memory_rss", "process_memory_vms", "process_threads"
        ]
        
        for field in required_fields:
            assert field in stats, f"Missing field: {field}"
        
        # Check data types
        assert isinstance(stats["cpu_count"], int)
        assert isinstance(stats["cpu_percent"], float)
        assert isinstance(stats["memory_total"], int)
        assert isinstance(stats["memory_percent"], float)
        assert isinstance(stats["app_uptime_seconds"], float)