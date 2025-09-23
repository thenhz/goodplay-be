from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.repositories.base_repository import BaseRepository
from ..models.global_team import GlobalTeam

class GlobalTeamRepository(BaseRepository):
    """Repository for global team operations"""

    def __init__(self):
        super().__init__("global_teams")

    def create_team(self, team: GlobalTeam) -> str:
        """Create a new global team"""
        return self.create(team.to_dict())

    def get_team_by_id(self, team_id: str) -> Optional[GlobalTeam]:
        """Get a team by ID"""
        data = self.find_by_id(team_id)
        return GlobalTeam.from_dict(data) if data else None

    def get_team_by_team_id(self, team_id: str) -> Optional[GlobalTeam]:
        """Get a team by team_id field"""
        data = self.find_one({"team_id": team_id})
        return GlobalTeam.from_dict(data) if data else None

    def get_all_teams(self, active_only: bool = True) -> List[GlobalTeam]:
        """Get all teams"""
        filter_dict = {"is_active": True} if active_only else {}
        teams_data = self.find_many(filter_dict, sort=[("total_score", -1)])
        return [GlobalTeam.from_dict(data) for data in teams_data]

    def get_teams_by_tournament(self, tournament_id: str) -> List[GlobalTeam]:
        """Get teams participating in a tournament"""
        teams_data = self.find_many({"tournament_id": tournament_id})
        return [GlobalTeam.from_dict(data) for data in teams_data]

    def get_team_leaderboard(self, limit: int = 10) -> List[GlobalTeam]:
        """Get team leaderboard by total score"""
        teams_data = self.find_many(
            {"is_active": True},
            limit=limit,
            sort=[("total_score", -1)]
        )
        return [GlobalTeam.from_dict(data) for data in teams_data]

    def update_team_score(self, team_id: str, points: float, source: str = "game") -> bool:
        """Add points to a team's score"""
        result = self.collection.update_one(
            {"team_id": team_id},
            {
                "$inc": {"total_score": points},
                "$set": {"updated_at": datetime.utcnow()},
                "$inc": {f"stats.points_by_source.{source}": points}
            }
        )
        return result.modified_count > 0

    def update_member_count(self, team_id: str, change: int) -> bool:
        """Update team member count"""
        result = self.collection.update_one(
            {"team_id": team_id},
            {
                "$inc": {"current_members": change},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0

    def set_tournament(self, team_id: str, tournament_id: str) -> bool:
        """Set tournament for a team"""
        result = self.collection.update_one(
            {"team_id": team_id},
            {"$set": {
                "tournament_id": tournament_id,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    def clear_tournament(self, team_id: str) -> bool:
        """Clear tournament for a team"""
        result = self.collection.update_one(
            {"team_id": team_id},
            {"$unset": {"tournament_id": ""},
             "$set": {"updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def reset_scores(self, team_ids: List[str]) -> int:
        """Reset scores for multiple teams"""
        result = self.collection.update_many(
            {"team_id": {"$in": team_ids}},
            {"$set": {
                "total_score": 0.0,
                "stats.total_points_earned": 0,
                "stats.points_by_source": {},
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count

    def update_team_stats(self, team_id: str, stats: Dict[str, Any]) -> bool:
        """Update team statistics"""
        result = self.collection.update_one(
            {"team_id": team_id},
            {"$set": {
                "stats": stats,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    def add_achievement(self, team_id: str, achievement_id: str) -> bool:
        """Add achievement to team"""
        result = self.collection.update_one(
            {"team_id": team_id},
            {"$addToSet": {"achievements": achievement_id}}
        )
        return result.modified_count > 0

    def get_teams_needing_balancing(self) -> List[GlobalTeam]:
        """Get teams that need member balancing"""
        teams = self.get_all_teams()

        if not teams:
            return []

        avg_members = sum(t.current_members for t in teams) / len(teams)
        threshold = avg_members * 0.3  # 30% deviation threshold

        unbalanced_teams = []
        for team in teams:
            deviation = abs(team.current_members - avg_members)
            if deviation > threshold:
                unbalanced_teams.append(team)

        return unbalanced_teams

    def initialize_default_teams(self) -> List[GlobalTeam]:
        """Initialize default teams if none exist"""
        existing_teams = self.get_all_teams(active_only=False)
        if existing_teams:
            return existing_teams

        default_teams = GlobalTeam.create_default_teams()
        for team in default_teams:
            self.create_team(team)

        return default_teams

    def get_team_statistics(self) -> Dict[str, Any]:
        """Get overall team statistics"""
        total_teams = self.collection.count_documents({"is_active": True})

        # Get total members across all teams
        pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": None,
                "total_members": {"$sum": "$current_members"},
                "total_score": {"$sum": "$total_score"},
                "avg_score": {"$avg": "$total_score"},
                "max_score": {"$max": "$total_score"}
            }}
        ]

        result = list(self.collection.aggregate(pipeline))
        if result:
            stats = result[0]
            return {
                "total_teams": total_teams,
                "total_members": stats.get("total_members", 0),
                "total_score": stats.get("total_score", 0),
                "average_score_per_team": stats.get("avg_score", 0),
                "highest_team_score": stats.get("max_score", 0),
                "average_members_per_team": stats.get("total_members", 0) / total_teams if total_teams > 0 else 0
            }

        return {
            "total_teams": 0,
            "total_members": 0,
            "total_score": 0,
            "average_score_per_team": 0,
            "highest_team_score": 0,
            "average_members_per_team": 0
        }