from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from ..models.impact_score import ImpactScore


class ImpactScoreRepository(BaseRepository):
    """Repository for impact score data access operations"""

    def __init__(self):
        super().__init__('user_impact_scores')

    def create_indexes(self):
        """Create optimized indexes for impact score queries"""
        # Single field indexes
        self.collection.create_index('user_id', unique=True)
        self.collection.create_index([('impact_score', -1)])  # Descending for rankings
        self.collection.create_index('last_calculated')

        # Component scores for specialized leaderboards
        self.collection.create_index([('gaming_component', -1)])
        self.collection.create_index([('social_component', -1)])
        self.collection.create_index([('donation_component', -1)])

        # Ranking indexes
        self.collection.create_index('rank_global')
        self.collection.create_index('rank_weekly')

        # Compound indexes for efficient queries
        self.collection.create_index([
            ('impact_score', -1),
            ('last_calculated', -1)
        ])

    def find_by_user_id(self, user_id: str) -> Optional[ImpactScore]:
        """Find impact score by user ID"""
        data = self.find_one({'user_id': ObjectId(user_id)})
        return ImpactScore.from_dict(data) if data else None

    def create_impact_score(self, impact_score: ImpactScore) -> str:
        """Create new impact score record"""
        data = impact_score.to_dict()
        return self.create(data)

    def update_impact_score(self, impact_score: ImpactScore) -> bool:
        """Update existing impact score"""
        data = impact_score.to_dict()
        return self.update_one(
            {'user_id': impact_score.user_id},
            data
        )

    def upsert_impact_score(self, impact_score: ImpactScore) -> bool:
        """Insert or update impact score"""
        filter_dict = {'user_id': impact_score.user_id}
        update_data = {'$set': impact_score.to_dict()}

        result = self.collection.update_one(
            filter_dict,
            update_data,
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    def get_global_rankings(self, limit: int = 100,
                           skip: int = 0) -> List[Dict[str, Any]]:
        """Get global impact score rankings"""
        pipeline = [
            {'$sort': {'impact_score': -1}},
            {'$skip': skip},
            {'$limit': limit},
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user_profile'
                }
            },
            {
                '$project': {
                    'user_id': 1,
                    'impact_score': 1,
                    'gaming_component': 1,
                    'social_component': 1,
                    'donation_component': 1,
                    'rank_global': 1,
                    'last_calculated': 1,
                    'user_profile.first_name': 1,
                    'user_profile.social_profile.display_name': 1,
                    'user_profile.preferences.privacy.leaderboard_participation': 1
                }
            }
        ]

        return list(self.collection.aggregate(pipeline))

    def get_component_rankings(self, component: str, limit: int = 100,
                              skip: int = 0) -> List[Dict[str, Any]]:
        """Get rankings by specific component (gaming, social, donation)"""
        component_field = f'{component}_component'

        pipeline = [
            {'$sort': {component_field: -1}},
            {'$skip': skip},
            {'$limit': limit},
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user_profile'
                }
            },
            {
                '$project': {
                    'user_id': 1,
                    'impact_score': 1,
                    component_field: 1,
                    f'{component}_details': 1,
                    'last_calculated': 1,
                    'user_profile.first_name': 1,
                    'user_profile.social_profile.display_name': 1,
                    'user_profile.preferences.privacy.leaderboard_participation': 1
                }
            }
        ]

        return list(self.collection.aggregate(pipeline))

    def get_weekly_active_users(self, weeks_back: int = 1) -> List[Dict[str, Any]]:
        """Get users active in the last N weeks with scores"""
        cutoff_date = datetime.utcnow() - timedelta(weeks=weeks_back)

        pipeline = [
            {'$match': {'last_calculated': {'$gte': cutoff_date}}},
            {'$sort': {'impact_score': -1}},
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user_profile'
                }
            },
            {
                '$project': {
                    'user_id': 1,
                    'impact_score': 1,
                    'gaming_component': 1,
                    'social_component': 1,
                    'donation_component': 1,
                    'last_calculated': 1,
                    'user_profile.first_name': 1,
                    'user_profile.social_profile.display_name': 1,
                    'user_profile.preferences.privacy.leaderboard_participation': 1
                }
            }
        ]

        return list(self.collection.aggregate(pipeline))

    def get_friends_rankings(self, user_id: str,
                            friend_ids: List[str]) -> List[Dict[str, Any]]:
        """Get impact score rankings for a user and their friends"""
        all_user_ids = [ObjectId(user_id)] + [ObjectId(fid) for fid in friend_ids]

        pipeline = [
            {'$match': {'user_id': {'$in': all_user_ids}}},
            {'$sort': {'impact_score': -1}},
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user_profile'
                }
            },
            {
                '$project': {
                    'user_id': 1,
                    'impact_score': 1,
                    'gaming_component': 1,
                    'social_component': 1,
                    'donation_component': 1,
                    'last_calculated': 1,
                    'user_profile.first_name': 1,
                    'user_profile.social_profile.display_name': 1
                }
            }
        ]

        return list(self.collection.aggregate(pipeline))

    def get_score_statistics(self) -> Dict[str, Any]:
        """Get overall score statistics"""
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'total_users': {'$sum': 1},
                    'avg_impact_score': {'$avg': '$impact_score'},
                    'max_impact_score': {'$max': '$impact_score'},
                    'min_impact_score': {'$min': '$impact_score'},
                    'avg_gaming_component': {'$avg': '$gaming_component'},
                    'avg_social_component': {'$avg': '$social_component'},
                    'avg_donation_component': {'$avg': '$donation_component'}
                }
            }
        ]

        result = list(self.collection.aggregate(pipeline))
        return result[0] if result else {}

    def update_rankings(self) -> int:
        """Update global and weekly rankings for all users"""
        # Update global rankings
        global_pipeline = [
            {'$sort': {'impact_score': -1}},
            {
                '$group': {
                    '_id': None,
                    'users': {
                        '$push': {
                            'user_id': '$user_id',
                            'impact_score': '$impact_score'
                        }
                    }
                }
            }
        ]

        global_result = list(self.collection.aggregate(global_pipeline))
        if not global_result:
            return 0

        updated_count = 0

        # Update global ranks
        for rank, user_data in enumerate(global_result[0]['users'], 1):
            self.collection.update_one(
                {'user_id': user_data['user_id']},
                {'$set': {'rank_global': rank}}
            )
            updated_count += 1

        # Update weekly rankings for active users
        cutoff_date = datetime.utcnow() - timedelta(weeks=1)
        weekly_pipeline = [
            {'$match': {'last_calculated': {'$gte': cutoff_date}}},
            {'$sort': {'impact_score': -1}},
            {
                '$group': {
                    '_id': None,
                    'users': {
                        '$push': {
                            'user_id': '$user_id',
                            'impact_score': '$impact_score'
                        }
                    }
                }
            }
        ]

        weekly_result = list(self.collection.aggregate(weekly_pipeline))
        if weekly_result:
            for rank, user_data in enumerate(weekly_result[0]['users'], 1):
                self.collection.update_one(
                    {'user_id': user_data['user_id']},
                    {'$set': {'rank_weekly': rank}}
                )

        return updated_count

    def get_stale_scores(self, hours_threshold: int = 24) -> List[str]:
        """Get user IDs with stale impact scores"""
        cutoff_date = datetime.utcnow() - timedelta(hours=hours_threshold)

        results = self.find_many(
            {'last_calculated': {'$lt': cutoff_date}},
            limit=None
        )

        return [str(result['user_id']) for result in results]

    def delete_user_score(self, user_id: str) -> bool:
        """Delete impact score for a user"""
        return self.delete_one({'user_id': ObjectId(user_id)})

    def get_user_rank_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's ranking information and percentiles"""
        user_score = self.find_by_user_id(user_id)
        if not user_score:
            return None

        # Get total user count
        total_users = self.count()

        # Get users with higher scores
        higher_score_count = self.count({
            'impact_score': {'$gt': user_score.impact_score}
        })

        # Calculate percentile
        percentile = ((total_users - higher_score_count) / total_users * 100) if total_users > 0 else 0

        return {
            'global_rank': user_score.rank_global or (higher_score_count + 1),
            'weekly_rank': user_score.rank_weekly,
            'percentile': round(percentile, 2),
            'total_users': total_users,
            'impact_score': user_score.impact_score,
            'components': user_score.get_component_breakdown()
        }