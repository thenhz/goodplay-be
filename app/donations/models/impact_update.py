from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class UpdateType(Enum):
    """Types of impact updates from ONLUS."""
    MILESTONE_REACHED = "milestone_reached"  # Major milestone achieved
    PROJECT_COMPLETED = "project_completed"  # Project completion
    BENEFICIARY_STORY = "beneficiary_story"  # Story from beneficiaries
    FINANCIAL_REPORT = "financial_report"  # Financial transparency update
    OPERATIONAL_UPDATE = "operational_update"  # Operational progress
    EMERGENCY_RESPONSE = "emergency_response"  # Emergency/urgent updates
    SEASONAL_CAMPAIGN = "seasonal_campaign"  # Seasonal campaign updates
    PARTNERSHIP_NEWS = "partnership_news"  # New partnerships/collaborations


class UpdatePriority(Enum):
    """Priority levels for impact updates."""
    LOW = "low"  # General updates, low urgency
    NORMAL = "normal"  # Standard updates
    HIGH = "high"  # Important updates requiring attention
    URGENT = "urgent"  # Urgent updates requiring immediate attention
    CRITICAL = "critical"  # Critical updates for emergencies


class UpdateStatus(Enum):
    """Status of impact updates."""
    DRAFT = "draft"  # Draft, not yet published
    PUBLISHED = "published"  # Published and visible
    FEATURED = "featured"  # Featured on main dashboard
    ARCHIVED = "archived"  # Archived, no longer displayed
    REMOVED = "removed"  # Removed due to issues


class ImpactUpdate:
    """
    Model for real-time impact updates from ONLUS organizations.

    These updates provide transparency and engagement by showing donors
    the real-time progress and impact of their contributions.

    Collection: impact_updates
    """

    def __init__(self, onlus_id: str, title: str, content: str, update_type: str,
                 priority: str = "normal", status: str = "published",
                 related_metric_ids: List[str] = None, affected_donation_ids: List[str] = None,
                 media_urls: List[str] = None, thumbnail_url: str = None,
                 location: str = None, beneficiary_count: int = None,
                 financial_impact: float = None, tags: List[str] = None,
                 author: str = None, contact_info: str = None,
                 featured_until: Optional[datetime] = None, publish_at: Optional[datetime] = None,
                 metadata: Dict[str, Any] = None, _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None,
                 published_at: Optional[datetime] = None):
        """
        Initialize ImpactUpdate.

        Args:
            onlus_id: ID of the ONLUS organization
            title: Update title
            content: Update content (supports Markdown)
            update_type: Type of update
            priority: Priority level of the update
            status: Current status of the update
            related_metric_ids: IDs of related impact metrics
            affected_donation_ids: IDs of donations contributing to this update
            media_urls: List of media URLs (images, videos)
            thumbnail_url: Thumbnail image URL
            location: Geographic location of the impact
            beneficiary_count: Number of beneficiaries affected
            financial_impact: Financial impact amount
            tags: Tags for categorization
            author: Author of the update
            contact_info: Contact information for questions
            featured_until: Featured status expiration
            publish_at: Scheduled publish time
            metadata: Additional update metadata
            _id: MongoDB document ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
            published_at: Publication timestamp
        """
        self._id = _id or ObjectId()
        self.onlus_id = onlus_id
        self.title = title
        self.content = content
        self.update_type = update_type
        self.priority = priority
        self.status = status
        self.related_metric_ids = related_metric_ids or []
        self.affected_donation_ids = affected_donation_ids or []
        self.media_urls = media_urls or []
        self.thumbnail_url = thumbnail_url
        self.location = location
        self.beneficiary_count = beneficiary_count
        self.financial_impact = float(financial_impact) if financial_impact else None
        self.tags = tags or []
        self.author = author
        self.contact_info = contact_info
        self.featured_until = featured_until
        self.publish_at = publish_at
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.published_at = published_at

        # Additional metadata
        self.metadata = metadata or {}

        # Validation
        self._validate()

    def _validate(self):
        """Validate update data."""
        if not self.onlus_id:
            raise ValueError("ONLUS ID cannot be empty")

        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Update title cannot be empty")

        if not self.content or len(self.content.strip()) == 0:
            raise ValueError("Update content cannot be empty")

        if self.update_type not in [t.value for t in UpdateType]:
            raise ValueError(f"Invalid update type: {self.update_type}")

        if self.priority not in [p.value for p in UpdatePriority]:
            raise ValueError(f"Invalid priority: {self.priority}")

        if self.status not in [s.value for s in UpdateStatus]:
            raise ValueError(f"Invalid status: {self.status}")

        if self.beneficiary_count is not None and self.beneficiary_count < 0:
            raise ValueError("Beneficiary count cannot be negative")

        if self.financial_impact is not None and self.financial_impact < 0:
            raise ValueError("Financial impact cannot be negative")

        # Validate media URLs format
        for url in self.media_urls:
            if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid media URL format: {url}")

    def publish(self) -> None:
        """Publish the update."""
        if self.status == UpdateStatus.DRAFT.value:
            self.status = UpdateStatus.PUBLISHED.value
            self.published_at = datetime.now(timezone.utc)
            self.updated_at = datetime.now(timezone.utc)

    def feature(self, until: datetime = None) -> None:
        """Feature the update on dashboard."""
        self.status = UpdateStatus.FEATURED.value
        self.featured_until = until
        self.updated_at = datetime.now(timezone.utc)

    def unfeature(self) -> None:
        """Remove featured status."""
        if self.status == UpdateStatus.FEATURED.value:
            self.status = UpdateStatus.PUBLISHED.value
        self.featured_until = None
        self.updated_at = datetime.now(timezone.utc)

    def archive(self) -> None:
        """Archive the update."""
        self.status = UpdateStatus.ARCHIVED.value
        self.updated_at = datetime.now(timezone.utc)

    def is_published(self) -> bool:
        """Check if update is published."""
        return self.status in [UpdateStatus.PUBLISHED.value, UpdateStatus.FEATURED.value]

    def is_featured(self) -> bool:
        """Check if update is currently featured."""
        if self.status != UpdateStatus.FEATURED.value:
            return False

        if self.featured_until is None:
            return True

        return datetime.now(timezone.utc) < self.featured_until

    def is_scheduled(self) -> bool:
        """Check if update is scheduled for future publication."""
        if self.status != UpdateStatus.DRAFT.value or not self.publish_at:
            return False

        return self.publish_at > datetime.now(timezone.utc)

    def should_auto_publish(self) -> bool:
        """Check if update should be auto-published now."""
        if not self.is_scheduled():
            return False

        return datetime.now(timezone.utc) >= self.publish_at

    def get_age_hours(self) -> float:
        """Get age of update in hours since publication."""
        if not self.published_at:
            return 0.0

        age = datetime.now(timezone.utc) - self.published_at
        return age.total_seconds() / 3600

    def is_recent(self, hours: int = 24) -> bool:
        """Check if update is recent (within specified hours)."""
        return self.get_age_hours() <= hours

    def add_related_metric(self, metric_id: str) -> None:
        """Add related metric ID."""
        if metric_id and metric_id not in self.related_metric_ids:
            self.related_metric_ids.append(metric_id)
            self.updated_at = datetime.now(timezone.utc)

    def remove_related_metric(self, metric_id: str) -> None:
        """Remove related metric ID."""
        if metric_id in self.related_metric_ids:
            self.related_metric_ids.remove(metric_id)
            self.updated_at = datetime.now(timezone.utc)

    def add_affected_donation(self, donation_id: str) -> None:
        """Add affected donation ID."""
        if donation_id and donation_id not in self.affected_donation_ids:
            self.affected_donation_ids.append(donation_id)
            self.updated_at = datetime.now(timezone.utc)

    def add_media(self, media_url: str) -> None:
        """Add media URL to update."""
        if media_url and media_url.startswith(('http://', 'https://')):
            if media_url not in self.media_urls:
                self.media_urls.append(media_url)
                self.updated_at = datetime.now(timezone.utc)

    def remove_media(self, media_url: str) -> None:
        """Remove media URL from update."""
        if media_url in self.media_urls:
            self.media_urls.remove(media_url)
            self.updated_at = datetime.now(timezone.utc)

    def add_tag(self, tag: str) -> None:
        """Add tag to update."""
        if tag and tag not in self.tags:
            self.tags.append(tag.lower())
            self.updated_at = datetime.now(timezone.utc)

    def remove_tag(self, tag: str) -> None:
        """Remove tag from update."""
        if tag in self.tags:
            self.tags.remove(tag.lower())
            self.updated_at = datetime.now(timezone.utc)

    def get_priority_score(self) -> int:
        """Get numeric priority score for sorting."""
        priority_scores = {
            UpdatePriority.LOW.value: 1,
            UpdatePriority.NORMAL.value: 2,
            UpdatePriority.HIGH.value: 3,
            UpdatePriority.URGENT.value: 4,
            UpdatePriority.CRITICAL.value: 5
        }
        return priority_scores.get(self.priority, 2)

    def get_engagement_metrics(self) -> Dict[str, Any]:
        """Get engagement metrics for the update."""
        return {
            'view_count': self.metadata.get('view_count', 0),
            'like_count': self.metadata.get('like_count', 0),
            'share_count': self.metadata.get('share_count', 0),
            'comment_count': self.metadata.get('comment_count', 0),
            'donation_count': len(self.affected_donation_ids),
            'age_hours': self.get_age_hours(),
            'is_recent': self.is_recent(),
            'priority_score': self.get_priority_score()
        }

    def increment_view_count(self) -> None:
        """Increment view count."""
        if 'view_count' not in self.metadata:
            self.metadata['view_count'] = 0
        self.metadata['view_count'] += 1

    def increment_engagement(self, action: str) -> None:
        """Increment engagement metric."""
        if action in ['like', 'share', 'comment']:
            key = f'{action}_count'
            if key not in self.metadata:
                self.metadata[key] = 0
            self.metadata[key] += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert update to dictionary for MongoDB storage."""
        return {
            '_id': self._id,
            'onlus_id': self.onlus_id,
            'title': self.title,
            'content': self.content,
            'update_type': self.update_type,
            'priority': self.priority,
            'status': self.status,
            'related_metric_ids': self.related_metric_ids,
            'affected_donation_ids': self.affected_donation_ids,
            'media_urls': self.media_urls,
            'thumbnail_url': self.thumbnail_url,
            'location': self.location,
            'beneficiary_count': self.beneficiary_count,
            'financial_impact': self.financial_impact,
            'tags': self.tags,
            'author': self.author,
            'contact_info': self.contact_info,
            'featured_until': self.featured_until,
            'publish_at': self.publish_at,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'published_at': self.published_at
        }

    def to_response_dict(self, include_content: bool = True) -> Dict[str, Any]:
        """Convert update to dictionary for API responses."""
        response = {
            'id': str(self._id),
            'onlus_id': self.onlus_id,
            'title': self.title,
            'update_type': self.update_type,
            'priority': self.priority,
            'priority_score': self.get_priority_score(),
            'status': self.status,
            'is_published': self.is_published(),
            'is_featured': self.is_featured(),
            'is_recent': self.is_recent(),
            'thumbnail_url': self.thumbnail_url,
            'location': self.location,
            'beneficiary_count': self.beneficiary_count,
            'financial_impact': self.financial_impact,
            'tags': self.tags,
            'author': self.author,
            'media_count': len(self.media_urls),
            'related_metrics_count': len(self.related_metric_ids),
            'affected_donations_count': len(self.affected_donation_ids),
            'engagement_metrics': self.get_engagement_metrics(),
            'age_hours': self.get_age_hours(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }

        # Include full content and media if requested
        if include_content:
            response.update({
                'content': self.content,
                'media_urls': self.media_urls,
                'contact_info': self.contact_info,
                'related_metric_ids': self.related_metric_ids,
                'affected_donation_ids': self.affected_donation_ids
            })

        # Include scheduled publish time for drafts
        if self.is_scheduled():
            response['publish_at'] = self.publish_at.isoformat()

        # Include featured expiration if applicable
        if self.featured_until:
            response['featured_until'] = self.featured_until.isoformat()

        return response

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImpactUpdate':
        """Create ImpactUpdate instance from dictionary."""
        return cls(
            onlus_id=data.get('onlus_id'),
            title=data.get('title'),
            content=data.get('content'),
            update_type=data.get('update_type'),
            priority=data.get('priority', 'normal'),
            status=data.get('status', 'published'),
            related_metric_ids=data.get('related_metric_ids', []),
            affected_donation_ids=data.get('affected_donation_ids', []),
            media_urls=data.get('media_urls', []),
            thumbnail_url=data.get('thumbnail_url'),
            location=data.get('location'),
            beneficiary_count=data.get('beneficiary_count'),
            financial_impact=data.get('financial_impact'),
            tags=data.get('tags', []),
            author=data.get('author'),
            contact_info=data.get('contact_info'),
            featured_until=data.get('featured_until'),
            publish_at=data.get('publish_at'),
            metadata=data.get('metadata', {}),
            _id=data.get('_id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            published_at=data.get('published_at')
        )

    @staticmethod
    def validate_update_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate update data for creation/updates.

        Args:
            data: Update data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "UPDATE_DATA_INVALID_FORMAT"

        # Required fields
        required_fields = ['onlus_id', 'title', 'content', 'update_type']
        for field in required_fields:
            if field not in data or not data[field]:
                return f"UPDATE_{field.upper()}_REQUIRED"

        # Validate update type
        if data['update_type'] not in [t.value for t in UpdateType]:
            return "UPDATE_TYPE_INVALID"

        # Validate priority
        if 'priority' in data and data['priority'] not in [p.value for p in UpdatePriority]:
            return "UPDATE_PRIORITY_INVALID"

        # Validate status
        if 'status' in data and data['status'] not in [s.value for s in UpdateStatus]:
            return "UPDATE_STATUS_INVALID"

        # Validate beneficiary count
        if 'beneficiary_count' in data and data['beneficiary_count'] is not None:
            try:
                beneficiary_count = int(data['beneficiary_count'])
                if beneficiary_count < 0:
                    return "UPDATE_BENEFICIARY_COUNT_NEGATIVE"
            except (ValueError, TypeError):
                return "UPDATE_BENEFICIARY_COUNT_INVALID"

        # Validate financial impact
        if 'financial_impact' in data and data['financial_impact'] is not None:
            try:
                financial_impact = float(data['financial_impact'])
                if financial_impact < 0:
                    return "UPDATE_FINANCIAL_IMPACT_NEGATIVE"
            except (ValueError, TypeError):
                return "UPDATE_FINANCIAL_IMPACT_INVALID"

        # Validate media URLs
        if 'media_urls' in data and data['media_urls']:
            if not isinstance(data['media_urls'], list):
                return "UPDATE_MEDIA_URLS_INVALID_FORMAT"
            for url in data['media_urls']:
                if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                    return "UPDATE_MEDIA_URL_INVALID"

        return None

    @classmethod
    def create_milestone_update(cls, onlus_id: str, title: str, content: str,
                               milestone_value: float, beneficiary_count: int = None,
                               media_urls: List[str] = None) -> 'ImpactUpdate':
        """Create a milestone achievement update."""
        return cls(
            onlus_id=onlus_id,
            title=title,
            content=content,
            update_type=UpdateType.MILESTONE_REACHED.value,
            priority=UpdatePriority.HIGH.value,
            financial_impact=milestone_value,
            beneficiary_count=beneficiary_count,
            media_urls=media_urls or []
        )

    @classmethod
    def create_emergency_update(cls, onlus_id: str, title: str, content: str,
                               location: str = None, beneficiary_count: int = None) -> 'ImpactUpdate':
        """Create an emergency response update."""
        return cls(
            onlus_id=onlus_id,
            title=title,
            content=content,
            update_type=UpdateType.EMERGENCY_RESPONSE.value,
            priority=UpdatePriority.CRITICAL.value,
            location=location,
            beneficiary_count=beneficiary_count
        )

    def __repr__(self) -> str:
        return f'<ImpactUpdate {self.title}: {self.update_type} ({self.priority})>'