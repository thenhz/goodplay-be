"""
Rate limiting decorator for multiplayer endpoints.

GOO-60: Implements rate limiting to prevent invitation spam.
"""

from functools import wraps
from flask import request, current_app
from collections import defaultdict
from time import time
from app.core.utils.responses import error_response


class RateLimiter:
    """
    Simple in-memory rate limiter.

    For production, consider using Redis for distributed rate limiting.
    """

    def __init__(self):
        # Storage: {user_id: [timestamp1, timestamp2, ...]}
        self.calls = defaultdict(list)

    def check_limit(self, user_id: str, max_calls: int = 10, window: int = 60) -> bool:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User ID to check
            max_calls: Maximum number of calls allowed
            window: Time window in seconds

        Returns:
            True if within limit, False if exceeded
        """
        now = time()

        # Remove calls outside the time window
        self.calls[user_id] = [
            timestamp for timestamp in self.calls[user_id]
            if now - timestamp < window
        ]

        # Check if limit exceeded
        if len(self.calls[user_id]) >= max_calls:
            return False

        # Record this call
        self.calls[user_id].append(now)
        return True

    def get_remaining_calls(self, user_id: str, max_calls: int = 10, window: int = 60) -> int:
        """Get number of remaining calls in current window"""
        now = time()
        self.calls[user_id] = [
            timestamp for timestamp in self.calls[user_id]
            if now - timestamp < window
        ]
        return max(0, max_calls - len(self.calls[user_id]))

    def reset_user(self, user_id: str):
        """Reset rate limit for a specific user"""
        if user_id in self.calls:
            del self.calls[user_id]


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(max_calls: int = 10, window: int = 60):
    """
    Decorator to rate limit endpoint calls per user.

    Args:
        max_calls: Maximum number of calls allowed in window
        window: Time window in seconds

    Usage:
        @rate_limit(max_calls=10, window=60)
        @auth_required
        def my_endpoint(current_user):
            ...

    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract user_id from kwargs (set by @auth_required decorator)
            current_user = kwargs.get('current_user')

            if not current_user:
                # If no user authentication, skip rate limiting
                return f(*args, **kwargs)

            # Extract user ID (handle both User object and string ID)
            from app.core.utils.helpers import extract_user_id
            user_id = extract_user_id(current_user)

            # Check rate limit
            if not _rate_limiter.check_limit(user_id, max_calls, window):
                current_app.logger.warning(
                    f"Rate limit exceeded for user {user_id}: {max_calls} calls/{window}s"
                )
                return error_response("RATE_LIMIT_EXCEEDED", status_code=429)

            # Call the original function
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    return _rate_limiter
