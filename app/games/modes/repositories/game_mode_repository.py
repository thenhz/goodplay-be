from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.repositories.base_repository import BaseRepository
from ..models.game_mode import GameMode

class GameModeRepository(BaseRepository):
    """Repository for game mode operations"""

    def __init__(self):
        super().__init__("game_modes")

    def create_indexes(self):
        """Create database indexes for optimal query performance"""
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Create indexes for game modes
        self.collection.create_index("name", unique=True)
        self.collection.create_index("type")
        self.collection.create_index("is_active")
        self.collection.create_index([("is_active", 1), ("type", 1)])

    def create_mode(self, mode: GameMode) -> str:
        """Create a new game mode"""
        return self.create(mode.to_dict())

    def get_mode_by_name(self, mode_name: str) -> Optional[GameMode]:
        """Get a game mode by name"""
        data = self.find_one({"name": mode_name})
        return GameMode.from_dict(data) if data else None

    def get_mode_by_id(self, mode_id: str) -> Optional[GameMode]:
        """Get a game mode by ID"""
        data = self.find_by_id(mode_id)
        return GameMode.from_dict(data) if data else None

    def get_all_modes(self) -> List[GameMode]:
        """Get all game modes"""
        modes_data = self.find_many()
        return [GameMode.from_dict(data) for data in modes_data]

    def get_active_modes(self) -> List[GameMode]:
        """Get all currently active modes"""
        modes_data = self.find_many({"is_active": True})
        modes = [GameMode.from_dict(data) for data in modes_data]

        # Filter by time constraints
        current_modes = []
        for mode in modes:
            if mode.is_currently_available():
                current_modes.append(mode)
            elif mode.has_expired():
                # Auto-deactivate expired modes
                self.deactivate_mode(mode.name)

        return current_modes

    def get_available_modes(self) -> List[GameMode]:
        """Get all modes available to users (active + considering time constraints)"""
        return self.get_active_modes()

    def get_default_mode(self) -> Optional[GameMode]:
        """Get the default mode (should be 'normal')"""
        data = self.find_one({"is_default": True})
        return GameMode.from_dict(data) if data else None

    def activate_mode(self, mode_name: str, start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None) -> bool:
        """Activate a game mode"""
        update_data = {
            "is_active": True,
            "updated_at": datetime.utcnow()
        }

        if start_date:
            update_data["start_date"] = start_date
        if end_date:
            update_data["end_date"] = end_date

        result = self.collection.update_one(
            {"name": mode_name},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def deactivate_mode(self, mode_name: str) -> bool:
        """Deactivate a game mode"""
        result = self.collection.update_one(
            {"name": mode_name},
            {"$set": {
                "is_active": False,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    def update_mode_config(self, mode_name: str, config_updates: Dict[str, Any]) -> bool:
        """Update mode configuration"""
        result = self.collection.update_one(
            {"name": mode_name},
            {"$set": {
                "config": config_updates,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    def upsert_mode(self, mode: GameMode) -> str:
        """Create or update a game mode"""
        existing = self.get_mode_by_name(mode.name)
        if existing:
            mode._id = existing._id
            self.update_by_id(str(existing._id), mode.to_dict())
            return str(existing._id)
        else:
            return self.create_mode(mode)

    def get_modes_by_status(self, is_active: bool) -> List[GameMode]:
        """Get modes by active status"""
        modes_data = self.find_many({"is_active": is_active})
        return [GameMode.from_dict(data) for data in modes_data]

    def get_scheduled_modes(self) -> List[GameMode]:
        """Get modes that are scheduled for future activation"""
        now = datetime.utcnow()
        modes_data = self.find_many({
            "is_active": True,
            "start_date": {"$gt": now}
        })
        return [GameMode.from_dict(data) for data in modes_data]

    def get_expired_modes(self) -> List[GameMode]:
        """Get modes that have expired and should be deactivated"""
        now = datetime.utcnow()
        modes_data = self.find_many({
            "is_active": True,
            "end_date": {"$lt": now}
        })
        return [GameMode.from_dict(data) for data in modes_data]

    def cleanup_expired_modes(self) -> int:
        """Automatically deactivate expired modes"""
        now = datetime.utcnow()
        result = self.collection.update_many(
            {
                "is_active": True,
                "end_date": {"$lt": now}
            },
            {"$set": {
                "is_active": False,
                "updated_at": now
            }}
        )
        return result.modified_count

    def ensure_default_mode_exists(self) -> GameMode:
        """Ensure the default 'normal' mode exists and is active"""
        normal_mode = self.get_mode_by_name("normal")
        if not normal_mode:
            normal_mode = GameMode.create_default_normal_mode()
            self.create_mode(normal_mode)
        elif not normal_mode.is_active:
            self.activate_mode("normal")

        return normal_mode

    def initialize_default_modes(self) -> List[GameMode]:
        """Initialize all default modes"""
        modes = []

        # Ensure normal mode exists and is active
        normal_mode = self.ensure_default_mode_exists()
        modes.append(normal_mode)

        # Create challenge mode template if it doesn't exist
        challenge_mode = self.get_mode_by_name("challenges")
        if not challenge_mode:
            challenge_mode = GameMode.create_challenges_mode()
            self.create_mode(challenge_mode)
            modes.append(challenge_mode)

        # Create team tournament mode template if it doesn't exist
        tournament_mode = self.get_mode_by_name("team_tournament")
        if not tournament_mode:
            tournament_mode = GameMode.create_team_tournament_mode()
            self.create_mode(tournament_mode)
            modes.append(tournament_mode)

        return modes

    def get_user_available_modes(self, user_id: str = None) -> List[GameMode]:
        """Get modes available to a specific user (for future user-specific restrictions)"""
        # For now, return all available modes
        # In the future, this could filter based on user level, subscription, etc.
        return self.get_available_modes()

    def delete_mode(self, mode_name: str) -> bool:
        """Delete a game mode (only if not default)"""
        mode = self.get_mode_by_name(mode_name)
        if not mode or mode.is_default:
            return False

        result = self.collection.delete_one({"name": mode_name})
        return result.deleted_count > 0