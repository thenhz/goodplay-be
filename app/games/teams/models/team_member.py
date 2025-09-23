from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from dataclasses import dataclass, field

@dataclass
class TeamMember:
    """TeamMember model representing a user's membership in a global team"""
    user_id: str
    team_id: str
    joined_at: datetime = field(default_factory=datetime.utcnow)
    contribution_score: float = 0.0
    games_played: int = 0
    challenges_participated: int = 0
    individual_best_score: int = 0
    team_role: str = "member"  # 'member', 'veteran', 'captain'
    is_active: bool = True
    performance_stats: Dict[str, Any] = field(default_factory=dict)
    achievements: list = field(default_factory=list)
    last_activity_at: Optional[datetime] = None
    tournament_stats: Dict[str, Any] = field(default_factory=dict)
    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the team member to a dictionary for MongoDB storage"""
        data = {
            "user_id": self.user_id,
            "team_id": self.team_id,
            "joined_at": self.joined_at,
            "contribution_score": self.contribution_score,
            "games_played": self.games_played,
            "challenges_participated": self.challenges_participated,
            "individual_best_score": self.individual_best_score,
            "team_role": self.team_role,
            "is_active": self.is_active,
            "performance_stats": self.performance_stats,
            "achievements": self.achievements,
            "last_activity_at": self.last_activity_at,
            "tournament_stats": self.tournament_stats
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamMember':
        """Create a TeamMember instance from a dictionary"""
        member = cls(
            user_id=data.get("user_id", ""),
            team_id=data.get("team_id", ""),
            joined_at=data.get("joined_at", datetime.utcnow()),
            contribution_score=data.get("contribution_score", 0.0),
            games_played=data.get("games_played", 0),
            challenges_participated=data.get("challenges_participated", 0),
            individual_best_score=data.get("individual_best_score", 0),
            team_role=data.get("team_role", "member"),
            is_active=data.get("is_active", True),
            performance_stats=data.get("performance_stats", {}),
            achievements=data.get("achievements", []),
            last_activity_at=data.get("last_activity_at"),
            tournament_stats=data.get("tournament_stats", {})
        )

        if "_id" in data:
            member._id = data["_id"]

        return member

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the team member to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "user_id": self.user_id,
            "team_id": self.team_id,
            "joined_at": self.joined_at.isoformat(),
            "contribution_score": self.contribution_score,
            "games_played": self.games_played,
            "challenges_participated": self.challenges_participated,
            "individual_best_score": self.individual_best_score,
            "team_role": self.team_role,
            "is_active": self.is_active,
            "performance_stats": self.get_enhanced_performance_stats(),
            "achievements": self.achievements,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "tournament_stats": self.tournament_stats,
            "days_in_team": self.get_days_in_team(),
            "activity_level": self.get_activity_level(),
            "contribution_rank": self.performance_stats.get("contribution_rank", 0)
        }

    def add_game_played(self, score: int, contribution_points: float) -> None:
        """Add a game played to member stats"""
        self.games_played += 1
        self.contribution_score += contribution_points

        if score > self.individual_best_score:
            self.individual_best_score = score

        self.last_activity_at = datetime.utcnow()
        self._update_performance_stats()

    def add_challenge_participation(self, challenge_result: Dict[str, Any]) -> None:
        """Add challenge participation to member stats"""
        self.challenges_participated += 1

        # Add contribution based on challenge result
        position = challenge_result.get("position", 0)
        points = challenge_result.get("points_earned", 0)

        # Bonus points for good performance in challenges
        if position == 1:
            contribution_bonus = points * 1.5
        elif position <= 3:
            contribution_bonus = points * 1.2
        else:
            contribution_bonus = points

        self.contribution_score += contribution_bonus
        self.last_activity_at = datetime.utcnow()
        self._update_performance_stats()

    def get_days_in_team(self) -> int:
        """Get number of days as team member"""
        return (datetime.utcnow() - self.joined_at).days

    def get_activity_level(self) -> str:
        """Get activity level based on recent activity"""
        if not self.last_activity_at:
            return "inactive"

        days_since_activity = (datetime.utcnow() - self.last_activity_at).days

        if days_since_activity == 0:
            return "very_active"
        elif days_since_activity <= 3:
            return "active"
        elif days_since_activity <= 7:
            return "moderate"
        elif days_since_activity <= 30:
            return "low"
        else:
            return "inactive"

    def get_enhanced_performance_stats(self) -> Dict[str, Any]:
        """Get enhanced performance statistics"""
        stats = self.performance_stats.copy()

        total_activities = self.games_played + self.challenges_participated

        stats.update({
            "total_activities": total_activities,
            "average_contribution_per_activity": (
                self.contribution_score / total_activities if total_activities > 0 else 0
            ),
            "challenge_participation_rate": (
                self.challenges_participated / total_activities * 100 if total_activities > 0 else 0
            ),
            "days_in_team": self.get_days_in_team(),
            "activity_level": self.get_activity_level(),
            "activities_per_day": (
                total_activities / max(1, self.get_days_in_team())
            )
        })

        return stats

    def _update_performance_stats(self) -> None:
        """Update performance statistics"""
        total_activities = self.games_played + self.challenges_participated

        self.performance_stats.update({
            "total_activities": total_activities,
            "last_updated": datetime.utcnow(),
            "contribution_trend": self._calculate_contribution_trend()
        })

    def _calculate_contribution_trend(self) -> str:
        """Calculate contribution trend"""
        # Simple trend calculation based on recent activity
        if not self.last_activity_at:
            return "declining"

        days_since_activity = (datetime.utcnow() - self.last_activity_at).days
        activities_per_week = (self.games_played + self.challenges_participated) / max(1, self.get_days_in_team() / 7)

        if activities_per_week > 10:
            return "rising"
        elif activities_per_week > 5:
            return "stable"
        elif days_since_activity <= 7:
            return "stable"
        else:
            return "declining"

    def promote_role(self) -> bool:
        """Promote member to next role level"""
        role_hierarchy = ["member", "veteran", "captain"]
        current_index = role_hierarchy.index(self.team_role)

        if current_index < len(role_hierarchy) - 1:
            self.team_role = role_hierarchy[current_index + 1]
            return True
        return False

    def demote_role(self) -> bool:
        """Demote member to previous role level"""
        role_hierarchy = ["member", "veteran", "captain"]
        current_index = role_hierarchy.index(self.team_role)

        if current_index > 0:
            self.team_role = role_hierarchy[current_index - 1]
            return True
        return False

    def set_inactive(self) -> None:
        """Set member as inactive"""
        self.is_active = False

    def reactivate(self) -> None:
        """Reactivate member"""
        self.is_active = True
        self.last_activity_at = datetime.utcnow()

    def add_achievement(self, achievement_id: str) -> bool:
        """Add an achievement to the member"""
        if achievement_id not in self.achievements:
            self.achievements.append(achievement_id)
            return True
        return False

    def update_tournament_stats(self, tournament_id: str, stats: Dict[str, Any]) -> None:
        """Update tournament-specific statistics"""
        if tournament_id not in self.tournament_stats:
            self.tournament_stats[tournament_id] = {}

        self.tournament_stats[tournament_id].update(stats)

    def get_tournament_contribution(self, tournament_id: str) -> float:
        """Get contribution for a specific tournament"""
        tournament_stats = self.tournament_stats.get(tournament_id, {})
        return tournament_stats.get("contribution_score", 0.0)

    def is_veteran(self) -> bool:
        """Check if member is a veteran (based on time and contribution)"""
        return (
            self.get_days_in_team() >= 30 and
            self.contribution_score >= 1000 and
            self.games_played >= 50
        )

    def is_captain_eligible(self) -> bool:
        """Check if member is eligible to be captain"""
        return (
            self.is_veteran() and
            self.contribution_score >= 5000 and
            self.get_activity_level() in ["active", "very_active"]
        )

    @staticmethod
    def create_member(user_id: str, team_id: str, role: str = "member") -> 'TeamMember':
        """Create a new team member"""
        return TeamMember(
            user_id=user_id,
            team_id=team_id,
            team_role=role,
            performance_stats={
                "created_at": datetime.utcnow(),
                "initial_role": role
            }
        )

    def __str__(self) -> str:
        return f"TeamMember(user={self.user_id}, team={self.team_id}, role={self.team_role}, score={self.contribution_score})"

    def __repr__(self) -> str:
        return self.__str__()