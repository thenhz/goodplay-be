from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class StoryType(Enum):
    """Types of impact stories available."""
    MILESTONE = "milestone"  # Donation milestone stories
    ONLUS_UPDATE = "onlus_update"  # Direct updates from ONLUS
    IMPACT_REPORT = "impact_report"  # Impact achievement stories
    COMMUNITY_HIGHLIGHT = "community_highlight"  # Community success stories
    SEASONAL = "seasonal"  # Special seasonal campaigns


class UnlockConditionType(Enum):
    """Types of conditions to unlock stories."""
    TOTAL_DONATED = "total_donated"  # Total amount donated by user
    DONATION_COUNT = "donation_count"  # Number of donations made
    ONLUS_DIVERSITY = "onlus_diversity"  # Number of different ONLUS supported
    IMPACT_SCORE = "impact_score"  # User impact score threshold
    SPECIAL_EVENT = "special_event"  # Special event participation
    TIME_BASED = "time_based"  # Time-based unlocks (anniversary, etc.)


class StoryStatus(Enum):
    """Status of story availability."""
    LOCKED = "locked"  # Not yet unlocked by user
    UNLOCKED = "unlocked"  # Available to view
    VIEWED = "viewed"  # User has viewed the story
    FEATURED = "featured"  # Currently featured story


class ImpactStory:
    """
    Model for progressive impact stories unlocked through donations.

    Stories provide transparency and engagement by showing users the real
    impact of their donations through multimedia content and progress tracking.

    Collection: impact_stories
    """

    # Predefined unlock levels for donation milestones (€)
    MILESTONE_LEVELS = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

    def __init__(self, title: str, content: str, story_type: str,
                 unlock_condition_type: str, unlock_condition_value: float,
                 onlus_id: str = None, category: str = None,
                 media_urls: List[str] = None, thumbnail_url: str = None,
                 estimated_read_time: int = 5, priority: int = 0,
                 is_active: bool = True, featured_until: Optional[datetime] = None,
                 metadata: Dict[str, Any] = None, tags: List[str] = None,
                 _id: Optional[ObjectId] = None, created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None, author: str = None):
        """
        Initialize ImpactStory.

        Args:
            title: Story title for display
            content: Main story content (supports Markdown)
            story_type: Type of story (milestone, onlus_update, etc.)
            unlock_condition_type: Type of unlock condition
            unlock_condition_value: Value threshold for unlock
            onlus_id: Associated ONLUS (if applicable)
            category: Story category for filtering
            media_urls: List of media URLs (images, videos)
            thumbnail_url: Thumbnail image URL
            estimated_read_time: Estimated reading time in minutes
            priority: Display priority (higher = more important)
            is_active: Whether story is currently active
            featured_until: Featured status expiration
            metadata: Additional story metadata
            tags: Tags for categorization and search
            _id: MongoDB document ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
            author: Story author/creator
        """
        self._id = _id or ObjectId()
        self.title = title
        self.content = content
        self.story_type = story_type
        self.unlock_condition_type = unlock_condition_type
        self.unlock_condition_value = float(unlock_condition_value)
        self.onlus_id = onlus_id
        self.category = category or "general"
        self.media_urls = media_urls or []
        self.thumbnail_url = thumbnail_url
        self.estimated_read_time = estimated_read_time
        self.priority = priority
        self.is_active = is_active
        self.featured_until = featured_until
        self.author = author
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

        # Additional metadata
        self.metadata = metadata or {}
        self.tags = tags or []

        # Validation
        self._validate()

    def _validate(self):
        """Validate story data."""
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Story title cannot be empty")

        if not self.content or len(self.content.strip()) == 0:
            raise ValueError("Story content cannot be empty")

        if self.story_type not in [t.value for t in StoryType]:
            raise ValueError(f"Invalid story type: {self.story_type}")

        if self.unlock_condition_type not in [t.value for t in UnlockConditionType]:
            raise ValueError(f"Invalid unlock condition type: {self.unlock_condition_type}")

        if self.unlock_condition_value < 0:
            raise ValueError("Unlock condition value cannot be negative")

        if self.estimated_read_time < 1:
            raise ValueError("Estimated read time must be at least 1 minute")

        # Validate media URLs format (basic check)
        for url in self.media_urls:
            if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid media URL format: {url}")

    def check_unlock_status(self, user_stats: Dict[str, Any]) -> bool:
        """
        Check if story should be unlocked for user based on their stats.

        Args:
            user_stats: Dictionary containing user statistics
                - total_donated: Total amount donated
                - donation_count: Number of donations
                - onlus_diversity: Number of different ONLUS supported
                - impact_score: Current impact score
                - special_events: List of special events participated

        Returns:
            bool: True if story should be unlocked
        """
        if not self.is_active:
            return False

        condition_type = self.unlock_condition_type
        condition_value = self.unlock_condition_value

        if condition_type == UnlockConditionType.TOTAL_DONATED.value:
            return user_stats.get('total_donated', 0) >= condition_value

        elif condition_type == UnlockConditionType.DONATION_COUNT.value:
            return user_stats.get('donation_count', 0) >= condition_value

        elif condition_type == UnlockConditionType.ONLUS_DIVERSITY.value:
            return user_stats.get('onlus_diversity', 0) >= condition_value

        elif condition_type == UnlockConditionType.IMPACT_SCORE.value:
            return user_stats.get('impact_score', 0) >= condition_value

        elif condition_type == UnlockConditionType.SPECIAL_EVENT.value:
            special_events = user_stats.get('special_events', [])
            return str(int(condition_value)) in special_events

        elif condition_type == UnlockConditionType.TIME_BASED.value:
            # Time-based stories are always unlocked if active
            return True

        return False

    def get_unlock_progress(self, user_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get unlock progress for user.

        Args:
            user_stats: User statistics dictionary

        Returns:
            Dict containing progress information
        """
        condition_type = self.unlock_condition_type
        condition_value = self.unlock_condition_value

        if condition_type == UnlockConditionType.TOTAL_DONATED.value:
            current = user_stats.get('total_donated', 0)
            progress_percent = min(100, (current / condition_value) * 100) if condition_value > 0 else 100

        elif condition_type == UnlockConditionType.DONATION_COUNT.value:
            current = user_stats.get('donation_count', 0)
            progress_percent = min(100, (current / condition_value) * 100) if condition_value > 0 else 100

        elif condition_type == UnlockConditionType.ONLUS_DIVERSITY.value:
            current = user_stats.get('onlus_diversity', 0)
            progress_percent = min(100, (current / condition_value) * 100) if condition_value > 0 else 100

        elif condition_type == UnlockConditionType.IMPACT_SCORE.value:
            current = user_stats.get('impact_score', 0)
            progress_percent = min(100, (current / condition_value) * 100) if condition_value > 0 else 100

        else:
            current = 0
            progress_percent = 100 if self.check_unlock_status(user_stats) else 0

        return {
            'current_value': current,
            'required_value': condition_value,
            'progress_percent': round(progress_percent, 1),
            'is_unlocked': self.check_unlock_status(user_stats)
        }

    def is_featured(self) -> bool:
        """Check if story is currently featured."""
        if not self.featured_until:
            return False
        return datetime.now(timezone.utc) < self.featured_until

    def get_next_milestone_level(self) -> Optional[float]:
        """Get next donation milestone level after this story's unlock value."""
        if self.unlock_condition_type != UnlockConditionType.TOTAL_DONATED.value:
            return None

        current_value = self.unlock_condition_value
        for level in sorted(self.MILESTONE_LEVELS):
            if level > current_value:
                return float(level)
        return None

    def add_media(self, media_url: str) -> None:
        """Add media URL to story."""
        if media_url and media_url.startswith(('http://', 'https://')):
            if media_url not in self.media_urls:
                self.media_urls.append(media_url)
                self.updated_at = datetime.now(timezone.utc)

    def remove_media(self, media_url: str) -> None:
        """Remove media URL from story."""
        if media_url in self.media_urls:
            self.media_urls.remove(media_url)
            self.updated_at = datetime.now(timezone.utc)

    def add_tag(self, tag: str) -> None:
        """Add tag to story."""
        if tag and tag not in self.tags:
            self.tags.append(tag.lower())
            self.updated_at = datetime.now(timezone.utc)

    def remove_tag(self, tag: str) -> None:
        """Remove tag from story."""
        if tag in self.tags:
            self.tags.remove(tag.lower())
            self.updated_at = datetime.now(timezone.utc)

    def set_featured(self, until: datetime) -> None:
        """Set story as featured until specified date."""
        self.featured_until = until
        self.updated_at = datetime.now(timezone.utc)

    def clear_featured(self) -> None:
        """Remove featured status."""
        self.featured_until = None
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert story to dictionary for MongoDB storage."""
        return {
            '_id': self._id,
            'title': self.title,
            'content': self.content,
            'story_type': self.story_type,
            'unlock_condition_type': self.unlock_condition_type,
            'unlock_condition_value': self.unlock_condition_value,
            'onlus_id': self.onlus_id,
            'category': self.category,
            'media_urls': self.media_urls,
            'thumbnail_url': self.thumbnail_url,
            'estimated_read_time': self.estimated_read_time,
            'priority': self.priority,
            'is_active': self.is_active,
            'featured_until': self.featured_until,
            'author': self.author,
            'metadata': self.metadata,
            'tags': self.tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def to_response_dict(self, user_stats: Dict[str, Any] = None,
                        include_content: bool = True) -> Dict[str, Any]:
        """Convert story to dictionary for API responses."""
        response = {
            'id': str(self._id),
            'title': self.title,
            'story_type': self.story_type,
            'unlock_condition_type': self.unlock_condition_type,
            'unlock_condition_value': self.unlock_condition_value,
            'onlus_id': self.onlus_id,
            'category': self.category,
            'thumbnail_url': self.thumbnail_url,
            'estimated_read_time': self.estimated_read_time,
            'priority': self.priority,
            'is_featured': self.is_featured(),
            'author': self.author,
            'tags': self.tags,
            'media_count': len(self.media_urls),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        # Include content only if requested (e.g., when story is unlocked)
        if include_content:
            response.update({
                'content': self.content,
                'media_urls': self.media_urls
            })

        # Include unlock progress if user stats provided
        if user_stats is not None:
            progress = self.get_unlock_progress(user_stats)
            response.update({
                'unlock_progress': progress,
                'is_unlocked': progress['is_unlocked']
            })

        return response

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImpactStory':
        """Create ImpactStory instance from dictionary."""
        return cls(
            title=data.get('title'),
            content=data.get('content'),
            story_type=data.get('story_type'),
            unlock_condition_type=data.get('unlock_condition_type'),
            unlock_condition_value=data.get('unlock_condition_value', 0),
            onlus_id=data.get('onlus_id'),
            category=data.get('category'),
            media_urls=data.get('media_urls', []),
            thumbnail_url=data.get('thumbnail_url'),
            estimated_read_time=data.get('estimated_read_time', 5),
            priority=data.get('priority', 0),
            is_active=data.get('is_active', True),
            featured_until=data.get('featured_until'),
            author=data.get('author'),
            metadata=data.get('metadata', {}),
            tags=data.get('tags', []),
            _id=data.get('_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    @staticmethod
    def validate_story_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate story data for creation/updates.

        Args:
            data: Story data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "STORY_DATA_INVALID_FORMAT"

        # Required fields
        required_fields = ['title', 'content', 'story_type', 'unlock_condition_type', 'unlock_condition_value']
        for field in required_fields:
            if field not in data or not data[field]:
                return f"STORY_{field.upper()}_REQUIRED"

        # Validate story type
        if data['story_type'] not in [t.value for t in StoryType]:
            return "STORY_TYPE_INVALID"

        # Validate unlock condition type
        if data['unlock_condition_type'] not in [t.value for t in UnlockConditionType]:
            return "STORY_UNLOCK_CONDITION_TYPE_INVALID"

        # Validate unlock condition value
        try:
            unlock_value = float(data['unlock_condition_value'])
            if unlock_value < 0:
                return "STORY_UNLOCK_CONDITION_VALUE_NEGATIVE"
        except (ValueError, TypeError):
            return "STORY_UNLOCK_CONDITION_VALUE_INVALID"

        # Validate estimated read time
        if 'estimated_read_time' in data:
            try:
                read_time = int(data['estimated_read_time'])
                if read_time < 1:
                    return "STORY_READ_TIME_TOO_SHORT"
            except (ValueError, TypeError):
                return "STORY_READ_TIME_INVALID"

        # Validate media URLs
        if 'media_urls' in data and data['media_urls']:
            if not isinstance(data['media_urls'], list):
                return "STORY_MEDIA_URLS_INVALID_FORMAT"
            for url in data['media_urls']:
                if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                    return "STORY_MEDIA_URL_INVALID"

        return None

    @classmethod
    def create_milestone_story(cls, title: str, content: str, unlock_amount: float,
                              onlus_id: str = None, category: str = "milestone",
                              media_urls: List[str] = None, author: str = "system") -> 'ImpactStory':
        """
        Create a donation milestone story.

        Args:
            title: Story title
            content: Story content
            unlock_amount: Donation amount to unlock story
            onlus_id: Associated ONLUS
            category: Story category
            media_urls: Media URLs
            author: Story author

        Returns:
            ImpactStory: New milestone story
        """
        return cls(
            title=title,
            content=content,
            story_type=StoryType.MILESTONE.value,
            unlock_condition_type=UnlockConditionType.TOTAL_DONATED.value,
            unlock_condition_value=unlock_amount,
            onlus_id=onlus_id,
            category=category,
            media_urls=media_urls or [],
            author=author
        )

    def __repr__(self) -> str:
        return f'<ImpactStory {self.title}: {self.story_type} unlock@{self.unlock_condition_value}>'