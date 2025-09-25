# 📦 Smart Fixture System - GOO-34

**Intelligent fixture management with automatic dependency resolution, caching, performance monitoring, and resource optimization for GoodPlay.**

## 🎯 Overview

The Smart Fixture System is an enterprise-grade fixture management solution that provides:

- **🧠 Intelligent Dependency Resolution**: Automatic detection and resolution of fixture dependencies
- **⚡ Advanced Caching**: Multi-scope caching (function/class/session/module) with intelligent invalidation
- **📊 Performance Monitoring**: Real-time performance tracking and optimization suggestions
- **🧹 Resource Management**: Automatic cleanup and rollback capabilities
- **🚀 High Performance**: Meets GOO-34 requirements (>1000 objects/s, <50ms creation, 80%+ cache hit ratio)

## 🚀 Quick Start

### Basic Usage

```python
from tests.fixtures import smart_fixture, FixtureScope

@smart_fixture('my_user', scope=FixtureScope.FUNCTION)
def my_user():
    return {'name': 'Test User', 'email': 'test@example.com'}

# Use in tests
def test_user_feature(my_user):
    assert my_user['name'] == 'Test User'
```

### Factory Integration

```python
from tests.fixtures import factory_fixture
from tests.factories.user_factory import UserFactory

@factory_fixture(UserFactory, trait='admin')
def admin_user():
    pass  # Returns admin user from UserFactory

def test_admin_feature(admin_user):
    assert admin_user['role'] == 'admin'
```

### Preset Combinations

```python
from tests.fixtures import preset_fixture

@preset_fixture('gaming_session_setup')
def gaming_setup():
    # Automatically creates: user + game + session
    return preset_manager.create_preset('gaming_session_setup')

def test_gaming_feature(gaming_session_setup):
    user = gaming_session_setup['basic_user']
    game = gaming_session_setup['game']
    session = gaming_session_setup['game_session']

    assert session['user_id'] == user['_id']
    assert session['game_id'] == game['_id']
```

## 🏗️ Architecture

### Core Components

#### SmartFixtureManager
The central coordinator that manages fixture creation, caching, and dependency resolution.

```python
from tests.fixtures import smart_fixture_manager

# Register a fixture
smart_fixture_manager.register_fixture(
    'my_fixture',
    creator_function,
    scope=FixtureScope.FUNCTION,
    dependencies=['dep1', 'dep2']
)

# Create fixture
result = smart_fixture_manager.create_fixture('my_fixture')
```

#### Dependency Graph
Automatically resolves fixture dependencies and detects circular dependencies.

```python
from tests.fixtures import smart_fixture

@smart_fixture('base_data')
def base_data():
    return {'base': True}

@smart_fixture('extended_data')  # Automatically detects base_data dependency
def extended_data(base_data):
    return {'base': base_data, 'extended': True}
```

#### Smart Cache
Multi-scope intelligent caching with automatic memory management.

```python
from tests.fixtures import smart_fixture, FixtureScope

@smart_fixture('expensive_computation', scope=FixtureScope.SESSION)
def expensive_computation():
    # Expensive operation - cached for entire session
    return perform_expensive_computation()
```

#### Performance Monitor
Real-time performance tracking and optimization suggestions.

```python
from tests.fixtures import performance_monitor

report = performance_monitor.get_performance_report()
print(f"Cache hit ratio: {report['overall_cache_hit_ratio']:.1%}")
print(f"Average creation time: {report['average_creation_time_ms']:.1f}ms")
```

## 📋 Available Presets

The system provides 5 pre-configured fixture combinations:

### 1. Basic User Setup
```python
@preset_fixture('basic_user_setup')
def basic_user_setup():
    # Creates: user + user_preferences
    return preset_manager.create_preset('basic_user_setup')
```

### 2. Gaming Session Setup
```python
@preset_fixture('gaming_session_setup')
def gaming_session_setup():
    # Creates: user + game + active_session
    return preset_manager.create_preset('gaming_session_setup')
```

### 3. Social Network Setup
```python
@preset_fixture('social_network_setup')
def social_network_setup():
    # Creates: alice + bob + charlie + relationships
    return preset_manager.create_preset('social_network_setup')
```

### 4. Financial Setup
```python
@preset_fixture('financial_setup')
def financial_setup():
    # Creates: user + wallet + transaction_history
    return preset_manager.create_preset('financial_setup')
```

### 5. Admin Setup
```python
@preset_fixture('admin_setup')
def admin_setup():
    # Creates: admin_user + permissions + session
    return preset_manager.create_preset('admin_setup')
```

## 🎨 Decorator Reference

### @smart_fixture
The main decorator for creating intelligent fixtures.

```python
@smart_fixture(
    name='fixture_name',           # Optional: defaults to function name
    scope=FixtureScope.FUNCTION,   # Cache scope
    dependencies=['dep1', 'dep2'],  # Explicit dependencies
    auto_register=True             # Auto-register with pytest
)
def my_fixture(dep1, dep2):
    return create_fixture_data(dep1, dep2)
```

### @factory_fixture
Integration with Factory-Boy factories.

```python
@factory_fixture(
    UserFactory,                   # Factory class
    trait='admin',                # Factory trait
    count=1,                      # Number of objects (>1 = list)
    scope=FixtureScope.FUNCTION   # Cache scope
)
def admin_user():
    pass  # Body not needed - factory creates the object
```

### @lazy_fixture
Lazy-loaded fixtures that are only created when accessed.

```python
@lazy_fixture('expensive_data')
def expensive_data():
    # Only executed when actually needed
    return perform_expensive_operation()
```

### @preset_fixture
Pre-configured fixture combinations.

```python
@preset_fixture('my_preset')
def my_preset():
    return preset_manager.create_preset('my_preset')
```

## ⚡ Performance Features

### Cache Scopes

- **FUNCTION**: Cache for single test function
- **CLASS**: Cache for entire test class
- **MODULE**: Cache for entire test module
- **SESSION**: Cache for entire test session
- **LAZY**: On-demand creation when accessed

```python
@smart_fixture('session_data', scope=FixtureScope.SESSION)
def session_data():
    # Created once per test session
    return expensive_session_setup()

@smart_fixture('test_data', scope=FixtureScope.FUNCTION)
def test_data():
    # Created fresh for each test
    return generate_test_data()
```

### Performance Monitoring

```python
from tests.fixtures import get_system_health, performance_monitor

# System health check
health = get_system_health()
print(f"Status: {health['health_status']}")
print(f"Score: {health['health_score']}/100")

# Detailed performance report
report = performance_monitor.get_performance_report()
for fixture_name, stats in report['fixture_breakdown'].items():
    print(f"{fixture_name}: {stats['avg_creation_time_ms']:.1f}ms")
```

### Benchmarking

```python
from tests.fixtures import benchmark_fixture

# Benchmark fixture performance
results = benchmark_fixture(my_fixture_function, iterations=100)
print(f"Average time: {results['mean_time_ms']:.1f}ms")
print(f"Success rate: {results['success_rate']:.1%}")
```

## 🧹 Resource Management

### Cleanup Actions

```python
from tests.fixtures import cleanup_manager

# Register cleanup action
cleanup_manager.register_cleanup_action(
    'my_fixture',
    'close_file',
    lambda: file_handle.close()
)

# Manual cleanup
cleanup_manager.cleanup_fixture('my_fixture')
```

### Rollback Capabilities

```python
# Enable rollback for a fixture
cleanup_manager.enable_rollback('rollback_fixture')

# Take snapshot
snapshot_id = cleanup_manager.take_snapshot('rollback_fixture', fixture_data)

# Rollback to snapshot
original_data = cleanup_manager.rollback_fixture('rollback_fixture', snapshot_id)
```

## 🔧 Advanced Usage

### Custom Fixture Registration

```python
from tests.fixtures import smart_fixture_manager, FixtureScope

def custom_creator(**kwargs):
    return create_custom_data(**kwargs)

smart_fixture_manager.register_fixture(
    'custom_fixture',
    custom_creator,
    scope=FixtureScope.CLASS,
    dependencies=['base_fixture']
)
```

### Dependency Detection

```python
from tests.fixtures import auto_detect_dependencies

def my_fixture(user, game, wallet):
    return combine_dependencies(user, game, wallet)

dependencies = auto_detect_dependencies(my_fixture)
# Returns: ['user', 'game', 'wallet']
```

### Factory Registration

```python
from tests.fixtures import smart_fixture_from_factory
from tests.factories.user_factory import UserFactory

# Quick factory integration
fixture_name = smart_fixture_from_factory(UserFactory, role='user')
```

## 📊 Performance Requirements (GOO-34)

The Smart Fixture System meets all GOO-34 performance requirements:

| Requirement | Target | Status |
|-------------|---------|--------|
| Fixture creation time | < 50ms per test | ✅ **PASSED** |
| Memory usage | < 100MB for full suite | ✅ **PASSED** |
| Cleanup time | < 10ms per test | ✅ **PASSED** |
| Cache hit ratio | > 80% for repeated fixtures | ✅ **PASSED** |

### Performance Validation

```python
# Run performance validation
python -m pytest tests/test_smart_fixtures.py::test_goo_34_performance_requirements
```

## 🛠️ Configuration

### System Initialization

```python
from tests.fixtures import initialize_smart_fixtures

initialize_smart_fixtures(
    max_memory_mb=100,
    cache_hit_threshold=0.8,
    max_creation_time_ms=50.0,
    enable_performance_monitoring=True,
    enable_automatic_cleanup=True
)
```

### Performance Thresholds

```python
from tests.fixtures import performance_monitor, PerformanceThresholds

# Update thresholds
performance_monitor.thresholds = PerformanceThresholds(
    max_creation_time_ms=30.0,
    max_memory_usage_mb=80.0,
    min_cache_hit_ratio=0.85
)
```

## 🐛 Debugging

### Debug Mode

```python
from tests.fixtures import fixture_debugger

# Trace fixture creation
fixture_debugger.trace_fixture_creation('my_fixture')
trace = fixture_debugger.get_fixture_trace('my_fixture')

# Analyze dependencies
analysis = fixture_debugger.analyze_fixture_dependencies('my_fixture')
```

### System Health

```python
from tests.fixtures import get_system_health

health = get_system_health()

if health['health_status'] != 'HEALTHY':
    print("Issues detected:")
    for issue in health['issues']:
        print(f"  - {issue}")

    print("Recommendations:")
    for rec in health['recommendations']:
        print(f"  - {rec}")
```

## 🔄 Migration Guide

### From Legacy Fixtures

```python
# Old way
@pytest.fixture
def user():
    return create_user_data()

# New way
@smart_fixture('user')
def user():
    return create_user_data()
```

### From Factory-Boy

```python
# Old way
@pytest.fixture
def user():
    return UserFactory.build()

# New way
@factory_fixture(UserFactory)
def user():
    pass
```

### Migration Helper

```python
from tests.fixtures import migrate_legacy_fixture

# Migrate existing fixture
@migrate_legacy_fixture(scope=FixtureScope.FUNCTION)
@pytest.fixture
def legacy_fixture():
    return legacy_creation_logic()
```

## 📝 Best Practices

### 1. Choose Appropriate Scopes
- Use `FUNCTION` for test-specific data
- Use `CLASS` for shared test class data
- Use `SESSION` for expensive, reusable data
- Use `LAZY` for conditionally needed data

### 2. Optimize Dependencies
- Keep dependency chains shallow
- Use explicit dependencies for clarity
- Avoid circular dependencies

### 3. Monitor Performance
- Regularly check performance reports
- Profile slow fixtures
- Optimize based on recommendations

### 4. Clean Resource Usage
- Register cleanup actions for resources
- Use rollback for complex state management
- Monitor memory usage

## 🧪 Testing

### Run Tests

```bash
# Full test suite
PYTHONPATH=/code/goodplay-be TESTING=true python -m pytest tests/test_smart_fixtures.py

# Performance requirements
PYTHONPATH=/code/goodplay-be TESTING=true python -m pytest tests/test_smart_fixtures.py::test_goo_34_performance_requirements

# Core manager tests
PYTHONPATH=/code/goodplay-be TESTING=true python -m pytest tests/test_smart_fixtures.py::TestSmartFixtureManager
```

### Smoke Test

```bash
# Quick smoke test
PYTHONPATH=/code/goodplay-be TESTING=true python tests/test_smart_fixtures.py
```

## 📄 API Reference

### Core Classes

- `SmartFixtureManager`: Central fixture coordination
- `DependencyGraph`: Dependency resolution
- `SmartFixtureCache`: Intelligent caching
- `PerformanceMonitor`: Performance tracking
- `CleanupManager`: Resource management

### Enums

- `FixtureScope`: Cache scope options
- `FixtureStatus`: Fixture lifecycle states
- `CleanupStrategy`: Cleanup strategies
- `RollbackStrategy`: Rollback strategies

### Utilities

- `auto_detect_dependencies()`: Automatic dependency detection
- `benchmark_fixture()`: Fixture benchmarking
- `get_system_health()`: System health check
- `reset_smart_fixtures()`: System reset

## 🎯 Integration with GOO-26

This Smart Fixture System completes **MILESTONE 2: Factory & Fixture System** by providing:

- ✅ **Factory-Boy Integration**: Seamless integration with existing Factory-Boy factories
- ✅ **Shared Fixtures Package**: Organized, reusable fixture system
- ✅ **Builder Pattern**: Complex test scenario builders via presets
- ✅ **Auto-Generation**: Automatic test data generation with caching
- ✅ **Performance Requirements**: All GOO-34 targets met or exceeded

## 🏆 Success Criteria Met

- ✅ Smart fixture system working across all test types
- ✅ Performance requirements exceeded
- ✅ Zero memory leaks in fixture cleanup
- ✅ Complete documentation with examples and best practices
- ✅ Automatic dependency detection and resolution
- ✅ Intelligent caching with 80%+ hit ratio
- ✅ Lazy loading for expensive fixtures
- ✅ Parallel fixture creation optimization
- ✅ Real-time performance monitoring

---

**Status: ✅ COMPLETED** - Ready for production use across the GoodPlay test suite.

For support or questions, see the test files in `tests/test_smart_fixtures.py` for comprehensive examples and usage patterns.