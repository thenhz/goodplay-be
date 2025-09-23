from typing import Tuple, Optional, Dict, Any, List
from flask import current_app
from datetime import datetime, timedelta
import threading
import time

from ..repositories.mode_schedule_repository import ModeScheduleRepository
from ..repositories.game_mode_repository import GameModeRepository
from ..models.mode_schedule import ModeSchedule

class ModeScheduler:
    """Service for executing scheduled mode operations"""

    def __init__(self):
        self.schedule_repository = ModeScheduleRepository()
        self.mode_repository = GameModeRepository()
        self._running = False
        self._scheduler_thread = None

    def execute_pending_schedules(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Execute all pending mode schedules"""
        try:
            pending_schedules = self.schedule_repository.get_pending_schedules()

            if not pending_schedules:
                return True, "NO_PENDING_SCHEDULES", {
                    "executed_count": 0,
                    "failed_count": 0,
                    "schedules": []
                }

            executed_count = 0
            failed_count = 0
            execution_results = []

            for schedule in pending_schedules:
                result = self._execute_single_schedule(schedule)
                execution_results.append(result)

                if result["success"]:
                    executed_count += 1
                    # Mark as executed in database
                    self.schedule_repository.execute_schedule(schedule.schedule_id)

                    # Create next recurrence if needed
                    if schedule.should_create_recurrence():
                        next_schedule = schedule.create_next_recurrence()
                        if next_schedule:
                            self.schedule_repository.create_schedule(next_schedule)
                            current_app.logger.info(f"Created next recurrence for {schedule.mode_name}")
                else:
                    failed_count += 1

            current_app.logger.info(f"Executed {executed_count} schedules, {failed_count} failed")

            return True, "SCHEDULES_EXECUTED", {
                "executed_count": executed_count,
                "failed_count": failed_count,
                "schedules": execution_results
            }

        except Exception as e:
            current_app.logger.error(f"Failed to execute pending schedules: {str(e)}")
            return False, "FAILED_TO_EXECUTE_SCHEDULES", None

    def _execute_single_schedule(self, schedule: ModeSchedule) -> Dict[str, Any]:
        """Execute a single schedule"""
        try:
            result = {
                "schedule_id": schedule.schedule_id,
                "mode_name": schedule.mode_name,
                "action": schedule.action,
                "scheduled_at": schedule.scheduled_at.isoformat(),
                "success": False,
                "message": "",
                "executed_at": datetime.utcnow().isoformat()
            }

            if schedule.action == "activate":
                success = self._activate_mode_from_schedule(schedule)
                result["success"] = success
                result["message"] = "MODE_ACTIVATED" if success else "ACTIVATION_FAILED"

            elif schedule.action == "deactivate":
                success = self._deactivate_mode_from_schedule(schedule)
                result["success"] = success
                result["message"] = "MODE_DEACTIVATED" if success else "DEACTIVATION_FAILED"

            else:
                result["message"] = "UNKNOWN_ACTION"

            return result

        except Exception as e:
            current_app.logger.error(f"Failed to execute schedule {schedule.schedule_id}: {str(e)}")
            return {
                "schedule_id": schedule.schedule_id,
                "mode_name": schedule.mode_name,
                "action": schedule.action,
                "success": False,
                "message": f"EXECUTION_ERROR: {str(e)}",
                "executed_at": datetime.utcnow().isoformat()
            }

    def _activate_mode_from_schedule(self, schedule: ModeSchedule) -> bool:
        """Activate a mode based on schedule"""
        try:
            # Get end date from schedule or config
            end_date = None
            if schedule.mode_config_override.get("end_date"):
                end_date = schedule.mode_config_override["end_date"]
            elif schedule.mode_config_override.get("duration_hours"):
                duration_hours = schedule.mode_config_override["duration_hours"]
                end_date = datetime.utcnow() + timedelta(hours=duration_hours)

            # Activate the mode
            success = self.mode_repository.activate_mode(
                schedule.mode_name,
                datetime.utcnow(),
                end_date
            )

            if success and schedule.mode_config_override:
                # Apply config overrides
                self.mode_repository.update_mode_config(
                    schedule.mode_name,
                    schedule.mode_config_override
                )

            current_app.logger.info(f"Activated mode {schedule.mode_name} via schedule {schedule.schedule_id}")
            return success

        except Exception as e:
            current_app.logger.error(f"Failed to activate mode {schedule.mode_name}: {str(e)}")
            return False

    def _deactivate_mode_from_schedule(self, schedule: ModeSchedule) -> bool:
        """Deactivate a mode based on schedule"""
        try:
            # Don't deactivate default mode
            mode = self.mode_repository.get_mode_by_name(schedule.mode_name)
            if mode and mode.is_default:
                current_app.logger.warning(f"Attempted to deactivate default mode {schedule.mode_name}")
                return False

            success = self.mode_repository.deactivate_mode(schedule.mode_name)

            if success:
                current_app.logger.info(f"Deactivated mode {schedule.mode_name} via schedule {schedule.schedule_id}")

            return success

        except Exception as e:
            current_app.logger.error(f"Failed to deactivate mode {schedule.mode_name}: {str(e)}")
            return False

    def start_background_scheduler(self, check_interval_seconds: int = 60) -> bool:
        """Start the background scheduler thread"""
        if self._running:
            current_app.logger.warning("Scheduler is already running")
            return False

        try:
            self._running = True
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                args=(check_interval_seconds,),
                daemon=True
            )
            self._scheduler_thread.start()

            current_app.logger.info(f"Mode scheduler started with {check_interval_seconds}s interval")
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to start scheduler: {str(e)}")
            self._running = False
            return False

    def stop_background_scheduler(self) -> bool:
        """Stop the background scheduler"""
        try:
            self._running = False
            if self._scheduler_thread and self._scheduler_thread.is_alive():
                self._scheduler_thread.join(timeout=5)

            current_app.logger.info("Mode scheduler stopped")
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to stop scheduler: {str(e)}")
            return False

    def _scheduler_loop(self, check_interval_seconds: int):
        """Main scheduler loop running in background thread"""
        while self._running:
            try:
                # Execute pending schedules
                with current_app.app_context():
                    self.execute_pending_schedules()

                    # Cleanup expired modes
                    self.mode_repository.cleanup_expired_modes()

                    # Cleanup old schedules (weekly)
                    if datetime.utcnow().hour == 2:  # Run at 2 AM
                        self.schedule_repository.cleanup_old_schedules()

            except Exception as e:
                current_app.logger.error(f"Error in scheduler loop: {str(e)}")

            # Sleep for the check interval
            time.sleep(check_interval_seconds)

    def get_next_executions(self, hours_ahead: int = 24) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get upcoming schedule executions"""
        try:
            upcoming_schedules = self.schedule_repository.get_upcoming_schedules(hours_ahead)

            executions = []
            for schedule in upcoming_schedules:
                executions.append({
                    "schedule_id": schedule.schedule_id,
                    "mode_name": schedule.mode_name,
                    "action": schedule.action,
                    "scheduled_at": schedule.scheduled_at.isoformat(),
                    "time_remaining_seconds": schedule.get_time_until_execution_seconds(),
                    "schedule_type": schedule.schedule_type,
                    "event_metadata": schedule.event_metadata
                })

            return True, "UPCOMING_EXECUTIONS_RETRIEVED", {
                "executions": executions,
                "count": len(executions),
                "hours_ahead": hours_ahead
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get next executions: {str(e)}")
            return False, "FAILED_TO_GET_EXECUTIONS", None

    def force_execute_schedule(self, schedule_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Force execute a specific schedule immediately"""
        try:
            schedule = self.schedule_repository.get_schedule_by_schedule_id(schedule_id)
            if not schedule:
                return False, "SCHEDULE_NOT_FOUND", None

            if schedule.is_executed or schedule.is_cancelled:
                return False, "SCHEDULE_ALREADY_PROCESSED", None

            # Execute the schedule
            result = self._execute_single_schedule(schedule)

            if result["success"]:
                # Mark as executed
                self.schedule_repository.execute_schedule(schedule_id)

                # Create next recurrence if needed
                if schedule.should_create_recurrence():
                    next_schedule = schedule.create_next_recurrence()
                    if next_schedule:
                        self.schedule_repository.create_schedule(next_schedule)

            return True, "SCHEDULE_FORCE_EXECUTED", result

        except Exception as e:
            current_app.logger.error(f"Failed to force execute schedule {schedule_id}: {str(e)}")
            return False, "FAILED_TO_FORCE_EXECUTE", None

    def cancel_schedule(self, schedule_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Cancel a pending schedule"""
        try:
            schedule = self.schedule_repository.get_schedule_by_schedule_id(schedule_id)
            if not schedule:
                return False, "SCHEDULE_NOT_FOUND", None

            if schedule.is_executed:
                return False, "SCHEDULE_ALREADY_EXECUTED", None

            if schedule.is_cancelled:
                return False, "SCHEDULE_ALREADY_CANCELLED", None

            # Cancel the schedule
            success = self.schedule_repository.cancel_schedule(schedule_id)

            if success:
                current_app.logger.info(f"Cancelled schedule {schedule_id}")

            return True, "SCHEDULE_CANCELLED", {
                "schedule_id": schedule_id,
                "mode_name": schedule.mode_name
            }

        except Exception as e:
            current_app.logger.error(f"Failed to cancel schedule {schedule_id}: {str(e)}")
            return False, "FAILED_TO_CANCEL_SCHEDULE", None

    def cleanup_old_data(self, days_old: int = 30) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Clean up old schedule data"""
        try:
            deleted_schedules = self.schedule_repository.cleanup_old_schedules(days_old)

            current_app.logger.info(f"Cleaned up {deleted_schedules} old schedules")

            return True, "CLEANUP_COMPLETED", {
                "deleted_schedules": deleted_schedules,
                "days_old": days_old
            }

        except Exception as e:
            current_app.logger.error(f"Failed to cleanup old data: {str(e)}")
            return False, "CLEANUP_FAILED", None

    def is_running(self) -> bool:
        """Check if the background scheduler is running"""
        return self._running and self._scheduler_thread and self._scheduler_thread.is_alive()

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get the current status of the scheduler"""
        return {
            "is_running": self.is_running(),
            "thread_alive": self._scheduler_thread.is_alive() if self._scheduler_thread else False,
            "started_at": getattr(self, '_started_at', None)
        }