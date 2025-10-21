import os
import logging
from typing import Callable, Optional
from flask import current_app, has_app_context
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Fallback logger for when there's no app context
logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for managing background scheduled tasks using APScheduler.

    Provides centralized task scheduling for cleanup jobs, notifications,
    and other recurring operations.
    """

    def __init__(self):
        self.scheduler = None
        self._started = False

    def _get_logger(self):
        """Get logger with app context if available, otherwise use module logger"""
        if has_app_context():
            return current_app.logger
        return logger

    def initialize(self):
        """Initialize the scheduler"""
        try:
            # Check if scheduler is enabled
            scheduler_enabled = os.getenv('SCHEDULER_ENABLED', 'true').lower() == 'true'

            if not scheduler_enabled:
                self._get_logger().info("Scheduler is disabled via SCHEDULER_ENABLED environment variable")
                return

            # Create scheduler
            self.scheduler = BackgroundScheduler(
                daemon=True,
                timezone='UTC'
            )

            self._get_logger().info("Scheduler service initialized")

        except Exception as e:
            self._get_logger().error(f"Error initializing scheduler: {str(e)}", exc_info=True)

    def start(self):
        """Start the scheduler"""
        try:
            if self.scheduler is None:
                self._get_logger().warning("Scheduler not initialized. Skipping start.")
                return

            if self._started:
                self._get_logger().info("Scheduler already started")
                return

            self.scheduler.start()
            self._started = True

            self._get_logger().info("Scheduler started successfully")

        except Exception as e:
            self._get_logger().error(f"Error starting scheduler: {str(e)}", exc_info=True)

    def shutdown(self):
        """Shutdown the scheduler gracefully"""
        try:
            if self.scheduler is None:
                return

            if not self._started:
                return

            self.scheduler.shutdown(wait=True)
            self._started = False

            self._get_logger().info("Scheduler shut down successfully")

        except Exception as e:
            self._get_logger().error(f"Error shutting down scheduler: {str(e)}", exc_info=True)

    def add_interval_job(
        self,
        func: Callable,
        job_id: str,
        minutes: Optional[int] = None,
        seconds: Optional[int] = None,
        hours: Optional[int] = None,
        **kwargs
    ):
        """
        Add job that runs at fixed intervals.

        Args:
            func: Function to execute
            job_id: Unique job identifier
            minutes: Interval in minutes
            seconds: Interval in seconds
            hours: Interval in hours
            **kwargs: Additional arguments for add_job
        """
        try:
            if self.scheduler is None:
                return

            # Build trigger params dict with only non-None values
            trigger_params = {'timezone': 'UTC'}
            if minutes is not None:
                trigger_params['minutes'] = minutes
            if seconds is not None:
                trigger_params['seconds'] = seconds
            if hours is not None:
                trigger_params['hours'] = hours

            trigger = IntervalTrigger(**trigger_params)

            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                **kwargs
            )

            self._get_logger().info(f"Added interval job: {job_id}")

        except Exception as e:
            self._get_logger().error(f"Error adding interval job {job_id}: {str(e)}", exc_info=True)

    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        day_of_week: Optional[str] = None,
        **kwargs
    ):
        """
        Add job that runs on cron schedule.

        Args:
            func: Function to execute
            job_id: Unique job identifier
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            day_of_week: Day(s) of week (mon, tue, wed, thu, fri, sat, sun)
            **kwargs: Additional arguments for add_job
        """
        try:
            if self.scheduler is None:
                return

            # Build trigger params dict with only non-None values
            trigger_params = {'timezone': 'UTC'}
            if hour is not None:
                trigger_params['hour'] = hour
            if minute is not None:
                trigger_params['minute'] = minute
            if day_of_week is not None:
                trigger_params['day_of_week'] = day_of_week

            trigger = CronTrigger(**trigger_params)

            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                **kwargs
            )

            self._get_logger().info(f"Added cron job: {job_id}")

        except Exception as e:
            self._get_logger().error(f"Error adding cron job {job_id}: {str(e)}", exc_info=True)

    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        try:
            if self.scheduler is None:
                return

            self.scheduler.remove_job(job_id)
            self._get_logger().info(f"Removed job: {job_id}")

        except Exception as e:
            self._get_logger().error(f"Error removing job {job_id}: {str(e)}", exc_info=True)

    def is_running(self) -> bool:
        """Check if scheduler is running"""
        if self.scheduler is None:
            return False
        return self._started


# Global scheduler instance
scheduler_service = SchedulerService()
