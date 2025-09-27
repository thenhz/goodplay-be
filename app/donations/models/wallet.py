from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId


class Wallet:
    """
    Virtual wallet model for managing user credits and donation settings.
    Handles balance management, auto-donation configuration, and transaction integrity.
    """

    def __init__(self, user_id: str, current_balance: float = 0.0, total_earned: float = 0.0,
                 total_donated: float = 0.0, auto_donation_settings: Dict[str, Any] = None,
                 _id: Optional[ObjectId] = None, created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None, version: int = 1):
        self._id = _id
        self.user_id = user_id
        self.current_balance = float(current_balance)
        self.total_earned = float(total_earned)
        self.total_donated = float(total_donated)
        self.auto_donation_settings = auto_donation_settings or {
            'enabled': False,
            'threshold': 10.0,  # Auto-donate when balance reaches this amount
            'percentage': 50,   # Percentage of balance to donate
            'preferred_onlus_id': None,
            'round_up_enabled': False
        }
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.version = version  # For optimistic locking

    def add_credits(self, amount: float, transaction_type: str = 'earned') -> bool:
        """
        Add credits to the wallet with validation.

        Args:
            amount: Amount to add (must be positive)
            transaction_type: Type of transaction ('earned', 'bonus', 'refund')

        Returns:
            bool: True if credits were added successfully
        """
        if amount <= 0:
            return False

        if amount > 1000:  # Daily earning limit for fraud prevention
            return False

        self.current_balance += amount
        if transaction_type == 'earned':
            self.total_earned += amount
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1
        return True

    def deduct_credits(self, amount: float, transaction_type: str = 'donated') -> bool:
        """
        Deduct credits from the wallet with validation.

        Args:
            amount: Amount to deduct (must be positive)
            transaction_type: Type of transaction ('donated', 'fee', 'adjustment')

        Returns:
            bool: True if credits were deducted successfully
        """
        if amount <= 0 or amount > self.current_balance:
            return False

        self.current_balance -= amount
        if transaction_type == 'donated':
            self.total_donated += amount
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1
        return True

    def can_donate(self, amount: float) -> bool:
        """
        Check if the wallet has sufficient balance for donation.

        Args:
            amount: Amount to check

        Returns:
            bool: True if donation is possible
        """
        return amount > 0 and self.current_balance >= amount

    def should_auto_donate(self) -> bool:
        """
        Check if auto-donation should be triggered based on settings.

        Returns:
            bool: True if auto-donation should be triggered
        """
        if not self.auto_donation_settings.get('enabled', False):
            return False

        threshold = self.auto_donation_settings.get('threshold', 10.0)
        return self.current_balance >= threshold

    def calculate_auto_donation_amount(self) -> float:
        """
        Calculate the amount to auto-donate based on settings.

        Returns:
            float: Amount to donate
        """
        if not self.should_auto_donate():
            return 0.0

        percentage = self.auto_donation_settings.get('percentage', 50)
        threshold = self.auto_donation_settings.get('threshold', 10.0)

        # Only donate the excess above threshold, with percentage applied
        excess = self.current_balance - threshold
        donation_amount = excess * (percentage / 100)

        # Round to 2 decimal places
        return round(donation_amount, 2)

    def apply_auto_donation(self) -> Optional[float]:
        """
        Apply auto-donation if conditions are met.

        Returns:
            Optional[float]: Amount donated, None if no donation occurred
        """
        if not self.should_auto_donate():
            return None

        donation_amount = self.calculate_auto_donation_amount()
        if donation_amount <= 0:
            return None

        if self.deduct_credits(donation_amount, 'donated'):
            return donation_amount
        return None

    def update_auto_donation_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Update auto-donation settings with validation.

        Args:
            settings: New auto-donation settings

        Returns:
            bool: True if settings were updated successfully
        """
        if not isinstance(settings, dict):
            return False

        # Validate settings
        if 'threshold' in settings:
            if not isinstance(settings['threshold'], (int, float)) or settings['threshold'] < 0:
                return False

        if 'percentage' in settings:
            if not isinstance(settings['percentage'], int) or not (1 <= settings['percentage'] <= 100):
                return False

        # Update settings
        self.auto_donation_settings.update(settings)
        self.updated_at = datetime.now(timezone.utc)
        self.version += 1
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get wallet statistics for reporting.

        Returns:
            Dict containing wallet statistics
        """
        return {
            'current_balance': self.current_balance,
            'total_earned': self.total_earned,
            'total_donated': self.total_donated,
            'donation_ratio': self.total_donated / self.total_earned if self.total_earned > 0 else 0,
            'auto_donation_enabled': self.auto_donation_settings.get('enabled', False),
            'auto_donation_threshold': self.auto_donation_settings.get('threshold', 0),
            'account_age_days': (datetime.now(timezone.utc) - self.created_at).days,
            'version': self.version
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert wallet to dictionary for MongoDB storage."""
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'current_balance': self.current_balance,
            'total_earned': self.total_earned,
            'total_donated': self.total_donated,
            'auto_donation_settings': self.auto_donation_settings,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'version': self.version
        }

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert wallet to dictionary for API responses."""
        return {
            'wallet_id': str(self._id) if self._id else None,
            'user_id': self.user_id,
            'current_balance': round(self.current_balance, 2),
            'total_earned': round(self.total_earned, 2),
            'total_donated': round(self.total_donated, 2),
            'auto_donation_settings': self.auto_donation_settings,
            'statistics': self.get_statistics(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Wallet':
        """Create Wallet instance from dictionary."""
        return cls(
            _id=data.get('_id'),
            user_id=data.get('user_id'),
            current_balance=data.get('current_balance', 0.0),
            total_earned=data.get('total_earned', 0.0),
            total_donated=data.get('total_donated', 0.0),
            auto_donation_settings=data.get('auto_donation_settings'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            version=data.get('version', 1)
        )

    @staticmethod
    def validate_wallet_data(data: Dict[str, Any]) -> Optional[str]:
        """
        Validate wallet data for creation/updates.

        Args:
            data: Wallet data to validate

        Returns:
            str: Error message if validation fails, None if valid
        """
        if not isinstance(data, dict):
            return "WALLET_DATA_INVALID_FORMAT"

        if 'user_id' not in data or not data['user_id']:
            return "WALLET_USER_ID_REQUIRED"

        if 'current_balance' in data:
            balance = data['current_balance']
            if not isinstance(balance, (int, float)) or balance < 0:
                return "WALLET_BALANCE_INVALID"

        if 'auto_donation_settings' in data:
            settings = data['auto_donation_settings']
            if not isinstance(settings, dict):
                return "WALLET_AUTO_DONATION_SETTINGS_INVALID"

            if 'threshold' in settings:
                threshold = settings['threshold']
                if not isinstance(threshold, (int, float)) or threshold < 0:
                    return "WALLET_AUTO_DONATION_THRESHOLD_INVALID"

            if 'percentage' in settings:
                percentage = settings['percentage']
                if not isinstance(percentage, int) or not (1 <= percentage <= 100):
                    return "WALLET_AUTO_DONATION_PERCENTAGE_INVALID"

        return None

    def __repr__(self) -> str:
        return f'<Wallet {self.user_id}: {self.current_balance}€>'