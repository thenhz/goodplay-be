from typing import Tuple, Optional, Dict, Any, List
from flask import current_app
from datetime import datetime, timedelta

from ..repositories.game_mode_repository import GameModeRepository
from ..repositories.mode_schedule_repository import ModeScheduleRepository
from ..models.game_mode import GameMode
from ..models.mode_schedule import ModeSchedule

class ModeManager:
    """Service for managing game modes and their lifecycle"""

    def __init__(self):
        self.mode_repository = GameModeRepository()
        self.schedule_repository = ModeScheduleRepository()

    def get_available_modes(self, user_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get all modes currently available to the user.

        Args:
            user_id: Optional user ID for user-specific mode filtering

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            modes = self.mode_repository.get_user_available_modes(user_id)

            # Ensure default mode is always available
            if not any(mode.is_default for mode in modes):
                default_mode = self.mode_repository.ensure_default_mode_exists()
                modes.append(default_mode)

            modes_data = [mode.to_api_dict() for mode in modes]

            current_app.logger.info(f"Retrieved {len(modes)} available modes for user {user_id}")

            return True, "MODES_RETRIEVED_SUCCESSFULLY", {
                "modes": modes_data,
                "default_mode": next((mode for mode in modes_data if mode["is_default"]), None),
                "count": len(modes_data)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get available modes: {str(e)}")
            return False, "FAILED_TO_GET_MODES", None

    def get_current_active_modes(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get all currently active modes"""
        try:
            modes = self.mode_repository.get_active_modes()
            modes_data = [mode.to_api_dict() for mode in modes]

            return True, "ACTIVE_MODES_RETRIEVED", {
                "active_modes": modes_data,
                "count": len(modes_data)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get active modes: {str(e)}")
            return False, "FAILED_TO_GET_ACTIVE_MODES", None

    def activate_mode(self, mode_name: str, start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None, admin_user_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Activate a game mode.

        Args:
            mode_name: Name of the mode to activate
            start_date: Optional start date
            end_date: Optional end date
            admin_user_id: ID of admin user performing the action

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Check if mode exists
            mode = self.mode_repository.get_mode_by_name(mode_name)
            if not mode:
                return False, "MODE_NOT_FOUND", None

            # Activate the mode
            success = self.mode_repository.activate_mode(mode_name, start_date, end_date)
            if not success:
                return False, "FAILED_TO_ACTIVATE_MODE", None

            # Get updated mode
            updated_mode = self.mode_repository.get_mode_by_name(mode_name)

            current_app.logger.info(f"Mode {mode_name} activated by admin {admin_user_id}")

            return True, "MODE_ACTIVATED_SUCCESSFULLY", {
                "mode": updated_mode.to_api_dict() if updated_mode else None
            }

        except Exception as e:
            current_app.logger.error(f"Failed to activate mode {mode_name}: {str(e)}")
            return False, "FAILED_TO_ACTIVATE_MODE", None

    def deactivate_mode(self, mode_name: str, admin_user_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Deactivate a game mode.

        Args:
            mode_name: Name of the mode to deactivate
            admin_user_id: ID of admin user performing the action

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Check if mode exists
            mode = self.mode_repository.get_mode_by_name(mode_name)
            if not mode:
                return False, "MODE_NOT_FOUND", None

            # Prevent deactivating default mode
            if mode.is_default:
                return False, "CANNOT_DEACTIVATE_DEFAULT_MODE", None

            # Deactivate the mode
            success = self.mode_repository.deactivate_mode(mode_name)
            if not success:
                return False, "FAILED_TO_DEACTIVATE_MODE", None

            # Cancel future schedules for this mode
            cancelled_count = self.schedule_repository.cancel_future_schedules_for_mode(mode_name)

            current_app.logger.info(f"Mode {mode_name} deactivated by admin {admin_user_id}, cancelled {cancelled_count} future schedules")

            return True, "MODE_DEACTIVATED_SUCCESSFULLY", {
                "mode_name": mode_name,
                "cancelled_schedules": cancelled_count
            }

        except Exception as e:
            current_app.logger.error(f"Failed to deactivate mode {mode_name}: {str(e)}")
            return False, "FAILED_TO_DEACTIVATE_MODE", None

    def schedule_mode_activation(self, mode_name: str, scheduled_at: datetime,
                               end_date: Optional[datetime] = None,
                               config_override: Dict[str, Any] = None,
                               admin_user_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Schedule a mode activation for the future.

        Args:
            mode_name: Name of the mode to schedule
            scheduled_at: When to activate the mode
            end_date: Optional end date for the mode
            config_override: Optional configuration overrides
            admin_user_id: ID of admin user creating the schedule

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Validate mode exists
            mode = self.mode_repository.get_mode_by_name(mode_name)
            if not mode:
                return False, "MODE_NOT_FOUND", None

            # Validate schedule time
            if scheduled_at <= datetime.utcnow():
                return False, "SCHEDULE_TIME_MUST_BE_FUTURE", None

            # Check for conflicting schedules
            if self.schedule_repository.has_conflicting_schedule(mode_name, "activate", scheduled_at):
                return False, "CONFLICTING_SCHEDULE_EXISTS", None

            # Create activation schedule
            activation_schedule = ModeSchedule(
                mode_name=mode_name,
                schedule_type="one_time",
                action="activate",
                scheduled_at=scheduled_at,
                mode_config_override=config_override or {},
                created_by=admin_user_id
            )

            activation_id = self.schedule_repository.create_schedule(activation_schedule)

            schedules_created = [activation_id]

            # Create deactivation schedule if end_date provided
            deactivation_id = None
            if end_date:
                if end_date <= scheduled_at:
                    return False, "END_DATE_MUST_BE_AFTER_START", None

                deactivation_schedule = ModeSchedule(
                    mode_name=mode_name,
                    schedule_type="one_time",
                    action="deactivate",
                    scheduled_at=end_date,
                    created_by=admin_user_id
                )

                deactivation_id = self.schedule_repository.create_schedule(deactivation_schedule)
                schedules_created.append(deactivation_id)

            current_app.logger.info(f"Scheduled activation for mode {mode_name} at {scheduled_at} by admin {admin_user_id}")

            return True, "MODE_ACTIVATION_SCHEDULED", {
                "activation_schedule_id": activation_id,
                "deactivation_schedule_id": deactivation_id,
                "mode_name": mode_name,
                "scheduled_at": scheduled_at.isoformat(),
                "end_date": end_date.isoformat() if end_date else None
            }

        except Exception as e:
            current_app.logger.error(f"Failed to schedule mode activation: {str(e)}")
            return False, "FAILED_TO_SCHEDULE_MODE", None

    def create_recurring_schedule(self, mode_name: str, action: str, start_time: datetime,
                                recurrence_config: Dict[str, Any], end_date: Optional[datetime] = None,
                                admin_user_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create a recurring schedule for mode activation/deactivation.

        Args:
            mode_name: Name of the mode
            action: 'activate' or 'deactivate'
            start_time: First execution time
            recurrence_config: Recurrence configuration
            end_date: Optional end date for recurrence
            admin_user_id: ID of admin user creating the schedule

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            # Validate mode exists
            mode = self.mode_repository.get_mode_by_name(mode_name)
            if not mode:
                return False, "MODE_NOT_FOUND", None

            # Validate recurrence config
            if not recurrence_config.get("type") in ["daily", "weekly", "monthly"]:
                return False, "INVALID_RECURRENCE_TYPE", None

            # Add end_date to recurrence_config if provided
            if end_date:
                recurrence_config["end_date"] = end_date

            # Create recurring schedule
            recurring_schedule = ModeSchedule(
                mode_name=mode_name,
                schedule_type="recurring",
                action=action,
                scheduled_at=start_time,
                recurrence_config=recurrence_config,
                created_by=admin_user_id
            )

            schedule_id = self.schedule_repository.create_or_update_recurring_schedule(recurring_schedule)

            current_app.logger.info(f"Created recurring schedule for mode {mode_name} by admin {admin_user_id}")

            return True, "RECURRING_SCHEDULE_CREATED", {
                "schedule_id": schedule_id,
                "mode_name": mode_name,
                "action": action,
                "recurrence_type": recurrence_config.get("type"),
                "next_execution": start_time.isoformat()
            }

        except Exception as e:
            current_app.logger.error(f"Failed to create recurring schedule: {str(e)}")
            return False, "FAILED_TO_CREATE_RECURRING_SCHEDULE", None

    def get_mode_schedule(self, mode_name: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get schedule information for modes.

        Args:
            mode_name: Optional specific mode name

        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: (success, message, data)
        """
        try:
            if mode_name:
                schedules = self.schedule_repository.get_active_schedules_by_mode(mode_name)
            else:
                schedules = self.schedule_repository.get_upcoming_schedules(24 * 7)  # Next week

            schedules_data = [schedule.to_api_dict() for schedule in schedules]

            return True, "SCHEDULES_RETRIEVED", {
                "schedules": schedules_data,
                "count": len(schedules_data)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get mode schedules: {str(e)}")
            return False, "FAILED_TO_GET_SCHEDULES", None

    def initialize_system(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Initialize the mode system with default modes"""
        try:
            # Initialize default modes
            default_modes = self.mode_repository.initialize_default_modes()

            # Clean up expired modes
            expired_count = self.mode_repository.cleanup_expired_modes()

            current_app.logger.info(f"Mode system initialized: {len(default_modes)} default modes, {expired_count} expired modes cleaned")

            return True, "MODE_SYSTEM_INITIALIZED", {
                "default_modes": [mode.to_api_dict() for mode in default_modes],
                "expired_modes_cleaned": expired_count
            }

        except Exception as e:
            current_app.logger.error(f"Failed to initialize mode system: {str(e)}")
            return False, "FAILED_TO_INITIALIZE_MODE_SYSTEM", None

    def get_mode_statistics(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get statistics about modes and schedules"""
        try:
            all_modes = self.mode_repository.get_all_modes()
            active_modes = self.mode_repository.get_active_modes()
            schedule_stats = self.schedule_repository.get_schedule_statistics()

            stats = {
                "total_modes": len(all_modes),
                "active_modes": len(active_modes),
                "inactive_modes": len(all_modes) - len(active_modes),
                "schedule_statistics": schedule_stats,
                "modes_breakdown": {}
            }

            # Add breakdown by mode
            for mode in all_modes:
                stats["modes_breakdown"][mode.name] = {
                    "is_active": mode.is_active,
                    "is_available": mode.is_currently_available(),
                    "is_default": mode.is_default
                }

            return True, "MODE_STATISTICS_RETRIEVED", stats

        except Exception as e:
            current_app.logger.error(f"Failed to get mode statistics: {str(e)}")
            return False, "FAILED_TO_GET_STATISTICS", None