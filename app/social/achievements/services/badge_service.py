from typing import Dict, Any, List, Tuple, Optional
from flask import current_app

from ..repositories.achievement_repository import AchievementRepository
from ..models.badge import Badge
from ..models.achievement import Achievement


class BadgeService:
    """
    Service for managing user badges and badge-related operations
    """

    def __init__(self):
        self.achievement_repo = AchievementRepository()

    def get_user_badges(self, user_id: str, visible_only: bool = False) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Get all badges for a user

        Args:
            user_id: ID of the user
            visible_only: Only return visible badges

        Returns:
            Tuple[bool, str, List[Dict]]: Success, message, badges data
        """
        try:
            badges = self.achievement_repo.find_user_badges(user_id, visible_only)
            badges_data = [badge.to_response_dict() for badge in badges]

            return True, "User badges retrieved", badges_data

        except Exception as e:
            current_app.logger.error(f"Error getting user badges: {str(e)}")
            return False, "Error retrieving user badges", []

    def get_user_badge_collection(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get comprehensive badge collection for a user with statistics

        Args:
            user_id: ID of the user

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, collection data
        """
        try:
            # Get all badges
            badges = self.achievement_repo.find_user_badges(user_id)

            # Group badges by rarity
            badges_by_rarity = {rarity: [] for rarity in Badge.VALID_RARITIES}
            for badge in badges:
                badges_by_rarity[badge.rarity].append(badge.to_response_dict())

            # Get badge counts
            badge_counts = self.achievement_repo.count_user_badges_by_rarity(user_id)

            # Calculate collection statistics
            total_badges = sum(badge_counts.values())
            visible_badges = len([b for b in badges if b.is_visible])

            # Get rarest badge
            rarest_badge = self._get_rarest_badge(badges)

            # Get recent badges (last 5)
            recent_badges = sorted(
                [badge.to_response_dict() for badge in badges],
                key=lambda x: x['earned_at'],
                reverse=True
            )[:5]

            collection_data = {
                "total_badges": total_badges,
                "visible_badges": visible_badges,
                "badges_by_rarity": badges_by_rarity,
                "badge_counts": badge_counts,
                "rarest_badge": rarest_badge,
                "recent_badges": recent_badges,
                "collection_value": self._calculate_collection_value(badges),
                "completion_stats": self._get_completion_stats(user_id)
            }

            return True, "Badge collection retrieved", collection_data

        except Exception as e:
            current_app.logger.error(f"Error getting badge collection: {str(e)}")
            return False, "Error retrieving badge collection", None

    def get_badges_by_rarity(self, user_id: str, rarity: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Get badges filtered by rarity

        Args:
            user_id: ID of the user
            rarity: Badge rarity to filter by

        Returns:
            Tuple[bool, str, List[Dict]]: Success, message, badges data
        """
        try:
            if rarity not in Badge.VALID_RARITIES:
                return False, "Invalid badge rarity", []

            badges = self.achievement_repo.find_user_badges_by_rarity(user_id, rarity)
            badges_data = [badge.to_response_dict() for badge in badges]

            return True, f"{rarity.title()} badges retrieved", badges_data

        except Exception as e:
            current_app.logger.error(f"Error getting badges by rarity: {str(e)}")
            return False, "Error retrieving badges by rarity", []

    def update_badge_visibility(self, user_id: str, badge_id: str, visible: bool) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Update badge visibility on user profile

        Args:
            user_id: ID of the user
            badge_id: ID of the badge
            visible: New visibility status

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, updated badge data
        """
        try:
            success = self.achievement_repo.update_badge_visibility(user_id, badge_id, visible)

            if success:
                # Get updated badge info
                badges = self.achievement_repo.find_user_badges(user_id)
                updated_badge = next((b for b in badges if str(b._id) == badge_id), None)

                if updated_badge:
                    return True, "Badge visibility updated", updated_badge.to_response_dict()
                else:
                    return True, "Badge visibility updated", None
            else:
                return False, "Badge not found or not owned by user", None

        except Exception as e:
            current_app.logger.error(f"Error updating badge visibility: {str(e)}")
            return False, "Error updating badge visibility", None

    def get_badge_showcase(self, user_id: str, limit: int = 6) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Get user's badge showcase (top visible badges for profile display)

        Args:
            user_id: ID of the user
            limit: Maximum number of badges to return

        Returns:
            Tuple[bool, str, List[Dict]]: Success, message, showcase badges
        """
        try:
            visible_badges = self.achievement_repo.find_user_badges(user_id, visible_only=True)

            # Sort badges by rarity priority (rarest first) and earned date
            sorted_badges = sorted(
                visible_badges,
                key=lambda b: (-b.get_rarity_priority(), -b.earned_at.timestamp())
            )

            showcase_badges = [badge.to_response_dict() for badge in sorted_badges[:limit]]

            return True, "Badge showcase retrieved", showcase_badges

        except Exception as e:
            current_app.logger.error(f"Error getting badge showcase: {str(e)}")
            return False, "Error retrieving badge showcase", []

    def get_badge_statistics(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get detailed badge statistics for a user

        Args:
            user_id: ID of the user

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, statistics data
        """
        try:
            badges = self.achievement_repo.find_user_badges(user_id)
            badge_counts = self.achievement_repo.count_user_badges_by_rarity(user_id)

            # Calculate various statistics
            total_badges = len(badges)
            if total_badges == 0:
                return True, "No badges found", {
                    "total_badges": 0,
                    "rarity_distribution": badge_counts,
                    "average_rarity_score": 0,
                    "badge_acquisition_rate": 0,
                    "most_productive_period": None
                }

            # Calculate average rarity score
            rarity_scores = [badge.get_rarity_priority() for badge in badges]
            average_rarity_score = sum(rarity_scores) / len(rarity_scores)

            # Calculate badge acquisition rate (badges per day since first badge)
            sorted_by_date = sorted(badges, key=lambda b: b.earned_at)
            first_badge_date = sorted_by_date[0].earned_at
            days_since_first = (badges[0].earned_at - first_badge_date).days + 1
            acquisition_rate = total_badges / days_since_first if days_since_first > 0 else 0

            # Find most productive period (month with most badges)
            monthly_counts = {}
            for badge in badges:
                month_key = f"{badge.earned_at.year}-{badge.earned_at.month:02d}"
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1

            most_productive_period = max(monthly_counts.items(), key=lambda x: x[1]) if monthly_counts else None

            statistics = {
                "total_badges": total_badges,
                "rarity_distribution": badge_counts,
                "average_rarity_score": round(average_rarity_score, 2),
                "badge_acquisition_rate": round(acquisition_rate, 2),
                "most_productive_period": {
                    "period": most_productive_period[0],
                    "badges_earned": most_productive_period[1]
                } if most_productive_period else None,
                "rarity_percentages": self._calculate_rarity_percentages(badge_counts, total_badges)
            }

            return True, "Badge statistics calculated", statistics

        except Exception as e:
            current_app.logger.error(f"Error calculating badge statistics: {str(e)}")
            return False, "Error calculating badge statistics", None

    def compare_badge_collections(self, user_id_1: str, user_id_2: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Compare badge collections between two users

        Args:
            user_id_1: ID of the first user
            user_id_2: ID of the second user

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, comparison data
        """
        try:
            # Get badges for both users
            badges_1 = self.achievement_repo.find_user_badges(user_id_1)
            badges_2 = self.achievement_repo.find_user_badges(user_id_2)

            # Get badge counts
            counts_1 = self.achievement_repo.count_user_badges_by_rarity(user_id_1)
            counts_2 = self.achievement_repo.count_user_badges_by_rarity(user_id_2)

            # Find common and unique badges
            achievement_ids_1 = {badge.achievement_id for badge in badges_1}
            achievement_ids_2 = {badge.achievement_id for badge in badges_2}

            common_badges = achievement_ids_1.intersection(achievement_ids_2)
            unique_to_1 = achievement_ids_1 - achievement_ids_2
            unique_to_2 = achievement_ids_2 - achievement_ids_1

            comparison_data = {
                "user_1": {
                    "user_id": user_id_1,
                    "total_badges": len(badges_1),
                    "rarity_counts": counts_1,
                    "unique_badges": len(unique_to_1)
                },
                "user_2": {
                    "user_id": user_id_2,
                    "total_badges": len(badges_2),
                    "rarity_counts": counts_2,
                    "unique_badges": len(unique_to_2)
                },
                "common_badges": len(common_badges),
                "collection_similarity": len(common_badges) / max(len(achievement_ids_1), len(achievement_ids_2), 1) * 100
            }

            return True, "Badge collections compared", comparison_data

        except Exception as e:
            current_app.logger.error(f"Error comparing badge collections: {str(e)}")
            return False, "Error comparing badge collections", None

    def _get_rarest_badge(self, badges: List[Badge]) -> Optional[Dict[str, Any]]:
        """Get the rarest badge from a list of badges"""
        if not badges:
            return None

        rarest = max(badges, key=lambda b: b.get_rarity_priority())
        return rarest.to_response_dict()

    def _calculate_collection_value(self, badges: List[Badge]) -> int:
        """Calculate total value of badge collection"""
        value = 0
        rarity_values = {
            Badge.COMMON: 10,
            Badge.RARE: 25,
            Badge.EPIC: 50,
            Badge.LEGENDARY: 100
        }

        for badge in badges:
            value += rarity_values.get(badge.rarity, 0)

        return value

    def _get_completion_stats(self, user_id: str) -> Dict[str, Any]:
        """Get achievement completion statistics"""
        try:
            # Get all active achievements
            all_achievements = self.achievement_repo.find_active_achievements()
            user_achievements = self.achievement_repo.find_user_achievements(user_id)

            total_available = len(all_achievements)
            completed = len([ua for ua in user_achievements if ua.is_completed])

            completion_by_category = {}
            for category in Achievement.VALID_CATEGORIES:
                category_achievements = [a for a in all_achievements if a.category == category]
                category_completed = len([
                    ua for ua in user_achievements
                    if ua.is_completed and any(
                        a.achievement_id == ua.achievement_id and a.category == category
                        for a in category_achievements
                    )
                ])

                completion_by_category[category] = {
                    "completed": category_completed,
                    "total": len(category_achievements),
                    "percentage": (category_completed / len(category_achievements) * 100) if category_achievements else 0
                }

            return {
                "total_completed": completed,
                "total_available": total_available,
                "overall_percentage": (completed / total_available * 100) if total_available > 0 else 0,
                "completion_by_category": completion_by_category
            }

        except Exception:
            return {"total_completed": 0, "total_available": 0, "overall_percentage": 0}

    def _calculate_rarity_percentages(self, badge_counts: Dict[str, int], total_badges: int) -> Dict[str, float]:
        """Calculate percentage distribution of badge rarities"""
        if total_badges == 0:
            return {rarity: 0.0 for rarity in Badge.VALID_RARITIES}

        percentages = {}
        for rarity in Badge.VALID_RARITIES:
            count = badge_counts.get(rarity, 0)
            percentages[rarity] = round((count / total_badges) * 100, 1)

        return percentages