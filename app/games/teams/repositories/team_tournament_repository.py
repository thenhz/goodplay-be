from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.repositories.base_repository import BaseRepository
from ..models.team_tournament import TeamTournament

class TeamTournamentRepository(BaseRepository):
    """Repository for team tournament operations"""

    def __init__(self):
        super().__init__("team_tournaments")

    def create_tournament(self, tournament: TeamTournament) -> str:
        """Create a new team tournament"""
        return self.create(tournament.to_dict())

    def get_tournament_by_id(self, tournament_id: str) -> Optional[TeamTournament]:
        """Get a tournament by ID"""
        data = self.find_by_id(tournament_id)
        return TeamTournament.from_dict(data) if data else None

    def get_tournament_by_tournament_id(self, tournament_id: str) -> Optional[TeamTournament]:
        """Get a tournament by tournament_id field"""
        data = self.find_one({"tournament_id": tournament_id})
        return TeamTournament.from_dict(data) if data else None

    def get_active_tournament(self) -> Optional[TeamTournament]:
        """Get the currently active tournament"""
        data = self.find_one({"status": "active"})
        return TeamTournament.from_dict(data) if data else None

    def get_tournaments_by_status(self, status: str) -> List[TeamTournament]:
        """Get tournaments by status"""
        tournaments_data = self.find_many({"status": status}, sort=[("created_at", -1)])
        return [TeamTournament.from_dict(data) for data in tournaments_data]

    def get_upcoming_tournaments(self, limit: int = 10) -> List[TeamTournament]:
        """Get upcoming tournaments"""
        tournaments_data = self.find_many(
            {"status": "upcoming"},
            limit=limit,
            sort=[("start_date", 1)]
        )
        return [TeamTournament.from_dict(data) for data in tournaments_data]

    def get_completed_tournaments(self, limit: int = 20) -> List[TeamTournament]:
        """Get completed tournaments"""
        tournaments_data = self.find_many(
            {"status": "completed"},
            limit=limit,
            sort=[("end_date", -1)]
        )
        return [TeamTournament.from_dict(data) for data in tournaments_data]

    def start_tournament(self, tournament_id: str) -> bool:
        """Start a tournament"""
        now = datetime.utcnow()
        result = self.collection.update_one(
            {"tournament_id": tournament_id, "status": "upcoming"},
            {"$set": {
                "status": "active",
                "start_date": now,
                "updated_at": now
            }}
        )
        return result.modified_count > 0

    def complete_tournament(self, tournament_id: str, final_standings: List[str]) -> bool:
        """Complete a tournament with final standings"""
        now = datetime.utcnow()
        result = self.collection.update_one(
            {"tournament_id": tournament_id, "status": "active"},
            {"$set": {
                "status": "completed",
                "end_date": now,
                "final_standings": final_standings,
                "updated_at": now
            }}
        )
        return result.modified_count > 0

    def cancel_tournament(self, tournament_id: str) -> bool:
        """Cancel a tournament"""
        result = self.collection.update_one(
            {"tournament_id": tournament_id, "status": {"$ne": "completed"}},
            {"$set": {
                "status": "cancelled",
                "end_date": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    def add_team_to_tournament(self, tournament_id: str, team_id: str) -> bool:
        """Add a team to a tournament"""
        result = self.collection.update_one(
            {"tournament_id": tournament_id, "status": "upcoming"},
            {
                "$addToSet": {"teams": team_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0

    def remove_team_from_tournament(self, tournament_id: str, team_id: str) -> bool:
        """Remove a team from a tournament"""
        result = self.collection.update_one(
            {"tournament_id": tournament_id, "status": "upcoming"},
            {
                "$pull": {"teams": team_id},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0

    def update_team_standing(self, tournament_id: str, team_id: str, points: float, activity_type: str) -> bool:
        """Update a team's standing in the tournament"""
        now = datetime.utcnow()

        # Update the specific team's standing
        result = self.collection.update_one(
            {
                "tournament_id": tournament_id,
                "status": "active",
                "current_standings.team_id": team_id
            },
            {
                "$inc": {
                    "current_standings.$.score": points,
                    f"current_standings.$.{activity_type}_count": 1
                },
                "$set": {
                    "current_standings.$.last_activity": now.isoformat(),
                    "updated_at": now
                }
            }
        )

        if result.modified_count > 0:
            # Re-sort standings by score
            self._resort_standings(tournament_id)
            return True

        return False

    def _resort_standings(self, tournament_id: str) -> None:
        """Resort tournament standings by score"""
        tournament = self.get_tournament_by_tournament_id(tournament_id)
        if not tournament:
            return

        # Sort standings by score
        sorted_standings = sorted(
            tournament.current_standings,
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        # Update positions
        for i, standing in enumerate(sorted_standings):
            standing["position"] = i + 1

        # Update in database
        self.collection.update_one(
            {"tournament_id": tournament_id},
            {"$set": {
                "current_standings": sorted_standings,
                "updated_at": datetime.utcnow()
            }}
        )

    def get_tournament_leaderboard(self, tournament_id: str) -> List[Dict[str, Any]]:
        """Get tournament leaderboard"""
        tournament = self.get_tournament_by_tournament_id(tournament_id)
        if not tournament:
            return []

        return sorted(tournament.current_standings, key=lambda x: x.get("score", 0), reverse=True)

    def initialize_tournament_standings(self, tournament_id: str, team_ids: List[str]) -> bool:
        """Initialize standings for a tournament"""
        standings = [
            {
                "team_id": team_id,
                "score": 0.0,
                "position": i + 1,
                "games_played": 0,
                "challenges_won": 0,
                "individual_games": 0,
                "last_activity": None
            }
            for i, team_id in enumerate(team_ids)
        ]

        result = self.collection.update_one(
            {"tournament_id": tournament_id},
            {"$set": {
                "current_standings": standings,
                "updated_at": datetime.utcnow()
            }}
        )
        return result.modified_count > 0

    def get_tournament_statistics(self, tournament_id: str) -> Dict[str, Any]:
        """Get detailed tournament statistics"""
        tournament = self.get_tournament_by_tournament_id(tournament_id)
        if not tournament:
            return {}

        stats = {
            "tournament_id": tournament_id,
            "name": tournament.name,
            "status": tournament.status,
            "total_teams": len(tournament.teams),
            "duration_days": tournament.get_duration_days(),
            "time_remaining_hours": tournament.get_time_remaining_hours()
        }

        if tournament.current_standings:
            total_score = sum(s.get("score", 0) for s in tournament.current_standings)
            total_games = sum(s.get("games_played", 0) for s in tournament.current_standings)
            total_challenges = sum(s.get("challenges_won", 0) for s in tournament.current_standings)

            stats.update({
                "total_points_awarded": total_score,
                "total_games_played": total_games,
                "total_challenges_completed": total_challenges,
                "average_score_per_team": total_score / len(tournament.teams) if tournament.teams else 0,
                "leader_score": tournament.current_standings[0].get("score", 0) if tournament.current_standings else 0,
                "competition_closeness": tournament._calculate_competition_closeness()
            })

        return stats

    def end_expired_tournaments(self) -> int:
        """End tournaments that have passed their end date"""
        now = datetime.utcnow()

        # Find active tournaments that have expired
        expired_tournaments = self.find_many({
            "status": "active",
            "end_date": {"$lt": now}
        })

        count = 0
        for tournament_data in expired_tournaments:
            tournament = TeamTournament.from_dict(tournament_data)

            # Sort final standings
            sorted_standings = sorted(
                tournament.current_standings,
                key=lambda x: x.get("score", 0),
                reverse=True
            )
            final_standings = [s["team_id"] for s in sorted_standings]

            # Complete the tournament
            if self.complete_tournament(tournament.tournament_id, final_standings):
                count += 1

        return count

    def cleanup_old_tournaments(self, days_old: int = 90) -> int:
        """Clean up very old completed tournaments"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = self.collection.delete_many({
            "status": {"$in": ["completed", "cancelled"]},
            "end_date": {"$lt": cutoff_date}
        })
        return result.deleted_count