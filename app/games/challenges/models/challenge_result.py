from datetime import datetime
from typing import Dict, Any, Optional, List
from bson import ObjectId
from dataclasses import dataclass, field

@dataclass
class ChallengeResult:
    """ChallengeResult model representing detailed results of a completed challenge"""
    challenge_id: str
    game_id: str
    challenge_type: str  # '1v1', 'NvN', 'cross_game'
    total_participants: int
    results: List[Dict[str, Any]] = field(default_factory=list)
    winner_ids: List[str] = field(default_factory=list)
    challenge_duration_seconds: int = 0
    completed_at: datetime = field(default_factory=datetime.utcnow)
    scoring_method: str = "raw_score"  # 'raw_score', 'normalized', 'time_based'
    team_results: Dict[str, Any] = field(default_factory=dict)  # For team tournaments
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    bonus_points: Dict[str, int] = field(default_factory=dict)  # User ID -> bonus points
    metadata: Dict[str, Any] = field(default_factory=dict)
    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the challenge result to a dictionary for MongoDB storage"""
        data = {
            "challenge_id": self.challenge_id,
            "game_id": self.game_id,
            "challenge_type": self.challenge_type,
            "total_participants": self.total_participants,
            "results": self.results,
            "winner_ids": self.winner_ids,
            "challenge_duration_seconds": self.challenge_duration_seconds,
            "completed_at": self.completed_at,
            "scoring_method": self.scoring_method,
            "team_results": self.team_results,
            "performance_metrics": self.performance_metrics,
            "bonus_points": self.bonus_points,
            "metadata": self.metadata
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChallengeResult':
        """Create a ChallengeResult instance from a dictionary"""
        result = cls(
            challenge_id=data.get("challenge_id", ""),
            game_id=data.get("game_id", ""),
            challenge_type=data.get("challenge_type", "1v1"),
            total_participants=data.get("total_participants", 0),
            results=data.get("results", []),
            winner_ids=data.get("winner_ids", []),
            challenge_duration_seconds=data.get("challenge_duration_seconds", 0),
            completed_at=data.get("completed_at", datetime.utcnow()),
            scoring_method=data.get("scoring_method", "raw_score"),
            team_results=data.get("team_results", {}),
            performance_metrics=data.get("performance_metrics", {}),
            bonus_points=data.get("bonus_points", {}),
            metadata=data.get("metadata", {})
        )

        if "_id" in data:
            result._id = data["_id"]

        return result

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the challenge result to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "challenge_id": self.challenge_id,
            "game_id": self.game_id,
            "challenge_type": self.challenge_type,
            "total_participants": self.total_participants,
            "results": self.results,
            "winner_ids": self.winner_ids,
            "challenge_duration_seconds": self.challenge_duration_seconds,
            "completed_at": self.completed_at.isoformat(),
            "scoring_method": self.scoring_method,
            "team_results": self.team_results,
            "performance_metrics": self.performance_metrics,
            "bonus_points": self.bonus_points,
            "metadata": self.metadata,
            "leaderboard": self.get_leaderboard(),
            "statistics": self.get_statistics()
        }

    def add_result(self, user_id: str, score: int, game_session_id: str = None,
                  play_duration_seconds: int = None, additional_data: Dict[str, Any] = None) -> None:
        """Add a participant result"""
        result = {
            "user_id": user_id,
            "score": score,
            "position": 0,  # Will be calculated later
            "game_session_id": game_session_id,
            "play_duration_seconds": play_duration_seconds,
            "points_earned": 0,  # Will be calculated
            "bonus_points": self.bonus_points.get(user_id, 0),
            "total_points": 0,  # Will be calculated
            **(additional_data or {})
        }

        # Remove existing result for this user
        self.results = [r for r in self.results if r.get("user_id") != user_id]
        self.results.append(result)

    def calculate_positions(self) -> None:
        """Calculate positions based on scores"""
        # Sort results by score (descending)
        sorted_results = sorted(self.results, key=lambda x: x.get("score", 0), reverse=True)

        # Assign positions
        for i, result in enumerate(sorted_results):
            result["position"] = i + 1

        # Determine winners (all participants with highest score)
        if sorted_results:
            highest_score = sorted_results[0].get("score", 0)
            self.winner_ids = [
                r["user_id"] for r in sorted_results
                if r.get("score", 0) == highest_score
            ]

        # Update results with calculated positions
        self.results = sorted_results

    def calculate_points(self, points_distribution: Dict[int, int] = None) -> None:
        """Calculate points earned based on positions"""
        if not points_distribution:
            # Default point distribution
            points_distribution = {
                1: 100,  # 1st place
                2: 75,   # 2nd place
                3: 50,   # 3rd place
                4: 25,   # 4th place
            }

        for result in self.results:
            position = result.get("position", 0)
            base_points = points_distribution.get(position, 10)  # Default 10 points for participation

            # Add bonus points
            bonus = result.get("bonus_points", 0)
            total_points = base_points + bonus

            result["points_earned"] = base_points
            result["total_points"] = total_points

    def calculate_team_contributions(self, team_assignments: Dict[str, str]) -> None:
        """Calculate team score contributions if participants are in teams"""
        team_scores = {}
        team_participants = {}

        for result in self.results:
            user_id = result["user_id"]
            team_id = team_assignments.get(user_id)

            if team_id:
                if team_id not in team_scores:
                    team_scores[team_id] = 0
                    team_participants[team_id] = []

                team_scores[team_id] += result.get("total_points", 0)
                team_participants[team_id].append({
                    "user_id": user_id,
                    "score": result.get("score", 0),
                    "points": result.get("total_points", 0),
                    "position": result.get("position", 0)
                })

        self.team_results = {
            "team_scores": team_scores,
            "team_participants": team_participants,
            "winning_team": max(team_scores.keys(), key=lambda k: team_scores[k]) if team_scores else None
        }

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get formatted leaderboard"""
        return sorted(self.results, key=lambda x: x.get("position", 999))

    def get_statistics(self) -> Dict[str, Any]:
        """Get challenge statistics"""
        if not self.results:
            return {}

        scores = [r.get("score", 0) for r in self.results]
        durations = [r.get("play_duration_seconds", 0) for r in self.results if r.get("play_duration_seconds")]

        stats = {
            "total_participants": len(self.results),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "score_range": max(scores) - min(scores) if scores else 0,
            "challenge_duration_minutes": self.challenge_duration_seconds / 60,
        }

        if durations:
            stats.update({
                "average_play_duration_seconds": sum(durations) / len(durations),
                "fastest_completion_seconds": min(durations),
                "slowest_completion_seconds": max(durations)
            })

        return stats

    def get_user_result(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get result for a specific user"""
        for result in self.results:
            if result.get("user_id") == user_id:
                return result
        return None

    def add_performance_metric(self, metric_name: str, value: Any) -> None:
        """Add a performance metric"""
        self.performance_metrics[metric_name] = value

    def add_bonus_points(self, user_id: str, points: int, reason: str = "") -> None:
        """Add bonus points for a user"""
        if user_id not in self.bonus_points:
            self.bonus_points[user_id] = 0
        self.bonus_points[user_id] += points

        # Update metadata with reason
        if "bonus_reasons" not in self.metadata:
            self.metadata["bonus_reasons"] = {}
        if user_id not in self.metadata["bonus_reasons"]:
            self.metadata["bonus_reasons"][user_id] = []
        self.metadata["bonus_reasons"][user_id].append({
            "points": points,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

    @staticmethod
    def create_from_challenge(challenge, participants: List[Dict[str, Any]]) -> 'ChallengeResult':
        """Create a ChallengeResult from a completed challenge"""
        from ..models.challenge import Challenge

        if isinstance(challenge, Challenge):
            challenge_duration = challenge.get_duration_seconds() or 0

            result = ChallengeResult(
                challenge_id=challenge.challenge_id,
                game_id=challenge.game_id,
                challenge_type=challenge.challenge_type,
                total_participants=len(participants),
                challenge_duration_seconds=challenge_duration,
                completed_at=challenge.completed_at or datetime.utcnow()
            )

            # Add participant results
            for participant in participants:
                result.add_result(
                    user_id=participant.get("user_id"),
                    score=participant.get("score", 0),
                    game_session_id=participant.get("game_session_id"),
                    play_duration_seconds=participant.get("play_duration_seconds"),
                    additional_data={
                        "response_time_seconds": participant.get("response_time_seconds"),
                        "completion_time": participant.get("completed_at")
                    }
                )

            # Calculate positions and points
            result.calculate_positions()
            result.calculate_points()

            return result

        return None

    def __str__(self) -> str:
        return f"ChallengeResult(challenge={self.challenge_id}, participants={self.total_participants}, winners={len(self.winner_ids)})"

    def __repr__(self) -> str:
        return self.__str__()