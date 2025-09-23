from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from dataclasses import dataclass, field
import uuid

@dataclass
class TeamTournament:
    """TeamTournament model representing a tournament between global teams"""
    name: str
    tournament_type: str = "seasonal_war"  # 'seasonal_war', 'monthly_battle', 'special_event'
    teams: List[str] = field(default_factory=list)  # List of team IDs
    status: str = "upcoming"  # 'upcoming', 'active', 'completed', 'cancelled'
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    description: str = ""
    rules: Dict[str, Any] = field(default_factory=dict)
    scoring_config: Dict[str, Any] = field(default_factory=dict)
    prizes: Dict[str, Any] = field(default_factory=dict)
    current_standings: List[Dict[str, Any]] = field(default_factory=list)
    final_standings: List[str] = field(default_factory=list)  # Team IDs in final order
    statistics: Dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None  # Admin user ID
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tournament_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the team tournament to a dictionary for MongoDB storage"""
        data = {
            "tournament_id": self.tournament_id,
            "name": self.name,
            "tournament_type": self.tournament_type,
            "teams": self.teams,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "description": self.description,
            "rules": self.rules,
            "scoring_config": self.scoring_config,
            "prizes": self.prizes,
            "current_standings": self.current_standings,
            "final_standings": self.final_standings,
            "statistics": self.statistics,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamTournament':
        """Create a TeamTournament instance from a dictionary"""
        tournament = cls(
            name=data.get("name", ""),
            tournament_type=data.get("tournament_type", "seasonal_war"),
            teams=data.get("teams", []),
            status=data.get("status", "upcoming"),
            start_date=data.get("start_date", datetime.utcnow()),
            end_date=data.get("end_date"),
            description=data.get("description", ""),
            rules=data.get("rules", {}),
            scoring_config=data.get("scoring_config", {}),
            prizes=data.get("prizes", {}),
            current_standings=data.get("current_standings", []),
            final_standings=data.get("final_standings", []),
            statistics=data.get("statistics", {}),
            created_by=data.get("created_by"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            tournament_id=data.get("tournament_id", str(uuid.uuid4()))
        )

        if "_id" in data:
            tournament._id = data["_id"]

        return tournament

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the team tournament to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "tournament_id": self.tournament_id,
            "name": self.name,
            "tournament_type": self.tournament_type,
            "teams": self.teams,
            "team_count": len(self.teams),
            "status": self.status,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "description": self.description,
            "rules": self.rules,
            "scoring_config": self.scoring_config,
            "prizes": self.prizes,
            "current_standings": self.current_standings,
            "final_standings": self.final_standings,
            "statistics": self.get_enhanced_statistics(),
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "duration_days": self.get_duration_days(),
            "time_remaining_hours": self.get_time_remaining_hours(),
            "is_active": self.is_active(),
            "can_join": self.can_join_teams()
        }

    def start_tournament(self) -> bool:
        """Start the tournament"""
        if self.status != "upcoming":
            return False

        if len(self.teams) < 2:
            return False

        self.status = "active"
        self.start_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Initialize current standings
        self.current_standings = [
            {
                "team_id": team_id,
                "score": 0.0,
                "position": i + 1,
                "games_played": 0,
                "challenges_won": 0,
                "individual_games": 0,
                "last_activity": None
            }
            for i, team_id in enumerate(self.teams)
        ]

        return True

    def complete_tournament(self) -> bool:
        """Complete the tournament and finalize standings"""
        if self.status != "active":
            return False

        self.status = "completed"
        self.end_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        # Finalize standings based on current standings
        sorted_standings = sorted(
            self.current_standings,
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        self.final_standings = [standing["team_id"] for standing in sorted_standings]

        # Update final positions
        for i, standing in enumerate(sorted_standings):
            standing["final_position"] = i + 1

        self.current_standings = sorted_standings

        return True

    def cancel_tournament(self) -> bool:
        """Cancel the tournament"""
        if self.status == "completed":
            return False

        self.status = "cancelled"
        self.end_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return True

    def add_team(self, team_id: str) -> bool:
        """Add a team to the tournament"""
        if self.status != "upcoming":
            return False

        if team_id in self.teams:
            return False

        max_teams = self.rules.get("max_teams", 10)
        if len(self.teams) >= max_teams:
            return False

        self.teams.append(team_id)
        self.updated_at = datetime.utcnow()
        return True

    def remove_team(self, team_id: str) -> bool:
        """Remove a team from the tournament"""
        if self.status != "upcoming":
            return False

        if team_id not in self.teams:
            return False

        self.teams.remove(team_id)
        self.updated_at = datetime.utcnow()
        return True

    def update_team_score(self, team_id: str, points: float, activity_type: str) -> bool:
        """Update a team's score in the tournament"""
        if self.status != "active":
            return False

        if team_id not in self.teams:
            return False

        # Find team in current standings
        team_standing = None
        for standing in self.current_standings:
            if standing["team_id"] == team_id:
                team_standing = standing
                break

        if not team_standing:
            return False

        # Update score and activity
        team_standing["score"] += points
        team_standing["last_activity"] = datetime.utcnow().isoformat()

        # Update activity counters
        if activity_type == "game":
            team_standing["games_played"] += 1
            if "individual_games" not in team_standing:
                team_standing["individual_games"] = 0
            team_standing["individual_games"] += 1
        elif activity_type == "challenge":
            team_standing["challenges_won"] += 1

        # Re-sort standings
        self.current_standings.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Update positions
        for i, standing in enumerate(self.current_standings):
            standing["position"] = i + 1

        self.updated_at = datetime.utcnow()
        return True

    def get_team_standing(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get current standing for a specific team"""
        for standing in self.current_standings:
            if standing["team_id"] == team_id:
                return standing
        return None

    def get_duration_days(self) -> Optional[int]:
        """Get tournament duration in days"""
        if not self.end_date:
            return None

        duration = self.end_date - self.start_date
        return duration.days

    def get_time_remaining_hours(self) -> Optional[int]:
        """Get time remaining in hours"""
        if not self.end_date or self.status != "active":
            return None

        now = datetime.utcnow()
        if now >= self.end_date:
            return 0

        remaining = self.end_date - now
        return int(remaining.total_seconds() / 3600)

    def is_active(self) -> bool:
        """Check if tournament is currently active"""
        return self.status == "active"

    def can_join_teams(self) -> bool:
        """Check if teams can still join"""
        if self.status != "upcoming":
            return False

        max_teams = self.rules.get("max_teams", 10)
        return len(self.teams) < max_teams

    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """Get enhanced tournament statistics"""
        stats = self.statistics.copy()

        if self.current_standings:
            total_games = sum(s.get("games_played", 0) for s in self.current_standings)
            total_challenges = sum(s.get("challenges_won", 0) for s in self.current_standings)
            total_score = sum(s.get("score", 0) for s in self.current_standings)

            stats.update({
                "total_games_played": total_games,
                "total_challenges_completed": total_challenges,
                "total_points_awarded": total_score,
                "average_score_per_team": total_score / len(self.teams) if self.teams else 0,
                "most_active_team": self._get_most_active_team(),
                "closest_competition": self._calculate_competition_closeness()
            })

        return stats

    def _get_most_active_team(self) -> Optional[str]:
        """Get the most active team by games played"""
        if not self.current_standings:
            return None

        most_active = max(
            self.current_standings,
            key=lambda x: x.get("games_played", 0) + x.get("challenges_won", 0) * 2
        )
        return most_active["team_id"]

    def _calculate_competition_closeness(self) -> float:
        """Calculate how close the competition is (lower = closer)"""
        if len(self.current_standings) < 2:
            return 0.0

        scores = [s.get("score", 0) for s in self.current_standings]
        scores.sort(reverse=True)

        # Calculate average difference between adjacent positions
        total_diff = sum(scores[i] - scores[i + 1] for i in range(len(scores) - 1))
        avg_diff = total_diff / (len(scores) - 1) if len(scores) > 1 else 0

        # Return as percentage of leader's score
        leader_score = scores[0] if scores else 1
        return (avg_diff / leader_score * 100) if leader_score > 0 else 0

    @staticmethod
    def create_seasonal_war(teams: List[str], name: str = None, duration_days: int = 30,
                          created_by: str = None) -> 'TeamTournament':
        """Create a seasonal war tournament"""
        if not name:
            name = f"Seasonal War {datetime.utcnow().strftime('%B %Y')}"

        end_date = datetime.utcnow() + timedelta(days=duration_days)

        return TeamTournament(
            name=name,
            tournament_type="seasonal_war",
            teams=teams,
            end_date=end_date,
            description=f"Epic {duration_days}-day battle between global teams",
            rules={
                "max_teams": len(teams),
                "duration_days": duration_days,
                "auto_assign_users": True,
                "scoring_method": "weighted"
            },
            scoring_config={
                "individual_weight": 0.7,
                "challenge_weight": 1.3,
                "bonus_multipliers": {
                    "weekend": 1.2,
                    "daily_streak": 1.1,
                    "first_victory": 1.5
                }
            },
            prizes={
                "1st_place": {"credits": 1000, "achievement": "seasonal_champion"},
                "2nd_place": {"credits": 750, "achievement": "seasonal_runner_up"},
                "3rd_place": {"credits": 500, "achievement": "seasonal_bronze"},
                "participation": {"credits": 100, "achievement": "seasonal_participant"}
            },
            created_by=created_by
        )

    @staticmethod
    def create_monthly_battle(teams: List[str], name: str = None,
                            created_by: str = None) -> 'TeamTournament':
        """Create a monthly battle tournament"""
        if not name:
            name = f"Monthly Battle {datetime.utcnow().strftime('%B %Y')}"

        # Monthly battle lasts until end of month
        now = datetime.utcnow()
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(seconds=1)

        return TeamTournament(
            name=name,
            tournament_type="monthly_battle",
            teams=teams,
            end_date=end_date,
            description="Monthly competition between teams",
            rules={
                "max_teams": len(teams),
                "auto_assign_users": True,
                "scoring_method": "cumulative"
            },
            scoring_config={
                "individual_weight": 1.0,
                "challenge_weight": 1.5,
                "bonus_multipliers": {
                    "weekend": 1.1,
                    "perfect_week": 2.0
                }
            },
            prizes={
                "1st_place": {"credits": 500, "achievement": "monthly_champion"},
                "participation": {"credits": 50, "achievement": "monthly_participant"}
            },
            created_by=created_by
        )

    def __str__(self) -> str:
        return f"TeamTournament(id={self._id}, name={self.name}, status={self.status}, teams={len(self.teams)})"

    def __repr__(self) -> str:
        return self.__str__()