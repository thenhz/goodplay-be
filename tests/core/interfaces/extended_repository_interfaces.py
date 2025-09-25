"""
Extended Repository Interfaces for GoodPlay Game System

Additional repository interfaces for specialized game features including
challenges, teams, modes, and leaderboards.
"""
from abc import abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base_interfaces import IBaseRepository


class IChallengeRepository(IBaseRepository['Challenge']):
    """
    Abstract interface for Challenge repository operations.

    Manages player challenges, matchmaking, and challenge lifecycle.
    """

    @abstractmethod
    def create_challenge(self, challenge: 'Challenge') -> str:
        """
        Create a new challenge.

        Args:
            challenge: Challenge instance to create

        Returns:
            str: Created challenge's ID
        """
        pass

    @abstractmethod
    def get_challenge_by_id(self, challenge_id: str) -> Optional['Challenge']:
        """
        Get a challenge by its ID.

        Args:
            challenge_id: Challenge's unique identifier

        Returns:
            Optional[Challenge]: Challenge if found, None otherwise
        """
        pass

    @abstractmethod
    def get_public_challenges(
        self,
        game_id: Optional[str] = None,
        skill_level: Optional[str] = None,
        limit: int = 20
    ) -> List['Challenge']:
        """
        Get public challenges available for joining.

        Args:
            game_id: Filter by specific game
            skill_level: Filter by skill level
            limit: Maximum number of challenges to return

        Returns:
            List[Challenge]: Available public challenges
        """
        pass

    @abstractmethod
    def get_user_challenges(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List['Challenge']:
        """
        Get challenges involving a specific user.

        Args:
            user_id: User's unique identifier
            status: Filter by challenge status
            limit: Maximum number of challenges to return

        Returns:
            List[Challenge]: User's challenges
        """
        pass

    @abstractmethod
    def update_challenge_status(self, challenge_id: str, status: str) -> bool:
        """
        Update challenge status.

        Args:
            challenge_id: Challenge's unique identifier
            status: New challenge status

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    def add_participant(
        self,
        challenge_id: str,
        user_id: str,
        participant_data: Dict[str, Any]
    ) -> bool:
        """
        Add a participant to a challenge.

        Args:
            challenge_id: Challenge's unique identifier
            user_id: User's unique identifier
            participant_data: Participant-specific data

        Returns:
            bool: True if participant added successfully
        """
        pass

    @abstractmethod
    def get_matchmaking_candidates(
        self,
        user_id: str,
        game_id: str,
        skill_level: str
    ) -> List['Challenge']:
        """
        Get challenges suitable for matchmaking.

        Args:
            user_id: User's unique identifier
            game_id: Game's unique identifier
            skill_level: User's skill level

        Returns:
            List[Challenge]: Suitable challenges for matchmaking
        """
        pass


class ITeamRepository(IBaseRepository['GlobalTeam']):
    """
    Abstract interface for Team repository operations.

    Manages global teams, team members, and team tournaments.
    """

    @abstractmethod
    def create_team(self, team: 'GlobalTeam') -> str:
        """
        Create a new global team.

        Args:
            team: GlobalTeam instance to create

        Returns:
            str: Created team's ID
        """
        pass

    @abstractmethod
    def get_team_by_id(self, team_id: str) -> Optional['GlobalTeam']:
        """
        Get a team by its ID.

        Args:
            team_id: Team's unique identifier

        Returns:
            Optional[GlobalTeam]: Team if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all_teams(self, active_only: bool = True) -> List['GlobalTeam']:
        """
        Get all global teams.

        Args:
            active_only: If True, only return active teams

        Returns:
            List[GlobalTeam]: All teams
        """
        pass

    @abstractmethod
    def add_team_member(self, team_id: str, user_id: str, role: str = "member") -> str:
        """
        Add a member to a team.

        Args:
            team_id: Team's unique identifier
            user_id: User's unique identifier
            role: Member role (member, veteran, captain)

        Returns:
            str: Team member record ID
        """
        pass

    @abstractmethod
    def get_team_members(
        self,
        team_id: str,
        role: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List['TeamMember']:
        """
        Get team members.

        Args:
            team_id: Team's unique identifier
            role: Filter by member role
            limit: Maximum number of members to return

        Returns:
            List[TeamMember]: Team members
        """
        pass

    @abstractmethod
    def update_team_score(self, team_id: str, score_delta: int) -> bool:
        """
        Update team's total score.

        Args:
            team_id: Team's unique identifier
            score_delta: Score amount to add

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    def get_team_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get team leaderboard data.

        Args:
            limit: Maximum number of teams to return

        Returns:
            List[Dict[str, Any]]: Team leaderboard data
        """
        pass

    @abstractmethod
    def assign_user_to_team(self, user_id: str) -> Optional[str]:
        """
        Automatically assign a user to a balanced team.

        Args:
            user_id: User's unique identifier

        Returns:
            Optional[str]: Assigned team ID if successful
        """
        pass


class IGameModeRepository(IBaseRepository['GameMode']):
    """
    Abstract interface for Game Mode repository operations.

    Manages temporary game modes and their scheduling.
    """

    @abstractmethod
    def create_game_mode(self, mode: 'GameMode') -> str:
        """
        Create a new game mode.

        Args:
            mode: GameMode instance to create

        Returns:
            str: Created mode's ID
        """
        pass

    @abstractmethod
    def get_active_modes(self) -> List['GameMode']:
        """
        Get all currently active game modes.

        Returns:
            List[GameMode]: Active game modes
        """
        pass

    @abstractmethod
    def get_mode_by_type(self, mode_type: str) -> Optional['GameMode']:
        """
        Get a game mode by its type.

        Args:
            mode_type: Mode type (normal, challenge, tournament)

        Returns:
            Optional[GameMode]: Game mode if found
        """
        pass

    @abstractmethod
    def activate_mode(self, mode_id: str, duration_hours: Optional[int] = None) -> bool:
        """
        Activate a game mode.

        Args:
            mode_id: Mode's unique identifier
            duration_hours: How long to keep mode active

        Returns:
            bool: True if activated successfully
        """
        pass

    @abstractmethod
    def deactivate_mode(self, mode_id: str) -> bool:
        """
        Deactivate a game mode.

        Args:
            mode_id: Mode's unique identifier

        Returns:
            bool: True if deactivated successfully
        """
        pass

    @abstractmethod
    def get_expired_modes(self) -> List['GameMode']:
        """
        Get modes that have expired and should be deactivated.

        Returns:
            List[GameMode]: Expired game modes
        """
        pass


class ILeaderboardRepository(IBaseRepository['LeaderboardEntry']):
    """
    Abstract interface for Leaderboard repository operations.

    Manages various leaderboards and rankings across the platform.
    """

    @abstractmethod
    def create_leaderboard_entry(self, entry: 'LeaderboardEntry') -> str:
        """
        Create a new leaderboard entry.

        Args:
            entry: LeaderboardEntry instance to create

        Returns:
            str: Created entry's ID
        """
        pass

    @abstractmethod
    def get_global_leaderboard(
        self,
        period: str = "weekly",
        limit: int = 50
    ) -> List['LeaderboardEntry']:
        """
        Get global leaderboard for a period.

        Args:
            period: Time period (daily, weekly, monthly, all-time)
            limit: Maximum number of entries to return

        Returns:
            List[LeaderboardEntry]: Leaderboard entries
        """
        pass

    @abstractmethod
    def get_game_leaderboard(
        self,
        game_id: str,
        period: str = "weekly",
        limit: int = 50
    ) -> List['LeaderboardEntry']:
        """
        Get leaderboard for a specific game.

        Args:
            game_id: Game's unique identifier
            period: Time period
            limit: Maximum number of entries to return

        Returns:
            List[LeaderboardEntry]: Game-specific leaderboard entries
        """
        pass

    @abstractmethod
    def get_user_ranking(
        self,
        user_id: str,
        leaderboard_type: str = "global",
        period: str = "weekly"
    ) -> Optional[Dict[str, Any]]:
        """
        Get a user's current ranking.

        Args:
            user_id: User's unique identifier
            leaderboard_type: Type of leaderboard
            period: Time period

        Returns:
            Optional[Dict[str, Any]]: User's ranking information
        """
        pass

    @abstractmethod
    def update_user_score(
        self,
        user_id: str,
        score_delta: int,
        leaderboard_type: str = "global"
    ) -> bool:
        """
        Update a user's score in leaderboards.

        Args:
            user_id: User's unique identifier
            score_delta: Score change amount
            leaderboard_type: Type of leaderboard to update

        Returns:
            bool: True if updated successfully
        """
        pass

    @abstractmethod
    def reset_period_leaderboard(self, period: str) -> bool:
        """
        Reset leaderboard for a specific period.

        Args:
            period: Time period to reset

        Returns:
            bool: True if reset successfully
        """
        pass


class ITournamentRepository(IBaseRepository['Tournament']):
    """
    Abstract interface for Tournament repository operations.

    Manages team tournaments, seasonal wars, and competition events.
    """

    @abstractmethod
    def create_tournament(self, tournament: 'Tournament') -> str:
        """
        Create a new tournament.

        Args:
            tournament: Tournament instance to create

        Returns:
            str: Created tournament's ID
        """
        pass

    @abstractmethod
    def get_active_tournaments(self) -> List['Tournament']:
        """
        Get all currently active tournaments.

        Returns:
            List[Tournament]: Active tournaments
        """
        pass

    @abstractmethod
    def get_tournament_by_type(
        self,
        tournament_type: str,
        active_only: bool = True
    ) -> Optional['Tournament']:
        """
        Get tournament by type.

        Args:
            tournament_type: Tournament type (seasonal_war, monthly_battle, special_event)
            active_only: If True, only return active tournaments

        Returns:
            Optional[Tournament]: Tournament if found
        """
        pass

    @abstractmethod
    def add_team_to_tournament(self, tournament_id: str, team_id: str) -> bool:
        """
        Add a team to a tournament.

        Args:
            tournament_id: Tournament's unique identifier
            team_id: Team's unique identifier

        Returns:
            bool: True if team added successfully
        """
        pass

    @abstractmethod
    def update_tournament_scores(
        self,
        tournament_id: str,
        team_scores: Dict[str, int]
    ) -> bool:
        """
        Update team scores for a tournament.

        Args:
            tournament_id: Tournament's unique identifier
            team_scores: Dictionary mapping team IDs to scores

        Returns:
            bool: True if scores updated successfully
        """
        pass

    @abstractmethod
    def get_tournament_standings(self, tournament_id: str) -> List[Dict[str, Any]]:
        """
        Get current tournament standings.

        Args:
            tournament_id: Tournament's unique identifier

        Returns:
            List[Dict[str, Any]]: Tournament standings with team rankings
        """
        pass


# Forward declarations for type hints
if False:  # TYPE_CHECKING equivalent
    from app.games.challenges.models.challenge import Challenge
    from app.games.teams.models.global_team import GlobalTeam
    from app.games.teams.models.team_member import TeamMember
    from app.games.modes.models.game_mode import GameMode
    from app.social.leaderboards.models.leaderboard_entry import LeaderboardEntry
    from app.games.teams.models.team_tournament import Tournament