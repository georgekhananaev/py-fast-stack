"""
System statistics endpoints - Superuser only.

Provides server metrics and benchmarks for monitoring.
"""
import psutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser, get_db
from app.models.user import User
from app.models.subscription import Subscription

router = APIRouter()


@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system statistics and benchmarks - Protected endpoint (Admin only).
    
    Returns server metrics including:
    - Total number of users
    - Total number of active users
    - Total number of subscribers
    - Total number of active subscribers
    - Server CPU usage percentage
    - Server memory usage
    - Server disk usage
    - Server uptime
    
    Authentication required: YES
    Token type: Bearer token (in Authorization header)
    Access level: SUPERUSER ONLY
    
    Returns:
        Dictionary with system statistics
        
    Raises:
        401: Not authenticated
        403: Not a superuser
    """
    try:
        # Get user statistics
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        active_users_result = await db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_users_result.scalar()
        
        # Get subscriber statistics
        total_subscribers_result = await db.execute(select(func.count(Subscription.id)))
        total_subscribers = total_subscribers_result.scalar()
        
        active_subscribers_result = await db.execute(
            select(func.count(Subscription.id)).where(Subscription.is_active == True)
        )
        active_subscribers = active_subscribers_result.scalar()
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get system uptime
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        current_time = datetime.now()
        uptime = current_time - boot_time
        
        # Format uptime
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users
            },
            "subscribers": {
                "total": total_subscribers,
                "active": active_subscribers,
                "inactive": total_subscribers - active_subscribers
            },
            "server": {
                "cpu_usage_percent": round(cpu_percent, 2),
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent": round(memory.percent, 2)
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": round(disk.percent, 2)
                },
                "uptime": uptime_str,
                "timestamp": current_time.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system statistics: {str(e)}"
        )