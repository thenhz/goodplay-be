from typing import List, Dict, Any, Tuple, Optional
from flask import current_app
from bson import ObjectId, regex
from app.core.repositories.user_repository import UserRepository
from app.social.repositories.relationship_repository import RelationshipRepository
from app.social.models.user_relationship import UserRelationship


class SocialDiscoveryService:
    """Service for social user discovery and search"""

    def __init__(self):
        self.user_repository = UserRepository()
        self.relationship_repository = RelationshipRepository()

    def search_users(self, current_user_id: str, query: str, limit: int = 20,
                    skip: int = 0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Search for users by name or email

        Args:
            current_user_id: ID of the user performing the search
            query: Search query string
            limit: Maximum number of results
            skip: Number of results to skip for pagination

        Returns:
            Tuple[success, message, data] where data contains users and pagination info
        """
        try:
            current_app.logger.info(f"User {current_user_id} searching for: {query}")

            if not query or len(query.strip()) < 2:
                return False, "SEARCH_QUERY_TOO_SHORT", None

            # Get current user's privacy settings
            current_user = self.user_repository.find_user_by_id(current_user_id)
            if not current_user:
                return False, "USER_NOT_FOUND", None

            # Create search filter
            search_regex = regex.Regex(f".*{query}.*", "i")
            search_filter = {
                "_id": {"$ne": ObjectId(current_user_id)},  # Exclude self
                "is_active": True,
                "$or": [
                    {"social_profile.display_name": search_regex},
                    {"first_name": search_regex},
                    {"last_name": search_regex},
                    {"email": search_regex}
                ]
            }

            # Get users from database
            users_data = self.user_repository.find_many(
                filter_dict=search_filter,
                limit=limit,
                skip=skip,
                sort=[("social_profile.display_name", 1)]
            )

            if not users_data:
                return True, "SEARCH_NO_RESULTS", {"users": [], "total": 0}

            # Get existing relationships for these users
            user_ids = [str(user["_id"]) for user in users_data]
            relationships = self._get_relationships_status(current_user_id, user_ids)

            # Filter based on privacy settings and format results
            filtered_users = []
            for user_data in users_data:
                user_id = str(user_data["_id"])

                # Check if user allows discovery
                privacy_prefs = user_data.get("preferences", {}).get("privacy", {})
                if not privacy_prefs.get("friends_discovery", True):
                    # Skip users who don't allow discovery unless they're already friends
                    relationship_status = relationships.get(user_id, {})
                    if relationship_status.get("type") != "friend" or relationship_status.get("status") != "accepted":
                        continue

                # Format user data for response
                user_info = self._format_user_for_search(user_data, relationships.get(user_id, {}))
                filtered_users.append(user_info)

            # Get total count for pagination
            total_count = len(filtered_users)

            current_app.logger.info(f"Search completed. Found {total_count} users for query: {query}")

            return True, "SEARCH_USERS_SUCCESS", {
                "users": filtered_users,
                "total": total_count,
                "query": query,
                "pagination": {
                    "limit": limit,
                    "skip": skip,
                    "has_more": total_count == limit
                }
            }

        except Exception as e:
            current_app.logger.error(f"Error searching users: {str(e)}")
            return False, "SEARCH_USERS_FAILED", None

    def get_friend_suggestions(self, current_user_id: str, limit: int = 10) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get friend suggestions based on mutual friends and common interests

        Args:
            current_user_id: ID of the user to get suggestions for
            limit: Maximum number of suggestions

        Returns:
            Tuple[success, message, data] containing suggested users
        """
        try:
            current_app.logger.info(f"Getting friend suggestions for user {current_user_id}")

            current_user = self.user_repository.find_user_by_id(current_user_id)
            if not current_user:
                return False, "USER_NOT_FOUND", None

            # Get current user's friends
            user_friends = self.relationship_repository.get_user_friends(current_user_id)
            friend_ids = [str(rel.target_user_id) if str(rel.user_id) == current_user_id
                         else str(rel.user_id) for rel in user_friends]

            # Get users with similar gaming preferences
            user_preferences = current_user.preferences.get("gaming", {})
            preferred_categories = user_preferences.get("preferred_categories", [])

            suggestions = []

            # Find users with similar gaming interests
            if preferred_categories:
                similar_users = self._find_users_by_gaming_preferences(
                    current_user_id, preferred_categories, friend_ids, limit
                )
                suggestions.extend(similar_users)

            # Find friends of friends (mutual connections)
            if len(suggestions) < limit and friend_ids:
                mutual_suggestions = self._find_friends_of_friends(
                    current_user_id, friend_ids, limit - len(suggestions)
                )
                suggestions.extend(mutual_suggestions)

            # Fill remaining slots with active users
            if len(suggestions) < limit:
                random_users = self._find_random_active_users(
                    current_user_id, friend_ids, suggestions, limit - len(suggestions)
                )
                suggestions.extend(random_users)

            # Get relationship status for all suggested users
            suggested_user_ids = [user["id"] for user in suggestions]
            relationships = self._get_relationships_status(current_user_id, suggested_user_ids)

            # Add relationship status to suggestions
            for suggestion in suggestions:
                user_id = suggestion["id"]
                suggestion["relationship"] = relationships.get(user_id, {
                    "type": None,
                    "status": None,
                    "is_friend": False,
                    "is_pending": False,
                    "is_blocked": False
                })

            current_app.logger.info(f"Found {len(suggestions)} friend suggestions")

            return True, "FRIEND_SUGGESTIONS_SUCCESS", {
                "suggestions": suggestions[:limit],
                "total": len(suggestions)
            }

        except Exception as e:
            current_app.logger.error(f"Error getting friend suggestions: {str(e)}")
            return False, "FRIEND_SUGGESTIONS_FAILED", None

    def _get_relationships_status(self, current_user_id: str, user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get relationship status between current user and a list of users"""
        relationships = {}

        for user_id in user_ids:
            relationship = self.relationship_repository.find_relationship_between_users(
                current_user_id, user_id
            )

            if relationship:
                relationships[user_id] = {
                    "type": relationship.relationship_type,
                    "status": relationship.status,
                    "is_friend": relationship.is_friend_request() and relationship.is_accepted(),
                    "is_pending": relationship.is_pending(),
                    "is_blocked": relationship.is_block(),
                    "initiated_by_me": str(relationship.initiated_by) == current_user_id
                }
            else:
                relationships[user_id] = {
                    "type": None,
                    "status": None,
                    "is_friend": False,
                    "is_pending": False,
                    "is_blocked": False,
                    "initiated_by_me": False
                }

        return relationships

    def _format_user_for_search(self, user_data: Dict[str, Any], relationship_info: Dict[str, Any]) -> Dict[str, Any]:
        """Format user data for search results"""
        social_profile = user_data.get("social_profile", {})
        gaming_stats = user_data.get("gaming_stats", {})

        return {
            "id": str(user_data["_id"]),
            "display_name": social_profile.get("display_name", "Unknown User"),
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "email": user_data.get("email"),
            "impact_score": user_data.get("impact_score", 0),
            "gaming_stats": {
                "total_play_time": gaming_stats.get("total_play_time", 0),
                "favorite_category": gaming_stats.get("favorite_category")
            },
            "friends_count": social_profile.get("friends_count", 0),
            "relationship": relationship_info,
            "privacy_level": social_profile.get("privacy_level", "public")
        }

    def _find_users_by_gaming_preferences(self, current_user_id: str, preferred_categories: List[str],
                                        exclude_user_ids: List[str], limit: int) -> List[Dict[str, Any]]:
        """Find users with similar gaming preferences"""
        try:
            # Create filter for users with similar preferences
            exclude_ids = [ObjectId(uid) for uid in exclude_user_ids + [current_user_id]]

            filter_dict = {
                "_id": {"$nin": exclude_ids},
                "is_active": True,
                "preferences.gaming.preferred_categories": {"$in": preferred_categories},
                "preferences.privacy.friends_discovery": {"$ne": False}  # Allow discovery
            }

            users_data = self.user_repository.find_many(
                filter_dict=filter_dict,
                limit=limit,
                sort=[("gaming_stats.total_play_time", -1)]
            )

            return [self._format_user_for_search(user, {}) for user in users_data]

        except Exception as e:
            current_app.logger.error(f"Error finding users by gaming preferences: {str(e)}")
            return []

    def _find_friends_of_friends(self, current_user_id: str, friend_ids: List[str], limit: int) -> List[Dict[str, Any]]:
        """Find friends of current user's friends"""
        try:
            if not friend_ids:
                return []

            # Get relationships of user's friends
            friends_relationships = []
            for friend_id in friend_ids[:5]:  # Limit to avoid too many queries
                friend_relations = self.relationship_repository.get_user_friends(friend_id, limit=10)
                friends_relationships.extend(friend_relations)

            # Extract unique user IDs (excluding current user and existing friends)
            suggested_ids = set()
            exclude_ids = set(friend_ids + [current_user_id])

            for rel in friends_relationships:
                other_user_id = str(rel.target_user_id) if str(rel.user_id) in friend_ids else str(rel.user_id)
                if other_user_id not in exclude_ids:
                    suggested_ids.add(other_user_id)

            if not suggested_ids:
                return []

            # Get user data for suggestions
            suggestions = []
            for user_id in list(suggested_ids)[:limit]:
                user_data = self.user_repository.find_by_id(user_id)
                if user_data and user_data.get("is_active", False):
                    # Check privacy settings
                    privacy_prefs = user_data.get("preferences", {}).get("privacy", {})
                    if privacy_prefs.get("friends_discovery", True):
                        suggestions.append(self._format_user_for_search(user_data, {}))

            return suggestions[:limit]

        except Exception as e:
            current_app.logger.error(f"Error finding friends of friends: {str(e)}")
            return []

    def _find_random_active_users(self, current_user_id: str, exclude_user_ids: List[str],
                                current_suggestions: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Find random active users to fill suggestion slots"""
        try:
            if limit <= 0:
                return []

            # Add current suggestions to exclusion list
            suggestion_ids = [s["id"] for s in current_suggestions]
            exclude_ids = [ObjectId(uid) for uid in exclude_user_ids + [current_user_id] + suggestion_ids]

            filter_dict = {
                "_id": {"$nin": exclude_ids},
                "is_active": True,
                "preferences.privacy.friends_discovery": {"$ne": False}
            }

            # Use aggregation to get random users
            pipeline = [
                {"$match": filter_dict},
                {"$sample": {"size": limit * 2}},  # Get more to account for filtering
                {"$limit": limit}
            ]

            users_data = list(self.user_repository.collection.aggregate(pipeline))

            return [self._format_user_for_search(user, {}) for user in users_data[:limit]]

        except Exception as e:
            current_app.logger.error(f"Error finding random active users: {str(e)}")
            return []