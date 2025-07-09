"""
Server statistics endpoints.

These endpoints provide system monitoring information for authenticated users.
"""
import os
import platform
import time
from datetime import datetime
from typing import Optional

import psutil
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.rate_limiter import limiter
from app.models.user import User
from app.schemas.server_stats import ServerStats, ServerStatsFormatted

router = APIRouter()

# Store app start time
APP_START_TIME = time.time()


def format_bytes(bytes_value: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def format_uptime(seconds: float) -> str:
    """Convert seconds to human-readable uptime format."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def get_server_stats() -> dict:
    """Collect server statistics."""
    current_time = datetime.utcnow()
    uptime_seconds = time.time() - APP_START_TIME
    
    # CPU info
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_freq = psutil.cpu_freq()
    
    # Memory info
    memory = psutil.virtual_memory()
    
    # Disk info (root partition)
    disk = psutil.disk_usage('/')
    
    # Current process info
    process = psutil.Process()
    process_memory = process.memory_info()
    
    return {
        # System info
        "hostname": platform.node(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        
        # CPU info
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_percent": cpu_percent,
        "cpu_freq_current": cpu_freq.current if cpu_freq else None,
        "cpu_freq_max": cpu_freq.max if cpu_freq else None,
        
        # Memory info
        "memory_total": memory.total,
        "memory_used": memory.used,
        "memory_available": memory.available,
        "memory_percent": memory.percent,
        
        # Disk info
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
        "disk_percent": disk.percent,
        
        # Application info
        "app_uptime_seconds": uptime_seconds,
        "app_start_time": datetime.utcfromtimestamp(APP_START_TIME),
        "current_time": current_time,
        
        # Process info
        "process_id": process.pid,
        "process_memory_rss": process_memory.rss,
        "process_memory_vms": process_memory.vms,
        "process_threads": process.num_threads(),
    }


@router.get("/", response_model=ServerStats)
@limiter.limit("10/minute")
async def get_stats(
    request: Request,
    current_user: User = Depends(deps.get_current_active_user)
) -> ServerStats:
    """
    Get server statistics - Protected endpoint.
    
    Returns current server resource usage and system information.
    Only accessible to authenticated users.
    
    Authentication required: YES
    Token type: Bearer (JWT)
    Access level: Any authenticated user
    Rate limit: 10 requests per minute
    
    Returns:
        ServerStats: Current server statistics
    """
    stats = get_server_stats()
    return ServerStats(**stats)


@router.get("/formatted", response_model=ServerStatsFormatted)
@limiter.limit("10/minute")
async def get_stats_formatted(
    request: Request,
    current_user: User = Depends(deps.get_current_active_user)
) -> ServerStatsFormatted:
    """
    Get server statistics with formatted values - Protected endpoint.
    
    Returns current server statistics with human-readable formatted values
    for memory, disk space, and uptime. Only accessible to authenticated users.
    
    Authentication required: YES
    Token type: Bearer (JWT)
    Access level: Any authenticated user
    Rate limit: 10 requests per minute
    
    Returns:
        ServerStatsFormatted: Server statistics with formatted values
    """
    stats = get_server_stats()
    
    # Add formatted values
    stats.update({
        "memory_total_formatted": format_bytes(stats["memory_total"]),
        "memory_used_formatted": format_bytes(stats["memory_used"]),
        "memory_available_formatted": format_bytes(stats["memory_available"]),
        "disk_total_formatted": format_bytes(stats["disk_total"]),
        "disk_used_formatted": format_bytes(stats["disk_used"]),
        "disk_free_formatted": format_bytes(stats["disk_free"]),
        "uptime_formatted": format_uptime(stats["app_uptime_seconds"]),
        "process_memory_rss_formatted": format_bytes(stats["process_memory_rss"]),
        "process_memory_vms_formatted": format_bytes(stats["process_memory_vms"]),
    })
    
    return ServerStatsFormatted(**stats)