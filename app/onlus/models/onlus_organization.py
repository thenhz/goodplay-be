from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class OrganizationStatus(Enum):
    """Status of verified ONLUS organization."""
    ACTIVE = "active"  # Organization is active and can receive donations
    INACTIVE = "inactive"  # Organization is temporarily inactive
    SUSPENDED = "suspended"  # Organization suspended due to issues
    UNDER_REVIEW = "under_review"  # Organization under compliance review
    DEACTIVATED = "deactivated"  # Organization permanently deactivated


class ComplianceStatus(Enum):
    """Compliance status of organization."""
    COMPLIANT = "compliant"  # Fully compliant
    MINOR_ISSUES = "minor_issues"  # Minor compliance issues
    MAJOR_ISSUES = "major_issues"  # Major compliance issues requiring attention
    NON_COMPLIANT = "non_compliant"  # Non-compliant, action required
    UNDER_INVESTIGATION = "under_investigation"  # Under compliance investigation


class VerificationLevel(Enum):
    """Level of verification completed."""
    BASIC = "basic"  # Basic verification completed
    STANDARD = "standard"  # Standard verification completed
    PREMIUM = "premium"  # Premium verification with enhanced checks
    GOLD = "gold"  # Gold level with ongoing monitoring


class ONLUSOrganization:
    """
    Model for verified ONLUS organizations.

    Represents organizations that have completed the verification
    process and are approved to receive donations through the platform.

    Collection: onlus_organizations
    """

    def __init__(self, application_id: str, organization_name: str,
                 legal_name: str, category: str, mission_statement: str,
                 description: str, contact_email: str, contact_phone: str,
                 website_url: str = None, logo_url: str = None,
                 address: Dict[str, str] = None,
                 legal_entity_type: str = None, tax_id: str = None,
                 incorporation_date: Optional[datetime] = None,
                 verification_date: Optional[datetime] = None,
                 operational_scope: str = None,
                 target_beneficiaries: str = None,
                 primary_activities: List[str] = None,
                 leadership_team: List[Dict[str, str]] = None,
                 board_members: List[Dict[str, str]] = None,
                 annual_budget: float = None,
                 funding_sources: List[str] = None,
                 impact_metrics: List[Dict[str, Any]] = None,
                 achievements: List[Dict[str, Any]] = None,
                 certifications: List[Dict[str, Any]] = None,
                 status: str = OrganizationStatus.ACTIVE.value,
                 compliance_status: str = ComplianceStatus.COMPLIANT.value,
                 verification_level: str = VerificationLevel.BASIC.value,
                 compliance_score: float = None,
                 transparency_score: float = None,
                 impact_score: float = None,
                 donor_rating: float = None,
                 total_donations_received: float = 0.0,
                 total_donors: int = 0,
                 last_donation_date: Optional[datetime] = None,
                 bank_account_verified: bool = False,
                 tax_deductible: bool = True,
                 featured_until: Optional[datetime] = None,
                 tags: List[str] = None,
                 social_media: Dict[str, str] = None,
                 documents: List[str] = None,
                 verification_checks: List[str] = None,
                 compliance_checks: List[str] = None,
                 last_compliance_review: Optional[datetime] = None,
                 next_review_date: Optional[datetime] = None,
                 metadata: Dict[str, Any] = None,
                 _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        """
        Initialize ONLUSOrganization.

        Args:
            application_id: Original application ID
            organization_name: Display name of organization
            legal_name: Legal name of organization
            category: ONLUS category
            mission_statement: Organization mission
            description: Detailed description
            contact_email: Primary contact email
            contact_phone: Primary contact phone
            website_url: Organization website
            logo_url: Organization logo URL
            address: Organization address
            legal_entity_type: Type of legal entity
            tax_id: Tax identification number
            incorporation_date: Incorporation date
            verification_date: When verification was completed
            operational_scope: Geographic/demographic scope
            target_beneficiaries: Target beneficiaries description
            primary_activities: List of primary activities
            leadership_team: Leadership team information
            board_members: Board members information
            annual_budget: Annual budget amount
            funding_sources: Sources of funding
            impact_metrics: Impact measurement data
            achievements: Organization achievements
            certifications: Professional certifications
            status: Current organization status
            compliance_status: Compliance status
            verification_level: Level of verification
            compliance_score: Compliance score (0-100)
            transparency_score: Transparency score (0-100)
            impact_score: Impact effectiveness score (0-100)
            donor_rating: Average donor rating (1-5)
            total_donations_received: Total donations received
            total_donors: Number of unique donors
            last_donation_date: Date of last donation
            bank_account_verified: Whether bank account is verified
            tax_deductible: Whether donations are tax deductible
            featured_until: Featured status expiration
            tags: Search and categorization tags
            social_media: Social media profiles
            documents: List of verified documents
            verification_checks: List of verification checks
            compliance_checks: List of compliance checks
            last_compliance_review: Last compliance review date
            next_review_date: Next scheduled review date
            metadata: Additional organization metadata
            _id: MongoDB document ID
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self._id = _id or ObjectId()
        self.application_id = application_id
        self.organization_name = organization_name
        self.legal_name = legal_name
        self.category = category
        self.mission_statement = mission_statement
        self.description = description
        self.contact_email = contact_email.lower()
        self.contact_phone = contact_phone
        self.website_url = website_url
        self.logo_url = logo_url
        self.address = address or {}
        self.legal_entity_type = legal_entity_type
        self.tax_id = tax_id
        self.incorporation_date = incorporation_date
        self.verification_date = verification_date or datetime.now(timezone.utc)
        self.operational_scope = operational_scope
        self.target_beneficiaries = target_beneficiaries
        self.primary_activities = primary_activities or []
        self.leadership_team = leadership_team or []
        self.board_members = board_members or []
        self.annual_budget = annual_budget
        self.funding_sources = funding_sources or []
        self.impact_metrics = impact_metrics or []
        self.achievements = achievements or []
        self.certifications = certifications or []
        self.status = status
        self.compliance_status = compliance_status
        self.verification_level = verification_level
        self.compliance_score = compliance_score
        self.transparency_score = transparency_score
        self.impact_score = impact_score
        self.donor_rating = donor_rating
        self.total_donations_received = total_donations_received
        self.total_donors = total_donors
        self.last_donation_date = last_donation_date
        self.bank_account_verified = bank_account_verified
        self.tax_deductible = tax_deductible
        self.featured_until = featured_until
        self.tags = tags or []
        self.social_media = social_media or {}
        self.documents = documents or []
        self.verification_checks = verification_checks or []
        self.compliance_checks = compliance_checks or []
        self.last_compliance_review = last_compliance_review
        self.next_review_date = next_review_date
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        org_dict = {
            '_id': self._id,
            'application_id': self.application_id,
            'organization_name': self.organization_name,
            'legal_name': self.legal_name,
            'category': self.category,
            'mission_statement': self.mission_statement,
            'description': self.description,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'website_url': self.website_url,
            'logo_url': self.logo_url,
            'address': self.address,
            'incorporation_date': self.incorporation_date,
            'verification_date': self.verification_date,
            'operational_scope': self.operational_scope,
            'target_beneficiaries': self.target_beneficiaries,
            'primary_activities': self.primary_activities,
            'annual_budget': self.annual_budget,
            'funding_sources': self.funding_sources,
            'impact_metrics': self.impact_metrics,
            'achievements': self.achievements,
            'certifications': self.certifications,
            'status': self.status,
            'compliance_status': self.compliance_status,
            'verification_level': self.verification_level,
            'compliance_score': self.compliance_score,
            'transparency_score': self.transparency_score,
            'impact_score': self.impact_score,
            'donor_rating': self.donor_rating,
            'total_donations_received': self.total_donations_received,
            'total_donors': self.total_donors,
            'last_donation_date': self.last_donation_date,
            'bank_account_verified': self.bank_account_verified,
            'tax_deductible': self.tax_deductible,
            'featured_until': self.featured_until,
            'tags': self.tags,
            'social_media': self.social_media,
            'documents': self.documents,
            'verification_checks': self.verification_checks,
            'compliance_checks': self.compliance_checks,
            'last_compliance_review': self.last_compliance_review,
            'next_review_date': self.next_review_date,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        # Include sensitive information only for authorized users
        if include_sensitive:
            org_dict.update({
                'legal_entity_type': self.legal_entity_type,
                'tax_id': self.tax_id,
                'leadership_team': self.leadership_team,
                'board_members': self.board_members
            })

        return org_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary."""
        if not data:
            return None

        return cls(
            _id=data.get('_id'),
            application_id=data.get('application_id'),
            organization_name=data.get('organization_name'),
            legal_name=data.get('legal_name'),
            category=data.get('category'),
            mission_statement=data.get('mission_statement'),
            description=data.get('description'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            website_url=data.get('website_url'),
            logo_url=data.get('logo_url'),
            address=data.get('address', {}),
            legal_entity_type=data.get('legal_entity_type'),
            tax_id=data.get('tax_id'),
            incorporation_date=data.get('incorporation_date'),
            verification_date=data.get('verification_date'),
            operational_scope=data.get('operational_scope'),
            target_beneficiaries=data.get('target_beneficiaries'),
            primary_activities=data.get('primary_activities', []),
            leadership_team=data.get('leadership_team', []),
            board_members=data.get('board_members', []),
            annual_budget=data.get('annual_budget'),
            funding_sources=data.get('funding_sources', []),
            impact_metrics=data.get('impact_metrics', []),
            achievements=data.get('achievements', []),
            certifications=data.get('certifications', []),
            status=data.get('status', OrganizationStatus.ACTIVE.value),
            compliance_status=data.get('compliance_status', ComplianceStatus.COMPLIANT.value),
            verification_level=data.get('verification_level', VerificationLevel.BASIC.value),
            compliance_score=data.get('compliance_score'),
            transparency_score=data.get('transparency_score'),
            impact_score=data.get('impact_score'),
            donor_rating=data.get('donor_rating'),
            total_donations_received=data.get('total_donations_received', 0.0),
            total_donors=data.get('total_donors', 0),
            last_donation_date=data.get('last_donation_date'),
            bank_account_verified=data.get('bank_account_verified', False),
            tax_deductible=data.get('tax_deductible', True),
            featured_until=data.get('featured_until'),
            tags=data.get('tags', []),
            social_media=data.get('social_media', {}),
            documents=data.get('documents', []),
            verification_checks=data.get('verification_checks', []),
            compliance_checks=data.get('compliance_checks', []),
            last_compliance_review=data.get('last_compliance_review'),
            next_review_date=data.get('next_review_date'),
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    @staticmethod
    def validate_organization_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate organization data.

        Args:
            data: Organization data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "ORGANIZATION_DATA_INVALID"

        # Required fields
        required_fields = [
            'application_id', 'organization_name', 'legal_name',
            'category', 'mission_statement', 'description',
            'contact_email', 'contact_phone'
        ]

        for field in required_fields:
            if not data.get(field):
                return f"{field.upper()}_REQUIRED"

        # Validate email format
        email = data.get('contact_email', '')
        if '@' not in email or '.' not in email:
            return "CONTACT_EMAIL_INVALID"

        # Validate status
        status = data.get('status', OrganizationStatus.ACTIVE.value)
        if status not in [s.value for s in OrganizationStatus]:
            return "ORGANIZATION_STATUS_INVALID"

        # Validate compliance status
        compliance_status = data.get('compliance_status', ComplianceStatus.COMPLIANT.value)
        if compliance_status not in [cs.value for cs in ComplianceStatus]:
            return "COMPLIANCE_STATUS_INVALID"

        # Validate verification level
        verification_level = data.get('verification_level', VerificationLevel.BASIC.value)
        if verification_level not in [vl.value for vl in VerificationLevel]:
            return "VERIFICATION_LEVEL_INVALID"

        # Validate scores
        score_fields = ['compliance_score', 'transparency_score', 'impact_score']
        for field in score_fields:
            score = data.get(field)
            if score is not None and (not isinstance(score, (int, float)) or score < 0 or score > 100):
                return f"{field.upper()}_INVALID"

        # Validate donor rating
        rating = data.get('donor_rating')
        if rating is not None and (not isinstance(rating, (int, float)) or rating < 1 or rating > 5):
            return "DONOR_RATING_INVALID"

        # Validate donation amounts
        for field in ['total_donations_received', 'annual_budget']:
            amount = data.get(field)
            if amount is not None and (not isinstance(amount, (int, float)) or amount < 0):
                return f"{field.upper()}_INVALID"

        return None

    def update_donation_stats(self, amount: float, is_new_donor: bool = False):
        """Update donation statistics."""
        if amount > 0:
            self.total_donations_received += amount
            if is_new_donor:
                self.total_donors += 1
            self.last_donation_date = datetime.now(timezone.utc)
            self.updated_at = datetime.now(timezone.utc)

    def update_rating(self, new_rating: float, total_ratings: int):
        """Update donor rating with new rating."""
        if 1 <= new_rating <= 5:
            current_total = (self.donor_rating or 0) * (total_ratings - 1)
            self.donor_rating = (current_total + new_rating) / total_ratings
            self.updated_at = datetime.now(timezone.utc)

    def update_compliance_status(self, status: str, score: float = None):
        """Update compliance status and score."""
        if status in [cs.value for cs in ComplianceStatus]:
            self.compliance_status = status
            if score is not None:
                self.compliance_score = score
            self.last_compliance_review = datetime.now(timezone.utc)
            self.next_review_date = datetime.now(timezone.utc) + timedelta(days=365)
            self.updated_at = datetime.now(timezone.utc)

    def suspend_organization(self, reason: str):
        """Suspend the organization."""
        self.status = OrganizationStatus.SUSPENDED.value
        self.metadata['suspension_reason'] = reason
        self.metadata['suspension_date'] = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def reactivate_organization(self):
        """Reactivate a suspended organization."""
        if self.status == OrganizationStatus.SUSPENDED.value:
            self.status = OrganizationStatus.ACTIVE.value
            self.metadata.pop('suspension_reason', None)
            self.metadata.pop('suspension_date', None)
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def set_featured(self, duration_days: int = 30):
        """Set organization as featured for specified duration."""
        self.featured_until = datetime.now(timezone.utc) + timedelta(days=duration_days)
        self.updated_at = datetime.now(timezone.utc)

    def is_featured(self) -> bool:
        """Check if organization is currently featured."""
        if self.featured_until:
            return datetime.now(timezone.utc) < self.featured_until
        return False

    def is_eligible_for_donations(self) -> bool:
        """Check if organization can receive donations."""
        return (self.status == OrganizationStatus.ACTIVE.value and
                self.compliance_status in [
                    ComplianceStatus.COMPLIANT.value,
                    ComplianceStatus.MINOR_ISSUES.value
                ] and
                self.bank_account_verified)

    def needs_compliance_review(self) -> bool:
        """Check if organization needs compliance review."""
        if self.next_review_date:
            return datetime.now(timezone.utc) >= self.next_review_date
        return True

    def get_overall_score(self) -> float:
        """Calculate overall organization score."""
        scores = []
        if self.compliance_score is not None:
            scores.append(self.compliance_score * 0.4)  # 40% weight
        if self.transparency_score is not None:
            scores.append(self.transparency_score * 0.3)  # 30% weight
        if self.impact_score is not None:
            scores.append(self.impact_score * 0.3)  # 30% weight

        return sum(scores) / len(scores) if scores else 0.0

    def add_achievement(self, title: str, description: str, date: datetime = None):
        """Add an achievement to the organization."""
        achievement = {
            'title': title,
            'description': description,
            'date': date or datetime.now(timezone.utc),
            'id': str(ObjectId())
        }
        self.achievements.append(achievement)
        self.updated_at = datetime.now(timezone.utc)

    def add_certification(self, name: str, issuer: str, date: datetime = None,
                         expiry_date: datetime = None):
        """Add a certification to the organization."""
        certification = {
            'name': name,
            'issuer': issuer,
            'issue_date': date or datetime.now(timezone.utc),
            'expiry_date': expiry_date,
            'id': str(ObjectId())
        }
        self.certifications.append(certification)
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        return f'<ONLUSOrganization {self.organization_name}: {self.status}>'