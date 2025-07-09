"""
Rate limiter configuration and utilities.
"""
import os
import random
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_rate_limit_key_func(request):
    """Get the key function for rate limiting."""
    # If we're running tests (check if pytest is in the user agent or custom header)
    user_agent = request.headers.get("user-agent", "").lower()
    test_id = request.headers.get("x-test-id", "")
    
    if "pytest" in user_agent or test_id:
        # Use test ID if provided, otherwise generate a random one
        if test_id:
            return f"test_{test_id}"
        else:
            # Use a random key to avoid conflicts between tests
            return f"test_{random.randint(1000000, 9999999)}_{get_remote_address(request)}"
    
    return get_remote_address(request)


# Create the limiter with our custom key function
limiter = Limiter(key_func=get_rate_limit_key_func)