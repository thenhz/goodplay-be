from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.repositories.base_repository import BaseRepository
from ..models.team_member import TeamMember

class TeamMemberRepository(BaseRepository):
    """Repository for team member operations"""

    def __init__(self):
        super().__init__("team_members")

    def create_indexes(self):
        import os
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        from pymongo import ASCENDING
        # Index for user_id - used frequently for user lookups
        self.collection.create_index([("user_id", ASCENDING)])
        # Index for team_id - used for team member queries
        self.collection.create_index([("team_id", ASCENDING)])
        # Compound index for user_id and team_id - used for specific member lookups
        self.collection.create_index([("user_id", ASCENDING), ("team_id", ASCENDING)])
        # Index for active members
        self.collection.create_index([("is_active", ASCENDING)])
        # Index for contribution_score - used for leaderboards
        self.collection.create_index([("contribution_score", -1)])
        # Compound index for team and role
        self.collection.create_index([("team_id", ASCENDING), ("team_role", ASCENDING)])
        # Index for last activity - used for finding inactive members
        self.collection.create_index([("last_activity_at", ASCENDING)])

    def create_member(self, member: TeamMember) -> str:
        """Create a new team member"""
        return self.create(member.to_dict())

    def get_member_by_id(self, member_id: str) -> Optional[TeamMember]:
        """Get a member by ID"""
        data = self.find_by_id(member_id)
        return TeamMember.from_dict(data) if data else None

    def get_member(self, user_id: str, team_id: str) -> Optional[TeamMember]:
        """Get a specific team member"""
        data = self.find_one({"user_id": user_id, "team_id": team_id})
        return TeamMember.from_dict(data) if data else None

    def get_user_team(self, user_id: str) -> Optional[TeamMember]:
        """Get user's current team membership"""
        data = self.find_one({"user_id": user_id, "is_active": True})
        return TeamMember.from_dict(data) if data else None

    def get_team_members(self, team_id: str, active_only: bool = True) -> List[TeamMember]:
        """Get all members of a team"""
        filter_dict = {"team_id": team_id}
        if active_only:
            filter_dict["is_active"] = True

        members_data = self.find_many(filter_dict, sort=[("contribution_score", -1)])
        return [TeamMember.from_dict(data) for data in members_data]

    def get_members_by_role(self, team_id: str, role: str) -> List[TeamMember]:
        """Get team members by role"""
        members_data = self.find_many({
            "team_id": team_id,
            "team_role": role,
            "is_active": True
        })
        return [TeamMember.from_dict(data) for data in members_data]

    def assign_user_to_team(self, user_id: str, team_id: str, role: str = "member") -> bool:
        """Assign a user to a team"""
        # First deactivate any existing membership
        self.collection.update_many(
            {"user_id": user_id, "is_active": True},
            {"$set": {"is_active": False}}
        )

        # Create new membership
        member = TeamMember.create_member(user_id, team_id, role)
        member_id = self.create_member(member)
        return bool(member_id)

    def remove_user_from_team(self, user_id: str, team_id: str) -> bool:
        """Remove a user from a team"""
        result = self.collection.update_one(
            {"user_id": user_id, "team_id": team_id},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0

    def update_contribution_score(self, user_id: str, team_id: str, points: float) -> bool:
        """Add points to member's contribution score"""
        result = self.collection.update_one(
            {"user_id": user_id, "team_id": team_id, "is_active": True},
            {
                "$inc": {"contribution_score": points},
                "$set": {"last_activity_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0

    def add_game_played(self, user_id: str, team_id: str, score: int, contribution_points: float) -> bool:
        """Record a game played by team member"""
        update_data = {
            "$inc": {
                "games_played": 1,
                "contribution_score": contribution_points
            },
            "$set": {"last_activity_at": datetime.utcnow()},
            "$max": {"individual_best_score": score}
        }

        result = self.collection.update_one(
            {"user_id": user_id, "team_id": team_id, "is_active": True},
            update_data
        )
        return result.modified_count > 0

    def add_challenge_participation(self, user_id: str, team_id: str, challenge_result: Dict[str, Any]) -> bool:
        """Record challenge participation"""
        position = challenge_result.get("position", 0)
        points = challenge_result.get("points_earned", 0)

        # Calculate contribution bonus
        if position == 1:
            contribution_bonus = points * 1.5
        elif position <= 3:
            contribution_bonus = points * 1.2
        else:
            contribution_bonus = points

        result = self.collection.update_one(
            {"user_id": user_id, "team_id": team_id, "is_active": True},
            {
                "$inc": {
                    "challenges_participated": 1,
                    "contribution_score": contribution_bonus
                },
                "$set": {"last_activity_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0

    def promote_member(self, user_id: str, team_id: str, new_role: str) -> bool:
        """Promote a team member"""
        result = self.collection.update_one(
            {"user_id": user_id, "team_id": team_id, "is_active": True},
            {"$set": {"team_role": new_role}}
        )
        return result.modified_count > 0

    def get_top_contributors(self, team_id: str, limit: int = 10) -> List[TeamMember]:
        """Get top contributors for a team"""
        members_data = self.find_many(
            {"team_id": team_id, "is_active": True},
            limit=limit,
            sort=[("contribution_score", -1)]
        )
        return [TeamMember.from_dict(data) for data in members_data]

    def get_inactive_members(self, team_id: str, days_inactive: int = 7) -> List[TeamMember]:
        """Get members who haven't been active recently"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_inactive)

        members_data = self.find_many({
            "team_id": team_id,
            "is_active": True,
            "$or": [
                {"last_activity_at": {"$lt": cutoff_date}},
                {"last_activity_at": {"$exists": False}}
            ]
        })
        return [TeamMember.from_dict(data) for data in members_data]

    def get_eligible_captains(self, team_id: str) -> List[TeamMember]:
        """Get members eligible to be captains"""
        members_data = self.find_many({
            "team_id": team_id,
            "is_active": True,
            "contribution_score": {"$gte": 5000},
            "games_played": {"$gte": 50}
        }, sort=[("contribution_score", -1)])

        members = [TeamMember.from_dict(data) for data in members_data]
        return [m for m in members if m.is_captain_eligible()]

    def get_team_member_statistics(self, team_id: str) -> Dict[str, Any]:
        """Get statistics for team members"""
        pipeline = [
            {"$match": {"team_id": team_id, "is_active": True}},
            {"$group": {
                "_id": None,
                "total_members": {"$sum": 1},
                "total_contribution": {"$sum": "$contribution_score"},
                "avg_contribution": {"$avg": "$contribution_score"},
                "total_games_played": {"$sum": "$games_played"},
                "total_challenges": {"$sum": "$challenges_participated"}
            }}
        ]

        result = list(self.collection.aggregate(pipeline))
        if result:
            stats = result[0]
            return {
                "total_members": stats.get("total_members", 0),
                "total_contribution_score": stats.get("total_contribution", 0),
                "average_contribution_per_member": stats.get("avg_contribution", 0),
                "total_games_played": stats.get("total_games_played", 0),
                "total_challenges_participated": stats.get("total_challenges", 0)
            }

        return {
            "total_members": 0,
            "total_contribution_score": 0,
            "average_contribution_per_member": 0,
            "total_games_played": 0,
            "total_challenges_participated": 0
        }

    def balance_teams(self, team_assignments: Dict[str, str]) -> int:
        """Bulk reassign users to teams for balancing"""
        operations = []

        for user_id, new_team_id in team_assignments.items():
            # Deactivate current membership
            operations.append({
                "updateMany": {
                    "filter": {"user_id": user_id, "is_active": True},
                    "update": {"$set": {"is_active": False}}
                }
            })

            # Create new membership
            new_member = TeamMember.create_member(user_id, new_team_id)
            operations.append({
                "insertOne": {"document": new_member.to_dict()}
            })

        if operations:
            result = self.collection.bulk_write(operations)
            return result.inserted_count

        return 0