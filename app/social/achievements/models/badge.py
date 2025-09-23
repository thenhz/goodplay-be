from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId


class Badge:
    """
    Model for user badges earned from achievements

    Collection: user_badges
    """

    # Badge rarities (inherited from Achievement)
    COMMON = 'common'
    RARE = 'rare'
    EPIC = 'epic'
    LEGENDARY = 'legendary'

    VALID_RARITIES = [COMMON, RARE, EPIC, LEGENDARY]

    def __init__(self, user_id: str, achievement_id: str, badge_name: str,
                 badge_description: str, rarity: str, icon_url: Optional[str] = None,
                 earned_at: Optional[datetime] = None, is_visible: bool = True,
                 _id: Optional[str] = None):
        """
        Initialize Badge

        Args:
            user_id: ID of the user who earned the badge
            achievement_id: ID of the achievement that awarded this badge
            badge_name: Display name of the badge
            badge_description: Description of the badge
            rarity: Rarity level of the badge
            icon_url: URL for badge icon
            earned_at: Timestamp when badge was earned
            is_visible: Whether badge is visible on user profile
            _id: MongoDB document ID
        """
        self._id = ObjectId(_id) if _id else ObjectId()
        self.user_id = ObjectId(user_id)
        self.achievement_id = achievement_id
        self.badge_name = badge_name
        self.badge_description = badge_description
        self.rarity = rarity
        self.icon_url = icon_url
        self.earned_at = earned_at or datetime.utcnow()
        self.is_visible = is_visible

        self._validate()

    def _validate(self):
        """Validate badge data"""
        if not self.badge_name or not isinstance(self.badge_name, str):
            raise ValueError("Badge name is required and must be string")

        if not self.badge_description or not isinstance(self.badge_description, str):
            raise ValueError("Badge description is required and must be string")

        if self.rarity not in self.VALID_RARITIES:
            raise ValueError(f"Invalid rarity: {self.rarity}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'badge_name': self.badge_name,
            'badge_description': self.badge_description,
            'rarity': self.rarity,
            'icon_url': self.icon_url,
            'earned_at': self.earned_at,
            'is_visible': self.is_visible
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Badge':
        """Create Badge from dictionary"""
        return cls(
            user_id=str(data['user_id']),
            achievement_id=data['achievement_id'],
            badge_name=data['badge_name'],
            badge_description=data['badge_description'],
            rarity=data['rarity'],
            icon_url=data.get('icon_url'),
            earned_at=data.get('earned_at'),
            is_visible=data.get('is_visible', True),
            _id=str(data['_id']) if '_id' in data else None
        )

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self._id),
            'user_id': str(self.user_id),
            'achievement_id': self.achievement_id,
            'badge_name': self.badge_name,
            'badge_description': self.badge_description,
            'rarity': self.rarity,
            'rarity_display': self.get_rarity_display(),
            'icon_url': self.icon_url,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'is_visible': self.is_visible
        }

    def get_rarity_display(self) -> str:
        """Get formatted rarity display name"""
        rarity_displays = {
            self.COMMON: 'Common',
            self.RARE: 'Rare',
            self.EPIC: 'Epic',
            self.LEGENDARY: 'Legendary'
        }
        return rarity_displays.get(self.rarity, 'Unknown')

    def get_rarity_color(self) -> str:
        """Get color code associated with rarity"""
        rarity_colors = {
            self.COMMON: '#808080',    # Gray
            self.RARE: '#0066CC',      # Blue
            self.EPIC: '#9933CC',      # Purple
            self.LEGENDARY: '#FF8000'  # Orange
        }
        return rarity_colors.get(self.rarity, '#000000')

    def get_rarity_priority(self) -> int:
        """Get priority value for sorting by rarity (higher = rarer)"""
        priorities = {
            self.COMMON: 1,
            self.RARE: 2,
            self.EPIC: 3,
            self.LEGENDARY: 4
        }
        return priorities.get(self.rarity, 0)

    def is_common(self) -> bool:
        """Check if badge is common rarity"""
        return self.rarity == self.COMMON

    def is_rare(self) -> bool:
        """Check if badge is rare rarity"""
        return self.rarity == self.RARE

    def is_epic(self) -> bool:
        """Check if badge is epic rarity"""
        return self.rarity == self.EPIC

    def is_legendary(self) -> bool:
        """Check if badge is legendary rarity"""
        return self.rarity == self.LEGENDARY

    def toggle_visibility(self):
        """Toggle badge visibility on user profile"""
        self.is_visible = not self.is_visible

    def set_visibility(self, visible: bool):
        """Set badge visibility"""
        self.is_visible = visible