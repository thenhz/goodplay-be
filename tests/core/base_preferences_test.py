"""
BasePreferencesTest - Specialized Base Class for User Preferences Testing (GOO-35)

Provides specialized testing capabilities for user preferences functionality
including validation, synchronization, defaults, and preference categories.
"""
from typing import Dict, Any, Optional, List, Union
from unittest.mock import MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone

from tests.core.base_service_test import BaseServiceTest


class BasePreferencesTest(BaseServiceTest):
    """
    Specialized base test class for user preferences functionality.

    Features:
    - Preference validation and schema testing
    - Default preferences management
    - Preference category testing (gaming, notifications, privacy, donations)
    - Preference synchronization scenarios
    - Migration and upgrade testing
    - Cross-platform preference consistency
    """

    # Default dependencies for preferences tests
    default_dependencies = [
        'user_repository',
        'preferences_repository',
        'preferences_service',
        'validation_service'
    ]

    # External dependencies for preferences
    default_external_dependencies = [
        'redis',  # For preference caching
        'config_service'  # For default preferences
    ]

    def setUp(self):
        """Enhanced setup for preferences testing"""
        super().setUp()
        self._setup_preferences_mocks()
        self._setup_validation_mocks()
        self._setup_default_preferences()

    def _setup_preferences_mocks(self):
        """Setup preferences-related mocks"""
        if hasattr(self, 'mock_preferences_repository'):
            # Default preferences repository behavior
            self.mock_preferences_repository.find_by_user_id.return_value = None
            self.mock_preferences_repository.create.return_value = str(ObjectId())
            self.mock_preferences_repository.update.return_value = True
            self.mock_preferences_repository.delete.return_value = True

        if hasattr(self, 'mock_preferences_service'):
            # Default preferences service behavior
            self.mock_preferences_service.get_user_preferences.return_value = (True, "Preferences retrieved", {})
            self.mock_preferences_service.update_user_preferences.return_value = (True, "Preferences updated", {})
            self.mock_preferences_service.reset_to_defaults.return_value = (True, "Preferences reset", {})

    def _setup_validation_mocks(self):
        """Setup preference validation mocks"""
        if hasattr(self, 'mock_validation_service'):
            self.mock_validation_service.validate_preferences.return_value = (True, "Valid", [])
            self.mock_validation_service.validate_preference_category.return_value = (True, "Valid category", [])

    def _setup_default_preferences(self):
        """Setup default preference structures for testing"""
        self.default_preferences = self.create_default_preferences()

    def create_default_preferences(self) -> Dict[str, Any]:
        """Create default preferences structure for testing"""
        return {
            'gaming': {
                'preferred_categories': ['puzzle', 'strategy'],
                'difficulty_level': 'medium',
                'tutorial_enabled': True,
                'auto_save': True,
                'sound_enabled': True,
                'music_enabled': True,
                'vibration_enabled': True,
                'screen_timeout': 300,
                'graphics_quality': 'high'
            },
            'notifications': {
                'push_enabled': True,
                'email_enabled': False,
                'frequency': 'daily',
                'achievement_alerts': True,
                'donation_confirmations': True,
                'friend_activity': True,
                'tournament_reminders': True,
                'maintenance_alerts': True,
                'challenge_invites': True,
                'leaderboard_updates': False
            },
            'privacy': {
                'profile_visibility': 'friends',
                'stats_sharing': True,
                'friends_discovery': True,
                'leaderboard_participation': True,
                'activity_visibility': 'friends',
                'contact_permissions': 'friends',
                'data_sharing': False,
                'analytics_tracking': True
            },
            'donations': {
                'auto_donate_enabled': False,
                'auto_donate_percentage': 5.0,
                'preferred_causes': ['education', 'environment'],
                'notification_threshold': 25.0,
                'monthly_goal': 50.0,
                'impact_sharing': True,
                'anonymous_donations': False,
                'tax_receipt_required': True
            },
            'accessibility': {
                'high_contrast': False,
                'large_text': False,
                'reduced_motion': False,
                'colorblind_support': False,
                'screen_reader_support': False,
                'voice_commands': False
            },
            'meta': {
                'version': 1,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'synchronized': True
            }
        }

    # Preference creation utilities

    def create_test_user_with_preferences(self, **user_overrides) -> Dict[str, Any]:
        """Create test user data with preferences included"""
        from tests.utils import user

        user_data = (user()
                    .as_type(user_overrides.pop('role', 'user'))
                    .with_preferences(self.create_test_preferences())
                    .merge(user_overrides)
                    .build())

        return user_data

    def create_test_preferences(self, user_id: str = None, **category_overrides) -> Dict[str, Any]:
        """Create test preferences with optional category overrides"""
        user_id = user_id or str(ObjectId())

        preferences = {
            '_id': ObjectId(),
            'user_id': user_id,
            'preferences': self.default_preferences.copy()
        }

        # Apply category overrides
        for category, overrides in category_overrides.items():
            if category in preferences['preferences']:
                preferences['preferences'][category].update(overrides)

        return preferences

    def create_custom_gaming_preferences(self, **gaming_prefs) -> Dict[str, Any]:
        """Create preferences with custom gaming settings"""
        gaming_overrides = {
            'gaming': gaming_prefs
        }
        return self.create_test_preferences(**gaming_overrides)

    def create_custom_notification_preferences(self, **notification_prefs) -> Dict[str, Any]:
        """Create preferences with custom notification settings"""
        notification_overrides = {
            'notifications': notification_prefs
        }
        return self.create_test_preferences(**notification_overrides)

    def create_privacy_preferences(self, privacy_level: str = 'medium') -> Dict[str, Any]:
        """Create preferences with predefined privacy levels"""
        privacy_levels = {
            'public': {
                'profile_visibility': 'public',
                'stats_sharing': True,
                'friends_discovery': True,
                'leaderboard_participation': True,
                'activity_visibility': 'public',
                'contact_permissions': 'everyone'
            },
            'medium': {
                'profile_visibility': 'friends',
                'stats_sharing': True,
                'friends_discovery': True,
                'leaderboard_participation': True,
                'activity_visibility': 'friends',
                'contact_permissions': 'friends'
            },
            'private': {
                'profile_visibility': 'private',
                'stats_sharing': False,
                'friends_discovery': False,
                'leaderboard_participation': False,
                'activity_visibility': 'private',
                'contact_permissions': 'none'
            }
        }

        privacy_settings = privacy_levels.get(privacy_level, privacy_levels['medium'])
        return self.create_test_preferences(privacy=privacy_settings)

    def create_accessibility_preferences(self, **accessibility_prefs) -> Dict[str, Any]:
        """Create preferences with accessibility settings"""
        accessibility_overrides = {
            'accessibility': accessibility_prefs
        }
        return self.create_test_preferences(**accessibility_overrides)

    def create_custom_gaming_preferences(self, difficulty_level: str = "medium", tutorial_enabled: bool = True, sound_enabled: bool = True, **kwargs) -> Dict[str, Any]:
        """Create user with custom gaming preferences"""
        gaming_overrides = {
            'gaming': {
                'difficulty_level': difficulty_level,
                'tutorial_enabled': tutorial_enabled,
                'preferred_categories': ['puzzle', 'strategy', 'action'],
                'sound_enabled': sound_enabled,
                'music_enabled': True,
                **kwargs
            }
        }
        return self.create_test_preferences(**gaming_overrides)

    def create_custom_notification_preferences(self, push_enabled: bool = True, email_enabled: bool = False, frequency: str = "daily", **kwargs) -> Dict[str, Any]:
        """Create user with custom notification preferences"""
        notification_overrides = {
            'notifications': {
                'push_enabled': push_enabled,
                'email_enabled': email_enabled,
                'frequency': frequency,
                'achievement_alerts': True,
                **kwargs
            }
        }
        return self.create_test_preferences(**notification_overrides)

    # Preference validation utilities

    def assert_preferences_valid(self, preferences: Dict[str, Any], category: str = None):
        """Assert preference structure is valid"""
        if category:
            # Validate specific category
            assert category in preferences.get('preferences', {}), f"Missing category: {category}"
            category_prefs = preferences['preferences'][category]
            self._assert_category_structure(category, category_prefs)
        else:
            # Validate all categories
            required_categories = ['gaming', 'notifications', 'privacy', 'donations']
            prefs_data = preferences.get('preferences', {})

            for cat in required_categories:
                assert cat in prefs_data, f"Missing required category: {cat}"
                self._assert_category_structure(cat, prefs_data[cat])

    def _assert_category_structure(self, category: str, category_prefs: Dict[str, Any]):
        """Assert specific category structure is valid"""
        required_fields = {
            'gaming': ['difficulty_level', 'tutorial_enabled', 'sound_enabled'],
            'notifications': ['push_enabled', 'email_enabled', 'frequency'],
            'privacy': ['profile_visibility', 'stats_sharing'],
            'donations': ['auto_donate_enabled', 'preferred_causes']
        }

        category_required = required_fields.get(category, [])
        for field in category_required:
            assert field in category_prefs, f"Missing required field in {category}: {field}"

    def assert_preference_value_valid(self, value: Any, expected_type: type, valid_values: List[Any] = None):
        """Assert preference value is valid type and within valid range"""
        assert isinstance(value, expected_type), f"Expected {expected_type.__name__}, got {type(value).__name__}"

        if valid_values:
            assert value in valid_values, f"Value {value} not in valid values: {valid_values}"

    # Mock preference scenarios

    def mock_preferences_retrieval_scenario(self, user_id: str, has_preferences: bool = True):
        """Mock preference retrieval scenario"""
        if has_preferences:
            preferences = self.create_test_preferences(user_id)
            self.mock_preferences_repository.find_by_user_id.return_value = preferences
            self.mock_preferences_service.get_user_preferences.return_value = (
                True, "PREFERENCES_RETRIEVED_SUCCESS", preferences
            )
            return preferences
        else:
            self.mock_preferences_repository.find_by_user_id.return_value = None
            self.mock_preferences_service.get_user_preferences.return_value = (
                True, "PREFERENCES_DEFAULT_CREATED", self.create_test_preferences(user_id)
            )
            return None

    def mock_preferences_update_scenario(self, user_id: str, updates: Dict[str, Any], validation_success: bool = True):
        """Mock preference update scenario"""
        current_preferences = self.create_test_preferences(user_id)

        if validation_success:
            self.mock_validation_service.validate_preferences.return_value = (True, "Valid", [])
            self.mock_preferences_repository.update.return_value = True

            # Create updated preferences
            updated_preferences = current_preferences.copy()
            for category, category_updates in updates.items():
                if category in updated_preferences['preferences']:
                    updated_preferences['preferences'][category].update(category_updates)

            self.mock_preferences_service.update_user_preferences.return_value = (
                True, "PREFERENCES_UPDATED_SUCCESS", updated_preferences
            )

            return updated_preferences
        else:
            validation_errors = [f"Invalid value for {list(updates.keys())[0]}"]
            self.mock_validation_service.validate_preferences.return_value = (False, "Invalid", validation_errors)
            self.mock_preferences_service.update_user_preferences.return_value = (
                False, "PREFERENCES_VALIDATION_FAILED", validation_errors
            )

            return None

    def mock_preferences_migration_scenario(self, user_id: str, old_version: int = 0, target_version: int = 1):
        """Mock preference migration scenario"""
        # Create old format preferences
        old_preferences = self.create_test_preferences(user_id)
        old_preferences['preferences']['meta']['version'] = old_version

        # Mock migration service
        if hasattr(self, 'mock_migration_service'):
            migrated_preferences = old_preferences.copy()
            migrated_preferences['preferences']['meta']['version'] = target_version
            migrated_preferences['preferences']['meta']['migrated'] = True

            self.mock_migration_service.migrate_preferences.return_value = (
                True, "Migration completed", migrated_preferences
            )

            return old_preferences, migrated_preferences

        return old_preferences, old_preferences

    # Preference synchronization testing

    def create_sync_conflict_scenario(self, user_id: str) -> Dict[str, Any]:
        """Create preference synchronization conflict scenario"""
        # Local preferences
        local_prefs = self.create_test_preferences(
            user_id,
            gaming={'difficulty_level': 'hard', 'sound_enabled': False}
        )
        local_prefs['preferences']['meta']['updated_at'] = datetime.now(timezone.utc).isoformat()

        # Remote preferences (conflicting)
        remote_prefs = self.create_test_preferences(
            user_id,
            gaming={'difficulty_level': 'easy', 'music_enabled': False}
        )
        remote_prefs['preferences']['meta']['updated_at'] = datetime.now(timezone.utc).isoformat()

        return {
            'local': local_prefs,
            'remote': remote_prefs,
            'conflicts': ['gaming.difficulty_level', 'gaming.music_enabled']
        }

    def mock_preference_sync_scenario(self, sync_conflict: bool = False):
        """Mock preference synchronization scenario"""
        if hasattr(self, 'mock_sync_service'):
            if sync_conflict:
                conflict = self.create_sync_conflict_scenario(str(ObjectId()))
                self.mock_sync_service.sync_preferences.return_value = (
                    False, "Sync conflict detected", conflict
                )
                return conflict
            else:
                self.mock_sync_service.sync_preferences.return_value = (
                    True, "Preferences synchronized", {}
                )
                return None

    # Preference testing utilities

    def run_preference_category_combinations(self, test_func, categories: List[str] = None):
        """Test function with different preference category combinations"""
        categories = categories or ['gaming', 'notifications', 'privacy', 'donations']
        results = {}

        for category in categories:
            # Create preferences with specific category modifications
            category_prefs = self.create_test_preferences(**{
                category: {'test_field': True}
            })

            results[category] = test_func(category_prefs, category)

        return results

    def validate_preference_constraints(self, preferences: Dict[str, Any]) -> List[str]:
        """Validate preference business rules and constraints"""
        violations = []
        prefs = preferences.get('preferences', {})

        # Gaming constraints
        gaming = prefs.get('gaming', {})
        if gaming.get('difficulty_level') == 'expert' and gaming.get('tutorial_enabled', True):
            violations.append("Expert difficulty should not have tutorial enabled")

        # Privacy constraints
        privacy = prefs.get('privacy', {})
        if privacy.get('profile_visibility') == 'private' and privacy.get('leaderboard_participation', False):
            violations.append("Private profiles cannot participate in leaderboards")

        # Notification constraints
        notifications = prefs.get('notifications', {})
        if not notifications.get('push_enabled', True) and notifications.get('achievement_alerts', True):
            violations.append("Achievement alerts require push notifications to be enabled")

        # Donation constraints
        donations = prefs.get('donations', {})
        if donations.get('auto_donate_enabled', False) and donations.get('auto_donate_percentage', 0) <= 0:
            violations.append("Auto-donate requires a positive percentage")

        return violations

    def create_preference_test_matrix(self) -> List[Dict[str, Any]]:
        """Create matrix of preference combinations for comprehensive testing"""
        test_cases = []

        # Basic valid combinations
        test_cases.extend([
            self.create_custom_gaming_preferences(difficulty_level='easy', tutorial_enabled=True),
            self.create_custom_gaming_preferences(difficulty_level='hard', tutorial_enabled=False),
            self.create_privacy_preferences('public'),
            self.create_privacy_preferences('private'),
            self.create_custom_notification_preferences(push_enabled=True, email_enabled=True),
            self.create_custom_notification_preferences(push_enabled=False, email_enabled=False),
        ])

        # Accessibility combinations
        test_cases.extend([
            self.create_accessibility_preferences(high_contrast=True, large_text=True),
            self.create_accessibility_preferences(reduced_motion=True, screen_reader_support=True),
        ])

        return test_cases

    def tearDown(self):
        """Clean up preferences-specific mocks"""
        super().tearDown()


# Convenience functions for preferences testing

def preferences_test(service_class=None, preference_categories: List[str] = None, **kwargs):
    """Decorator for creating preferences test class with specific configuration"""
    def decorator(cls):
        if service_class:
            cls.service_class = service_class

        # Add category-specific dependencies
        if preference_categories:
            category_deps = {
                'gaming': ['game_preferences_service'],
                'notifications': ['notification_service', 'push_service'],
                'privacy': ['privacy_service', 'data_protection_service'],
                'donations': ['donation_service', 'payment_service'],
                'accessibility': ['accessibility_service']
            }

            extra_deps = []
            for category in preference_categories:
                extra_deps.extend(category_deps.get(category, []))

            cls.dependencies = BasePreferencesTest.default_dependencies + extra_deps

        return cls

    return decorator


# Usage Examples:
"""
# Basic preferences service test
class TestPreferencesService(BasePreferencesTest):
    service_class = PreferencesService

    def test_get_user_preferences_success(self):
        user_id = str(ObjectId())
        preferences = self.mock_preferences_retrieval_scenario(user_id)

        result = self.service.get_user_preferences(user_id)

        assert result[0] is True
        self.assert_preferences_valid(result[2])

    def test_update_preferences_validation(self):
        user_id = str(ObjectId())
        updates = {
            'gaming': {'difficulty_level': 'invalid_level'}
        }

        self.mock_preferences_update_scenario(user_id, updates, validation_success=False)

        result = self.service.update_user_preferences(user_id, updates)

        assert result[0] is False
        assert 'validation' in result[1].lower()

# Category-specific testing
@preferences_test(service_class=GamingPreferencesService, preference_categories=['gaming'])
class TestGamingPreferences(BasePreferencesTest):
    def test_difficulty_progression(self):
        user_id = str(ObjectId())

        # Test progression from easy to expert
        difficulties = ['easy', 'medium', 'hard', 'expert']
        for difficulty in difficulties:
            prefs = self.create_custom_gaming_preferences(difficulty_level=difficulty)
            self.assert_preferences_valid(prefs, 'gaming')

    def test_gaming_constraint_validation(self):
        # Test expert difficulty with tutorial constraint
        prefs = self.create_custom_gaming_preferences(
            difficulty_level='expert',
            tutorial_enabled=True
        )

        violations = self.validate_preference_constraints(prefs)
        assert len(violations) > 0

# Comprehensive preference matrix testing
class TestPreferenceMatrix(BasePreferencesTest):
    service_class = PreferencesService

    def test_all_preference_combinations(self):
        test_matrix = self.create_preference_test_matrix()

        for i, preferences in enumerate(test_matrix):
            with self.subTest(f"preference_combination_{i}"):
                # Test each combination
                violations = self.validate_preference_constraints(preferences)
                if violations:
                    print(f"Preference combination {i} has violations: {violations}")

                # Basic validation should still pass
                self.assert_preferences_valid(preferences)

# Synchronization testing
class TestPreferenceSync(BasePreferencesTest):
    service_class = PreferenceSyncService

    def test_sync_conflict_resolution(self):
        conflict_scenario = self.mock_preference_sync_scenario(sync_conflict=True)

        result = self.service.resolve_sync_conflict(
            conflict_scenario['local'],
            conflict_scenario['remote'],
            resolution_strategy='merge'
        )

        assert result[0] is True
        resolved_prefs = result[2]
        self.assert_preferences_valid(resolved_prefs)
"""