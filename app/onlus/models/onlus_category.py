from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class ONLUSCategory(Enum):
    """Primary categories for ONLUS organizations."""
    HEALTHCARE = "healthcare"  # Medical research, hospitals, health awareness
    EDUCATION = "education"  # Schools, scholarships, educational programs
    ENVIRONMENT = "environment"  # Conservation, climate action, sustainability
    SOCIAL_SERVICES = "social_services"  # Poverty relief, disability support, homelessness
    HUMANITARIAN = "humanitarian"  # Disaster relief, refugee assistance, human rights
    ARTS_CULTURE = "arts_culture"  # Museums, cultural preservation, community arts
    ANIMAL_WELFARE = "animal_welfare"  # Animal rights, wildlife conservation, pet rescue
    RESEARCH = "research"  # Scientific research, academic institutions
    COMMUNITY = "community"  # Community development, local initiatives
    OTHER = "other"  # Other charitable causes


class ONLUSCategoryInfo:
    """
    Model for ONLUS category information and requirements.

    Provides category definitions, verification requirements,
    and compliance standards for each ONLUS category.

    Collection: onlus_categories
    """

    def __init__(self, category: str, name: str, description: str,
                 verification_requirements: List[str] = None,
                 compliance_standards: List[str] = None,
                 icon: str = None, color: str = None,
                 is_active: bool = True, priority: int = 0,
                 metadata: Dict[str, Any] = None,
                 _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """
        Initialize ONLUSCategoryInfo.

        Args:
            category: Category enum value
            name: Display name for the category
            description: Category description
            verification_requirements: List of required verification documents
            compliance_standards: List of compliance standards for this category
            icon: Icon identifier for UI display
            color: Color code for UI display
            is_active: Whether category is currently active
            priority: Display priority (higher = more prominent)
            metadata: Additional category metadata
            _id: MongoDB document ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self._id = _id or ObjectId()
        self.category = category
        self.name = name
        self.description = description
        self.verification_requirements = verification_requirements or []
        self.compliance_standards = compliance_standards or []
        self.icon = icon
        self.color = color
        self.is_active = is_active
        self.priority = priority
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            '_id': self._id,
            'category': self.category,
            'name': self.name,
            'description': self.description,
            'verification_requirements': self.verification_requirements,
            'compliance_standards': self.compliance_standards,
            'icon': self.icon,
            'color': self.color,
            'is_active': self.is_active,
            'priority': self.priority,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary."""
        if not data:
            return None

        return cls(
            _id=data.get('_id'),
            category=data.get('category'),
            name=data.get('name'),
            description=data.get('description'),
            verification_requirements=data.get('verification_requirements', []),
            compliance_standards=data.get('compliance_standards', []),
            icon=data.get('icon'),
            color=data.get('color'),
            is_active=data.get('is_active', True),
            priority=data.get('priority', 0),
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    @staticmethod
    def validate_category_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate category data.

        Args:
            data: Category data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "CATEGORY_DATA_INVALID"

        # Required fields
        if not data.get('category'):
            return "CATEGORY_REQUIRED"
        if not data.get('name'):
            return "CATEGORY_NAME_REQUIRED"
        if not data.get('description'):
            return "CATEGORY_DESCRIPTION_REQUIRED"

        # Validate category enum
        if data['category'] not in [cat.value for cat in ONLUSCategory]:
            return "CATEGORY_INVALID"

        # Validate verification requirements
        verification_reqs = data.get('verification_requirements', [])
        if not isinstance(verification_reqs, list):
            return "VERIFICATION_REQUIREMENTS_INVALID"

        # Validate compliance standards
        compliance_stds = data.get('compliance_standards', [])
        if not isinstance(compliance_stds, list):
            return "COMPLIANCE_STANDARDS_INVALID"

        # Validate priority
        priority = data.get('priority', 0)
        if not isinstance(priority, int) or priority < 0:
            return "CATEGORY_PRIORITY_INVALID"

        return None

    def update_verification_requirements(self, requirements: List[str]):
        """Update verification requirements for this category."""
        if isinstance(requirements, list):
            self.verification_requirements = requirements
            self.updated_at = datetime.now(timezone.utc)

    def update_compliance_standards(self, standards: List[str]):
        """Update compliance standards for this category."""
        if isinstance(standards, list):
            self.compliance_standards = standards
            self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f'<ONLUSCategoryInfo {self.category}: {self.name}>'