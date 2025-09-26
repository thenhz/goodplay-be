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


# Convenience functions for integration with existing services

def integrate_with_game_service():
    """
    Integrate impact score updates with game service.
    This should be called from the game service module.
    """
    try:
        from app.games.services.game_session_service import GameSessionService

        # Monkey patch the game session service to trigger impact score updates
        original_end_session = GameSessionService.end_game_session

        def end_session_with_impact_update(self, session_id: str, reason: str = "completed"):
            # Call original method
            result = original_end_session(self, session_id, reason)

            # If successful, trigger impact score update
            if result[0]:  # Assuming result is (success, message, data)
                session_data = result[2] if len(result) > 2 else {}
                if 'user_id' in session_data:
                    trigger_game_session_complete(
                        str(session_data['user_id']),
                        session_data
                    )

            return result

        # Replace the method
        GameSessionService.end_game_session = end_session_with_impact_update

        current_app.logger.info("Game service integration completed")
        return True

    except Exception as e:
        current_app.logger.error(f"Error integrating with game service: {str(e)}")
        return False


def integrate_with_social_service():
    """
    Integrate impact score updates with social service.
    This should be called from the social service module.
    """
    try:
        from app.social.services.relationship_service import RelationshipService

        # Monkey patch relationship service for friend activities
        original_accept_request = RelationshipService.accept_friend_request

        def accept_request_with_impact_update(self, current_user_id: str, request_id: str):
            result = original_accept_request(self, current_user_id, request_id)

            # Trigger impact score update for both users
            if result[0]:  # Success
                activity_data = {'request_id': request_id}

                # Update for user who accepted
                trigger_social_activity(
                    current_user_id,
                    'friend_request_accepted',
                    activity_data
                )

                # Update for user who sent request (if we can determine it)
                # This would require additional logic to find the requester

            return result

        RelationshipService.accept_friend_request = accept_request_with_impact_update

        current_app.logger.info("Social service integration completed")
        return True

    except Exception as e:
        current_app.logger.error(f"Error integrating with social service: {str(e)}")
        return False


def integrate_with_achievement_service():
    """
    Integrate impact score updates with achievement service.
    Note: Disabled due to private method access issues.
    """
    try:
        # Achievement integration disabled - the unlock_achievement method is private
        # and should not be monkey-patched. Consider using event-based integration instead.
        current_app.logger.info("Achievement service integration skipped (method is private)")
        return False

    except Exception as e:
        current_app.logger.error(f"Error integrating with achievement service: {str(e)}")
        return False


def setup_all_integrations():
    """
    Set up all service integrations.
    Call this during application initialization after all modules are loaded.
    """
    try:
        success_count = 0

        # Register hooks first
        if register_integration_hooks():
            success_count += 1

        # Integrate with services
        if integrate_with_game_service():
            success_count += 1

        if integrate_with_social_service():
            success_count += 1

        if integrate_with_achievement_service():
            success_count += 1

        current_app.logger.info(f"Impact score integrations completed: {success_count}/3 successful")
        return success_count == 3

    except Exception as e:
        current_app.logger.error(f"Error setting up integrations: {str(e)}")
        return False