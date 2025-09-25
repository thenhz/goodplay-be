"""
ONLUS Factory Module

Factory-Boy implementations for generating ONLUS (Non-profit organization)
domain objects including organizations, campaigns, and charity-related models
with realistic data and proper organizational relationships.
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import factory
from factory import LazyFunction, LazyAttribute, Sequence, Trait, SubFactory
from faker import Faker

# Import our custom providers and base classes
from tests.factories.base import MongoFactory, TimestampMixin, fake
from tests.factories.providers import CauseProvider, FinancialDataProvider

# Register our custom providers
fake.add_provider(CauseProvider)
fake.add_provider(FinancialDataProvider)


class ONLUSFactory(MongoFactory):
    """Factory-Boy factory for creating ONLUS (Non-profit organization) objects

    Creates charity organizations with realistic operational data,
    financial tracking, and impact metrics.

    Usage:
        onlus = ONLUSFactory()  # Basic charity
        large = ONLUSFactory(large_org=True)  # Large organization
        local = ONLUSFactory(local_charity=True)  # Local charity
    """

    class Meta:
        model = dict

    onlus_id = Sequence(lambda n: f'onlus_{n}_{fake.uuid4()[:8]}')

    # Basic organization information
    name = LazyFunction(fake.onlus_name)
    legal_name = LazyAttribute(lambda obj: f"{obj.name}, Inc." if random.random() > 0.3 else obj.name)
    organization_type = LazyFunction(fake.onlus_type)

    # Contact and location
    email = LazyAttribute(lambda obj: f"contact@{obj.name.lower().replace(' ', '').replace(',', '')}.org")
    phone = LazyFunction(fake.phone_number)
    website = LazyAttribute(lambda obj: f"https://www.{obj.name.lower().replace(' ', '').replace(',', '')}.org")

    # Address information
    address = LazyFunction(lambda: {
        'street': fake.street_address(),
        'city': fake.city(),
        'state': fake.state(),
        'country': fake.country(),
        'postal_code': fake.postcode()
    })

    # Mission and description
    mission_statement = LazyFunction(lambda: fake.text(max_nb_chars=300))
    description = LazyFunction(lambda: fake.text(max_nb_chars=500))
    short_description = LazyFunction(lambda: fake.sentence())

    # Cause areas
    primary_cause = LazyFunction(fake.donation_cause)
    secondary_causes = LazyFunction(lambda: fake.donation_causes(count=random.randint(1, 3)))

    # Legal and operational status
    tax_id = LazyFunction(lambda: f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}")
    registration_number = LazyFunction(lambda: f"REG{random.randint(100000, 999999)}")
    is_verified = LazyFunction(lambda: random.choice([True, True, True, False]))  # 75% verified
    verification_date = LazyAttribute(lambda obj: fake.date_time_between(
        start_date='-2y', end_date='-1m'
    ) if obj.is_verified else None)

    # Operational status
    is_active = LazyFunction(lambda: random.choice([True, True, True, False]))  # 75% active
    status = LazyAttribute(lambda obj: random.choice(['active', 'pending']) if obj.is_active else 'suspended')

    # Financial information
    annual_budget = LazyFunction(lambda: round(random.uniform(10000, 10000000), 2))
    total_donations_received = LazyFunction(lambda: round(random.uniform(5000, 5000000), 2))
    administrative_cost_percentage = LazyFunction(lambda: round(random.uniform(5, 25), 1))

    # Impact metrics
    beneficiaries_served = LazyFunction(lambda: random.randint(100, 100000))
    projects_completed = LazyFunction(lambda: random.randint(5, 500))
    active_projects = LazyFunction(lambda: random.randint(1, 50))

    # Ratings and transparency
    transparency_score = LazyFunction(lambda: round(random.uniform(7.0, 10.0), 1))
    efficiency_rating = LazyFunction(lambda: random.choice(['A+', 'A', 'A-', 'B+', 'B', 'B-']))
    donor_rating = LazyFunction(lambda: round(random.uniform(4.0, 5.0), 1))

    # Media and branding
    logo_url = LazyFunction(lambda: f"https://cdn.goodplay.test/onlus/{fake.uuid4()[:8]}/logo.png")
    banner_image_url = LazyFunction(lambda: f"https://cdn.goodplay.test/onlus/{fake.uuid4()[:8]}/banner.jpg")
    social_media = LazyFunction(lambda: {
        'facebook': f"https://facebook.com/{fake.user_name()}",
        'twitter': f"https://twitter.com/{fake.user_name()}",
        'instagram': f"https://instagram.com/{fake.user_name()}" if random.random() > 0.3 else None,
        'linkedin': f"https://linkedin.com/company/{fake.user_name()}" if random.random() > 0.5 else None
    })

    # Team information
    team_size = LazyFunction(lambda: random.randint(3, 100))
    volunteers_count = LazyFunction(lambda: random.randint(10, 1000))

    # Partnership and certifications
    partner_organizations = LazyFunction(lambda: [
        fake.onlus_name() for _ in range(random.randint(0, 5))
    ])
    certifications = LazyFunction(lambda: random.sample([
        'GuideStar Seal', 'Charity Navigator 4-Star', 'BBB Accredited',
        'GiveWell Recommended', 'Candid Platinum Seal', 'Great Nonprofits Top-Rated'
    ], random.randint(0, 3)))

    # Geographic operation scope
    operation_scope = LazyFunction(lambda: random.choice(['local', 'regional', 'national', 'international']))
    countries_served = LazyFunction(lambda: [
        fake.country() for _ in range(random.randint(1, 10))
    ])

    # Organization type traits
    class Params:
        large_org = factory.Trait(
            annual_budget=LazyFunction(lambda: round(random.uniform(1000000, 50000000), 2)),
            total_donations_received=LazyFunction(lambda: round(random.uniform(500000, 25000000), 2)),
            team_size=LazyFunction(lambda: random.randint(50, 500)),
            volunteers_count=LazyFunction(lambda: random.randint(500, 5000)),
            beneficiaries_served=LazyFunction(lambda: random.randint(10000, 1000000)),
            projects_completed=LazyFunction(lambda: random.randint(50, 1000)),
            operation_scope='international',
            is_verified=True,
            transparency_score=LazyFunction(lambda: round(random.uniform(8.5, 10.0), 1)),
            efficiency_rating=LazyFunction(lambda: random.choice(['A+', 'A', 'A-'])),
            administrative_cost_percentage=LazyFunction(lambda: round(random.uniform(5, 15), 1))
        )

        local_charity = factory.Trait(
            annual_budget=LazyFunction(lambda: round(random.uniform(10000, 500000), 2)),
            total_donations_received=LazyFunction(lambda: round(random.uniform(5000, 250000), 2)),
            team_size=LazyFunction(lambda: random.randint(3, 25)),
            volunteers_count=LazyFunction(lambda: random.randint(10, 200)),
            beneficiaries_served=LazyFunction(lambda: random.randint(100, 5000)),
            projects_completed=LazyFunction(lambda: random.randint(5, 50)),
            operation_scope='local',
            countries_served=LazyFunction(lambda: [fake.country()]),
            administrative_cost_percentage=LazyFunction(lambda: round(random.uniform(10, 25), 1))
        )

        emergency_relief = factory.Trait(
            primary_cause='disaster_relief',
            secondary_causes=['emergency_response', 'humanitarian_aid'],
            organization_type='Emergency Relief Organization',
            operation_scope='international',
            active_projects=LazyFunction(lambda: random.randint(5, 25)),
            is_verified=True
        )

        education_focused = factory.Trait(
            primary_cause='education',
            secondary_causes=['children', 'research'],
            organization_type='Educational Foundation',
            beneficiaries_served=LazyFunction(lambda: random.randint(1000, 50000)),
            projects_completed=LazyFunction(lambda: random.randint(20, 200))
        )

        environmental = factory.Trait(
            primary_cause='environment',
            secondary_causes=['animals', 'research'],
            organization_type='Environmental NGO',
            projects_completed=LazyFunction(lambda: random.randint(10, 100)),
            operation_scope=LazyFunction(lambda: random.choice(['regional', 'national', 'international']))
        )

    @classmethod
    def create_org_ecosystem(cls, count: int = 10) -> List[Dict[str, Any]]:
        """Create a diverse ecosystem of organizations"""
        organizations = []

        # Distribution of organization types
        type_weights = [
            ('large_org', 0.2),
            ('local_charity', 0.4),
            ('emergency_relief', 0.1),
            ('education_focused', 0.15),
            ('environmental', 0.15)
        ]

        for _ in range(count):
            org_type = random.choices(
                [t[0] for t in type_weights],
                weights=[t[1] for t in type_weights]
            )[0]

            org = cls.build(**{org_type: True})
            organizations.append(org)

        return organizations


class CampaignFactory(MongoFactory):
    """Factory-Boy factory for creating Campaign objects

    Creates fundraising campaigns with goals, timelines, and impact tracking.
    """

    class Meta:
        model = dict

    campaign_id = Sequence(lambda n: f'campaign_{n}_{fake.uuid4()[:8]}')
    onlus_id = LazyFunction(lambda: str(fake.mongodb_object_id()))

    # Campaign details
    name = LazyFunction(fake.campaign_title)
    tagline = LazyFunction(lambda: fake.sentence())
    description = LazyFunction(lambda: fake.text(max_nb_chars=800))
    short_description = LazyFunction(lambda: fake.sentence())

    # Campaign goals
    financial_goal = LazyFunction(lambda: round(random.uniform(1000, 100000), 2))
    current_amount = LazyFunction(lambda: round(random.uniform(0, 80000), 2))
    donor_count = LazyFunction(lambda: random.randint(0, 500))

    # Timeline
    start_date = LazyFunction(lambda: fake.date_time_between(start_date='-6m', end_date='now'))
    end_date = LazyAttribute(lambda obj: obj.start_date + timedelta(
        days=random.randint(30, 365)
    ))

    # Status
    status = LazyFunction(lambda: random.choices(
        ['draft', 'active', 'completed', 'cancelled', 'paused'],
        weights=[5, 60, 25, 5, 5]
    )[0])

    # Campaign type and urgency
    campaign_type = LazyFunction(lambda: random.choice([
        'general_fundraising', 'emergency_appeal', 'project_specific',
        'capital_campaign', 'program_funding', 'matching_gift'
    ]))

    urgency_level = LazyFunction(lambda: random.choice(['low', 'medium', 'high', 'critical']))

    # Impact and beneficiaries
    beneficiary_count = LazyFunction(lambda: random.randint(10, 10000))
    impact_description = LazyFunction(lambda: fake.sentence())
    success_stories = LazyFunction(lambda: [
        fake.text(max_nb_chars=200) for _ in range(random.randint(0, 3))
    ])

    # Media
    banner_image_url = LazyFunction(lambda: f"https://cdn.goodplay.test/campaigns/{fake.uuid4()[:8]}/banner.jpg")
    gallery_images = LazyFunction(lambda: [
        f"https://cdn.goodplay.test/campaigns/{fake.uuid4()[:8]}/image_{i}.jpg"
        for i in range(random.randint(2, 8))
    ])

    video_url = LazyFunction(lambda: f"https://video.goodplay.test/campaigns/{fake.uuid4()[:8]}.mp4"
        if random.random() > 0.4 else None)

    # Updates and communication
    update_count = LazyFunction(lambda: random.randint(0, 20))
    last_update_date = LazyFunction(lambda: fake.date_time_between(start_date='-30d', end_date='now'))

    # Campaign traits
    class Params:
        emergency_campaign = factory.Trait(
            campaign_type='emergency_appeal',
            urgency_level='critical',
            financial_goal=LazyFunction(lambda: round(random.uniform(10000, 500000), 2)),
            end_date=LazyFunction(lambda: datetime.now(timezone.utc) + timedelta(days=random.randint(7, 60))),
            impact_description=LazyFunction(lambda: "Provides immediate emergency relief to disaster victims")
        )

        successful_campaign = factory.Trait(
            status='completed',
            current_amount=LazyAttribute(lambda obj: obj.financial_goal * random.uniform(1.0, 1.5)),
            donor_count=LazyFunction(lambda: random.randint(100, 2000)),
            update_count=LazyFunction(lambda: random.randint(10, 30)),
            success_stories=LazyFunction(lambda: [
                fake.text(max_nb_chars=200) for _ in range(random.randint(3, 6))
            ])
        )

        new_campaign = factory.Trait(
            status='active',
            start_date=LazyFunction(lambda: datetime.now(timezone.utc) - timedelta(days=random.randint(1, 7))),
            current_amount=LazyFunction(lambda: round(random.uniform(0, 5000), 2)),
            donor_count=LazyFunction(lambda: random.randint(0, 50)),
            update_count=LazyFunction(lambda: random.randint(0, 3))
        )

    @classmethod
    def create_campaign_lifecycle(cls, onlus_id: str) -> List[Dict[str, Any]]:
        """Create campaigns showing a realistic lifecycle for an organization"""
        campaigns = []

        # Successful past campaign
        past_campaign = cls.build(
            onlus_id=onlus_id,
            successful_campaign=True,
            start_date=fake.date_time_between(start_date='-2y', end_date='-6m'),
            end_date=fake.date_time_between(start_date='-6m', end_date='-3m')
        )
        campaigns.append(past_campaign)

        # Current active campaign
        active_campaign = cls.build(
            onlus_id=onlus_id,
            status='active',
            start_date=fake.date_time_between(start_date='-3m', end_date='-1m')
        )
        campaigns.append(active_campaign)

        # New upcoming campaign
        new_campaign = cls.build(
            onlus_id=onlus_id,
            new_campaign=True
        )
        campaigns.append(new_campaign)

        return campaigns


class ProjectFactory(MongoFactory):
    """Factory-Boy factory for creating Project objects

    Represents specific projects or programs run by ONLUS organizations.
    """

    class Meta:
        model = dict

    project_id = Sequence(lambda n: f'project_{n}_{fake.uuid4()[:8]}')
    onlus_id = LazyFunction(lambda: str(fake.mongodb_object_id()))
    campaign_id = LazyFunction(lambda: str(fake.mongodb_object_id()) if random.random() > 0.3 else None)

    # Project details
    name = LazyFunction(lambda: f"{fake.word().title()} {random.choice(['Initiative', 'Project', 'Program', 'Drive'])}")
    description = LazyFunction(lambda: fake.text(max_nb_chars=600))
    objectives = LazyFunction(lambda: [
        fake.sentence() for _ in range(random.randint(2, 5))
    ])

    # Project scope and impact
    target_beneficiaries = LazyFunction(lambda: random.randint(50, 50000))
    actual_beneficiaries = LazyFunction(lambda: random.randint(0, 45000))
    geographic_scope = LazyFunction(lambda: random.choice(['local', 'regional', 'national', 'international']))

    # Timeline and status
    start_date = LazyFunction(lambda: fake.date_time_between(start_date='-2y', end_date='now'))
    planned_end_date = LazyAttribute(lambda obj: obj.start_date + timedelta(
        days=random.randint(90, 1095)  # 3 months to 3 years
    ))
    actual_end_date = LazyAttribute(lambda obj: obj.planned_end_date + timedelta(
        days=random.randint(-30, 60)  # Projects can finish early or late
    ) if obj.status == 'completed' else None)

    status = LazyFunction(lambda: random.choices(
        ['planning', 'active', 'on_hold', 'completed', 'cancelled'],
        weights=[10, 50, 5, 30, 5]
    )[0])

    # Budget and resources
    total_budget = LazyFunction(lambda: round(random.uniform(5000, 500000), 2))
    funds_allocated = LazyFunction(lambda: round(random.uniform(1000, 400000), 2))
    funds_spent = LazyFunction(lambda: round(random.uniform(0, 350000), 2))

    # Team and partnerships
    team_members = LazyFunction(lambda: random.randint(2, 20))
    partner_count = LazyFunction(lambda: random.randint(0, 10))
    volunteer_hours = LazyFunction(lambda: random.randint(100, 10000))

    # Results and metrics
    success_metrics = LazyFunction(lambda: {
        'completion_rate': round(random.uniform(0.7, 1.0), 2),
        'beneficiary_satisfaction': round(random.uniform(4.0, 5.0), 1),
        'budget_efficiency': round(random.uniform(0.8, 1.2), 2),
        'timeline_adherence': round(random.uniform(0.6, 1.1), 2)
    })

    # Documentation
    reports_published = LazyFunction(lambda: random.randint(0, 10))
    media_coverage = LazyFunction(lambda: random.randint(0, 25))

    class Params:
        completed_project = factory.Trait(
            status='completed',
            actual_beneficiaries=LazyAttribute(lambda obj: min(
                obj.target_beneficiaries, random.randint(int(obj.target_beneficiaries * 0.8),
                int(obj.target_beneficiaries * 1.2))
            )),
            funds_spent=LazyAttribute(lambda obj: min(obj.funds_allocated,
                obj.total_budget * random.uniform(0.85, 1.05))),
            reports_published=LazyFunction(lambda: random.randint(3, 10)),
            media_coverage=LazyFunction(lambda: random.randint(5, 25))
        )

        large_scale_project = factory.Trait(
            target_beneficiaries=LazyFunction(lambda: random.randint(5000, 100000)),
            total_budget=LazyFunction(lambda: round(random.uniform(100000, 2000000), 2)),
            team_members=LazyFunction(lambda: random.randint(10, 50)),
            partner_count=LazyFunction(lambda: random.randint(3, 15)),
            geographic_scope='international'
        )


class VolunteerFactory(MongoFactory):
    """Factory-Boy factory for creating Volunteer objects

    Represents volunteers associated with ONLUS organizations.
    """

    class Meta:
        model = dict

    volunteer_id = Sequence(lambda n: f'volunteer_{n}_{fake.uuid4()[:8]}')
    user_id = LazyFunction(lambda: str(fake.mongodb_object_id()))
    onlus_id = LazyFunction(lambda: str(fake.mongodb_object_id()))

    # Volunteer details
    role = LazyFunction(lambda: random.choice([
        'general_volunteer', 'event_coordinator', 'fundraising_assistant',
        'social_media_manager', 'program_assistant', 'mentor', 'translator'
    ]))

    skills = LazyFunction(lambda: random.sample([
        'communication', 'event_planning', 'social_media', 'fundraising',
        'teaching', 'mentoring', 'translation', 'photography', 'writing',
        'project_management', 'graphic_design', 'web_development'
    ], random.randint(2, 6)))

    # Availability and commitment
    availability = LazyFunction(lambda: {
        'weekdays': random.choice([True, False]),
        'weekends': random.choice([True, False]),
        'evenings': random.choice([True, False]),
        'hours_per_week': random.randint(2, 20)
    })

    commitment_level = LazyFunction(lambda: random.choice(['casual', 'regular', 'dedicated']))

    # Experience and contribution
    start_date = LazyFunction(lambda: fake.date_time_between(start_date='-3y', end_date='now'))
    total_hours_contributed = LazyFunction(lambda: random.randint(10, 2000))
    projects_participated = LazyFunction(lambda: random.randint(1, 20))

    # Status
    status = LazyFunction(lambda: random.choices(
        ['active', 'inactive', 'on_break', 'alumni'],
        weights=[70, 15, 10, 5]
    )[0])

    # Recognition
    recognition_received = LazyFunction(lambda: random.sample([
        'volunteer_of_the_month', 'outstanding_service', 'community_impact',
        'leadership_award', 'dedication_recognition'
    ], random.randint(0, 3)))

    class Params:
        long_term_volunteer = factory.Trait(
            start_date=LazyFunction(lambda: fake.date_time_between(start_date='-5y', end_date='-1y')),
            total_hours_contributed=LazyFunction(lambda: random.randint(500, 5000)),
            projects_participated=LazyFunction(lambda: random.randint(10, 50)),
            commitment_level='dedicated',
            status='active',
            recognition_received=LazyFunction(lambda: random.sample([
                'volunteer_of_the_month', 'outstanding_service', 'leadership_award'
            ], random.randint(2, 3)))
        )