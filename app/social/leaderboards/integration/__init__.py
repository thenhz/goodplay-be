"""
Integration hooks for real-time impact score updates

This module provides integration points for various system events
to trigger automatic impact score recalculation and leaderboard updates.
"""

from .event_handlers import (
    handle_game_session_complete,
    handle_social_activity,
    handle_donation_activity,
    handle_achievement_unlock
)

from .hooks import register_integration_hooks

__all__ = [
    'handle_game_session_complete',
    'handle_social_activity',
    'handle_donation_activity',
    'handle_achievement_unlock',
    'register_integration_hooks'
]