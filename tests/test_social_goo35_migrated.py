"""
GOO-35 Social Testing Suite - Migrated Legacy Version

Migrated from legacy test_social.py to use GOO-35 Testing Utilities
with BaseSocialTest for comprehensive social system testing.
"""
import os
import sys
from bson import ObjectId
from datetime import datetime, timezone

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.core.base_social_test import BaseSocialTest
from app.social.services.relationship_service import RelationshipService


class TestSocialSystemGOO35(BaseSocialTest):
    """GOO-35 Social System Testing"""
    service_class = RelationshipService

    def test_social_user_creation(self):
        """Test social user data structure"""
        user = self.create_test_social_user(
            display_name='Social User',
            email='social@test.com'
        )

        self.assertEqual(user['display_name'], 'Social User')
        self.assertEqual(user['email'], 'social@test.com')
        self.assertIsNotNone(user['_id'])

    def test_friend_request_system(self):
        """Test friend request functionality"""
        user1 = self.create_test_social_user(display_name='User 1')
        user2 = self.create_test_social_user(display_name='User 2')

        friend_request = self.create_test_friend_request(
            sender_id=user1['_id'],
            target_id=user2['_id'],
            status='pending'
        )

        self.assertEqual(friend_request['sender_id'], user1['_id'])
        self.assertEqual(friend_request['target_id'], user2['_id'])
        self.assertEqual(friend_request['status'], 'pending')

    def test_social_achievement_system(self):
        """Test social achievement functionality"""
        achievement = self.create_test_achievement(
            achievement_type='social',
            name='Social Butterfly'
        )

        self.assertEqual(achievement['type'], 'social')
        self.assertEqual(achievement['name'], 'Social Butterfly')
        self.assertIsNotNone(achievement['_id'])

    def test_user_relationship_types(self):
        """Test different relationship types"""
        user1 = self.create_test_social_user()
        user2 = self.create_test_social_user()

        relationship_types = ['friend', 'blocked', 'following']

        for rel_type in relationship_types:
            relationship = self.create_test_relationship(
                user1_id=user1['_id'],
                user2_id=user2['_id'],
                relationship_type=rel_type
            )

            self.assertEqual(relationship['relationship_type'], rel_type)
            self.assertIn(user1['_id'], [relationship['user1_id'], relationship['user2_id']])
            self.assertIn(user2['_id'], [relationship['user1_id'], relationship['user2_id']])