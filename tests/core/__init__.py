"""
GoodPlay Test Core Module

This module provides the foundational architecture for the GoodPlay test suite,
including configuration management, base test classes, and utilities.

Components:
- TestConfig: Centralized test configuration management
- TestBase: Base class for all test cases
- Utils: Common testing utilities and helpers
- Interfaces: Abstract test interfaces for consistent testing patterns
"""

from .config import TestConfig
from .utils import TestUtils
from .test_base import TestBase

# Import all interfaces
from .interfaces import (
    # Base interfaces
    IBaseRepository,
    IRepositoryFactory,
    IMockRepository,

    # Core repository interfaces
    IUserRepository,
    IGameRepository,
    IGameSessionRepository,
    IPreferencesRepository,
    IAchievementRepository,
    ISocialRepository,

    # Extended repository interfaces
    IChallengeRepository,
    ITeamRepository,
    IGameModeRepository,
    ILeaderboardRepository,
    ITournamentRepository,

    # Service interfaces
    IAuthService,
    IGameService,
    ISocialService,
    IPreferencesService,
    IChallengeService,
    ITeamService,
    INotificationService
)

__all__ = [
    # Core test components
    'TestConfig',
    'TestBase',
    'TestUtils',

    # Base interfaces
    'IBaseRepository',
    'IRepositoryFactory',
    'IMockRepository',

    # Core repository interfaces
    'IUserRepository',
    'IGameRepository',
    'IGameSessionRepository',
    'IPreferencesRepository',
    'IAchievementRepository',
    'ISocialRepository',

    # Extended repository interfaces
    'IChallengeRepository',
    'ITeamRepository',
    'IGameModeRepository',
    'ILeaderboardRepository',
    'ITournamentRepository',

    # Service interfaces
    'IAuthService',
    'IGameService',
    'ISocialService',
    'IPreferencesService',
    'IChallengeService',
    'ITeamService',
    'INotificationService'
]