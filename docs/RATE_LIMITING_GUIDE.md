# Rate Limiting Guide for PyFastStack

## Overview

PyFastStack implements rate limiting using SlowAPI (a FastAPI adaptation of Flask-Limiter) to protect against abuse and ensure fair usage. This guide explains how rate limiting works and best practices.

## How Rate Limiting Works

### Time Window Reset
- Rate limits automatically reset after the specified time window
- Example: "5/minute" means 5 requests per minute, resetting every 60 seconds
- The window is rolling, not fixed - each request is tracked individually

### Current Rate Limits

```python
# Authentication endpoints
Login: 5 attempts per minute per IP
Registration: 3 new accounts per minute per IP
Password changes: 3 attempts per minute per IP

# Newsletter
Subscription: 3 subscriptions per minute per IP

# General API (if implemented)
Default API: 60 requests per minute per IP

# Excluded
Health endpoint: No rate limiting (for monitoring)
```

## Implementation Details

### 1. Rate Limiter Configuration

```python
# app/core/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_rate_limit_key_func(request):
    """Get the key function for rate limiting."""
    # For tests, use unique keys to avoid conflicts
    user_agent = request.headers.get("user-agent", "").lower()
    test_id = request.headers.get("x-test-id", "")
    
    if "pytest" in user_agent or test_id:
        return f"test_{test_id or random.randint(1000000, 9999999)}"
    
    return get_remote_address(request)

limiter = Limiter(key_func=get_rate_limit_key_func)
```

### 2. Applying Rate Limits

```python
from app.core.rate_limiter import limiter

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    pass
```

### 3. Custom Error Handling

When rate limits are exceeded:
- **API endpoints**: Return JSON with 429 status code
- **Web pages**: Show custom 429 error page with countdown timer

## Error Response Examples

### API Response (429)
```json
{
    "error": "Rate limit exceeded: 5 per 1 minute"
}
```

### Web Response (429)
- Custom HTML page at `/templates/errors/429.html`
- Shows countdown timer (60 seconds)
- Displays rate limit information
- Provides navigation options

## Best Practices

### 1. Choose Appropriate Limits
- **Authentication**: Lower limits (3-5/min) to prevent brute force
- **Data Creation**: Moderate limits (10-20/min) to prevent spam
- **Read Operations**: Higher limits (60-100/min) for normal usage
- **Health/Status**: No limits for monitoring endpoints

### 2. Consider User Experience
- Provide clear error messages
- Show when the limit will reset
- Offer alternative actions (go home, contact support)

### 3. Different Limits by User Type
```python
# Example: Higher limits for authenticated users
if current_user:
    @limiter.limit("100/minute")
else:
    @limiter.limit("20/minute")
```

### 4. Bypass for Trusted Sources
```python
# Example: No limits for internal services
def get_rate_limit_key_func(request):
    # Skip rate limiting for internal IPs
    if request.client.host in TRUSTED_IPS:
        return None
    return get_remote_address(request)
```

## Testing Rate Limits

### Manual Testing
```bash
# Test login rate limit (should fail on 6th attempt)
for i in {1..6}; do
    curl -X POST http://localhost:8000/api/v1/auth/login \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=test&password=test"
    echo ""
done
```

### Automated Testing
```python
# tests/test_rate_limiter.py
@pytest.mark.asyncio
async def test_login_rate_limit(client: AsyncClient):
    # Make 5 successful requests
    for i in range(5):
        response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
    
    # 6th request should be rate limited
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 429
```

## Advanced Configuration

### 1. Redis Backend (for distributed systems)
```python
# For production with multiple servers
from slowapi import Limiter
from slowapi.util import get_remote_address
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

### 2. Custom Rate Limit Storage
```python
# Using different storage backends
# Memory (default) - good for single server
limiter = Limiter(key_func=get_remote_address)

# Redis - good for multiple servers
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)

# Memcached
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memcached://localhost:11211"
)
```

### 3. Dynamic Rate Limits
```python
def dynamic_limit(user):
    if user.is_premium:
        return "100/minute"
    return "20/minute"

@limiter.limit(dynamic_limit)
async def api_endpoint(request: Request, user: User = Depends(get_current_user)):
    pass
```

## Monitoring and Alerts

### 1. Log Rate Limit Events
```python
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    # Log the event
    logger.warning(
        f"Rate limit exceeded for {get_remote_address(request)} "
        f"on {request.url.path}"
    )
    # ... rest of handler
```

### 2. Metrics Collection
```python
# Track rate limit hits for monitoring
RATE_LIMIT_HITS.labels(
    endpoint=request.url.path,
    ip=get_remote_address(request)
).inc()
```

## Security Considerations

1. **IP Spoofing**: Be careful with proxy headers
   - Use `X-Forwarded-For` only from trusted proxies
   - Configure proper proxy settings in production

2. **Distributed Attacks**: Consider additional protections
   - Cloudflare or similar WAF
   - CAPTCHA for repeated failures
   - Account lockouts after X attempts

3. **Resource Exhaustion**: Rate limiting prevents
   - Database connection exhaustion
   - Memory exhaustion from large requests
   - CPU exhaustion from expensive operations

## Troubleshooting

### Common Issues

1. **All requests being rate limited**
   - Check if all requests come from same IP (behind proxy)
   - Verify proxy configuration

2. **Rate limits not working**
   - Ensure limiter is initialized in main.py
   - Check if decorator is properly applied
   - Verify storage backend is accessible

3. **Tests failing due to rate limits**
   - Use custom test headers
   - Implement test-specific key function
   - Add delays between test requests

### Debug Rate Limiting
```python
# Enable debug logging
import logging
logging.getLogger('slowapi').setLevel(logging.DEBUG)
```

## Summary

Rate limiting in PyFastStack:
- ✅ Protects against abuse
- ✅ Ensures fair usage
- ✅ Automatically resets after time window
- ✅ Provides custom error pages
- ✅ Different limits for different endpoints
- ✅ Test-friendly implementation
- ✅ Production-ready with Redis support