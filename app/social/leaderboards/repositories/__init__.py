"""
Leaderboards Repositories Module

Data access layer for impact scores and leaderboards.
"""

from .impact_score_repository import ImpactScoreRepository
from .leaderboard_repository import LeaderboardRepository

__all__ = ['ImpactScoreRepository', 'LeaderboardRepository']