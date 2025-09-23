from typing import Tuple, Optional, Dict, Any, List
from flask import current_app
from datetime import datetime, timedelta
import random

from ..repositories.global_team_repository import GlobalTeamRepository
from ..repositories.team_member_repository import TeamMemberRepository
from ..repositories.team_tournament_repository import TeamTournamentRepository
from ..models.global_team import GlobalTeam
from ..models.team_member import TeamMember
from ..models.team_tournament import TeamTournament

class TeamManager:
    """Service for managing global teams and team assignments"""

    def __init__(self):
        self.team_repository = GlobalTeamRepository()
        self.member_repository = TeamMemberRepository()
        self.tournament_repository = TeamTournamentRepository()

    def get_all_teams(self, active_only: bool = True) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get all global teams"""
        try:
            teams = self.team_repository.get_all_teams(active_only)
            teams_data = [team.to_api_dict() for team in teams]

            return True, "TEAMS_RETRIEVED_SUCCESSFULLY", {
                "teams": teams_data,
                "count": len(teams_data)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get teams: {str(e)}")
            return False, "FAILED_TO_GET_TEAMS", None

    def get_team_leaderboard(self, limit: int = 10) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get team leaderboard"""
        try:
            teams = self.team_repository.get_team_leaderboard(limit)
            leaderboard = []

            for i, team in enumerate(teams):
                team_data = team.to_api_dict()
                team_data["rank"] = i + 1
                leaderboard.append(team_data)

            return True, "LEADERBOARD_RETRIEVED_SUCCESSFULLY", {
                "leaderboard": leaderboard,
                "count": len(leaderboard)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get leaderboard: {str(e)}")
            return False, "FAILED_TO_GET_LEADERBOARD", None

    def get_user_team(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get user's current team"""
        try:
            member = self.member_repository.get_user_team(user_id)
            if not member:
                return False, "USER_NOT_IN_TEAM", None

            team = self.team_repository.get_team_by_team_id(member.team_id)
            if not team:
                return False, "TEAM_NOT_FOUND", None

            return True, "USER_TEAM_RETRIEVED", {
                "team": team.to_api_dict(),
                "membership": member.to_api_dict()
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get user team: {str(e)}")
            return False, "FAILED_TO_GET_USER_TEAM", None

    def assign_user_to_team(self, user_id: str, team_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Assign user to a team (automatic if team_id not specified)"""
        try:
            # Check if user is already in a team
            existing_member = self.member_repository.get_user_team(user_id)
            if existing_member:
                return False, "USER_ALREADY_IN_TEAM", {
                    "current_team_id": existing_member.team_id
                }

            # If no specific team requested, auto-assign
            if not team_id:
                team_id = self._find_best_team_for_user(user_id)
                if not team_id:
                    return False, "NO_AVAILABLE_TEAMS", None

            # Verify team exists
            team = self.team_repository.get_team_by_team_id(team_id)
            if not team:
                return False, "TEAM_NOT_FOUND", None

            if not team.is_recruiting():
                return False, "TEAM_NOT_RECRUITING", None

            # Assign user to team
            success = self.member_repository.assign_user_to_team(user_id, team_id)
            if not success:
                return False, "FAILED_TO_ASSIGN_USER", None

            # Update team member count
            self.team_repository.update_member_count(team_id, 1)

            current_app.logger.info(f"User {user_id} assigned to team {team_id}")

            return True, "USER_ASSIGNED_TO_TEAM", {
                "team_id": team_id,
                "team_name": team.name
            }

        except Exception as e:
            current_app.logger.error(f"Failed to assign user to team: {str(e)}")
            return False, "FAILED_TO_ASSIGN_USER", None

    def remove_user_from_team(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Remove user from their current team"""
        try:
            member = self.member_repository.get_user_team(user_id)
            if not member:
                return False, "USER_NOT_IN_TEAM", None

            # Remove from team
            success = self.member_repository.remove_user_from_team(user_id, member.team_id)
            if not success:
                return False, "FAILED_TO_REMOVE_USER", None

            # Update team member count
            self.team_repository.update_member_count(member.team_id, -1)

            current_app.logger.info(f"User {user_id} removed from team {member.team_id}")

            return True, "USER_REMOVED_FROM_TEAM", {
                "former_team_id": member.team_id
            }

        except Exception as e:
            current_app.logger.error(f"Failed to remove user from team: {str(e)}")
            return False, "FAILED_TO_REMOVE_USER", None

    def get_team_members(self, team_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get team members with details"""
        try:
            team = self.team_repository.get_team_by_team_id(team_id)
            if not team:
                return False, "TEAM_NOT_FOUND", None

            members = self.member_repository.get_team_members(team_id)
            members_data = [member.to_api_dict() for member in members]

            # Get team statistics
            stats = self.member_repository.get_team_member_statistics(team_id)

            return True, "TEAM_MEMBERS_RETRIEVED", {
                "team": team.to_api_dict(),
                "members": members_data,
                "member_count": len(members_data),
                "team_statistics": stats
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get team members: {str(e)}")
            return False, "FAILED_TO_GET_TEAM_MEMBERS", None

    def record_game_contribution(self, user_id: str, score: int, game_type: str = "individual") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Record a user's game contribution to their team"""
        try:
            member = self.member_repository.get_user_team(user_id)
            if not member:
                return False, "USER_NOT_IN_TEAM", None

            # Calculate contribution points based on score and game type
            base_points = min(score / 10, 100)  # Max 100 points per game

            if game_type == "challenge":
                contribution_points = base_points * 1.5  # Bonus for challenges
            else:
                contribution_points = base_points

            # Record in member stats
            success = self.member_repository.add_game_played(
                user_id, member.team_id, score, contribution_points
            )
            if not success:
                return False, "FAILED_TO_RECORD_CONTRIBUTION", None

            # Add to team score
            self.team_repository.update_team_score(member.team_id, contribution_points, game_type)

            # Update active tournament if exists
            active_tournament = self.tournament_repository.get_active_tournament()
            if active_tournament and member.team_id in active_tournament.teams:
                self.tournament_repository.update_team_standing(
                    active_tournament.tournament_id, member.team_id, contribution_points, "game"
                )

            return True, "CONTRIBUTION_RECORDED_SUCCESSFULLY", {
                "contribution_points": contribution_points,
                "team_id": member.team_id
            }

        except Exception as e:
            current_app.logger.error(f"Failed to record contribution: {str(e)}")
            return False, "FAILED_TO_RECORD_CONTRIBUTION", None

    def record_challenge_result(self, user_id: str, challenge_result: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Record challenge result for team contribution"""
        try:
            member = self.member_repository.get_user_team(user_id)
            if not member:
                return False, "USER_NOT_IN_TEAM", None

            # Record challenge participation
            success = self.member_repository.add_challenge_participation(
                user_id, member.team_id, challenge_result
            )
            if not success:
                return False, "FAILED_TO_RECORD_CHALLENGE_RESULT", None

            # Calculate team points from challenge
            position = challenge_result.get("position", 0)
            base_points = challenge_result.get("points_earned", 0)

            if position == 1:
                team_points = base_points * 2.0  # Winner bonus
            elif position <= 3:
                team_points = base_points * 1.5  # Top 3 bonus
            else:
                team_points = base_points

            # Add to team score
            self.team_repository.update_team_score(member.team_id, team_points, "challenge")

            # Update active tournament
            active_tournament = self.tournament_repository.get_active_tournament()
            if active_tournament and member.team_id in active_tournament.teams:
                self.tournament_repository.update_team_standing(
                    active_tournament.tournament_id, member.team_id, team_points, "challenge"
                )

            return True, "CHALLENGE_RESULT_RECORDED", {
                "team_points": team_points,
                "team_id": member.team_id
            }

        except Exception as e:
            current_app.logger.error(f"Failed to record challenge result: {str(e)}")
            return False, "FAILED_TO_RECORD_CHALLENGE_RESULT", None

    def balance_teams(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Balance team members across teams"""
        try:
            teams = self.team_repository.get_all_teams()
            if len(teams) < 2:
                return False, "INSUFFICIENT_TEAMS_FOR_BALANCING", None

            # Get all active members
            all_members = []
            for team in teams:
                members = self.member_repository.get_team_members(team.team_id)
                all_members.extend(members)

            if not all_members:
                return False, "NO_MEMBERS_TO_BALANCE", None

            # Calculate target members per team
            target_per_team = len(all_members) // len(teams)

            # Create balanced assignments
            balanced_assignments = self._create_balanced_assignments(all_members, teams, target_per_team)

            # Execute balancing
            reassigned_count = self.member_repository.balance_teams(balanced_assignments)

            # Update team member counts
            for team in teams:
                new_count = sum(1 for assignment in balanced_assignments.values() if assignment == team.team_id)
                team.current_members = new_count
                self.team_repository.update_member_count(team.team_id, new_count - team.current_members)

            current_app.logger.info(f"Balanced teams: reassigned {reassigned_count} members")

            return True, "TEAMS_BALANCED_SUCCESSFULLY", {
                "reassigned_members": reassigned_count,
                "team_distributions": {team.name: team.current_members for team in teams}
            }

        except Exception as e:
            current_app.logger.error(f"Failed to balance teams: {str(e)}")
            return False, "FAILED_TO_BALANCE_TEAMS", None

    def initialize_teams(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Initialize default teams if none exist"""
        try:
            existing_teams = self.team_repository.get_all_teams(active_only=False)
            if existing_teams:
                return True, "TEAMS_ALREADY_INITIALIZED", {
                    "teams": [team.to_api_dict() for team in existing_teams]
                }

            # Create default teams
            default_teams = self.team_repository.initialize_default_teams()
            teams_data = [team.to_api_dict() for team in default_teams]

            current_app.logger.info(f"Initialized {len(default_teams)} default teams")

            return True, "TEAMS_INITIALIZED_SUCCESSFULLY", {
                "teams": teams_data,
                "count": len(teams_data)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to initialize teams: {str(e)}")
            return False, "FAILED_TO_INITIALIZE_TEAMS", None

    def _find_best_team_for_user(self, user_id: str) -> Optional[str]:
        """Find the best team for a user based on current balance"""
        teams = self.team_repository.get_all_teams()
        if not teams:
            return None

        # Find team with least members that's still recruiting
        available_teams = [team for team in teams if team.is_recruiting()]
        if not available_teams:
            return None

        # Sort by member count (ascending) then by total score (ascending) for balance
        available_teams.sort(key=lambda t: (t.current_members, t.total_score))
        return available_teams[0].team_id

    def _create_balanced_assignments(self, members: List[TeamMember], teams: List[GlobalTeam], target_per_team: int) -> Dict[str, str]:
        """Create balanced team assignments"""
        # Sort members by contribution score for fair distribution
        sorted_members = sorted(members, key=lambda m: m.contribution_score, reverse=True)

        assignments = {}
        team_counts = {team.team_id: 0 for team in teams}

        # Distribute members round-robin style
        for i, member in enumerate(sorted_members):
            team_index = i % len(teams)
            target_team = teams[team_index]
            assignments[member.user_id] = target_team.team_id
            team_counts[target_team.team_id] += 1

        return assignments