"""
Abstract Interfaces Module for GoodPlay Repository Pattern

Provides comprehensive abstract interfaces for repositories and services
to enable dependency injection, type safety, and proper testing patterns.

This module exports all interface definitions used throughout the GoodPlay
application for maintaining clean architecture and testability.
"""

# Base interfaces
from .base_interfaces import (
    IBaseRepository,
    IRepositoryFactory,
    IMockRepository
)

# Core repository interfaces
from .repository_interfaces import (
    IUserRepository,
    IGameRepository,
    IGameSessionRepository,
    IPreferencesRepository,
    IAchievementRepository,
    ISocialRepository
)

# Extended repository interfaces
from .extended_repository_interfaces import (
    IChallengeRepository,
    ITeamRepository,
    IGameModeRepository,
    ILeaderboardRepository,
    ITournamentRepository
)

# Service interfaces
from .service_interfaces import (
    IAuthService,
    IGameService,
    ISocialService,
    IPreferencesService,
    IChallengeService,
    ITeamService,
    INotificationService
)


# Organized exports for easy importing

# Base Repository Interfaces
BASE_INTERFACES = [
    'IBaseRepository',
    'IRepositoryFactory',
    'IMockRepository'
]

# Core Repository Interfaces
CORE_REPOSITORY_INTERFACES = [
    'IUserRepository',
    'IGameRepository',
    'IGameSessionRepository',
    'IPreferencesRepository',
    'IAchievementRepository',
    'ISocialRepository'
]

# Extended Repository Interfaces
EXTENDED_REPOSITORY_INTERFACES = [
    'IChallengeRepository',
    'ITeamRepository',
    'IGameModeRepository',
    'ILeaderboardRepository',
    'ITournamentRepository'
]

# Service Interfaces
SERVICE_INTERFACES = [
    'IAuthService',
    'IGameService',
    'ISocialService',
    'IPreferencesService',
    'IChallengeService',
    'ITeamService',
    'INotificationService'
]

# All repository interfaces combined
REPOSITORY_INTERFACES = (
    BASE_INTERFACES +
    CORE_REPOSITORY_INTERFACES +
    EXTENDED_REPOSITORY_INTERFACES
)

# All interfaces
ALL_INTERFACES = REPOSITORY_INTERFACES + SERVICE_INTERFACES


# Export all interfaces
__all__ = ALL_INTERFACES