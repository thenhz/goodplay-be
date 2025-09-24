from typing import Optional, List, Dict, Any, Tuple
from flask import current_app

from app.social.challenges.models.social_challenge import SocialChallenge
from app.social.challenges.repositories.social_challenge_repository import SocialChallengeRepository
from app.social.challenges.repositories.challenge_participant_repository import ChallengeParticipantRepository


class SocialMatchmakingService:
    """Service for social challenge discovery and matchmaking"""

    def __init__(self):
        self.challenge_repo = SocialChallengeRepository()
        self.participant_repo = ChallengeParticipantRepository()

    def discover_public_challenges(self, user_id: str, filters: Dict[str, Any] = None,
                                 limit: int = 20, offset: int = 0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Discover public challenges available for joining"""
        try:
            challenge_type = filters.get('challenge_type') if filters else None
            challenges = self.challenge_repo.get_public_challenges(challenge_type, limit, offset)

            # Filter out challenges user is already participating in
            user_challenges = set()
            user_participations = self.participant_repo.get_user_participations(user_id, status="active")
            user_challenges = {p.challenge_id for p in user_participations}

            available_challenges = []
            for challenge in challenges:
                if challenge.challenge_id not in user_challenges and challenge.can_user_join(user_id):
                    challenge_data = challenge.to_api_dict()
                    challenge_data["match_score"] = self._calculate_match_score(challenge, user_id)
                    available_challenges.append(challenge_data)

            # Sort by match score
            available_challenges.sort(key=lambda x: x["match_score"], reverse=True)

            return True, "Public challenges discovered", {
                "challenges": available_challenges,
                "count": len(available_challenges)
            }

        except Exception as e:
            current_app.logger.error(f"Error discovering public challenges: {str(e)}")
            return False, "Failed to discover challenges", None

    def discover_friend_challenges(self, user_id: str, friend_ids: List[str],
                                 limit: int = 20, offset: int = 0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Discover challenges created by friends"""
        try:
            if not friend_ids:
                return True, "No friends to discover challenges from", {"challenges": [], "count": 0}

            challenges = self.challenge_repo.get_friend_challenges(user_id, friend_ids, limit, offset)

            friend_challenges = []
            for challenge in challenges:
                if challenge.can_user_join(user_id):
                    challenge_data = challenge.to_api_dict()
                    challenge_data["match_score"] = self._calculate_match_score(challenge, user_id)
                    challenge_data["created_by_friend"] = True
                    friend_challenges.append(challenge_data)

            # Sort by match score
            friend_challenges.sort(key=lambda x: x["match_score"], reverse=True)

            return True, "Friend challenges discovered", {
                "challenges": friend_challenges,
                "count": len(friend_challenges)
            }

        except Exception as e:
            current_app.logger.error(f"Error discovering friend challenges: {str(e)}")
            return False, "Failed to discover friend challenges", None

    def get_recommended_challenges(self, user_id: str, limit: int = 10) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get personalized challenge recommendations"""
        try:
            # Get user's participation history
            user_participations = self.participant_repo.get_user_participations(user_id, limit=50)
            user_preferences = self._analyze_user_preferences(user_participations)

            # Get available challenges
            public_challenges = self.challenge_repo.get_public_challenges(limit=100)

            recommendations = []
            for challenge in public_challenges:
                if not challenge.can_user_join(user_id):
                    continue

                # Calculate recommendation score
                match_score = self._calculate_match_score(challenge, user_id)
                preference_score = self._calculate_preference_score(challenge, user_preferences)
                recommendation_score = (match_score * 0.4) + (preference_score * 0.6)

                challenge_data = challenge.to_api_dict()
                challenge_data["recommendation_score"] = recommendation_score
                challenge_data["match_reasons"] = self._get_match_reasons(challenge, user_preferences)

                recommendations.append(challenge_data)

            # Sort by recommendation score
            recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
            recommendations = recommendations[:limit]

            return True, "Challenge recommendations generated", {
                "recommendations": recommendations,
                "count": len(recommendations),
                "user_preferences": user_preferences
            }

        except Exception as e:
            current_app.logger.error(f"Error getting recommendations: {str(e)}")
            return False, "Failed to get recommendations", None

    def search_challenges(self, user_id: str, query: str, filters: Dict[str, Any] = None,
                         limit: int = 20, offset: int = 0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Search challenges by text query with filters"""
        try:
            if not query or len(query.strip()) < 2:
                return False, "Search query too short", None

            # Build search filters
            search_filters = filters or {}

            # Only show challenges user can join
            search_filters["status"] = {"$in": ["open", "active"]}

            challenges = self.challenge_repo.search_challenges(query, search_filters, limit, offset)

            search_results = []
            for challenge in challenges:
                if challenge.can_user_join(user_id):
                    challenge_data = challenge.to_api_dict()
                    challenge_data["search_relevance"] = self._calculate_search_relevance(challenge, query)
                    search_results.append(challenge_data)

            # Sort by search relevance
            search_results.sort(key=lambda x: x["search_relevance"], reverse=True)

            return True, "Challenge search completed", {
                "results": search_results,
                "count": len(search_results),
                "query": query
            }

        except Exception as e:
            current_app.logger.error(f"Error searching challenges: {str(e)}")
            return False, "Failed to search challenges", None

    def get_challenges_by_category(self, user_id: str, category: str,
                                 limit: int = 20, offset: int = 0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get challenges filtered by category"""
        try:
            challenges = self.challenge_repo.get_challenges_by_category(category, limit, offset)

            category_challenges = []
            for challenge in challenges:
                if challenge.can_user_join(user_id):
                    challenge_data = challenge.to_api_dict()
                    challenge_data["match_score"] = self._calculate_match_score(challenge, user_id)
                    category_challenges.append(challenge_data)

            # Sort by match score
            category_challenges.sort(key=lambda x: x["match_score"], reverse=True)

            return True, f"Challenges in category '{category}' retrieved", {
                "challenges": category_challenges,
                "count": len(category_challenges),
                "category": category
            }

        except Exception as e:
            current_app.logger.error(f"Error getting challenges by category: {str(e)}")
            return False, "Failed to get challenges by category", None

    def get_trending_challenges(self, user_id: str, limit: int = 10) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get currently trending challenges"""
        try:
            # Get challenges with high recent activity
            recent_challenges = self.challenge_repo.get_active_challenges(limit=100)

            trending = []
            for challenge in recent_challenges:
                if not challenge.can_user_join(user_id):
                    continue

                # Calculate trending score based on participants and recency
                trending_score = self._calculate_trending_score(challenge)

                challenge_data = challenge.to_api_dict()
                challenge_data["trending_score"] = trending_score
                challenge_data["is_trending"] = True

                trending.append(challenge_data)

            # Sort by trending score
            trending.sort(key=lambda x: x["trending_score"], reverse=True)
            trending = trending[:limit]

            return True, "Trending challenges retrieved", {
                "challenges": trending,
                "count": len(trending)
            }

        except Exception as e:
            current_app.logger.error(f"Error getting trending challenges: {str(e)}")
            return False, "Failed to get trending challenges", None

    def get_similar_challenges(self, challenge_id: str, user_id: str,
                             limit: int = 5) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get challenges similar to the given challenge"""
        try:
            # Get the reference challenge
            reference_challenge = self.challenge_repo.get_by_challenge_id(challenge_id)
            if not reference_challenge:
                return False, "Reference challenge not found", None

            # Find similar challenges
            filters = {
                "challenge_type": reference_challenge.challenge_type,
                "status": {"$in": ["open", "active"]},
                "challenge_id": {"$ne": challenge_id}  # Exclude the reference challenge
            }

            similar_challenges_data = self.challenge_repo.find_many(filters, limit=limit * 2)
            similar_challenges = [SocialChallenge.from_dict(data) for data in similar_challenges_data]

            recommendations = []
            for challenge in similar_challenges:
                if not challenge.can_user_join(user_id):
                    continue

                # Calculate similarity score
                similarity_score = self._calculate_similarity_score(reference_challenge, challenge)

                challenge_data = challenge.to_api_dict()
                challenge_data["similarity_score"] = similarity_score
                challenge_data["similar_aspects"] = self._get_similarity_aspects(reference_challenge, challenge)

                recommendations.append(challenge_data)

            # Sort by similarity score
            recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
            recommendations = recommendations[:limit]

            return True, "Similar challenges found", {
                "challenges": recommendations,
                "count": len(recommendations),
                "reference_challenge_id": challenge_id
            }

        except Exception as e:
            current_app.logger.error(f"Error getting similar challenges: {str(e)}")
            return False, "Failed to get similar challenges", None

    def _analyze_user_preferences(self, participations: List) -> Dict[str, Any]:
        """Analyze user preferences from participation history"""
        if not participations:
            return {"challenge_types": [], "categories": [], "difficulty_levels": [], "avg_social_score": 0}

        challenge_types = {}
        categories = {}
        difficulty_levels = {}
        total_social_score = 0

        for participation in participations:
            # We'd need to join with challenge data to get full preferences
            # For now, use available data from participation
            if hasattr(participation, 'challenge_type'):
                challenge_types[participation.challenge_type] = challenge_types.get(participation.challenge_type, 0) + 1

            total_social_score += participation.social_score

        avg_social_score = total_social_score / len(participations) if participations else 0

        return {
            "preferred_types": sorted(challenge_types.keys(), key=challenge_types.get, reverse=True)[:3],
            "preferred_categories": sorted(categories.keys(), key=categories.get, reverse=True)[:3],
            "preferred_difficulties": sorted(difficulty_levels.keys(), key=difficulty_levels.get, reverse=True)[:3],
            "avg_social_engagement": avg_social_score,
            "participation_count": len(participations)
        }

    def _calculate_match_score(self, challenge: SocialChallenge, user_id: str) -> float:
        """Calculate how well a challenge matches a user"""
        score = 0.0

        # Base score for availability
        if challenge.can_user_join(user_id):
            score += 20

        # Difficulty preference (medium difficulty gets higher score)
        if challenge.difficulty_level == 3:
            score += 15
        elif challenge.difficulty_level in [2, 4]:
            score += 10
        else:
            score += 5

        # Time remaining (more time = higher score)
        time_remaining = challenge.get_time_remaining_hours()
        if time_remaining:
            if time_remaining > 72:  # More than 3 days
                score += 15
            elif time_remaining > 24:  # More than 1 day
                score += 10
            else:
                score += 5

        # Participant count (not too empty, not too full)
        participant_ratio = challenge.current_participants / challenge.max_participants
        if 0.3 <= participant_ratio <= 0.7:
            score += 10
        elif 0.1 <= participant_ratio <= 0.9:
            score += 5

        # Social features bonus
        if challenge.allow_cheering and challenge.allow_comments:
            score += 5

        return min(score, 100)  # Cap at 100

    def _calculate_preference_score(self, challenge: SocialChallenge, preferences: Dict[str, Any]) -> float:
        """Calculate score based on user preferences"""
        score = 0.0

        # Challenge type preference
        if challenge.challenge_type in preferences.get("preferred_types", []):
            score += 30

        # Category preference
        if challenge.challenge_category in preferences.get("preferred_categories", []):
            score += 25

        # Difficulty preference
        if challenge.difficulty_level in preferences.get("preferred_difficulties", []):
            score += 20

        # Social engagement preference
        avg_social = preferences.get("avg_social_engagement", 0)
        if challenge.allow_cheering and challenge.allow_comments and avg_social > 10:
            score += 15

        return min(score, 100)

    def _calculate_search_relevance(self, challenge: SocialChallenge, query: str) -> float:
        """Calculate search relevance score"""
        relevance = 0.0
        query_lower = query.lower()

        # Title match (highest weight)
        if query_lower in challenge.title.lower():
            relevance += 40

        # Description match
        if query_lower in challenge.description.lower():
            relevance += 20

        # Tag match
        for tag in challenge.tags:
            if query_lower in tag.lower():
                relevance += 15

        # Category match
        if query_lower in challenge.challenge_category.lower():
            relevance += 25

        # Type match
        if query_lower in challenge.challenge_type.lower():
            relevance += 30

        return min(relevance, 100)

    def _calculate_trending_score(self, challenge: SocialChallenge) -> float:
        """Calculate trending score based on activity metrics"""
        score = 0.0

        # Recent creation bonus
        hours_since_creation = (challenge.created_at - challenge.created_at).total_seconds() / 3600
        if hours_since_creation < 24:
            score += 20
        elif hours_since_creation < 72:
            score += 10

        # Participation rate
        participant_ratio = challenge.current_participants / challenge.max_participants
        score += participant_ratio * 30

        # Public and social features bonus
        if challenge.is_public:
            score += 15

        if challenge.allow_cheering and challenge.allow_comments:
            score += 10

        # Active status bonus
        if challenge.status == "active":
            score += 25

        return min(score, 100)

    def _calculate_similarity_score(self, reference: SocialChallenge, target: SocialChallenge) -> float:
        """Calculate similarity between two challenges"""
        score = 0.0

        # Same type
        if reference.challenge_type == target.challenge_type:
            score += 30

        # Same category
        if reference.challenge_category == target.challenge_category:
            score += 25

        # Similar difficulty
        diff_difference = abs(reference.difficulty_level - target.difficulty_level)
        if diff_difference == 0:
            score += 20
        elif diff_difference == 1:
            score += 10

        # Similar duration
        ref_duration = (reference.end_date - reference.start_date).total_seconds()
        target_duration = (target.end_date - target.start_date).total_seconds()
        duration_ratio = min(ref_duration, target_duration) / max(ref_duration, target_duration)
        score += duration_ratio * 15

        # Common tags
        common_tags = set(reference.tags) & set(target.tags)
        score += len(common_tags) * 3

        return min(score, 100)

    def _get_match_reasons(self, challenge: SocialChallenge, preferences: Dict[str, Any]) -> List[str]:
        """Get reasons why a challenge is recommended"""
        reasons = []

        if challenge.challenge_type in preferences.get("preferred_types", []):
            reasons.append(f"Matches your preferred type: {challenge.challenge_type}")

        if challenge.challenge_category in preferences.get("preferred_categories", []):
            reasons.append(f"Similar to challenges you've enjoyed: {challenge.challenge_category}")

        if challenge.difficulty_level in preferences.get("preferred_difficulties", []):
            reasons.append(f"Matches your preferred difficulty level: {challenge.difficulty_level}")

        if challenge.allow_cheering and preferences.get("avg_social_engagement", 0) > 10:
            reasons.append("High social engagement features")

        time_remaining = challenge.get_time_remaining_hours()
        if time_remaining and time_remaining > 48:
            reasons.append("Plenty of time to participate")

        return reasons

    def _get_similarity_aspects(self, reference: SocialChallenge, target: SocialChallenge) -> List[str]:
        """Get aspects that make challenges similar"""
        aspects = []

        if reference.challenge_type == target.challenge_type:
            aspects.append(f"Same challenge type: {target.challenge_type}")

        if reference.challenge_category == target.challenge_category:
            aspects.append(f"Same category: {target.challenge_category}")

        if reference.difficulty_level == target.difficulty_level:
            aspects.append(f"Same difficulty level: {target.difficulty_level}")

        common_tags = set(reference.tags) & set(target.tags)
        if common_tags:
            aspects.append(f"Common interests: {', '.join(common_tags)}")

        return aspects