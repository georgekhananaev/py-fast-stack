"""
Server statistics schemas.

These schemas define the structure for server monitoring data.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ServerStats(BaseModel):
    """Server statistics response model."""
    
    # System info
    hostname: str = Field(..., description="Server hostname")
    platform: str = Field(..., description="Operating system platform")
    platform_version: str = Field(..., description="OS version")
    architecture: str = Field(..., description="System architecture")
    python_version: str = Field(..., description="Python version")
    
    # CPU info
    cpu_count: int = Field(..., description="Number of CPU cores")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    cpu_freq_current: Optional[float] = Field(None, description="Current CPU frequency in MHz")
    cpu_freq_max: Optional[float] = Field(None, description="Maximum CPU frequency in MHz")
    
    # Memory info
    memory_total: int = Field(..., description="Total memory in bytes")
    memory_used: int = Field(..., description="Used memory in bytes")
    memory_available: int = Field(..., description="Available memory in bytes")
    memory_percent: float = Field(..., description="Memory usage percentage")
    
    # Disk info
    disk_total: int = Field(..., description="Total disk space in bytes")
    disk_used: int = Field(..., description="Used disk space in bytes")
    disk_free: int = Field(..., description="Free disk space in bytes")
    disk_percent: float = Field(..., description="Disk usage percentage")
    
    # Application info
    app_uptime_seconds: float = Field(..., description="Application uptime in seconds")
    app_start_time: datetime = Field(..., description="Application start time")
    current_time: datetime = Field(..., description="Current server time")
    
    # Process info
    process_id: int = Field(..., description="Process ID")
    process_memory_rss: int = Field(..., description="Process resident set size in bytes")
    process_memory_vms: int = Field(..., description="Process virtual memory size in bytes")
    process_threads: int = Field(..., description="Number of threads")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "hostname": "webserver-01",
                "platform": "Linux",
                "platform_version": "5.15.0-56-generic",
                "architecture": "x86_64",
                "python_version": "3.11.5",
                "cpu_count": 4,
                "cpu_percent": 15.5,
                "cpu_freq_current": 2400.0,
                "cpu_freq_max": 3600.0,
                "memory_total": 17179869184,
                "memory_used": 8589934592,
                "memory_available": 8589934592,
                "memory_percent": 50.0,
                "disk_total": 107374182400,
                "disk_used": 53687091200,
                "disk_free": 53687091200,
                "disk_percent": 50.0,
                "app_uptime_seconds": 3600.0,
                "app_start_time": "2024-01-01T12:00:00",
                "current_time": "2024-01-01T13:00:00",
                "process_id": 12345,
                "process_memory_rss": 104857600,
                "process_memory_vms": 209715200,
                "process_threads": 10
            }
        }


class ServerStatsFormatted(ServerStats):
    """Server statistics with human-readable formatted values."""
    
    # Formatted values for display
    memory_total_formatted: str = Field(..., description="Total memory (human-readable)")
    memory_used_formatted: str = Field(..., description="Used memory (human-readable)")
    memory_available_formatted: str = Field(..., description="Available memory (human-readable)")
    disk_total_formatted: str = Field(..., description="Total disk space (human-readable)")
    disk_used_formatted: str = Field(..., description="Used disk space (human-readable)")
    disk_free_formatted: str = Field(..., description="Free disk space (human-readable)")
    uptime_formatted: str = Field(..., description="Uptime (human-readable)")
    process_memory_rss_formatted: str = Field(..., description="Process RSS (human-readable)")
    process_memory_vms_formatted: str = Field(..., description="Process VMS (human-readable)")