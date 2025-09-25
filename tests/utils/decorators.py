"""
Parametrized Test Decorators for GoodPlay Testing (GOO-35)

Provides intelligent decorators for parametrized testing that dramatically
reduce boilerplate code by automatically generating test variations.
"""
import functools
from typing import List, Dict, Any, Callable, Optional, Union
import pytest
from unittest.mock import patch

from .builders import user, admin_user, game, puzzle_game, session
from .mocks import mock_authentication, AuthenticationMocker


# User Type Parametrization

def test_all_user_types(types: List[str] = None, exclude: List[str] = None):
    """
    Decorator to test function with all user types

    Args:
        types: Specific user types to test (default: all)
        exclude: User types to exclude from testing

    Usage:
        @test_all_user_types()
        def test_user_action(self, user_type, user_data):
            # Test runs for each user type
            pass
    """
    default_types = ['admin', 'user', 'guest', 'premium']
    types = types or default_types

    if exclude:
        types = [t for t in types if t not in exclude]

    user_configs = {
        'admin': lambda: user().as_admin().build(),
        'user': lambda: user().build(),
        'guest': lambda: user().as_guest().build(),
        'premium': lambda: user().as_premium().build()
    }

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            results = []
            for user_type in types:
                user_data = user_configs[user_type]()

                # Add user_type and user_data to test arguments
                test_kwargs = kwargs.copy()
                test_kwargs.update({
                    'user_type': user_type,
                    'user_data': user_data
                })

                try:
                    result = test_func(*args, **test_kwargs)
                    results.append((user_type, True, result))
                except Exception as e:
                    results.append((user_type, False, str(e)))

            # Check if any tests failed
            failed_tests = [(user_type, error) for user_type, success, error in results if not success]
            if failed_tests:
                failure_msg = "; ".join([f"{user_type}: {error}" for user_type, error in failed_tests])
                pytest.fail(f"Test failed for user types: {failure_msg}")

            return results

        return wrapper

    return decorator


def test_all_games(games: List[str] = None, exclude: List[str] = None):
    """
    Decorator to test function with all game types

    Usage:
        @test_all_games(['puzzle', 'action'])
        def test_game_feature(self, game_type, game_data):
            pass
    """
    default_games = ['puzzle', 'action', 'strategy', 'casual']
    games = games or default_games

    if exclude:
        games = [g for g in games if g not in exclude]

    game_configs = {
        'puzzle': lambda: game().as_puzzle().build(),
        'action': lambda: game().as_action().build(),
        'strategy': lambda: game().with_category('strategy').with_difficulty('hard').build(),
        'casual': lambda: game().with_category('casual').with_difficulty('easy').free().build()
    }

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            results = []
            for game_type in games:
                game_data = game_configs[game_type]()

                test_kwargs = kwargs.copy()
                test_kwargs.update({
                    'game_type': game_type,
                    'game_data': game_data
                })

                try:
                    result = test_func(*args, **test_kwargs)
                    results.append((game_type, True, result))
                except Exception as e:
                    results.append((game_type, False, str(e)))

            failed_tests = [(game_type, error) for game_type, success, error in results if not success]
            if failed_tests:
                failure_msg = "; ".join([f"{game_type}: {error}" for game_type, error in failed_tests])
                pytest.fail(f"Test failed for game types: {failure_msg}")

            return results

        return wrapper

    return decorator


def test_all_auth_scenarios(scenarios: List[str] = None):
    """
    Decorator to test function with all authentication scenarios

    Usage:
        @test_all_auth_scenarios(['valid', 'expired', 'invalid'])
        def test_protected_endpoint(self, auth_scenario, auth_mocker):
            pass
    """
    default_scenarios = ['valid', 'expired', 'invalid', 'missing']
    scenarios = scenarios or default_scenarios

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            results = []

            for scenario in scenarios:
                auth_mocker = AuthenticationMocker()

                if scenario == 'valid':
                    auth_mocker.mock_jwt_token("test_user_123", "user")
                elif scenario == 'expired':
                    # Mock expired token by setting past expiration
                    from datetime import datetime, timezone
                    auth_mocker.mock_jwt_token("test_user_123", "user", exp=datetime.now(timezone.utc).replace(year=2020).timestamp())
                elif scenario == 'invalid':
                    # Mock invalid token by making jwt functions raise exceptions
                    auth_mocker.mock_no_authentication()
                elif scenario == 'missing':
                    # No authentication setup - should fail
                    pass

                test_kwargs = kwargs.copy()
                test_kwargs.update({
                    'auth_scenario': scenario,
                    'auth_mocker': auth_mocker
                })

                try:
                    result = test_func(*args, **test_kwargs)
                    results.append((scenario, True, result))
                except Exception as e:
                    results.append((scenario, False, str(e)))
                finally:
                    auth_mocker.stop_mocking()

            return results

        return wrapper

    return decorator


def test_with_permissions(permissions: List[List[str]] = None):
    """
    Decorator to test function with different permission sets

    Usage:
        @test_with_permissions([['read'], ['read', 'write'], ['read', 'write', 'admin']])
        def test_permission_based_action(self, permissions, auth_mocker):
            pass
    """
    default_permissions = [
        ['read'],
        ['read', 'write'],
        ['read', 'write', 'admin'],
        []  # No permissions
    ]
    permissions = permissions or default_permissions

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            results = []

            for perm_set in permissions:
                auth_mocker = AuthenticationMocker()

                # Determine role based on permissions
                if 'admin' in perm_set:
                    role = 'admin'
                elif 'write' in perm_set:
                    role = 'user'
                elif 'read' in perm_set:
                    role = 'user'
                else:
                    role = 'guest'

                auth_mocker.mock_jwt_token("test_user_123", role, permissions=perm_set)

                test_kwargs = kwargs.copy()
                test_kwargs.update({
                    'permissions': perm_set,
                    'auth_mocker': auth_mocker
                })

                try:
                    result = test_func(*args, **test_kwargs)
                    results.append((str(perm_set), True, result))
                except Exception as e:
                    results.append((str(perm_set), False, str(e)))
                finally:
                    auth_mocker.stop_mocking()

            return results

        return wrapper

    return decorator


def test_performance_scenarios(scenarios: List[Dict[str, Any]] = None):
    """
    Decorator to test function with different performance scenarios

    Usage:
        @test_performance_scenarios([
            {'name': 'small_load', 'iterations': 10, 'max_time_ms': 100},
            {'name': 'large_load', 'iterations': 1000, 'max_time_ms': 5000}
        ])
        def test_performance(self, scenario, iterations, max_time_ms):
            pass
    """
    default_scenarios = [
        {'name': 'small_load', 'iterations': 10, 'max_time_ms': 100},
        {'name': 'medium_load', 'iterations': 100, 'max_time_ms': 1000},
        {'name': 'large_load', 'iterations': 1000, 'max_time_ms': 5000}
    ]
    scenarios = scenarios or default_scenarios

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            results = []

            for scenario in scenarios:
                test_kwargs = kwargs.copy()
                test_kwargs.update({
                    'scenario': scenario,
                    'iterations': scenario['iterations'],
                    'max_time_ms': scenario['max_time_ms']
                })

                try:
                    result = test_func(*args, **test_kwargs)
                    results.append((scenario['name'], True, result))
                except Exception as e:
                    results.append((scenario['name'], False, str(e)))

            failed_tests = [(name, error) for name, success, error in results if not success]
            if failed_tests:
                failure_msg = "; ".join([f"{name}: {error}" for name, error in failed_tests])
                pytest.fail(f"Performance test failed for scenarios: {failure_msg}")

            return results

        return wrapper

    return decorator


# Pytest Integration Decorators

def parametrize_users(user_types: List[str] = None):
    """
    Pytest parametrize decorator for user types

    Usage:
        @parametrize_users(['admin', 'user'])
        def test_user_action(self, user_type, user_data):
            pass
    """
    default_types = ['admin', 'user', 'guest', 'premium']
    user_types = user_types or default_types

    user_configs = {
        'admin': user().as_admin().build(),
        'user': user().build(),
        'guest': user().as_guest().build(),
        'premium': user().as_premium().build()
    }

    params = [(user_type, user_configs[user_type]) for user_type in user_types]

    return pytest.mark.parametrize("user_type,user_data", params)


def parametrize_games(game_types: List[str] = None):
    """
    Pytest parametrize decorator for game types

    Usage:
        @parametrize_games(['puzzle', 'action'])
        def test_game_feature(self, game_type, game_data):
            pass
    """
    default_types = ['puzzle', 'action', 'strategy', 'casual']
    game_types = game_types or default_types

    game_configs = {
        'puzzle': game().as_puzzle().build(),
        'action': game().as_action().build(),
        'strategy': game().with_category('strategy').build(),
        'casual': game().with_category('casual').free().build()
    }

    params = [(game_type, game_configs[game_type]) for game_type in game_types]

    return pytest.mark.parametrize("game_type,game_data", params)


def parametrize_auth(scenarios: List[str] = None):
    """
    Pytest parametrize decorator for auth scenarios

    Usage:
        @parametrize_auth(['valid', 'invalid'])
        def test_auth_endpoint(self, auth_scenario):
            pass
    """
    default_scenarios = ['valid', 'expired', 'invalid', 'missing']
    scenarios = scenarios or default_scenarios

    return pytest.mark.parametrize("auth_scenario", scenarios)


# Advanced Composite Decorators

def test_user_game_combinations(user_types: List[str] = None, game_types: List[str] = None):
    """
    Decorator to test all combinations of users and games

    Usage:
        @test_user_game_combinations(['admin', 'user'], ['puzzle', 'action'])
        def test_user_plays_game(self, user_type, user_data, game_type, game_data):
            pass
    """
    default_user_types = ['admin', 'user', 'guest']
    default_game_types = ['puzzle', 'action', 'casual']

    user_types = user_types or default_user_types
    game_types = game_types or default_game_types

    user_configs = {
        'admin': lambda: user().as_admin().build(),
        'user': lambda: user().build(),
        'guest': lambda: user().as_guest().build()
    }

    game_configs = {
        'puzzle': lambda: game().as_puzzle().build(),
        'action': lambda: game().as_action().build(),
        'casual': lambda: game().with_category('casual').free().build()
    }

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            results = []

            for user_type in user_types:
                for game_type in game_types:
                    user_data = user_configs[user_type]()
                    game_data = game_configs[game_type]()

                    test_kwargs = kwargs.copy()
                    test_kwargs.update({
                        'user_type': user_type,
                        'user_data': user_data,
                        'game_type': game_type,
                        'game_data': game_data
                    })

                    combination_name = f"{user_type}+{game_type}"

                    try:
                        result = test_func(*args, **test_kwargs)
                        results.append((combination_name, True, result))
                    except Exception as e:
                        results.append((combination_name, False, str(e)))

            failed_tests = [(combo, error) for combo, success, error in results if not success]
            if failed_tests:
                failure_msg = "; ".join([f"{combo}: {error}" for combo, error in failed_tests])
                pytest.fail(f"Test failed for combinations: {failure_msg}")

            return results

        return wrapper

    return decorator


def test_all_crud_operations(operations: List[str] = None):
    """
    Decorator to test all CRUD operations

    Usage:
        @test_all_crud_operations(['create', 'read', 'update', 'delete'])
        def test_crud_operation(self, operation):
            if operation == 'create':
                # test create
            elif operation == 'read':
                # test read
            # etc.
    """
    default_operations = ['create', 'read', 'update', 'delete']
    operations = operations or default_operations

    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            results = []

            for operation in operations:
                test_kwargs = kwargs.copy()
                test_kwargs.update({'operation': operation})

                try:
                    result = test_func(*args, **test_kwargs)
                    results.append((operation, True, result))
                except Exception as e:
                    results.append((operation, False, str(e)))

            failed_tests = [(op, error) for op, success, error in results if not success]
            if failed_tests:
                failure_msg = "; ".join([f"{op}: {error}" for op, error in failed_tests])
                pytest.fail(f"CRUD test failed for operations: {failure_msg}")

            return results

        return wrapper

    return decorator


# Data-driven Test Decorators

def test_with_data_scenarios(scenarios: List[Dict[str, Any]]):
    """
    Decorator for data-driven testing with custom scenarios

    Usage:
        @test_with_data_scenarios([
            {'name': 'valid_email', 'email': 'test@example.com', 'should_pass': True},
            {'name': 'invalid_email', 'email': 'invalid', 'should_pass': False}
        ])
        def test_email_validation(self, scenario, email, should_pass):
            pass
    """
    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            results = []

            for scenario in scenarios:
                test_kwargs = kwargs.copy()
                test_kwargs.update(scenario)

                scenario_name = scenario.get('name', f"scenario_{scenarios.index(scenario)}")

                try:
                    result = test_func(*args, **test_kwargs)
                    results.append((scenario_name, True, result))
                except Exception as e:
                    results.append((scenario_name, False, str(e)))

            return results

        return wrapper

    return decorator


# Conditional Test Decorators

def test_if_user_has_permission(required_permission: str):
    """
    Decorator to conditionally run test based on user permissions

    Usage:
        @test_if_user_has_permission('admin')
        def test_admin_only_feature(self):
            pass
    """
    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            # This would typically check current user permissions
            # For testing, we'll create scenarios with and without permission

            results = []
            scenarios = [
                {'has_permission': True, 'permissions': ['read', 'write', required_permission]},
                {'has_permission': False, 'permissions': ['read']}
            ]

            for scenario in scenarios:
                auth_mocker = AuthenticationMocker()
                role = 'admin' if scenario['has_permission'] else 'user'
                auth_mocker.mock_jwt_token("test_user_123", role, permissions=scenario['permissions'])

                test_kwargs = kwargs.copy()
                test_kwargs.update({
                    'has_permission': scenario['has_permission'],
                    'auth_mocker': auth_mocker
                })

                scenario_name = f"with_permission_{scenario['has_permission']}"

                try:
                    result = test_func(*args, **test_kwargs)
                    results.append((scenario_name, True, result))
                except Exception as e:
                    results.append((scenario_name, False, str(e)))
                finally:
                    auth_mocker.stop_mocking()

            return results

        return wrapper

    return decorator


# Utility Decorators

def repeat_test(times: int = 3):
    """
    Decorator to repeat test multiple times (useful for flaky tests)

    Usage:
        @repeat_test(5)
        def test_potentially_flaky_operation(self):
            pass
    """
    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            failures = []

            for i in range(times):
                try:
                    result = test_func(*args, **kwargs)
                    return result  # Success on first try
                except Exception as e:
                    failures.append(f"Attempt {i+1}: {str(e)}")

            # All attempts failed
            failure_msg = "; ".join(failures)
            pytest.fail(f"Test failed {times} times: {failure_msg}")

        return wrapper

    return decorator


def timeout_test(seconds: int = 10):
    """
    Decorator to add timeout to test execution

    Usage:
        @timeout_test(30)
        def test_long_running_operation(self):
            pass
    """
    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            import signal

            def timeout_handler(signum, frame):
                pytest.fail(f"Test timed out after {seconds} seconds")

            # Set timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)

            try:
                result = test_func(*args, **kwargs)
                return result
            finally:
                signal.alarm(0)  # Cancel timeout

        return wrapper

    return decorator


# Composite Decorator Factory

def create_comprehensive_test_decorator(
    user_types: List[str] = None,
    game_types: List[str] = None,
    auth_scenarios: List[str] = None,
    performance_scenarios: List[Dict[str, Any]] = None
):
    """
    Factory to create comprehensive test decorators combining multiple aspects

    Usage:
        comprehensive_test = create_comprehensive_test_decorator(
            user_types=['admin', 'user'],
            game_types=['puzzle'],
            auth_scenarios=['valid']
        )

        @comprehensive_test
        def test_comprehensive_feature(self, user_type, user_data, game_type, game_data, auth_scenario, auth_mocker):
            pass
    """
    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            results = []

            # Get default values
            users = user_types or ['user']
            games = game_types or ['puzzle']
            auth = auth_scenarios or ['valid']
            perf = performance_scenarios or []

            user_configs = {
                'admin': lambda: user().as_admin().build(),
                'user': lambda: user().build(),
                'guest': lambda: user().as_guest().build()
            }

            game_configs = {
                'puzzle': lambda: game().as_puzzle().build(),
                'action': lambda: game().as_action().build()
            }

            for user_type in users:
                for game_type in games:
                    for auth_scenario in auth:
                        # Setup user data
                        user_data = user_configs.get(user_type, lambda: user().build())()
                        game_data = game_configs.get(game_type, lambda: game().build())()

                        # Setup auth
                        auth_mocker = AuthenticationMocker()
                        if auth_scenario == 'valid':
                            auth_mocker.mock_jwt_token("test_user_123", user_type)

                        test_kwargs = kwargs.copy()
                        test_kwargs.update({
                            'user_type': user_type,
                            'user_data': user_data,
                            'game_type': game_type,
                            'game_data': game_data,
                            'auth_scenario': auth_scenario,
                            'auth_mocker': auth_mocker
                        })

                        test_name = f"{user_type}+{game_type}+{auth_scenario}"

                        try:
                            result = test_func(*args, **test_kwargs)
                            results.append((test_name, True, result))
                        except Exception as e:
                            results.append((test_name, False, str(e)))
                        finally:
                            auth_mocker.stop_mocking()

            failed_tests = [(name, error) for name, success, error in results if not success]
            if failed_tests:
                failure_msg = "; ".join([f"{name}: {error}" for name, error in failed_tests])
                pytest.fail(f"Comprehensive test failed: {failure_msg}")

            return results

        return wrapper

    return decorator


# Usage Examples in docstring:
"""
# Basic usage examples:

@test_all_user_types(['admin', 'user'])
def test_user_feature(self, user_type, user_data):
    assert user_data['email'] is not None
    if user_type == 'admin':
        assert 'admin' in user_data.get('role', '')

@test_all_games(['puzzle', 'action'])
def test_game_feature(self, game_type, game_data):
    assert game_data['title'] is not None
    if game_type == 'puzzle':
        assert game_data['category'] == 'puzzle'

@test_all_auth_scenarios(['valid', 'invalid'])
def test_protected_endpoint(self, auth_scenario, auth_mocker):
    # Test logic that depends on authentication state
    pass

@test_with_permissions([['read'], ['read', 'write'], ['admin']])
def test_permission_based_feature(self, permissions, auth_mocker):
    # Test logic that depends on user permissions
    pass

@test_user_game_combinations(['admin', 'user'], ['puzzle'])
def test_user_plays_game(self, user_type, user_data, game_type, game_data):
    # Test all combinations of users and games
    pass

# Advanced usage with pytest integration:

@parametrize_users(['admin', 'user'])
def test_with_pytest_parametrize(self, user_type, user_data):
    # This integrates with pytest.mark.parametrize
    pass

# Data-driven testing:

@test_with_data_scenarios([
    {'name': 'valid_email', 'email': 'test@example.com', 'expected': True},
    {'name': 'invalid_email', 'email': 'invalid', 'expected': False}
])
def test_email_validation(self, scenario, email, expected):
    # Test with different data scenarios
    pass

# Comprehensive testing:

comprehensive = create_comprehensive_test_decorator(
    user_types=['admin', 'user'],
    game_types=['puzzle', 'action']
)

@comprehensive
def test_comprehensive_feature(self, user_type, user_data, game_type, game_data, auth_scenario, auth_mocker):
    # Test all combinations automatically
    pass
"""