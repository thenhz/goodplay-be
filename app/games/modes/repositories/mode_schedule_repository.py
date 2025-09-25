from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.repositories.base_repository import BaseRepository
from ..models.mode_schedule import ModeSchedule

class ModeScheduleRepository(BaseRepository):
    """Repository for mode schedule operations"""

    def __init__(self):
        super().__init__("mode_schedules")

    def create_indexes(self):
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        from pymongo import ASCENDING
        # Index for schedule_id field - used frequently for lookups
        self.collection.create_index([("schedule_id", ASCENDING)], unique=True)
        # Index for mode_name - used for finding schedules by mode
        self.collection.create_index([("mode_name", ASCENDING)])
        # Index for scheduled_at - used for finding pending and upcoming schedules
        self.collection.create_index([("scheduled_at", ASCENDING)])
        # Index for is_executed - used for filtering executed schedules
        self.collection.create_index([("is_executed", ASCENDING)])
        # Index for is_cancelled - used for filtering cancelled schedules
        self.collection.create_index([("is_cancelled", ASCENDING)])
        # Index for schedule_type - used for filtering recurring vs one-time schedules
        self.collection.create_index([("schedule_type", ASCENDING)])
        # Index for created_by - used for getting schedules created by a user
        self.collection.create_index([("created_by", ASCENDING)])
        # Index for executed_at - used for cleanup operations
        self.collection.create_index([("executed_at", ASCENDING)])
        # Compound index for pending schedules - frequently used query
        self.collection.create_index([("is_executed", ASCENDING), ("is_cancelled", ASCENDING), ("scheduled_at", ASCENDING)])
        # Compound index for mode and action - used for conflict checking
        self.collection.create_index([("mode_name", ASCENDING), ("action", ASCENDING)])

    def create_schedule(self, schedule: ModeSchedule) -> str:
        """Create a new mode schedule"""
        return self.create(schedule.to_dict())

    def get_schedule_by_id(self, schedule_id: str) -> Optional[ModeSchedule]:
        """Get a schedule by ID"""
        data = self.find_by_id(schedule_id)
        return ModeSchedule.from_dict(data) if data else None

    def get_schedule_by_schedule_id(self, schedule_id: str) -> Optional[ModeSchedule]:
        """Get a schedule by schedule_id field"""
        data = self.find_one({"schedule_id": schedule_id})
        return ModeSchedule.from_dict(data) if data else None

    def get_all_schedules(self, limit: int = 100, skip: int = 0) -> List[ModeSchedule]:
        """Get all schedules with pagination"""
        schedules_data = self.find_many({}, limit=limit, skip=skip, sort=[("scheduled_at", 1)])
        return [ModeSchedule.from_dict(data) for data in schedules_data]

    def get_pending_schedules(self) -> List[ModeSchedule]:
        """Get all schedules that are due for execution"""
        now = datetime.utcnow()
        schedules_data = self.find_many({
            "is_executed": False,
            "is_cancelled": False,
            "scheduled_at": {"$lte": now}
        }, sort=[("scheduled_at", 1)])
        return [ModeSchedule.from_dict(data) for data in schedules_data]

    def get_upcoming_schedules(self, hours_ahead: int = 24) -> List[ModeSchedule]:
        """Get schedules coming up in the next N hours"""
        now = datetime.utcnow()
        end_time = now + timedelta(hours=hours_ahead)

        schedules_data = self.find_many({
            "is_executed": False,
            "is_cancelled": False,
            "scheduled_at": {
                "$gt": now,
                "$lte": end_time
            }
        }, sort=[("scheduled_at", 1)])
        return [ModeSchedule.from_dict(data) for data in schedules_data]

    def get_schedules_by_mode(self, mode_name: str) -> List[ModeSchedule]:
        """Get all schedules for a specific mode"""
        schedules_data = self.find_many({"mode_name": mode_name}, sort=[("scheduled_at", 1)])
        return [ModeSchedule.from_dict(data) for data in schedules_data]

    def get_active_schedules_by_mode(self, mode_name: str) -> List[ModeSchedule]:
        """Get active (non-executed, non-cancelled) schedules for a specific mode"""
        schedules_data = self.find_many({
            "mode_name": mode_name,
            "is_executed": False,
            "is_cancelled": False
        }, sort=[("scheduled_at", 1)])
        return [ModeSchedule.from_dict(data) for data in schedules_data]

    def get_schedules_by_type(self, schedule_type: str) -> List[ModeSchedule]:
        """Get schedules by type (one_time, recurring, event)"""
        schedules_data = self.find_many({"schedule_type": schedule_type}, sort=[("scheduled_at", 1)])
        return [ModeSchedule.from_dict(data) for data in schedules_data]

    def get_recurring_schedules(self) -> List[ModeSchedule]:
        """Get all recurring schedules"""
        return self.get_schedules_by_type("recurring")

    def execute_schedule(self, schedule_id: str) -> bool:
        """Mark a schedule as executed"""
        now = datetime.utcnow()
        result = self.collection.update_one(
            {"schedule_id": schedule_id},
            {"$set": {
                "is_executed": True,
                "executed_at": now,
                "updated_at": now
            }}
        )
        return result.modified_count > 0

    def cancel_schedule(self, schedule_id: str) -> bool:
        """Cancel a schedule"""
        result = self.collection.update_one(
            {"schedule_id": schedule_id},
            {"$set": {
                "is_cancelled": True,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    def cancel_future_schedules_for_mode(self, mode_name: str) -> int:
        """Cancel all future schedules for a specific mode"""
        now = datetime.utcnow()
        result = self.collection.update_many(
            {
                "mode_name": mode_name,
                "is_executed": False,
                "is_cancelled": False,
                "scheduled_at": {"$gt": now}
            },
            {"$set": {
                "is_cancelled": True,
                "updated_at": now
            }}
        )
        return result.modified_count

    def get_schedules_created_by(self, created_by: str) -> List[ModeSchedule]:
        """Get schedules created by a specific user"""
        schedules_data = self.find_many({"created_by": created_by}, sort=[("created_at", -1)])
        return [ModeSchedule.from_dict(data) for data in schedules_data]

    def delete_old_executed_schedules(self, days_old: int = 30) -> int:
        """Delete executed schedules older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        result = self.collection.delete_many({
            "is_executed": True,
            "executed_at": {"$lt": cutoff_date}
        })
        return result.deleted_count

    def get_schedule_statistics(self) -> Dict[str, Any]:
        """Get statistics about schedules"""
        total_schedules = self.collection.count_documents({})
        pending_schedules = self.collection.count_documents({
            "is_executed": False,
            "is_cancelled": False
        })
        executed_schedules = self.collection.count_documents({"is_executed": True})
        cancelled_schedules = self.collection.count_documents({"is_cancelled": True})
        recurring_schedules = self.collection.count_documents({"schedule_type": "recurring"})

        return {
            "total_schedules": total_schedules,
            "pending_schedules": pending_schedules,
            "executed_schedules": executed_schedules,
            "cancelled_schedules": cancelled_schedules,
            "recurring_schedules": recurring_schedules
        }

    def create_or_update_recurring_schedule(self, schedule: ModeSchedule) -> str:
        """Create or update a recurring schedule (handles duplicates)"""
        # Check if similar recurring schedule exists
        existing = self.find_one({
            "mode_name": schedule.mode_name,
            "schedule_type": "recurring",
            "action": schedule.action,
            "is_executed": False,
            "is_cancelled": False,
            "recurrence_config.type": schedule.recurrence_config.get("type"),
            "recurrence_config.interval": schedule.recurrence_config.get("interval")
        })

        if existing:
            # Update existing schedule
            schedule._id = existing["_id"]
            self.update_by_id(str(existing["_id"]), schedule.to_dict())
            return str(existing["_id"])
        else:
            # Create new schedule
            return self.create_schedule(schedule)

    def get_next_execution_time(self, mode_name: str, action: str) -> Optional[datetime]:
        """Get the next scheduled execution time for a mode action"""
        schedule_data = self.find_one({
            "mode_name": mode_name,
            "action": action,
            "is_executed": False,
            "is_cancelled": False,
            "scheduled_at": {"$gt": datetime.utcnow()}
        }, sort=[("scheduled_at", 1)])

        if schedule_data:
            return schedule_data.get("scheduled_at")
        return None

    def has_conflicting_schedule(self, mode_name: str, action: str, scheduled_at: datetime,
                                tolerance_minutes: int = 5) -> bool:
        """Check if there's a conflicting schedule within tolerance window"""
        start_time = scheduled_at - timedelta(minutes=tolerance_minutes)
        end_time = scheduled_at + timedelta(minutes=tolerance_minutes)

        existing = self.find_one({
            "mode_name": mode_name,
            "action": action,
            "is_executed": False,
            "is_cancelled": False,
            "scheduled_at": {
                "$gte": start_time,
                "$lte": end_time
            }
        })

        return existing is not None

    def cleanup_old_schedules(self, days_old: int = 90) -> int:
        """Clean up old schedules to prevent database bloat"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Delete old executed non-recurring schedules
        result = self.collection.delete_many({
            "schedule_type": {"$ne": "recurring"},
            "is_executed": True,
            "executed_at": {"$lt": cutoff_date}
        })

        return result.deleted_count