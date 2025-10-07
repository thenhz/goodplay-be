"""Multiplayer decorators package"""

from .rate_limiter import rate_limit, get_rate_limiter

__all__ = ['rate_limit', 'get_rate_limiter']
