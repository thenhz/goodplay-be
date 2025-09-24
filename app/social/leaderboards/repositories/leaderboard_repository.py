from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from ..models.leaderboard import Leaderboard
from ..models.leaderboard_entry import LeaderboardEntry


class LeaderboardRepository(BaseRepository):
    """Repository for leaderboard data access operations"""

    def __init__(self):
        super().__init__('leaderboards')

    def create_indexes(self):
        """Create optimized indexes for leaderboard queries"""
        # Compound unique index for leaderboard identification
        self.collection.create_index([
            ('leaderboard_type', 1),
            ('period', 1)
        ], unique=True)

        # Single field indexes
        self.collection.create_index('leaderboard_type')
        self.collection.create_index('period')
        self.collection.create_index('last_updated')

        # Entry-level indexes for efficient sorting and filtering
        self.collection.create_index('entries.user_id')
        self.collection.create_index([('entries.score', -1)])
        self.collection.create_index('entries.rank')

        # Metadata indexes for statistics
        self.collection.create_index('metadata.total_participants')

    def find_by_type_and_period(self, leaderboard_type: str,
                                period: str) -> Optional[Leaderboard]:
        """Find leaderboard by type and period"""
        data = self.find_one({
            'leaderboard_type': leaderboard_type,
            'period': period
        })
        return Leaderboard.from_dict(data) if data else None

    def create_leaderboard(self, leaderboard: Leaderboard) -> str:
        """Create new leaderboard"""
        data = leaderboard.to_dict()
        return self.create(data)

    def update_leaderboard(self, leaderboard: Leaderboard) -> bool:
        """Update existing leaderboard"""
        filter_dict = {
            'leaderboard_type': leaderboard.leaderboard_type,
            'period': leaderboard.period
        }
        return self.update_one(filter_dict, leaderboard.to_dict())

    def upsert_leaderboard(self, leaderboard: Leaderboard) -> bool:
        """Insert or update leaderboard"""
        filter_dict = {
            'leaderboard_type': leaderboard.leaderboard_type,
            'period': leaderboard.period
        }
        update_data = {'$set': leaderboard.to_dict()}

        result = self.collection.update_one(
            filter_dict,
            update_data,
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    def get_all_leaderboard_types(self) -> List[str]:
        """Get all available leaderboard types"""
        return self.collection.distinct('leaderboard_type')

    def get_leaderboards_by_type(self, leaderboard_type: str) -> List[Leaderboard]:
        """Get all leaderboards of a specific type"""
        results = self.find_many({'leaderboard_type': leaderboard_type})
        return [Leaderboard.from_dict(data) for data in results]

    def get_leaderboards_by_period(self, period: str) -> List[Leaderboard]:
        """Get all leaderboards of a specific period"""
        results = self.find_many({'period': period})
        return [Leaderboard.from_dict(data) for data in results]

    def get_leaderboard_summary(self) -> Dict[str, Any]:
        """Get summary of all leaderboards"""
        pipeline = [
            {
                '$group': {
                    '_id': {
                        'type': '$leaderboard_type',
                        'period': '$period'
                    },
                    'total_participants': {'$sum': '$metadata.total_participants'},
                    'last_updated': {'$max': '$last_updated'}
                }
            },
            {
                '$group': {
                    '_id': '$_id.type',
                    'periods': {
                        '$push': {
                            'period': '$_id.period',
                            'participants': '$total_participants',
                            'last_updated': '$last_updated'
                        }
                    },
                    'total_participants': {'$sum': '$total_participants'}
                }
            }
        ]

        results = list(self.collection.aggregate(pipeline))

        summary = {}
        for result in results:
            summary[result['_id']] = {
                'total_participants': result['total_participants'],
                'periods': result['periods']
            }

        return summary

    def add_entry_to_leaderboard(self, leaderboard_type: str, period: str,
                                entry: LeaderboardEntry) -> bool:
        """Add or update entry in leaderboard"""
        filter_dict = {
            'leaderboard_type': leaderboard_type,
            'period': period,
            'entries.user_id': {'$ne': entry.user_id}
        }

        # Add new entry
        add_result = self.collection.update_one(
            filter_dict,
            {
                '$push': {'entries': entry.to_dict()},
                '$set': {'last_updated': datetime.now(timezone.utc)}
            }
        )

        if add_result.modified_count > 0:
            return True

        # Update existing entry
        update_filter = {
            'leaderboard_type': leaderboard_type,
            'period': period,
            'entries.user_id': entry.user_id
        }

        update_result = self.collection.update_one(
            update_filter,
            {
                '$set': {
                    'entries.$.score': entry.score,
                    'entries.$.rank': entry.rank,
                    'entries.$.score_components': entry.score_components,
                    'last_updated': datetime.now(timezone.utc)
                }
            }
        )

        return update_result.modified_count > 0

    def remove_entry_from_leaderboard(self, leaderboard_type: str,
                                     period: str, user_id: str) -> bool:
        """Remove entry from leaderboard"""
        result = self.collection.update_one(
            {
                'leaderboard_type': leaderboard_type,
                'period': period
            },
            {
                '$pull': {'entries': {'user_id': ObjectId(user_id)}},
                '$set': {'last_updated': datetime.now(timezone.utc)}
            }
        )
        return result.modified_count > 0

    def get_user_leaderboard_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's positions across all leaderboards"""
        pipeline = [
            {'$unwind': '$entries'},
            {'$match': {'entries.user_id': ObjectId(user_id)}},
            {
                '$project': {
                    'leaderboard_type': 1,
                    'period': 1,
                    'rank': '$entries.rank',
                    'score': '$entries.score',
                    'total_participants': '$metadata.total_participants',
                    'last_updated': 1
                }
            }
        ]

        return list(self.collection.aggregate(pipeline))

    def get_top_performers(self, leaderboard_type: str, period: str,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performers from a specific leaderboard"""
        pipeline = [
            {
                '$match': {
                    'leaderboard_type': leaderboard_type,
                    'period': period
                }
            },
            {'$unwind': '$entries'},
            {'$sort': {'entries.rank': 1}},
            {'$limit': limit},
            {
                '$project': {
                    'user_id': '$entries.user_id',
                    'display_name': '$entries.display_name',
                    'score': '$entries.score',
                    'rank': '$entries.rank',
                    'score_components': '$entries.score_components',
                    'user_data': '$entries.user_data'
                }
            }
        ]

        return list(self.collection.aggregate(pipeline))

    def get_leaderboard_entries_paginated(self, leaderboard_type: str,
                                         period: str, skip: int = 0,
                                         limit: int = 50) -> Dict[str, Any]:
        """Get paginated entries from a leaderboard"""
        pipeline = [
            {
                '$match': {
                    'leaderboard_type': leaderboard_type,
                    'period': period
                }
            },
            {
                '$project': {
                    'entries': {
                        '$slice': [
                            {'$sortArray': {'input': '$entries', 'sortBy': {'rank': 1}}},
                            skip,
                            limit
                        ]
                    },
                    'metadata': 1,
                    'last_updated': 1,
                    'total_entries': {'$size': '$entries'}
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else {}

    def update_leaderboard_metadata(self, leaderboard_type: str,
                                   period: str, metadata: Dict[str, Any]) -> bool:
        """Update leaderboard metadata"""
        result = self.collection.update_one(
            {
                'leaderboard_type': leaderboard_type,
                'period': period
            },
            {
                '$set': {
                    'metadata': metadata,
                    'last_updated': datetime.now(timezone.utc)
                }
            }
        )
        return result.modified_count > 0

    def clear_leaderboard_entries(self, leaderboard_type: str,
                                 period: str) -> bool:
        """Clear all entries from a leaderboard"""
        result = self.collection.update_one(
            {
                'leaderboard_type': leaderboard_type,
                'period': period
            },
            {
                '$set': {
                    'entries': [],
                    'metadata.total_participants': 0,
                    'metadata.min_score': 0.0,
                    'metadata.max_score': 0.0,
                    'metadata.avg_score': 0.0,
                    'metadata.score_range': 0.0,
                    'last_updated': datetime.now(timezone.utc)
                }
            }
        )
        return result.modified_count > 0

    def get_stale_leaderboards(self, hours_threshold: int = 1) -> List[Dict[str, str]]:
        """Get leaderboards that need updating"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)

        results = self.find_many(
            {'last_updated': {'$lt': cutoff_date}},
            limit=None
        )

        return [
            {
                'leaderboard_type': result['leaderboard_type'],
                'period': result['period']
            }
            for result in results
        ]

    def get_leaderboard_statistics(self, leaderboard_type: str,
                                  period: str) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a leaderboard"""
        pipeline = [
            {
                '$match': {
                    'leaderboard_type': leaderboard_type,
                    'period': period
                }
            },
            {'$unwind': '$entries'},
            {
                '$group': {
                    '_id': None,
                    'total_participants': {'$sum': 1},
                    'avg_score': {'$avg': '$entries.score'},
                    'max_score': {'$max': '$entries.score'},
                    'min_score': {'$min': '$entries.score'},
                    'median_rank': {'$avg': '$entries.rank'},
                    'score_distribution': {
                        '$push': '$entries.score'
                    }
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        if not result:
            return None

        stats = result[0]

        # Calculate percentiles
        scores = sorted(stats['score_distribution'])
        n = len(scores)

        if n > 0:
            stats['percentiles'] = {
                '25th': scores[int(0.25 * n)] if n > 4 else scores[0],
                '50th': scores[int(0.50 * n)] if n > 2 else scores[0],
                '75th': scores[int(0.75 * n)] if n > 4 else scores[-1],
                '90th': scores[int(0.90 * n)] if n > 10 else scores[-1]
            }
        else:
            stats['percentiles'] = {}

        # Remove raw score distribution from response
        del stats['score_distribution']

        return stats

    def bulk_update_ranks(self, leaderboard_type: str, period: str) -> bool:
        """Bulk update ranks for all entries in a leaderboard"""
        # Get leaderboard and sort entries by score
        pipeline = [
            {
                '$match': {
                    'leaderboard_type': leaderboard_type,
                    'period': period
                }
            },
            {'$unwind': '$entries'},
            {'$sort': {'entries.score': -1}},
            {
                '$group': {
                    '_id': {'type': '$leaderboard_type', 'period': '$period'},
                    'entries': {
                        '$push': {
                            'user_id': '$entries.user_id',
                            'score': '$entries.score',
                            'display_name': '$entries.display_name',
                            'user_data': '$entries.user_data',
                            'score_components': '$entries.score_components'
                        }
                    }
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        if not result:
            return False

        # Add ranks and prepare entries for update
        entries = result[0]['entries']
        for rank, entry in enumerate(entries, 1):
            entry['rank'] = rank
            entry['created_at'] = datetime.now(timezone.utc)

        # Update leaderboard with re-ranked entries
        update_result = self.collection.update_one(
            {
                'leaderboard_type': leaderboard_type,
                'period': period
            },
            {
                '$set': {
                    'entries': entries,
                    'last_updated': datetime.now(timezone.utc)
                }
            }
        )

        return update_result.modified_count > 0

    def delete_leaderboard(self, leaderboard_type: str, period: str) -> bool:
        """Delete a leaderboard"""
        return self.delete_one({
            'leaderboard_type': leaderboard_type,
            'period': period
        })

    def get_cross_leaderboard_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user's performance across all leaderboards"""
        pipeline = [
            {'$unwind': '$entries'},
            {'$match': {'entries.user_id': ObjectId(user_id)}},
            {
                '$group': {
                    '_id': '$entries.user_id',
                    'leaderboards': {
                        '$push': {
                            'type': '$leaderboard_type',
                            'period': '$period',
                            'rank': '$entries.rank',
                            'score': '$entries.score',
                            'total_participants': '$metadata.total_participants'
                        }
                    },
                    'avg_rank': {'$avg': '$entries.rank'},
                    'best_rank': {'$min': '$entries.rank'},
                    'total_score': {'$sum': '$entries.score'},
                    'leaderboard_count': {'$sum': 1}
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else {}