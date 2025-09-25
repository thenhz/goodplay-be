"""
Financial Factory Module

Factory-Boy implementations for generating financial domain objects
including wallets, transactions, and donation-related models with
realistic data and proper financial relationships.
"""
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
import factory
from factory import LazyFunction, LazyAttribute, Sequence, Trait, SubFactory
from faker import Faker

# Import our custom providers and base classes
from tests.factories.base import MongoFactory, TimestampMixin, fake
from tests.factories.providers import FinancialDataProvider

# Register our custom providers
fake.add_provider(FinancialDataProvider)


class WalletFactory(MongoFactory):
    """Factory-Boy factory for creating Wallet objects

    Manages user financial data including balances, earnings, and donations
    with realistic financial relationships and audit trails.

    Usage:
        wallet = WalletFactory()  # Basic wallet
        rich = WalletFactory(high_balance=True)  # High balance wallet
        donor = WalletFactory(active_donor=True)  # Active donor wallet
    """

    class Meta:
        model = dict

    user_id = LazyFunction(lambda: str(fake.mongodb_object_id()))

    # Current balance and financial state
    current_balance = LazyFunction(lambda: round(random.uniform(0, 1000), 2))
    pending_balance = LazyFunction(lambda: round(random.uniform(0, 50), 2))
    reserved_balance = LazyFunction(lambda: round(random.uniform(0, 100), 2))

    # Lifetime totals
    total_earned = LazyAttribute(lambda obj: obj.current_balance + round(random.uniform(0, 5000), 2))
    total_donated = LazyFunction(lambda: round(random.uniform(0, 2000), 2))
    total_spent = LazyFunction(lambda: round(random.uniform(0, 1000), 2))

    # Transaction counts for analytics
    transaction_count = LazyFunction(lambda: random.randint(0, 500))
    donation_count = LazyFunction(lambda: random.randint(0, 100))
    earning_transactions = LazyFunction(lambda: random.randint(0, 200))

    # Limits and restrictions
    daily_donation_limit = LazyFunction(lambda: round(random.uniform(100, 1000), 2))
    monthly_donation_limit = LazyFunction(lambda: round(random.uniform(1000, 10000), 2))

    # Current period tracking
    daily_donated_amount = LazyFunction(lambda: round(random.uniform(0, 200), 2))
    monthly_donated_amount = LazyFunction(lambda: round(random.uniform(0, 2000), 2))

    # Account status
    is_active = True
    is_verified = LazyFunction(lambda: random.choice([True, True, False]))  # 67% verified
    verification_level = LazyAttribute(lambda obj: random.choice(['basic', 'standard', 'premium']) if obj.is_verified else 'unverified')

    # Security and compliance
    last_audit_date = LazyFunction(lambda: fake.date_time_between(start_date='-1y', end_date='-1d'))
    suspicious_activity_flag = LazyFunction(lambda: random.choice([False, False, False, True]))  # 25% flagged

    # Wallet traits
    class Params:
        high_balance = factory.Trait(
            current_balance=LazyFunction(lambda: round(random.uniform(2000, 10000), 2)),
            total_earned=LazyFunction(lambda: round(random.uniform(10000, 50000), 2)),
            total_donated=LazyFunction(lambda: round(random.uniform(2000, 20000), 2)),
            transaction_count=LazyFunction(lambda: random.randint(200, 1000)),
            donation_count=LazyFunction(lambda: random.randint(50, 200)),
            is_verified=True,
            verification_level='premium',
            daily_donation_limit=LazyFunction(lambda: round(random.uniform(1000, 5000), 2)),
            monthly_donation_limit=LazyFunction(lambda: round(random.uniform(10000, 50000), 2))
        )

        active_donor = factory.Trait(
            total_donated=LazyFunction(lambda: round(random.uniform(500, 5000), 2)),
            donation_count=LazyFunction(lambda: random.randint(20, 100)),
            daily_donated_amount=LazyFunction(lambda: round(random.uniform(10, 100), 2)),
            monthly_donated_amount=LazyFunction(lambda: round(random.uniform(100, 1000), 2)),
            is_verified=True,
            verification_level=LazyFunction(lambda: random.choice(['standard', 'premium']))
        )

        new_user = factory.Trait(
            current_balance=LazyFunction(lambda: round(random.uniform(0, 50), 2)),
            total_earned=LazyFunction(lambda: round(random.uniform(0, 100), 2)),
            total_donated=0.0,
            total_spent=0.0,
            transaction_count=LazyFunction(lambda: random.randint(0, 10)),
            donation_count=0,
            earning_transactions=LazyFunction(lambda: random.randint(0, 10)),
            is_verified=False,
            verification_level='unverified',
            daily_donation_limit=100.0,
            monthly_donation_limit=1000.0
        )

        suspended = factory.Trait(
            is_active=False,
            suspicious_activity_flag=True,
            current_balance=0.0,
            pending_balance=LazyFunction(lambda: round(random.uniform(0, 500), 2)),
            reserved_balance=LazyFunction(lambda: round(random.uniform(100, 1000), 2))
        )

    @classmethod
    def create_wallet_with_history(cls, transaction_count: int = 20, **kwargs) -> Dict[str, Any]:
        """Create a wallet with a realistic transaction history"""
        wallet = cls.build(**kwargs)

        # Ensure totals are consistent with transaction history
        earned_amount = sum(round(random.uniform(1, 50), 2) for _ in range(transaction_count // 2))
        donated_amount = sum(round(random.uniform(5, 100), 2) for _ in range(transaction_count // 3))

        wallet.update({
            'total_earned': earned_amount,
            'total_donated': donated_amount,
            'current_balance': max(0, earned_amount - donated_amount + random.uniform(-50, 50)),
            'transaction_count': transaction_count
        })

        return wallet


class TransactionFactory(MongoFactory):
    """Factory-Boy factory for creating Transaction objects

    Creates financial transactions with proper audit trails and
    realistic transaction patterns.

    Usage:
        transaction = TransactionFactory()  # Basic transaction
        donation = TransactionFactory(donation=True)  # Donation transaction
        earning = TransactionFactory(earning=True)  # Earning transaction
    """

    class Meta:
        model = dict

    transaction_id = Sequence(lambda n: f'txn_{n}_{fake.uuid4()[:12]}')
    user_id = LazyFunction(lambda: str(fake.mongodb_object_id()))
    wallet_id = LazyFunction(lambda: str(fake.mongodb_object_id()))

    # Transaction basic info
    type = LazyFunction(fake.transaction_type)
    amount = LazyAttribute(lambda obj: fake.transaction_amount(obj.type))
    currency = 'USD'  # Platform standard

    # Transaction status
    status = LazyFunction(lambda: random.choices(
        ['pending', 'completed', 'failed', 'cancelled', 'refunded'],
        weights=[10, 80, 5, 3, 2]
    )[0])

    # Description and metadata
    description = LazyAttribute(lambda obj: {
        'earned': f"Gaming credits earned from {fake.word()} game",
        'donated': f"Donation to {fake.onlus_name()}",
        'bonus': f"Bonus credits for {fake.sentence()[:-1].lower()}",
        'refund': f"Refund for {fake.sentence()[:-1].lower()}",
        'adjustment': f"Account adjustment: {fake.sentence()[:-1].lower()}"
    }.get(obj.type, f"Transaction: {fake.sentence()}"))

    # Related entities
    game_id = LazyFunction(lambda: str(fake.mongodb_object_id()) if random.random() > 0.4 else None)
    onlus_id = LazyFunction(lambda: str(fake.mongodb_object_id()) if random.random() > 0.6 else None)
    session_id = LazyFunction(lambda: str(fake.mongodb_object_id()) if random.random() > 0.5 else None)

    # Audit and compliance
    reference_id = LazyFunction(lambda: fake.uuid4())
    external_transaction_id = LazyFunction(lambda: f"ext_{fake.uuid4()[:16]}" if random.random() > 0.7 else None)

    # Balances (for audit trail)
    balance_before = LazyFunction(lambda: round(random.uniform(0, 1000), 2))
    balance_after = LazyAttribute(lambda obj: max(0, obj.balance_before +
        (obj.amount if obj.type in ['earned', 'bonus', 'refund'] else -obj.amount)))

    # Processing information
    processed_at = LazyAttribute(lambda obj: obj.created_at + timedelta(
        seconds=random.randint(1, 3600) if obj.status == 'completed' else 0
    ))

    processing_fee = LazyFunction(lambda: round(random.uniform(0, 2), 2))
    net_amount = LazyAttribute(lambda obj: obj.amount - obj.processing_fee)

    # Error handling
    error_code = LazyAttribute(lambda obj: random.choice([
        'INSUFFICIENT_FUNDS', 'NETWORK_ERROR', 'INVALID_ACCOUNT'
    ]) if obj.status == 'failed' else None)

    error_message = LazyAttribute(lambda obj: {
        'INSUFFICIENT_FUNDS': 'Insufficient funds in wallet',
        'NETWORK_ERROR': 'Network connection failed',
        'INVALID_ACCOUNT': 'Invalid recipient account'
    }.get(obj.error_code) if obj.error_code else None)

    # Transaction type traits
    class Params:
        earning = factory.Trait(
            type='earned',
            amount=LazyFunction(lambda: round(random.uniform(1, 50), 2)),
            description=LazyFunction(lambda: f"Credits earned from {fake.game_name()}"),
            game_id=LazyFunction(lambda: str(fake.mongodb_object_id())),
            session_id=LazyFunction(lambda: str(fake.mongodb_object_id())),
            processing_fee=0.0,
            status='completed'
        )

        donation = factory.Trait(
            type='donated',
            amount=LazyFunction(lambda: fake.donation_amount('regular')),
            description=LazyFunction(lambda: f"Donation to {fake.onlus_name()}"),
            onlus_id=LazyFunction(lambda: str(fake.mongodb_object_id())),
            processing_fee=LazyFunction(lambda: round(random.uniform(0.1, 1.0), 2)),
            status='completed'
        )

        large_donation = factory.Trait(
            type='donated',
            amount=LazyFunction(lambda: fake.donation_amount('veteran')),
            description=LazyFunction(lambda: f"Major donation to {fake.onlus_name()}"),
            onlus_id=LazyFunction(lambda: str(fake.mongodb_object_id())),
            processing_fee=LazyFunction(lambda: round(random.uniform(1.0, 5.0), 2)),
            status='completed',
            external_transaction_id=LazyFunction(lambda: f"ext_{fake.uuid4()}")
        )

        bonus = factory.Trait(
            type='bonus',
            amount=LazyFunction(lambda: round(random.uniform(10, 100), 2)),
            description=LazyFunction(lambda: random.choice([
                "Achievement bonus credits",
                "Weekly challenge completion bonus",
                "Referral bonus credits",
                "Special event bonus",
                "Streak bonus credits"
            ])),
            processing_fee=0.0,
            status='completed'
        )

        failed_transaction = factory.Trait(
            status='failed',
            processed_at=None,
            balance_after=LazyAttribute(lambda obj: obj.balance_before),  # No balance change
            error_code=LazyFunction(lambda: random.choice([
                'INSUFFICIENT_FUNDS', 'NETWORK_ERROR', 'INVALID_ACCOUNT', 'DECLINED'
            ])),
            processing_fee=0.0
        )

        refund = factory.Trait(
            type='refund',
            amount=LazyFunction(lambda: round(random.uniform(5, 200), 2)),
            description=LazyFunction(lambda: f"Refund for cancelled donation to {fake.onlus_name()}"),
            status='completed',
            reference_id=LazyFunction(lambda: fake.uuid4()),
            processing_fee=0.0
        )

    @classmethod
    def create_transaction_history(cls, wallet_id: str, user_id: str, count: int = 20) -> List[Dict[str, Any]]:
        """Create a realistic transaction history for a wallet"""
        transactions = []
        current_balance = round(random.uniform(50, 500), 2)

        # Transaction type distribution
        transaction_types = [
            ('earning', 0.5),    # 50% earnings
            ('donation', 0.3),   # 30% donations
            ('bonus', 0.15),     # 15% bonuses
            ('refund', 0.05)     # 5% refunds
        ]

        for i in range(count):
            # Choose transaction type based on weights
            tx_type = random.choices(
                [t[0] for t in transaction_types],
                weights=[t[1] for t in transaction_types]
            )[0]

            # Calculate new balance
            if tx_type == 'earning':
                amount = round(random.uniform(1, 50), 2)
                new_balance = current_balance + amount
            elif tx_type == 'donation':
                amount = min(round(random.uniform(5, 100), 2), current_balance * 0.8)
                new_balance = current_balance - amount
            elif tx_type == 'bonus':
                amount = round(random.uniform(10, 100), 2)
                new_balance = current_balance + amount
            else:  # refund
                amount = round(random.uniform(5, 50), 2)
                new_balance = current_balance + amount

            # Create transaction with proper balance tracking
            transaction = cls.build(
                wallet_id=wallet_id,
                user_id=user_id,
                **{tx_type: True},
                balance_before=current_balance,
                balance_after=new_balance,
                created_at=fake.date_time_between(start_date='-6m', end_date='now')
            )

            transactions.append(transaction)
            current_balance = new_balance

        # Sort by date to maintain chronological order
        transactions.sort(key=lambda x: x['created_at'])
        return transactions

    @classmethod
    def create_donation_campaign_transactions(cls, onlus_id: str, donation_count: int = 50) -> List[Dict[str, Any]]:
        """Create transactions for a donation campaign"""
        transactions = []

        for _ in range(donation_count):
            # Vary donation amounts - some small, some large
            if random.random() < 0.8:  # 80% regular donations
                trait = 'donation'
            else:  # 20% large donations
                trait = 'large_donation'

            transaction = cls.build(
                onlus_id=onlus_id,
                **{trait: True},
                created_at=fake.date_time_between(start_date='-3m', end_date='now')
            )
            transactions.append(transaction)

        return transactions


class DonationFactory(MongoFactory):
    """Factory-Boy factory for creating Donation objects

    Specialized factory for donation-specific data with ONLUS relationships
    and impact tracking.
    """

    class Meta:
        model = dict

    donation_id = Sequence(lambda n: f'donation_{n}_{fake.uuid4()[:8]}')
    user_id = LazyFunction(lambda: str(fake.mongodb_object_id()))
    onlus_id = LazyFunction(lambda: str(fake.mongodb_object_id()))
    transaction_id = LazyFunction(lambda: str(fake.mongodb_object_id()))

    # Donation details
    amount = LazyFunction(lambda: fake.donation_amount('regular'))
    currency = 'USD'
    donation_type = LazyFunction(lambda: random.choice([
        'one_time', 'monthly_recurring', 'campaign_specific', 'emergency'
    ]))

    # Impact tracking
    cause_category = LazyFunction(fake.donation_cause)
    impact_description = LazyFunction(lambda: random.choice([
        "Provided meals for 10 families",
        "Planted 5 trees in reforestation project",
        "Funded 2 hours of educational content",
        "Supported clean water access for 1 week",
        "Provided medical supplies for local clinic",
        "Funded animal shelter operations for 3 days"
    ]))

    # Campaign information
    campaign_id = LazyFunction(lambda: str(fake.mongodb_object_id()) if random.random() > 0.4 else None)
    campaign_name = LazyFunction(lambda: fake.campaign_title() if random.random() > 0.4 else None)

    # Recognition and privacy
    is_anonymous = LazyFunction(lambda: random.choice([False, False, False, True]))  # 25% anonymous
    show_on_leaderboard = LazyFunction(lambda: random.choice([True, True, False]))  # 67% public
    donor_message = LazyFunction(lambda: fake.sentence() if random.random() > 0.6 else None)

    # Status and verification
    status = LazyFunction(lambda: random.choices(
        ['pending', 'verified', 'disbursed', 'failed'],
        weights=[5, 25, 65, 5]
    )[0])

    verified_at = LazyAttribute(lambda obj: fake.date_time_between(
        start_date=obj.created_at, end_date='now'
    ) if obj.status in ['verified', 'disbursed'] else None)

    disbursed_at = LazyAttribute(lambda obj: fake.date_time_between(
        start_date=obj.verified_at or obj.created_at, end_date='now'
    ) if obj.status == 'disbursed' else None)

    class Params:
        large_donation = factory.Trait(
            amount=LazyFunction(lambda: fake.donation_amount('veteran')),
            donation_type=LazyFunction(lambda: random.choice(['one_time', 'campaign_specific'])),
            impact_description=LazyFunction(lambda: random.choice([
                "Funded entire classroom renovation",
                "Provided clean water system for village",
                "Sponsored 50 children's education for 1 month",
                "Funded mobile medical clinic for rural area",
                "Supported wildlife conservation for 100 acres"
            ])),
            is_anonymous=LazyFunction(lambda: random.choice([True, False])),
            show_on_leaderboard=True
        )

        recurring_donation = factory.Trait(
            donation_type='monthly_recurring',
            amount=LazyFunction(lambda: round(random.uniform(10, 100), 2)),
            impact_description=LazyFunction(lambda: "Part of ongoing monthly support program"),
            show_on_leaderboard=False
        )

        emergency_donation = factory.Trait(
            donation_type='emergency',
            cause_category='disaster_relief',
            amount=LazyFunction(lambda: fake.donation_amount('regular')),
            impact_description=LazyFunction(lambda: "Emergency relief support"),
            campaign_name=LazyFunction(lambda: random.choice([
                "Earthquake Emergency Response",
                "Flood Relief Fund",
                "Wildfire Recovery Support",
                "Hurricane Emergency Aid"
            ]))
        )

    @classmethod
    def create_user_donation_history(cls, user_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Create donation history for a specific user"""
        donations = []

        # Mix of donation types
        for _ in range(count):
            donation_type = random.choices(
                ['regular', 'large_donation', 'recurring_donation', 'emergency_donation'],
                weights=[60, 20, 15, 5]
            )[0]

            if donation_type == 'regular':
                donation = cls.build(user_id=user_id)
            else:
                donation = cls.build(user_id=user_id, **{donation_type: True})

            donations.append(donation)

        return donations

    @classmethod
    def create_campaign_donations(cls, campaign_id: str, onlus_id: str, count: int = 25) -> List[Dict[str, Any]]:
        """Create donations for a specific campaign"""
        return cls.build_batch(
            count,
            campaign_id=campaign_id,
            onlus_id=onlus_id,
            donation_type='campaign_specific',
            campaign_name=fake.campaign_title()
        )