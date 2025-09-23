from datetime import datetime
from typing import Dict, Any, Optional, List
from bson import ObjectId
from dataclasses import dataclass, field
import uuid

@dataclass
class GlobalTeam:
    """GlobalTeam model representing a team in global competitions"""
    name: str
    color: str = "#FF0000"  # Hex color for UI
    icon: str = "🔥"  # Emoji or icon identifier
    description: str = ""
    is_active: bool = True
    current_members: int = 0
    max_members: Optional[int] = None  # None = unlimited
    total_score: float = 0.0
    tournament_id: Optional[str] = None  # Current tournament
    team_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    stats: Dict[str, Any] = field(default_factory=dict)
    achievements: List[str] = field(default_factory=list)
    team_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the global team to a dictionary for MongoDB storage"""
        data = {
            "team_id": self.team_id,
            "name": self.name,
            "color": self.color,
            "icon": self.icon,
            "description": self.description,
            "is_active": self.is_active,
            "current_members": self.current_members,
            "max_members": self.max_members,
            "total_score": self.total_score,
            "tournament_id": self.tournament_id,
            "team_config": self.team_config,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "stats": self.stats,
            "achievements": self.achievements
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalTeam':
        """Create a GlobalTeam instance from a dictionary"""
        team = cls(
            name=data.get("name", ""),
            color=data.get("color", "#FF0000"),
            icon=data.get("icon", "🔥"),
            description=data.get("description", ""),
            is_active=data.get("is_active", True),
            current_members=data.get("current_members", 0),
            max_members=data.get("max_members"),
            total_score=data.get("total_score", 0.0),
            tournament_id=data.get("tournament_id"),
            team_config=data.get("team_config", {}),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            stats=data.get("stats", {}),
            achievements=data.get("achievements", []),
            team_id=data.get("team_id", str(uuid.uuid4()))
        )

        if "_id" in data:
            team._id = data["_id"]

        return team

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the global team to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "team_id": self.team_id,
            "name": self.name,
            "color": self.color,
            "icon": self.icon,
            "description": self.description,
            "is_active": self.is_active,
            "current_members": self.current_members,
            "max_members": self.max_members,
            "total_score": self.total_score,
            "tournament_id": self.tournament_id,
            "team_config": self.team_config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "stats": self.get_enhanced_stats(),
            "achievements": self.achievements,
            "average_score_per_member": self.get_average_score_per_member(),
            "team_rank": self.stats.get("current_rank", 0),
            "is_recruiting": self.is_recruiting()
        }

    def add_member(self) -> bool:
        """Add a member to the team"""
        if self.max_members and self.current_members >= self.max_members:
            return False

        self.current_members += 1
        self.updated_at = datetime.utcnow()
        return True

    def remove_member(self) -> bool:
        """Remove a member from the team"""
        if self.current_members <= 0:
            return False

        self.current_members -= 1
        self.updated_at = datetime.utcnow()
        return True

    def add_score(self, points: float, source: str = "game") -> None:
        """Add points to the team's total score"""
        self.total_score += points
        self.updated_at = datetime.utcnow()

        # Update stats
        if "total_points_earned" not in self.stats:
            self.stats["total_points_earned"] = 0
        self.stats["total_points_earned"] += points

        # Track score sources
        if "points_by_source" not in self.stats:
            self.stats["points_by_source"] = {}
        if source not in self.stats["points_by_source"]:
            self.stats["points_by_source"][source] = 0
        self.stats["points_by_source"][source] += points

    def get_average_score_per_member(self) -> float:
        """Get average score per team member"""
        if self.current_members == 0:
            return 0.0
        return self.total_score / self.current_members

    def is_recruiting(self) -> bool:
        """Check if team is accepting new members"""
        if not self.is_active:
            return False
        if self.max_members and self.current_members >= self.max_members:
            return False
        return True

    def update_stats(self, new_stats: Dict[str, Any]) -> None:
        """Update team statistics"""
        self.stats.update(new_stats)
        self.updated_at = datetime.utcnow()

    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get enhanced statistics with calculated values"""
        enhanced_stats = self.stats.copy()
        enhanced_stats.update({
            "average_score_per_member": self.get_average_score_per_member(),
            "total_score": self.total_score,
            "current_members": self.current_members,
            "games_played": self.stats.get("games_played", 0),
            "challenges_won": self.stats.get("challenges_won", 0),
            "individual_games": self.stats.get("individual_games", 0),
            "team_level": self._calculate_team_level(),
            "activity_score": self._calculate_activity_score()
        })
        return enhanced_stats

    def _calculate_team_level(self) -> int:
        """Calculate team level based on total score and activity"""
        total_points = self.stats.get("total_points_earned", 0)
        games_played = self.stats.get("games_played", 0)

        # Simple level calculation: 1000 points per level + activity bonus
        base_level = int(total_points / 1000)
        activity_bonus = min(games_played // 50, 10)  # Max 10 levels from activity

        return max(1, base_level + activity_bonus)

    def _calculate_activity_score(self) -> float:
        """Calculate activity score based on recent participation"""
        games_played = self.stats.get("games_played", 0)
        challenges_participated = self.stats.get("challenges_participated", 0)
        members = max(1, self.current_members)

        # Activity score per member
        activity_per_member = (games_played + challenges_participated * 2) / members
        return min(100.0, activity_per_member)  # Cap at 100

    def add_achievement(self, achievement_id: str) -> bool:
        """Add an achievement to the team"""
        if achievement_id not in self.achievements:
            self.achievements.append(achievement_id)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def set_tournament(self, tournament_id: str) -> None:
        """Set the current tournament for this team"""
        self.tournament_id = tournament_id
        self.updated_at = datetime.utcnow()

    def clear_tournament(self) -> None:
        """Clear the current tournament"""
        self.tournament_id = None
        self.updated_at = datetime.utcnow()

    def reset_score(self) -> None:
        """Reset team score (for new tournaments)"""
        self.total_score = 0.0
        self.stats["total_points_earned"] = 0
        self.stats["points_by_source"] = {}
        self.updated_at = datetime.utcnow()

    @staticmethod
    def create_default_teams() -> List['GlobalTeam']:
        """Create default teams for global competitions"""
        teams = [
            GlobalTeam(
                name="Phoenix Rising",
                color="#FF4500",
                icon="🔥",
                description="Rising from challenges with fiery determination",
                team_config={
                    "theme": "fire",
                    "motto": "Rise from the ashes",
                    "bonus_multiplier": 1.0
                }
            ),
            GlobalTeam(
                name="Ocean Depths",
                color="#0066CC",
                icon="🌊",
                description="Deep thinkers who flow like water",
                team_config={
                    "theme": "water",
                    "motto": "Adapt and overcome",
                    "bonus_multiplier": 1.0
                }
            ),
            GlobalTeam(
                name="Storm Warriors",
                color="#9932CC",
                icon="⚡",
                description="Electric energy and lightning-fast reflexes",
                team_config={
                    "theme": "lightning",
                    "motto": "Strike with precision",
                    "bonus_multiplier": 1.0
                }
            ),
            GlobalTeam(
                name="Earth Guardians",
                color="#228B22",
                icon="🌍",
                description="Grounded strength and natural wisdom",
                team_config={
                    "theme": "earth",
                    "motto": "Strong as stone",
                    "bonus_multiplier": 1.0
                }
            )
        ]
        return teams

    @staticmethod
    def create_custom_team(name: str, color: str, icon: str, description: str = "") -> 'GlobalTeam':
        """Create a custom team"""
        return GlobalTeam(
            name=name,
            color=color,
            icon=icon,
            description=description,
            team_config={
                "custom": True,
                "created_by": "admin",
                "bonus_multiplier": 1.0
            }
        )

    def __str__(self) -> str:
        return f"GlobalTeam(id={self._id}, name={self.name}, members={self.current_members}, score={self.total_score})"

    def __repr__(self) -> str:
        return self.__str__()