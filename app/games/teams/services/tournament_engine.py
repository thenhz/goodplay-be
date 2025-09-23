from typing import Tuple, Optional, Dict, Any, List
from flask import current_app
from datetime import datetime, timedelta

from ..repositories.team_tournament_repository import TeamTournamentRepository
from ..repositories.global_team_repository import GlobalTeamRepository
from ..repositories.team_member_repository import TeamMemberRepository
from ..models.team_tournament import TeamTournament
from .team_manager import TeamManager

class TournamentEngine:
    """Service for managing team tournaments"""

    def __init__(self):
        self.tournament_repository = TeamTournamentRepository()
        self.team_repository = GlobalTeamRepository()
        self.member_repository = TeamMemberRepository()
        self.team_manager = TeamManager()

    def create_tournament(self, tournament_type: str, name: str = None,
                         duration_days: int = 30, team_ids: List[str] = None,
                         admin_user_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Create a new team tournament"""
        try:
            # Get teams to participate
            if not team_ids:
                teams = self.team_repository.get_all_teams()
                team_ids = [team.team_id for team in teams]

            if len(team_ids) < 2:
                return False, "INSUFFICIENT_TEAMS_FOR_TOURNAMENT", None

            # Create tournament based on type
            if tournament_type == "seasonal_war":
                tournament = TeamTournament.create_seasonal_war(
                    teams=team_ids,
                    name=name,
                    duration_days=duration_days,
                    created_by=admin_user_id
                )
            elif tournament_type == "monthly_battle":
                tournament = TeamTournament.create_monthly_battle(
                    teams=team_ids,
                    name=name,
                    created_by=admin_user_id
                )
            else:
                return False, "INVALID_TOURNAMENT_TYPE", None

            # Save tournament
            tournament_id = self.tournament_repository.create_tournament(tournament)

            current_app.logger.info(f"Created {tournament_type} tournament: {tournament.name}")

            return True, "TOURNAMENT_CREATED_SUCCESSFULLY", {
                "tournament": tournament.to_api_dict(),
                "tournament_id": tournament.tournament_id
            }

        except Exception as e:
            current_app.logger.error(f"Failed to create tournament: {str(e)}")
            return False, "FAILED_TO_CREATE_TOURNAMENT", None

    def start_tournament(self, tournament_id: str, auto_assign_users: bool = True) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Start a tournament"""
        try:
            tournament = self.tournament_repository.get_tournament_by_tournament_id(tournament_id)
            if not tournament:
                return False, "TOURNAMENT_NOT_FOUND", None

            if tournament.status != "upcoming":
                return False, "TOURNAMENT_NOT_STARTABLE", None

            # Auto-assign users to teams if requested
            if auto_assign_users:
                self._auto_assign_users_to_teams(tournament.teams)

            # Start the tournament
            success = self.tournament_repository.start_tournament(tournament_id)
            if not success:
                return False, "FAILED_TO_START_TOURNAMENT", None

            # Initialize standings
            self.tournament_repository.initialize_tournament_standings(tournament_id, tournament.teams)

            # Set tournament on teams
            for team_id in tournament.teams:
                self.team_repository.set_tournament(team_id, tournament_id)

            current_app.logger.info(f"Started tournament {tournament_id}")

            return True, "TOURNAMENT_STARTED_SUCCESSFULLY", {
                "tournament_id": tournament_id,
                "participating_teams": len(tournament.teams)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to start tournament: {str(e)}")
            return False, "FAILED_TO_START_TOURNAMENT", None

    def complete_tournament(self, tournament_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Complete a tournament and award prizes"""
        try:
            tournament = self.tournament_repository.get_tournament_by_tournament_id(tournament_id)
            if not tournament:
                return False, "TOURNAMENT_NOT_FOUND", None

            if tournament.status != "active":
                return False, "TOURNAMENT_NOT_ACTIVE", None

            # Get final standings
            leaderboard = self.tournament_repository.get_tournament_leaderboard(tournament_id)
            final_standings = [entry["team_id"] for entry in leaderboard]

            # Complete tournament
            success = self.tournament_repository.complete_tournament(tournament_id, final_standings)
            if not success:
                return False, "FAILED_TO_COMPLETE_TOURNAMENT", None

            # Award prizes
            prizes_awarded = self._award_tournament_prizes(tournament, leaderboard)

            # Clear tournament from teams
            for team_id in tournament.teams:
                self.team_repository.clear_tournament(team_id)

            current_app.logger.info(f"Completed tournament {tournament_id}, awarded {prizes_awarded} prizes")

            return True, "TOURNAMENT_COMPLETED_SUCCESSFULLY", {
                "tournament_id": tournament_id,
                "final_standings": final_standings,
                "prizes_awarded": prizes_awarded
            }

        except Exception as e:
            current_app.logger.error(f"Failed to complete tournament: {str(e)}")
            return False, "FAILED_TO_COMPLETE_TOURNAMENT", None

    def get_active_tournament(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get the currently active tournament"""
        try:
            tournament = self.tournament_repository.get_active_tournament()
            if not tournament:
                return False, "NO_ACTIVE_TOURNAMENT", None

            # Get enhanced tournament data with leaderboard
            leaderboard = self.tournament_repository.get_tournament_leaderboard(tournament.tournament_id)

            return True, "ACTIVE_TOURNAMENT_RETRIEVED", {
                "tournament": tournament.to_api_dict(),
                "leaderboard": leaderboard
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get active tournament: {str(e)}")
            return False, "FAILED_TO_GET_ACTIVE_TOURNAMENT", None

    def get_tournament_leaderboard(self, tournament_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get tournament leaderboard with team details"""
        try:
            tournament = self.tournament_repository.get_tournament_by_tournament_id(tournament_id)
            if not tournament:
                return False, "TOURNAMENT_NOT_FOUND", None

            leaderboard = self.tournament_repository.get_tournament_leaderboard(tournament_id)

            # Enhance leaderboard with team details
            enhanced_leaderboard = []
            for entry in leaderboard:
                team = self.team_repository.get_team_by_team_id(entry["team_id"])
                if team:
                    enhanced_entry = {
                        **entry,
                        "team_name": team.name,
                        "team_icon": team.icon,
                        "team_color": team.color,
                        "member_count": team.current_members
                    }
                    enhanced_leaderboard.append(enhanced_entry)

            return True, "TOURNAMENT_LEADERBOARD_RETRIEVED", {
                "tournament": tournament.to_api_dict(),
                "leaderboard": enhanced_leaderboard
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get tournament leaderboard: {str(e)}")
            return False, "FAILED_TO_GET_TOURNAMENT_LEADERBOARD", None

    def get_tournament_statistics(self, tournament_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get detailed tournament statistics"""
        try:
            stats = self.tournament_repository.get_tournament_statistics(tournament_id)
            if not stats:
                return False, "TOURNAMENT_NOT_FOUND", None

            return True, "TOURNAMENT_STATISTICS_RETRIEVED", stats

        except Exception as e:
            current_app.logger.error(f"Failed to get tournament statistics: {str(e)}")
            return False, "FAILED_TO_GET_TOURNAMENT_STATISTICS", None

    def cancel_tournament(self, tournament_id: str, admin_user_id: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Cancel a tournament"""
        try:
            tournament = self.tournament_repository.get_tournament_by_tournament_id(tournament_id)
            if not tournament:
                return False, "TOURNAMENT_NOT_FOUND", None

            if tournament.status == "completed":
                return False, "CANNOT_CANCEL_COMPLETED_TOURNAMENT", None

            # Cancel tournament
            success = self.tournament_repository.cancel_tournament(tournament_id)
            if not success:
                return False, "FAILED_TO_CANCEL_TOURNAMENT", None

            # Clear tournament from teams
            for team_id in tournament.teams:
                self.team_repository.clear_tournament(team_id)

            current_app.logger.info(f"Tournament {tournament_id} cancelled by admin {admin_user_id}")

            return True, "TOURNAMENT_CANCELLED_SUCCESSFULLY", {
                "tournament_id": tournament_id
            }

        except Exception as e:
            current_app.logger.error(f"Failed to cancel tournament: {str(e)}")
            return False, "FAILED_TO_CANCEL_TOURNAMENT", None

    def end_expired_tournaments(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """End tournaments that have expired"""
        try:
            ended_count = self.tournament_repository.end_expired_tournaments()

            current_app.logger.info(f"Ended {ended_count} expired tournaments")

            return True, "EXPIRED_TOURNAMENTS_ENDED", {
                "ended_count": ended_count
            }

        except Exception as e:
            current_app.logger.error(f"Failed to end expired tournaments: {str(e)}")
            return False, "FAILED_TO_END_EXPIRED_TOURNAMENTS", None

    def _auto_assign_users_to_teams(self, team_ids: List[str]) -> None:
        """Automatically assign users to teams for tournament"""
        try:
            # Get all users without teams or with teams not in tournament
            all_teams = self.team_repository.get_all_teams()
            tournament_teams = [team for team in all_teams if team.team_id in team_ids]

            if not tournament_teams:
                return

            # Balance users across tournament teams
            self.team_manager.balance_teams()

            current_app.logger.info(f"Auto-assigned users to {len(tournament_teams)} tournament teams")

        except Exception as e:
            current_app.logger.error(f"Failed to auto-assign users: {str(e)}")

    def _award_tournament_prizes(self, tournament: TeamTournament, leaderboard: List[Dict[str, Any]]) -> int:
        """Award prizes to tournament winners"""
        try:
            prizes_awarded = 0

            for i, entry in enumerate(leaderboard):
                position = i + 1
                team_id = entry["team_id"]

                # Determine prize category
                if position == 1:
                    prize_key = "1st_place"
                elif position == 2:
                    prize_key = "2nd_place"
                elif position == 3:
                    prize_key = "3rd_place"
                else:
                    prize_key = "participation"

                prize = tournament.prizes.get(prize_key)
                if prize:
                    # Award achievement to team
                    achievement_id = prize.get("achievement")
                    if achievement_id:
                        self.team_repository.add_achievement(team_id, achievement_id)

                    # Award credits to team members (would need credit system)
                    credits = prize.get("credits", 0)
                    if credits > 0:
                        team_members = self.member_repository.get_team_members(team_id)
                        for member in team_members:
                            # This would integrate with a credit system
                            # self.credit_service.award_credits(member.user_id, credits, f"Tournament prize: {tournament.name}")
                            pass

                    prizes_awarded += 1

            return prizes_awarded

        except Exception as e:
            current_app.logger.error(f"Failed to award prizes: {str(e)}")
            return 0