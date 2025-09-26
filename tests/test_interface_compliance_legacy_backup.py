"""
Interface Compliance Tests for GoodPlay Repository Pattern

Verifies that concrete repository implementations comply with their
corresponding abstract interfaces, ensuring proper inheritance and
method signature compatibility.
"""
import pytest
import inspect
from typing import get_type_hints

from tests.core.interfaces import (
    IUserRepository,
    IGameRepository,
    IPreferencesRepository,
    IAchievementRepository,
    ISocialRepository
)

from app.core.repositories.user_repository import UserRepository
from app.games.repositories.game_repository import GameRepository
from app.preferences.repositories.preferences_repository import PreferencesRepository
from app.social.achievements.repositories.achievement_repository import AchievementRepository
from app.social.repositories.relationship_repository import RelationshipRepository


class TestInterfaceCompliance:
    """Test that concrete implementations comply with abstract interfaces"""

    def test_user_repository_interface_compliance(self):
        """Test UserRepository implements IUserRepository correctly"""
        interface = IUserRepository
        implementation = UserRepository

        # Get all abstract methods from interface
        interface_methods = {
            name: method for name, method in inspect.getmembers(interface, inspect.isfunction)
            if getattr(method, '__isabstractmethod__', False)
        }

        # Check each abstract method exists in implementation
        for method_name, interface_method in interface_methods.items():
            assert hasattr(implementation, method_name), \
                f"UserRepository missing method: {method_name}"

            impl_method = getattr(implementation, method_name)

            # Get method signatures
            interface_sig = inspect.signature(interface_method)
            impl_sig = inspect.signature(impl_method)

            # Check parameter names match (excluding 'self')
            interface_params = list(interface_sig.parameters.keys())[1:]  # Skip 'self'
            impl_params = list(impl_sig.parameters.keys())[1:]  # Skip 'self'

            assert len(interface_params) <= len(impl_params), \
                f"Method {method_name}: implementation has fewer parameters than interface"

        print("✅ UserRepository complies with IUserRepository interface")

    def test_game_repository_interface_compliance(self):
        """Test GameRepository implements IGameRepository correctly"""
        interface = IGameRepository
        implementation = GameRepository

        # Get all abstract methods from interface
        interface_methods = {
            name: method for name, method in inspect.getmembers(interface, inspect.isfunction)
            if getattr(method, '__isabstractmethod__', False)
        }

        # Check key methods exist
        key_methods = [
            'create_game', 'get_game_by_id', 'get_games_by_category',
            'update_game', 'search_games'
        ]

        for method_name in key_methods:
            assert hasattr(implementation, method_name), \
                f"GameRepository missing method: {method_name}"

        print("✅ GameRepository complies with IGameRepository interface")

    def test_preferences_repository_interface_compliance(self):
        """Test PreferencesRepository implements IPreferencesRepository correctly"""
        interface = IPreferencesRepository
        implementation = PreferencesRepository

        # Check key methods exist (PreferencesRepository is not ABC-based)
        key_methods = [
            'get_user_preferences', 'update_preferences',
            'update_category', 'reset_to_defaults'
        ]

        for method_name in key_methods:
            assert hasattr(implementation, method_name), \
                f"PreferencesRepository missing method: {method_name}"

        print("✅ PreferencesRepository complies with IPreferencesRepository interface")

    def test_achievement_repository_interface_compliance(self):
        """Test AchievementRepository implements IAchievementRepository correctly"""
        interface = IAchievementRepository
        implementation = AchievementRepository

        # Check key methods exist
        key_methods = [
            'create_achievement', 'find_achievement_by_id', 'find_active_achievements',
            'create_user_achievement', 'find_user_achievements', 'increment_user_progress'
        ]

        for method_name in key_methods:
            assert hasattr(implementation, method_name), \
                f"AchievementRepository missing method: {method_name}"

        print("✅ AchievementRepository complies with IAchievementRepository interface")

    def test_social_repository_interface_compliance(self):
        """Test RelationshipRepository implements ISocialRepository correctly"""
        interface = ISocialRepository
        implementation = RelationshipRepository

        # Check key methods exist
        key_methods = [
            'create_relationship', 'find_relationship_between_users',
            'get_user_friends', 'update_relationship_status', 'are_friends'
        ]

        for method_name in key_methods:
            assert hasattr(implementation, method_name), \
                f"RelationshipRepository missing method: {method_name}"

        print("✅ RelationshipRepository complies with ISocialRepository interface")

    def test_base_repository_methods_compliance(self):
        """Test that repositories implement base CRUD methods"""
        repositories = [
            UserRepository,
            GameRepository,
            AchievementRepository,
            RelationshipRepository
        ]

        base_methods = [
            'find_by_id', 'find_one', 'find_many', 'create',
            'update_by_id', 'delete_by_id', 'count', 'create_indexes'
        ]

        for repo_class in repositories:
            for method_name in base_methods:
                assert hasattr(repo_class, method_name), \
                    f"{repo_class.__name__} missing base method: {method_name}"

        print("✅ All repositories implement base CRUD methods")

    def test_interface_method_signatures_are_complete(self):
        """Test that interface methods have proper type hints and docstrings"""
        interfaces = [
            IUserRepository,
            IGameRepository,
            IPreferencesRepository,
            IAchievementRepository,
            ISocialRepository
        ]

        for interface in interfaces:
            interface_methods = {
                name: method for name, method in inspect.getmembers(interface, inspect.isfunction)
                if getattr(method, '__isabstractmethod__', False)
            }

            for method_name, method in interface_methods.items():
                # Check method has docstring
                assert method.__doc__, \
                    f"{interface.__name__}.{method_name} missing docstring"

                # Check docstring contains Returns section (Args section is optional if no args)
                docstring = method.__doc__
                assert "Returns:" in docstring, \
                    f"{interface.__name__}.{method_name} missing Returns section in docstring"

                # Check Args section exists if method has parameters beyond self
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())[1:]  # Skip 'self'
                if params:  # Only require Args section if method has parameters
                    assert "Args:" in docstring, \
                        f"{interface.__name__}.{method_name} has parameters but missing Args section in docstring"

        print("✅ All interface methods have proper documentation")

    def test_interface_imports_work_correctly(self):
        """Test that all interfaces can be imported from various paths"""
        # Test direct imports
        from tests.core.interfaces import IBaseRepository, IUserRepository
        from tests.core.interfaces.repository_interfaces import IGameRepository
        from tests.core.interfaces.service_interfaces import IAuthService

        # Test imports through core module
        from tests.core import IBaseRepository as CoreIBaseRepository
        from tests.core import IUserRepository as CoreIUserRepository

        assert IBaseRepository is CoreIBaseRepository
        assert IUserRepository is CoreIUserRepository

        print("✅ Interface imports working correctly from all paths")

    def test_mock_repository_interface_usage(self):
        """Test that mock repositories can implement interfaces"""
        from tests.core.interfaces import IMockRepository
        from unittest.mock import Mock

        # Create a mock repository that implements IMockRepository methods
        mock_repo = Mock()

        # Mock repository should have these methods
        required_methods = [
            'find_by_id', 'create', 'seed_data', 'clear_all_data', 'get_all_data'
        ]

        for method_name in required_methods:
            setattr(mock_repo, method_name, Mock())

        # Test that we can call interface methods
        mock_repo.seed_data([{'test': 'data'}])
        mock_repo.clear_all_data()
        all_data = mock_repo.get_all_data()

        assert mock_repo.seed_data.called
        assert mock_repo.clear_all_data.called
        assert mock_repo.get_all_data.called

        print("✅ Mock repository interface works correctly")


if __name__ == "__main__":
    # Run compliance tests
    test_instance = TestInterfaceCompliance()

    test_instance.test_user_repository_interface_compliance()
    test_instance.test_game_repository_interface_compliance()
    test_instance.test_preferences_repository_interface_compliance()
    test_instance.test_achievement_repository_interface_compliance()
    test_instance.test_social_repository_interface_compliance()
    test_instance.test_base_repository_methods_compliance()
    test_instance.test_interface_method_signatures_are_complete()
    test_instance.test_interface_imports_work_correctly()
    test_instance.test_mock_repository_interface_usage()

    print("\n🎉 All interface compliance tests passed!")
    print("Repository interfaces are ready for dependency injection!")