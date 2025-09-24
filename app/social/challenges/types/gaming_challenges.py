from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.social.challenges.models.social_challenge import SocialChallenge, ChallengeRules, ChallengeRewards


class GamingChallengeTypes:
    """Factory and configuration for gaming-related social challenges"""

    @staticmethod
    def create_speed_run_challenge(creator_id: str, title: str, game_id: str = None,
                                 target_time_seconds: int = 300, duration_hours: int = 72) -> SocialChallenge:
        """Create a speed run challenge among friends"""
        rules = ChallengeRules(
            target_metric="game_completion_time",
            target_value=target_time_seconds,
            time_limit_hours=duration_hours,
            min_participants=2,
            max_participants=8,
            requires_friends=True,
            allow_public_join=False,
            scoring_method="lowest",  # Fastest time wins
            difficulty_multiplier=1.5
        )

        rewards = ChallengeRewards(
            winner_credits=150,
            participant_credits=50,
            winner_badges=["speed_demon", "racing_champion"],
            participant_badges=["speed_runner"],
            social_bonus_multiplier=1.3
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Race to complete the game in under {target_time_seconds} seconds! Fastest time wins!",
            challenge_type="gaming_social",
            challenge_category="speed_run",
            difficulty_level=3,
            tags=["speed", "racing", "competition", "gaming"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            friends_only=True
        )

        return challenge

    @staticmethod
    def create_high_score_challenge(creator_id: str, title: str, game_id: str = None,
                                  target_score: int = 1000, duration_hours: int = 168) -> SocialChallenge:
        """Create a high score challenge among friends"""
        rules = ChallengeRules(
            target_metric="game_high_score",
            target_value=target_score,
            time_limit_hours=duration_hours,
            min_participants=2,
            max_participants=10,
            requires_friends=True,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.2
        )

        rewards = ChallengeRewards(
            winner_credits=120,
            participant_credits=40,
            winner_badges=["high_score_hero", "point_master"],
            participant_badges=["score_chaser"],
            social_bonus_multiplier=1.4
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Compete to reach the highest score! Target: {target_score:,} points",
            challenge_type="gaming_social",
            challenge_category="high_score",
            difficulty_level=2,
            tags=["high_score", "points", "competition", "skill"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            is_public=True,
            friends_only=False
        )

        return challenge

    @staticmethod
    def create_endurance_challenge(creator_id: str, title: str, game_id: str = None,
                                 target_minutes: int = 60, duration_hours: int = 168) -> SocialChallenge:
        """Create an endurance gaming challenge"""
        rules = ChallengeRules(
            target_metric="game_play_duration",
            target_value=target_minutes,
            time_limit_hours=duration_hours,
            min_participants=3,
            max_participants=12,
            requires_friends=True,
            allow_public_join=True,
            scoring_method="highest",  # Most time played wins
            difficulty_multiplier=1.1
        )

        rewards = ChallengeRewards(
            winner_credits=100,
            participant_credits=35,
            winner_badges=["endurance_champion", "time_master"],
            participant_badges=["dedicated_player"],
            social_bonus_multiplier=1.2
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"See who can play the longest! Target: {target_minutes} minutes of continuous play",
            challenge_type="gaming_social",
            challenge_category="endurance",
            difficulty_level=2,
            tags=["endurance", "time", "dedication", "stamina"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            is_public=True,
            friends_only=False
        )

        return challenge

    @staticmethod
    def create_variety_challenge(creator_id: str, title: str, target_games: int = 5,
                               duration_hours: int = 168) -> SocialChallenge:
        """Create a game variety challenge"""
        rules = ChallengeRules(
            target_metric="games_played_count",
            target_value=target_games,
            time_limit_hours=duration_hours,
            min_participants=2,
            max_participants=15,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",  # Most games played wins
            difficulty_multiplier=1.3
        )

        rewards = ChallengeRewards(
            winner_credits=130,
            participant_credits=45,
            winner_badges=["game_explorer", "variety_master"],
            participant_badges=["explorer"],
            social_bonus_multiplier=1.6  # Higher social bonus for variety
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Play {target_games} different games this week! Variety is the spice of life!",
            challenge_type="gaming_social",
            challenge_category="variety",
            difficulty_level=2,
            tags=["variety", "exploration", "discovery", "games"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            is_public=True,
            friends_only=False
        )

        return challenge

    @staticmethod
    def create_perfect_game_challenge(creator_id: str, title: str, game_id: str = None,
                                    duration_hours: int = 72) -> SocialChallenge:
        """Create a perfect game challenge (complete without errors)"""
        rules = ChallengeRules(
            target_metric="perfect_completion",
            target_value=1,  # One perfect completion
            time_limit_hours=duration_hours,
            min_participants=2,
            max_participants=6,
            requires_friends=True,
            allow_public_join=False,
            scoring_method="target",  # First to achieve perfect score wins
            difficulty_multiplier=2.0  # High difficulty
        )

        rewards = ChallengeRewards(
            winner_credits=200,
            participant_credits=60,
            winner_badges=["perfectionist", "flawless_victory"],
            participant_badges=["precision_player"],
            social_bonus_multiplier=1.1
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description="Complete the game with perfect execution - no mistakes allowed!",
            challenge_type="gaming_social",
            challenge_category="perfect_game",
            difficulty_level=4,
            tags=["perfect", "precision", "skill", "mastery"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            friends_only=True
        )

        return challenge

    @staticmethod
    def create_team_coordination_challenge(creator_id: str, title: str, team_size: int = 4,
                                         target_score: int = 500, duration_hours: int = 96) -> SocialChallenge:
        """Create a team coordination challenge"""
        rules = ChallengeRules(
            target_metric="team_coordination_score",
            target_value=target_score,
            time_limit_hours=duration_hours,
            min_participants=team_size,
            max_participants=team_size * 3,  # Multiple teams
            requires_friends=True,
            allow_public_join=False,
            scoring_method="collective",  # Team effort matters
            difficulty_multiplier=1.4
        )

        rewards = ChallengeRewards(
            winner_credits=160,
            participant_credits=55,
            winner_badges=["team_captain", "coordination_master"],
            participant_badges=["team_player"],
            social_bonus_multiplier=2.0  # High social bonus for teamwork
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Work together as a team to achieve {target_score} coordination points!",
            challenge_type="gaming_social",
            challenge_category="team_coordination",
            difficulty_level=3,
            tags=["teamwork", "coordination", "cooperation", "strategy"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            friends_only=True,
            allow_cheering=True,
            allow_comments=True
        )

        return challenge

    @staticmethod
    def create_daily_quest_challenge(creator_id: str, title: str, quest_count: int = 7,
                                   duration_hours: int = 168) -> SocialChallenge:
        """Create a daily quest completion challenge"""
        rules = ChallengeRules(
            target_metric="daily_quests_completed",
            target_value=quest_count,
            time_limit_hours=duration_hours,
            min_participants=3,
            max_participants=20,
            requires_friends=False,
            allow_public_join=True,
            scoring_method="highest",
            difficulty_multiplier=1.1
        )

        rewards = ChallengeRewards(
            winner_credits=110,
            participant_credits=30,
            winner_badges=["quest_master", "daily_champion"],
            participant_badges=["quest_completer"],
            social_bonus_multiplier=1.3
        )

        challenge = SocialChallenge(
            creator_id=creator_id,
            title=title,
            description=f"Complete {quest_count} daily quests this week! Consistency is key!",
            challenge_type="gaming_social",
            challenge_category="daily_quest",
            difficulty_level=2,
            tags=["daily", "quests", "consistency", "routine"],
            rules=rules,
            rewards=rewards,
            end_date=datetime.utcnow() + timedelta(hours=duration_hours),
            is_public=True,
            friends_only=False
        )

        return challenge

    @staticmethod
    def get_gaming_challenge_configurations() -> Dict[str, Dict[str, Any]]:
        """Get all gaming challenge type configurations"""
        return {
            "speed_run": {
                "name": "Speed Run Challenge",
                "description": "Race to complete games in the fastest time",
                "difficulty": "Hard",
                "typical_duration": "3 days",
                "min_participants": 2,
                "max_participants": 8,
                "tags": ["speed", "racing", "skill", "timing"]
            },
            "high_score": {
                "name": "High Score Challenge",
                "description": "Compete for the highest game scores",
                "difficulty": "Medium",
                "typical_duration": "1 week",
                "min_participants": 2,
                "max_participants": 10,
                "tags": ["score", "points", "skill", "competition"]
            },
            "endurance": {
                "name": "Endurance Challenge",
                "description": "See who can play the longest",
                "difficulty": "Medium",
                "typical_duration": "1 week",
                "min_participants": 3,
                "max_participants": 12,
                "tags": ["endurance", "time", "dedication"]
            },
            "variety": {
                "name": "Game Variety Challenge",
                "description": "Play the most different games",
                "difficulty": "Easy",
                "typical_duration": "1 week",
                "min_participants": 2,
                "max_participants": 15,
                "tags": ["variety", "exploration", "discovery"]
            },
            "perfect_game": {
                "name": "Perfect Game Challenge",
                "description": "Complete games with perfect execution",
                "difficulty": "Very Hard",
                "typical_duration": "3 days",
                "min_participants": 2,
                "max_participants": 6,
                "tags": ["perfect", "precision", "mastery"]
            },
            "team_coordination": {
                "name": "Team Coordination Challenge",
                "description": "Work together for team objectives",
                "difficulty": "Hard",
                "typical_duration": "4 days",
                "min_participants": 4,
                "max_participants": 12,
                "tags": ["teamwork", "coordination", "strategy"]
            },
            "daily_quest": {
                "name": "Daily Quest Challenge",
                "description": "Complete daily objectives consistently",
                "difficulty": "Easy",
                "typical_duration": "1 week",
                "min_participants": 3,
                "max_participants": 20,
                "tags": ["daily", "consistency", "routine"]
            }
        }

    @staticmethod
    def get_category_metrics() -> Dict[str, Dict[str, Any]]:
        """Get metrics configuration for each gaming challenge category"""
        return {
            "speed_run": {
                "primary_metric": "completion_time_seconds",
                "secondary_metrics": ["attempts_count", "best_time"],
                "scoring": "lowest_wins",
                "units": "seconds"
            },
            "high_score": {
                "primary_metric": "highest_score",
                "secondary_metrics": ["games_played", "average_score"],
                "scoring": "highest_wins",
                "units": "points"
            },
            "endurance": {
                "primary_metric": "total_play_time_minutes",
                "secondary_metrics": ["longest_session", "session_count"],
                "scoring": "highest_wins",
                "units": "minutes"
            },
            "variety": {
                "primary_metric": "unique_games_played",
                "secondary_metrics": ["total_sessions", "completion_rate"],
                "scoring": "highest_wins",
                "units": "games"
            },
            "perfect_game": {
                "primary_metric": "perfect_completions",
                "secondary_metrics": ["attempts", "accuracy_percentage"],
                "scoring": "first_to_achieve",
                "units": "completions"
            },
            "team_coordination": {
                "primary_metric": "team_score",
                "secondary_metrics": ["individual_contribution", "coordination_rating"],
                "scoring": "collective_highest",
                "units": "points"
            },
            "daily_quest": {
                "primary_metric": "quests_completed",
                "secondary_metrics": ["streak_days", "completion_rate"],
                "scoring": "highest_wins",
                "units": "quests"
            }
        }