from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from flask import current_app
from app.donations.repositories.impact_story_repository import ImpactStoryRepository
from app.donations.services.impact_tracking_service import ImpactTrackingService


class StoryUnlockingService:
    """
    Service for managing progressive story unlocking based on user achievements.

    Handles story unlock logic, progress tracking, and user engagement.
    """

    def __init__(self):
        self.story_repository = ImpactStoryRepository()
        self.impact_service = ImpactTrackingService()

    def get_available_stories(self, user_id: str, category: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get stories available for a user."""
        try:
            user_stats = self.impact_service._get_user_statistics(user_id)
            stories = self.story_repository.get_stories_for_user(
                user_stats=user_stats,
                include_locked=False,
                category=category
            )

            return True, "STORIES_RETRIEVED_SUCCESS", {
                'available_stories': stories,
                'user_stats': user_stats
            }
        except Exception as e:
            current_app.logger.error(f"Error getting available stories for {user_id}: {str(e)}")
            return False, "STORIES_RETRIEVAL_ERROR", None

    def get_story_progress(self, user_id: str, story_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get unlock progress for a specific story."""
        try:
            story = self.story_repository.get_story_by_id(story_id)
            if not story:
                return False, "STORY_NOT_FOUND", None

            user_stats = self.impact_service._get_user_statistics(user_id)
            progress = story.get_unlock_progress(user_stats)

            return True, "STORY_PROGRESS_SUCCESS", {
                'story': story.to_response_dict(user_stats=user_stats, include_content=False),
                'progress': progress
            }
        except Exception as e:
            current_app.logger.error(f"Error getting story progress for {story_id}: {str(e)}")
            return False, "STORY_PROGRESS_ERROR", None

    def get_next_unlockable_stories(self, user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get the next stories user can unlock."""
        try:
            user_stats = self.impact_service._get_user_statistics(user_id)
            next_stories = self.story_repository.get_next_unlock_stories(user_stats)

            return True, "NEXT_STORIES_SUCCESS", {
                'next_stories': next_stories,
                'user_stats': user_stats
            }
        except Exception as e:
            current_app.logger.error(f"Error getting next unlockable stories for {user_id}: {str(e)}")
            return False, "NEXT_STORIES_ERROR", None