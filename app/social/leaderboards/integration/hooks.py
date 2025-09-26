"""
Integration hooks system for connecting impact score system
with existing services and events throughout the application.
"""

from typing import Dict, Any, Callable, List
from flask import current_app
from .event_handlers import (
    handle_game_session_complete,
    handle_social_activity,
    handle_donation_activity,
    handle_achievement_unlock,
    handle_user_login,
    handle_weekly_reset,
    handle_tournament_result
)


class EventHookManager:
    """
    Manager for registering and triggering event hooks
    throughout the application for impact score updates.
    """

    def __init__(self):
        self.hooks: Dict[str, List[Callable]] = {}

    def register_hook(self, event_name: str, handler: Callable):
        """Register an event handler for a specific event"""
        if event_name not in self.hooks:
            self.hooks[event_name] = []
        self.hooks[event_name].append(handler)

    def trigger_event(self, event_name: str, **kwargs) -> List[bool]:
        """Trigger all handlers for an event and return results"""
        if event_name not in self.hooks:
            return []

        results = []
        for handler in self.hooks[event_name]:
            try:
                result = handler(**kwargs)
                results.append(result)
            except Exception as e:
                current_app.logger.error(f"Error in event handler for {event_name}: {str(e)}")
                results.append(False)

        return results

    def get_registered_events(self) -> List[str]:
        """Get list of all registered event names"""
        return list(self.hooks.keys())


# Global hook manager instance
hook_manager = EventHookManager()


def register_integration_hooks():
    """
    Register all integration hooks with the system.
    Call this during application initialization.
    """
    try:
        # Game-related events
        hook_manager.register_hook('game_session_complete', handle_game_session_complete)
        hook_manager.register_hook('tournament_complete', handle_tournament_result)

        # Social events
        hook_manager.register_hook('social_activity', handle_social_activity)
        hook_manager.register_hook('achievement_unlock', handle_achievement_unlock)

        # Donation events
        hook_manager.register_hook('donation_complete', handle_donation_activity)

        # User events
        hook_manager.register_hook('user_login', handle_user_login)

        # System events
        hook_manager.register_hook('weekly_reset', handle_weekly_reset)

        current_app.logger.info("Impact score integration hooks registered successfully")
        return True

    except Exception as e:
        current_app.logger.error(f"Error registering integration hooks: {str(e)}")
        return False


def trigger_game_session_complete(user_id: str, session_data: Dict[str, Any]) -> bool:
    """
    Trigger game session complete event

    Args:
        user_id: User who completed the session
        session_data: Session completion data

    Returns:
        bool: True if all handlers succeeded
    """
    results = hook_manager.trigger_event('game_session_complete',
                                        user_id=user_id,
                                        session_data=session_data)
    return all(results)


def trigger_social_activity(user_id: str, activity_type: str, activity_data: Dict[str, Any]) -> bool:
    """
    Trigger social activity event

    Args:
        user_id: User who performed the activity
        activity_type: Type of social activity
        activity_data: Activity-specific data

    Returns:
        bool: True if all handlers succeeded
    """
    results = hook_manager.trigger_event('social_activity',
                                        user_id=user_id,
                                        activity_type=activity_type,
                                        activity_data=activity_data)
    return all(results)


def trigger_donation_complete(user_id: str, donation_data: Dict[str, Any]) -> bool:
    """
    Trigger donation complete event

    Args:
        user_id: User who made the donation
        donation_data: Donation transaction data

    Returns:
        bool: True if all handlers succeeded
    """
    results = hook_manager.trigger_event('donation_complete',
                                        user_id=user_id,
                                        donation_data=donation_data)
    return all(results)


def trigger_achievement_unlock(user_id: str, achievement_data: Dict[str, Any]) -> bool:
    """
    Trigger achievement unlock event

    Args:
        user_id: User who unlocked the achievement
        achievement_data: Achievement data

    Returns:
        bool: True if all handlers succeeded
    """
    results = hook_manager.trigger_event('achievement_unlock',
                                        user_id=user_id,
                                        achievement_data=achievement_data)
    return all(results)


def trigger_user_login(user_id: str, login_data: Dict[str, Any]) -> bool:
    """
    Trigger user login event

    Args:
        user_id: User who logged in
        login_data: Login data

    Returns:
        bool: True if all handlers succeeded
    """
    results = hook_manager.trigger_event('user_login',
                                        user_id=user_id,
                                        login_data=login_data)
    return all(results)


def trigger_weekly_reset() -> bool:
    """
    Trigger weekly reset event

    Returns:
        bool: True if all handlers succeeded
    """
    results = hook_manager.trigger_event('weekly_reset')
    return all(results)


def trigger_tournament_complete(tournament_data: Dict[str, Any]) -> bool:
    """
    Trigger tournament complete event

    Args:
        tournament_data: Tournament result data

    Returns:
        bool: True if all handlers succeeded
    """
    results = hook_manager.trigger_event('tournament_complete',
                                        tournament_data=tournament_data)
    return all(results)


# Setup function for event-based integrations only

def setup_all_integrations():
    """
    Set up event-based integration system.
    Call this during application initialization.
    """
    try:
        # Register hooks for event-based integration
        if register_integration_hooks():
            current_app.logger.info("Event-based impact score integration completed successfully")
            return True
        else:
            current_app.logger.error("Failed to register integration hooks")
            return False

    except Exception as e:
        current_app.logger.error(f"Error setting up event-based integrations: {str(e)}")
        return False