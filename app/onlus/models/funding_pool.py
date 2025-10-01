from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId
from enum import Enum


class FundingPoolStatus(Enum):
    """Status of funding pool."""
    ACTIVE = "active"  # Pool is active and available for allocation
    PAUSED = "paused"  # Pool temporarily paused
    DEPLETED = "depleted"  # Pool has no available funds
    CLOSED = "closed"  # Pool permanently closed
    MAINTENANCE = "maintenance"  # Pool under maintenance


class FundingPoolType(Enum):
    """Type of funding pool."""
    GENERAL = "general"  # General donation pool
    EMERGENCY = "emergency"  # Emergency response fund
    MATCHING = "matching"  # Corporate matching fund
    CATEGORY_SPECIFIC = "category_specific"  # Category-specific fund
    PROJECT_SPECIFIC = "project_specific"  # Project-specific fund
    ENDOWMENT = "endowment"  # Endowment fund


class FundingPool:
    """
    Model for managing pools of available funds for allocation.

    Represents pools of donations that are available for allocation
    to ONLUS organizations based on various criteria and restrictions.

    Collection: funding_pools
    """

    def __init__(self, pool_name: str, pool_type: str,
                 total_balance: float, available_balance: float,
                 allocated_balance: float = 0.0,
                 reserved_balance: float = 0.0,
                 category_restrictions: List[str] = None,
                 geographical_restrictions: List[str] = None,
                 donor_preferences: Dict[str, Any] = None,
                 allocation_rules: Dict[str, Any] = None,
                 minimum_allocation: float = 0.0,
                 maximum_allocation: float = None,
                 auto_allocation_enabled: bool = True,
                 priority_weight: float = 1.0,
                 expiry_date: Optional[datetime] = None,
                 status: str = "active", admin_user_id: str = None,
                 source_transactions: List[str] = None,
                 allocation_history: List[Dict[str, Any]] = None,
                 performance_metrics: Dict[str, Any] = None,
                 _id: Optional[ObjectId] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 last_allocation_at: Optional[datetime] = None,
                 metadata: Dict[str, Any] = None):
        self._id = _id
        self.pool_name = pool_name.strip()
        self.pool_type = pool_type
        self.total_balance = float(total_balance)
        self.available_balance = float(available_balance)
        self.allocated_balance = float(allocated_balance)
        self.reserved_balance = float(reserved_balance)
        self.category_restrictions = category_restrictions or []
        self.geographical_restrictions = geographical_restrictions or []
        self.donor_preferences = donor_preferences or {}
        self.allocation_rules = allocation_rules or {}
        self.minimum_allocation = float(minimum_allocation)
        self.maximum_allocation = float(maximum_allocation) if maximum_allocation else None
        self.auto_allocation_enabled = auto_allocation_enabled
        self.priority_weight = float(priority_weight)
        self.expiry_date = expiry_date
        self.status = status
        self.admin_user_id = admin_user_id
        self.source_transactions = source_transactions or []
        self.allocation_history = allocation_history or []
        self.performance_metrics = performance_metrics or {}
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.last_allocation_at = last_allocation_at

    def add_funds(self, amount: float, transaction_id: str = None,
                 source_info: Dict[str, Any] = None) -> bool:
        """Add funds to the pool."""
        if amount <= 0:
            return False

        self.total_balance += amount
        self.available_balance += amount

        if transaction_id:
            self.source_transactions.append(transaction_id)

        # Record fund addition in metadata
        fund_entry = {
            'amount': amount,
            'transaction_id': transaction_id,
            'source_info': source_info or {},
            'timestamp': datetime.now(timezone.utc)
        }
        if 'fund_additions' not in self.metadata:
            self.metadata['fund_additions'] = []
        self.metadata['fund_additions'].append(fund_entry)

        self.updated_at = datetime.now(timezone.utc)
        return True

    def reserve_funds(self, amount: float, reservation_id: str = None) -> bool:
        """Reserve funds for pending allocation."""
        if amount <= 0 or amount > self.available_balance:
            return False

        self.available_balance -= amount
        self.reserved_balance += amount

        # Track reservation
        reservation_entry = {
            'amount': amount,
            'reservation_id': reservation_id or str(ObjectId()),
            'timestamp': datetime.now(timezone.utc)
        }
        if 'reservations' not in self.metadata:
            self.metadata['reservations'] = []
        self.metadata['reservations'].append(reservation_entry)

        self.updated_at = datetime.now(timezone.utc)
        return True

    def allocate_funds(self, amount: float, allocation_id: str,
                      onlus_id: str, request_id: str = None) -> bool:
        """Allocate funds from the pool."""
        # Check if funds are available (from available or reserved balance)
        if amount > (self.available_balance + self.reserved_balance):
            return False

        # Deduct from available balance first, then reserved
        if amount <= self.available_balance:
            self.available_balance -= amount
        else:
            remaining = amount - self.available_balance
            self.available_balance = 0
            self.reserved_balance -= remaining

        self.allocated_balance += amount
        self.last_allocation_at = datetime.now(timezone.utc)

        # Record allocation in history
        allocation_entry = {
            'allocation_id': allocation_id,
            'onlus_id': onlus_id,
            'request_id': request_id,
            'amount': amount,
            'timestamp': datetime.now(timezone.utc)
        }
        self.allocation_history.append(allocation_entry)

        self.updated_at = datetime.now(timezone.utc)

        # Update status if depleted
        if self.available_balance <= 0 and self.reserved_balance <= 0:
            self.status = FundingPoolStatus.DEPLETED.value

        return True

    def release_reservation(self, reservation_id: str) -> bool:
        """Release reserved funds back to available balance."""
        if 'reservations' not in self.metadata:
            return False

        for reservation in self.metadata['reservations']:
            if reservation.get('reservation_id') == reservation_id:
                amount = reservation['amount']
                self.reserved_balance -= amount
                self.available_balance += amount
                self.metadata['reservations'].remove(reservation)
                self.updated_at = datetime.now(timezone.utc)
                return True

        return False

    def can_allocate(self, amount: float, category: str = None,
                    geography: str = None) -> bool:
        """Check if allocation is possible based on rules and restrictions."""
        if amount <= 0 or self.status != FundingPoolStatus.ACTIVE.value:
            return False

        # Check balance availability
        if amount > (self.available_balance + self.reserved_balance):
            return False

        # Check minimum/maximum allocation limits
        if amount < self.minimum_allocation:
            return False

        if self.maximum_allocation and amount > self.maximum_allocation:
            return False

        # Check category restrictions
        if self.category_restrictions and category:
            if category not in self.category_restrictions:
                return False

        # Check geographical restrictions
        if self.geographical_restrictions and geography:
            if geography not in self.geographical_restrictions:
                return False

        # Check expiry date
        if self.expiry_date and datetime.now(timezone.utc) > self.expiry_date:
            return False

        return True

    def get_utilization_rate(self) -> float:
        """Get pool utilization rate (allocated/total)."""
        if self.total_balance <= 0:
            return 0.0
        return self.allocated_balance / self.total_balance

    def get_availability_rate(self) -> float:
        """Get pool availability rate (available/total)."""
        if self.total_balance <= 0:
            return 0.0
        return self.available_balance / self.total_balance

    def is_expired(self) -> bool:
        """Check if pool has expired."""
        if not self.expiry_date:
            return False
        return datetime.now(timezone.utc) > self.expiry_date

    def days_until_expiry(self) -> Optional[int]:
        """Get days until pool expiry."""
        if not self.expiry_date:
            return None
        delta = self.expiry_date - datetime.now(timezone.utc)
        return max(0, delta.days)

    def pause_pool(self, reason: str = None) -> None:
        """Pause the funding pool."""
        self.status = FundingPoolStatus.PAUSED.value
        if reason:
            self.metadata['pause_reason'] = reason
        self.updated_at = datetime.now(timezone.utc)

    def reactivate_pool(self) -> None:
        """Reactivate the funding pool."""
        if self.available_balance > 0 or self.reserved_balance > 0:
            self.status = FundingPoolStatus.ACTIVE.value
        else:
            self.status = FundingPoolStatus.DEPLETED.value

        if 'pause_reason' in self.metadata:
            del self.metadata['pause_reason']

        self.updated_at = datetime.now(timezone.utc)

    def close_pool(self, reason: str = None) -> None:
        """Permanently close the funding pool."""
        self.status = FundingPoolStatus.CLOSED.value
        if reason:
            self.metadata['closure_reason'] = reason
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert funding pool to dictionary."""
        return {
            '_id': self._id,
            'pool_name': self.pool_name,
            'pool_type': self.pool_type,
            'total_balance': self.total_balance,
            'available_balance': self.available_balance,
            'allocated_balance': self.allocated_balance,
            'reserved_balance': self.reserved_balance,
            'category_restrictions': self.category_restrictions,
            'geographical_restrictions': self.geographical_restrictions,
            'donor_preferences': self.donor_preferences,
            'allocation_rules': self.allocation_rules,
            'minimum_allocation': self.minimum_allocation,
            'maximum_allocation': self.maximum_allocation,
            'auto_allocation_enabled': self.auto_allocation_enabled,
            'priority_weight': self.priority_weight,
            'expiry_date': self.expiry_date,
            'status': self.status,
            'admin_user_id': self.admin_user_id,
            'source_transactions': self.source_transactions,
            'allocation_history': self.allocation_history,
            'performance_metrics': self.performance_metrics,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_allocation_at': self.last_allocation_at,
            'utilization_rate': self.get_utilization_rate(),
            'availability_rate': self.get_availability_rate(),
            'is_expired': self.is_expired(),
            'days_until_expiry': self.days_until_expiry()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FundingPool':
        """Create funding pool from dictionary."""
        return cls(**data)

    def __str__(self) -> str:
        return f"FundingPool({self.pool_name}, {self.available_balance}€ available, {self.status})"

    def __repr__(self) -> str:
        return self.__str__()