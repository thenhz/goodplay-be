"""
Smart Fixture System for GoodPlay - GOO-34

Intelligent fixture management with automatic dependency resolution,
caching, performance monitoring, and resource optimization.

Usage Examples:

    # Basic smart fixture
    @smart_fixture('user_with_preferences')
    def user_with_preferences():
        return UserFactory.build()

    # Fixture with dependencies
    @smart_fixture('gaming_session', dependencies=['user', 'game'])
    def gaming_session(user, game):
        return GameSessionFactory.build(user_id=user['_id'], game_id=game['_id'])

    # Factory-based fixture
    @factory_fixture(UserFactory, trait='admin')
    def admin_user():
        pass

    # Preset fixture combination
    @preset_fixture('basic_user_setup')
    def basic_user_setup():
        return preset_manager.create_preset('basic_user_setup')

    # Lazy loading fixture
    @lazy_fixture('expensive_computation')
    def expensive_computation():
        return perform_expensive_operation()

Performance Features:
- Automatic dependency resolution
- Intelligent caching (function/class/session/module scopes)
- Memory usage monitoring and optimization
- Performance profiling and alerts
- Automatic cleanup and resource management
- Rollback capabilities for fixture state

Architecture:
- SmartFixtureManager: Core intelligent fixture management
- DependencyGraph: Automatic dependency resolution
- SmartFixtureCache: Multi-scope intelligent caching
- PerformanceMonitor: Real-time performance tracking
- CleanupManager: Automatic resource cleanup and rollback
"""

# Core system exports
from .smart_manager import (
    SmartFixtureManager,
    FixtureScope,
    FixtureStatus,
    smart_fixture_manager,
    FixtureMetadata,
    PerformanceMetrics,
    DependencyGraph,
    SmartFixtureCache
)

# Decorators and convenience functions
from .decorators import (
    smart_fixture,
    factory_fixture,
    preset_fixture,
    lazy_fixture,
    performance_monitor as performance_monitor_decorator,
    smart,  # Alias
    factory,  # Alias
    preset,  # Alias
    lazy  # Alias
)

# Preset system
from .presets import (
    FixturePresetManager,
    preset_manager,
    # Preset fixtures
    basic_user_setup,
    gaming_session_setup,
    social_network_setup,
    financial_setup,
    admin_setup,
    test_data_ecosystem
)

# Performance monitoring
from .performance import (
    PerformanceThresholds,
    FixturePerformanceData,
    MemoryTracker,
    PerformanceProfiler,
    PerformanceOptimizer,
    SmartFixturePerformanceMonitor,
    performance_monitor
)

# Cleanup and resource management
from .cleanup import (
    CleanupStrategy,
    RollbackStrategy,
    CleanupAction,
    RollbackSnapshot,
    ResourceTracker,
    SmartCleanupManager,
    cleanup_manager
)

# Utilities and helpers
from .utils import (
    auto_detect_dependencies,
    validate_fixture_function,
    migrate_legacy_fixture,
    create_fixture_factory,
    benchmark_fixture,
    FixtureDebugger,
    fixture_debugger,
    smart_fixture_from_factory,
    reset_smart_fixtures,
    get_system_health,
    generate_fixture_documentation
)

# Version info
__version__ = '1.0.0'
__author__ = 'GoodPlay Team'
__description__ = 'Smart Fixture System with intelligent dependency resolution and caching'

# Public API
__all__ = [
    # Core Classes
    'SmartFixtureManager',
    'FixtureScope',
    'FixtureStatus',
    'FixtureMetadata',
    'PerformanceMetrics',
    'DependencyGraph',
    'SmartFixtureCache',

    # Manager Instances
    'smart_fixture_manager',
    'preset_manager',
    'performance_monitor',
    'cleanup_manager',
    'fixture_debugger',

    # Decorators
    'smart_fixture',
    'factory_fixture',
    'preset_fixture',
    'lazy_fixture',
    'performance_monitor_decorator',
    'smart',
    'factory',
    'preset',
    'lazy',

    # Preset Fixtures
    'basic_user_setup',
    'gaming_session_setup',
    'social_network_setup',
    'financial_setup',
    'admin_setup',
    'test_data_ecosystem',

    # Performance Classes
    'PerformanceThresholds',
    'FixturePerformanceData',
    'MemoryTracker',
    'PerformanceProfiler',
    'PerformanceOptimizer',
    'SmartFixturePerformanceMonitor',

    # Cleanup Classes
    'CleanupStrategy',
    'RollbackStrategy',
    'CleanupAction',
    'RollbackSnapshot',
    'ResourceTracker',
    'SmartCleanupManager',

    # Utility Functions
    'auto_detect_dependencies',
    'validate_fixture_function',
    'migrate_legacy_fixture',
    'create_fixture_factory',
    'benchmark_fixture',
    'smart_fixture_from_factory',
    'reset_smart_fixtures',
    'get_system_health',
    'generate_fixture_documentation',

    # Enums
    'FixtureScope',
    'FixtureStatus',
    'CleanupStrategy',
    'RollbackStrategy'
]


def initialize_smart_fixtures(
    max_memory_mb: int = 100,
    cache_hit_threshold: float = 0.8,
    max_creation_time_ms: float = 50.0,
    enable_performance_monitoring: bool = True,
    enable_automatic_cleanup: bool = True
):
    """
    Initialize the Smart Fixture System with custom configuration

    Args:
        max_memory_mb: Maximum memory usage threshold
        cache_hit_threshold: Minimum cache hit ratio threshold
        max_creation_time_ms: Maximum fixture creation time threshold
        enable_performance_monitoring: Enable performance tracking
        enable_automatic_cleanup: Enable automatic resource cleanup
    """
    # Configure performance thresholds
    thresholds = PerformanceThresholds(
        max_memory_usage_mb=max_memory_mb,
        min_cache_hit_ratio=cache_hit_threshold,
        max_creation_time_ms=max_creation_time_ms
    )

    # Update performance monitor
    performance_monitor.thresholds = thresholds

    # Configure cleanup manager
    cleanup_manager.memory_pressure_threshold_mb = max_memory_mb * 0.8  # 80% of max
    cleanup_manager.automatic_gc_enabled = enable_automatic_cleanup

    # Set smart fixture manager configuration
    smart_fixture_manager.max_creation_time_ms = max_creation_time_ms

    print(f"✅ Smart Fixture System initialized:")
    print(f"   - Max memory: {max_memory_mb}MB")
    print(f"   - Cache hit threshold: {cache_hit_threshold:.1%}")
    print(f"   - Max creation time: {max_creation_time_ms}ms")
    print(f"   - Performance monitoring: {'enabled' if enable_performance_monitoring else 'disabled'}")
    print(f"   - Automatic cleanup: {'enabled' if enable_automatic_cleanup else 'disabled'}")


def register_factory_boy_integration():
    """
    Register existing Factory-Boy factories with the smart fixture system
    """
    try:
        from tests.factories.user_factory import UserFactory, UserPreferencesFactory
        from tests.factories.game_factory import GameFactory, GameSessionFactory

        # Register factories
        smart_fixture_manager.register_factory('user', UserFactory)
        smart_fixture_manager.register_factory('user_preferences', UserPreferencesFactory)
        smart_fixture_manager.register_factory('game', GameFactory)
        smart_fixture_manager.register_factory('game_session', GameSessionFactory)

        print("✅ Factory-Boy integration registered")

        try:
            from tests.factories.social_factory import AchievementFactory
            from tests.factories.financial_factory import WalletFactory, TransactionFactory
            from tests.factories.onlus_factory import ONLUSFactory

            smart_fixture_manager.register_factory('achievement', AchievementFactory)
            smart_fixture_manager.register_factory('wallet', WalletFactory)
            smart_fixture_manager.register_factory('transaction', TransactionFactory)
            smart_fixture_manager.register_factory('onlus', ONLUSFactory)

            print("✅ Extended Factory-Boy factories registered")

        except ImportError:
            print("⚠️  Some Factory-Boy factories not available yet")

    except ImportError as e:
        print(f"⚠️  Factory-Boy integration not available: {e}")


def get_quick_start_guide() -> str:
    """Get a quick start guide for the Smart Fixture System"""
    return """
# Smart Fixture System - Quick Start Guide

## 1. Basic Usage

```python
from tests.fixtures import smart_fixture, FixtureScope

@smart_fixture('my_user', scope=FixtureScope.FUNCTION)
def my_user():
    return {'name': 'Test User', 'email': 'test@example.com'}
```

## 2. Factory Integration

```python
from tests.fixtures import factory_fixture
from tests.factories.user_factory import UserFactory

@factory_fixture(UserFactory, trait='admin')
def admin_user():
    pass  # Returns admin user from UserFactory
```

## 3. Preset Combinations

```python
from tests.fixtures import preset_fixture

@preset_fixture('gaming_session_setup')
def gaming_setup():
    # Automatically creates: user + game + session
    return preset_manager.create_preset('gaming_session_setup')
```

## 4. Performance Monitoring

```python
from tests.fixtures import performance_monitor

# Get system performance report
report = performance_monitor.get_performance_report()
print(f"Cache hit ratio: {report['cache_hit_ratio']:.1%}")
```

## 5. System Health Check

```python
from tests.fixtures import get_system_health

health = get_system_health()
print(f"System status: {health['health_status']}")
```

## Available Presets

- `basic_user_setup`: User with preferences
- `gaming_session_setup`: User + Game + Active session
- `social_network_setup`: Multiple users with relationships
- `financial_setup`: User + Wallet + Transaction history
- `admin_setup`: Admin user with full permissions

For more examples and advanced usage, see the documentation.
"""


# Auto-initialize with default settings when imported
try:
    register_factory_boy_integration()
except Exception as e:
    print(f"Note: Factory-Boy auto-registration skipped: {e}")

# Export quick start for easy access
quick_start = get_quick_start_guide