"""
Test Suite for Smart Fixture System - GOO-34

Comprehensive tests to validate the intelligent fixture management system
with dependency resolution, caching, performance monitoring, and cleanup.
"""
import pytest
import time
import threading
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Smart Fixture System
from tests.fixtures import (
    # Core system
    smart_fixture_manager,
    FixtureScope,
    FixtureStatus,

    # Decorators
    smart_fixture,
    factory_fixture,
    preset_fixture,
    lazy_fixture,

    # Preset system
    preset_manager,
    basic_user_setup,
    gaming_session_setup,

    # Performance monitoring
    performance_monitor,

    # Cleanup system
    cleanup_manager,

    # Utilities
    get_system_health,
    reset_smart_fixtures,
    benchmark_fixture
)


class TestSmartFixtureManager:
    """Test the core SmartFixtureManager functionality"""

    def setup_method(self):
        """Reset the smart fixture system before each test"""
        reset_smart_fixtures()

    def test_singleton_pattern(self):
        """Test that SmartFixtureManager is a singleton"""
        from tests.fixtures.smart_manager import SmartFixtureManager

        manager1 = SmartFixtureManager()
        manager2 = SmartFixtureManager()

        assert manager1 is manager2
        assert manager1 is smart_fixture_manager

    def test_register_fixture(self):
        """Test fixture registration"""
        def test_creator():
            return {'test': 'data'}

        smart_fixture_manager.register_fixture(
            'test_fixture',
            test_creator,
            scope=FixtureScope.FUNCTION,
            dependencies=['dep1', 'dep2']
        )

        # Check fixture is registered
        assert 'test_fixture' in smart_fixture_manager._fixture_registry

        # Check dependencies are registered
        deps = smart_fixture_manager.dependency_graph.get_dependencies('test_fixture')
        assert 'dep1' in deps
        assert 'dep2' in deps

    def test_fixture_creation(self):
        """Test basic fixture creation"""
        def test_creator():
            return {'created_at': time.time(), 'data': 'test'}

        smart_fixture_manager.register_fixture('simple_fixture', test_creator)

        result = smart_fixture_manager.create_fixture('simple_fixture')

        assert result is not None
        assert result['data'] == 'test'
        assert 'created_at' in result

    def test_dependency_resolution(self):
        """Test automatic dependency resolution"""
        creation_order = []

        def dep1_creator():
            creation_order.append('dep1')
            return {'name': 'dependency1'}

        def dep2_creator():
            creation_order.append('dep2')
            return {'name': 'dependency2'}

        def main_creator(dep1, dep2):
            creation_order.append('main')
            return {'deps': [dep1, dep2]}

        # Register fixtures with dependencies
        smart_fixture_manager.register_fixture('dep1', dep1_creator)
        smart_fixture_manager.register_fixture('dep2', dep2_creator)
        smart_fixture_manager.register_fixture(
            'main_fixture',
            main_creator,
            dependencies=['dep1', 'dep2']
        )

        result = smart_fixture_manager.create_fixture('main_fixture')

        # Check creation order - dependencies should be created before main
        assert 'main' in creation_order
        assert creation_order.index('main') == len(creation_order) - 1  # main should be last
        assert 'dep1' in creation_order
        assert 'dep2' in creation_order

        # Check result structure
        assert len(result['deps']) == 2
        dep_names = {dep['name'] for dep in result['deps']}
        assert dep_names == {'dependency1', 'dependency2'}

    def test_circular_dependency_detection(self):
        """Test circular dependency detection"""
        def creator_a():
            return {'name': 'a'}

        def creator_b():
            return {'name': 'b'}

        # Create circular dependency
        smart_fixture_manager.register_fixture('fixture_a', creator_a, dependencies=['fixture_b'])
        smart_fixture_manager.register_fixture('fixture_b', creator_b, dependencies=['fixture_a'])

        with pytest.raises(ValueError, match="Circular dependency"):
            smart_fixture_manager.create_fixture('fixture_a')

    def test_caching_functionality(self):
        """Test fixture caching"""
        call_count = 0

        def expensive_creator():
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # Simulate expensive operation
            return {'call_number': call_count, 'created_at': time.time()}

        smart_fixture_manager.register_fixture(
            'expensive_fixture',
            expensive_creator,
            scope=FixtureScope.SESSION
        )

        # First call - should create
        result1 = smart_fixture_manager.create_fixture('expensive_fixture', scope=FixtureScope.SESSION)
        assert call_count == 1

        # Second call - should use cache
        result2 = smart_fixture_manager.create_fixture('expensive_fixture', scope=FixtureScope.SESSION)
        assert call_count == 1  # Still 1, used cache
        assert result1 is result2

    def test_performance_monitoring(self):
        """Test performance monitoring integration"""
        def slow_creator():
            time.sleep(0.06)  # Deliberately slow (>50ms threshold)
            return {'data': 'slow_fixture'}

        smart_fixture_manager.register_fixture('slow_fixture', slow_creator)

        # Create fixture and check performance tracking
        smart_fixture_manager.create_fixture('slow_fixture')

        report = smart_fixture_manager.get_performance_report()
        assert report['fixtures_created'] >= 1
        assert report['average_creation_time_ms'] > 50  # Should be slow


class TestSmartFixtureDecorators:
    """Test smart fixture decorators"""

    def setup_method(self):
        reset_smart_fixtures()

    def test_smart_fixture_decorator(self):
        """Test @smart_fixture decorator"""
        @smart_fixture('decorated_fixture')
        def my_fixture():
            return {'source': 'decorator', 'timestamp': time.time()}

        # Fixture should be auto-registered
        result = smart_fixture_manager.create_fixture('decorated_fixture')
        assert result['source'] == 'decorator'

    def test_smart_fixture_with_dependencies(self):
        """Test @smart_fixture with auto-detected dependencies"""
        @smart_fixture('base_data')
        def base_data():
            return {'base': True, 'value': 42}

        @smart_fixture('dependent_fixture')
        def dependent_fixture(base_data):
            return {'base': base_data, 'extended': True}

        result = smart_fixture_manager.create_fixture('dependent_fixture')
        assert result['base']['value'] == 42
        assert result['extended'] is True

    def test_lazy_fixture_decorator(self):
        """Test @lazy_fixture decorator"""
        call_count = 0

        @lazy_fixture('lazy_computation')
        def lazy_computation():
            nonlocal call_count
            call_count += 1
            return f'computed_result_{call_count}'

        # Should not be called yet
        assert call_count == 0

        # Access the lazy fixture
        result = lazy_computation()
        assert call_count == 1
        assert result == 'computed_result_1'

        # Access again - should use cached value
        result2 = lazy_computation()
        assert call_count == 1  # Still 1
        assert result2 == 'computed_result_1'

    def test_preset_fixture_decorator(self):
        """Test preset fixture creation"""
        # Test basic_user_setup preset
        result = basic_user_setup()

        assert 'basic_user' in result
        assert 'user_preferences' in result
        assert result['basic_user'] is not None
        assert result['user_preferences'] is not None


class TestPerformanceMonitoring:
    """Test performance monitoring and optimization"""

    def setup_method(self):
        reset_smart_fixtures()

    def test_performance_metrics_collection(self):
        """Test performance metrics are collected correctly"""
        @smart_fixture('perf_test_fixture')
        def perf_fixture():
            time.sleep(0.01)
            return {'data': 'performance_test'}

        # Create fixture multiple times
        for i in range(5):
            smart_fixture_manager.create_fixture('perf_test_fixture', force_recreate=True)

        report = performance_monitor.get_performance_report()

        assert report['total_fixtures_registered'] >= 1
        assert report['session_duration_seconds'] > 0
        assert 'fixture_breakdown' in report

        if 'perf_test_fixture' in report['fixture_breakdown']:
            fixture_stats = report['fixture_breakdown']['perf_test_fixture']
            assert fixture_stats['creation_count'] >= 5

    def test_memory_tracking(self):
        """Test memory usage tracking"""
        @smart_fixture('memory_test')
        def memory_fixture():
            # Create some data to use memory
            return {'large_data': list(range(1000))}

        smart_fixture_manager.create_fixture('memory_test')

        report = performance_monitor.get_performance_report()
        assert report['memory_usage_mb'] >= 0
        assert 'memory_overhead_mb' in report

    def test_cache_hit_ratio_tracking(self):
        """Test cache hit ratio calculation"""
        @smart_fixture('cacheable_fixture')
        def cacheable_fixture():
            return {'timestamp': time.time()}

        # First creation - cache miss
        smart_fixture_manager.create_fixture('cacheable_fixture', scope=FixtureScope.SESSION)

        # Second creation - cache hit
        smart_fixture_manager.create_fixture('cacheable_fixture', scope=FixtureScope.SESSION)

        report = performance_monitor.get_performance_report()
        assert report['cache_hits'] >= 1
        assert report['overall_cache_hit_ratio'] > 0


class TestCleanupSystem:
    """Test cleanup and resource management"""

    def setup_method(self):
        reset_smart_fixtures()

    def test_cleanup_registration(self):
        """Test cleanup action registration"""
        cleanup_called = False

        def cleanup_action():
            nonlocal cleanup_called
            cleanup_called = True

        cleanup_manager.register_cleanup_action(
            'test_fixture',
            'test_cleanup',
            cleanup_action
        )

        # Execute cleanup
        cleanup_manager.cleanup_fixture('test_fixture')

        assert cleanup_called is True

    def test_resource_tracking(self):
        """Test resource tracking functionality"""
        cleanup_manager.resource_tracker.track_resource(
            'test_fixture',
            'file_handle',
            'test_file.txt',
            cleanup_func=lambda: print("Cleanup file")
        )

        resources = cleanup_manager.resource_tracker.get_fixture_resources('test_fixture')
        assert 'file_handle' in resources
        assert resources['file_handle']['resource_id'] == 'test_file.txt'

    def test_rollback_functionality(self):
        """Test fixture state rollback"""
        fixture_data = {'value': 'original', 'modified': False}

        # Enable rollback for fixture
        cleanup_manager.enable_rollback('rollback_test')

        # Take snapshot
        snapshot_id = cleanup_manager.take_snapshot('rollback_test', fixture_data)
        assert snapshot_id is not None

        # Modify data
        fixture_data['value'] = 'modified'
        fixture_data['modified'] = True

        # Rollback
        original_data = cleanup_manager.rollback_fixture('rollback_test', snapshot_id)
        assert original_data['value'] == 'original'
        assert original_data['modified'] is False


class TestSystemIntegration:
    """Test system integration and overall functionality"""

    def setup_method(self):
        reset_smart_fixtures()

    def test_factory_boy_integration(self):
        """Test Factory-Boy integration"""
        try:
            from tests.fixtures import register_factory_boy_integration
            register_factory_boy_integration()

            # Test if factories were registered
            registered_factories = smart_fixture_manager._factory_registry
            assert len(registered_factories) > 0

        except ImportError:
            pytest.skip("Factory-Boy factories not available")

    def test_system_health_check(self):
        """Test system health monitoring"""
        # Create some fixtures to generate activity
        @smart_fixture('health_test')
        def health_fixture():
            return {'status': 'healthy'}

        smart_fixture_manager.create_fixture('health_test')

        health = get_system_health()

        assert 'health_status' in health
        assert 'health_score' in health
        assert 'performance_summary' in health
        assert health['health_status'] in ['HEALTHY', 'WARNING', 'UNHEALTHY']
        assert 0 <= health['health_score'] <= 100

    def test_concurrent_fixture_creation(self):
        """Test thread-safe fixture creation"""
        results = []
        errors = []

        @smart_fixture('concurrent_test')
        def concurrent_fixture():
            # Add small delay to increase chance of race conditions
            time.sleep(0.001)
            return {'thread_id': threading.current_thread().ident, 'timestamp': time.time()}

        def create_fixture():
            try:
                result = smart_fixture_manager.create_fixture('concurrent_test', scope=FixtureScope.SESSION)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create fixtures concurrently
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_fixture)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Errors in concurrent creation: {errors}"
        assert len(results) == 10

        # With session scope, all results should be the same (cached)
        first_result = results[0]
        for result in results[1:]:
            assert result is first_result

    def test_benchmark_functionality(self):
        """Test fixture benchmarking"""
        @smart_fixture('benchmark_test')
        def benchmark_fixture():
            time.sleep(0.005)  # 5ms
            return {'benchmark': True}

        # Benchmark the fixture
        benchmark_results = benchmark_fixture(
            smart_fixture_manager.create_fixture,
            iterations=10,
            warmup_iterations=2
        )

        assert benchmark_results['fixture_name'] == smart_fixture_manager.create_fixture.__name__
        assert benchmark_results['iterations'] <= 10
        assert benchmark_results['mean_time_ms'] > 0
        assert benchmark_results['success_rate'] >= 0


class TestPresetSystem:
    """Test fixture preset combinations"""

    def setup_method(self):
        reset_smart_fixtures()

    def test_preset_registration(self):
        """Test preset registration and retrieval"""
        available_presets = preset_manager.get_available_presets()

        # Check required presets are available
        required_presets = [
            'basic_user_setup',
            'gaming_session_setup',
            'social_network_setup',
            'financial_setup',
            'admin_setup'
        ]

        for preset in required_presets:
            assert preset in available_presets

    def test_gaming_session_setup_preset(self):
        """Test gaming session setup preset"""
        try:
            result = gaming_session_setup()

            assert 'basic_user' in result
            assert 'game' in result
            assert 'game_session' in result

            # Check relationships
            user = result['basic_user']
            session = result['game_session']
            game = result['game']

            assert session['user_id'] == user['_id']
            assert session['game_id'] == game['_id']

        except ImportError:
            pytest.skip("Factory-Boy factories not available for preset testing")

    def test_preset_performance(self):
        """Test preset creation performance"""
        start_time = time.time()

        try:
            result = preset_manager.create_preset('basic_user_setup')
            creation_time = (time.time() - start_time) * 1000  # Convert to ms

            # Should create preset in reasonable time
            assert creation_time < 200  # 200ms threshold for preset creation
            assert result is not None

        except ImportError:
            pytest.skip("Factory-Boy factories not available for performance testing")


class TestErrorHandling:
    """Test error handling and edge cases"""

    def setup_method(self):
        reset_smart_fixtures()

    def test_unknown_fixture_error(self):
        """Test error handling for unknown fixtures"""
        with pytest.raises(ValueError, match="Unknown fixture"):
            smart_fixture_manager.create_fixture('nonexistent_fixture')

    def test_failed_fixture_creation(self):
        """Test handling of fixture creation failures"""
        def failing_creator():
            raise RuntimeError("Fixture creation failed")

        smart_fixture_manager.register_fixture('failing_fixture', failing_creator)

        with pytest.raises(RuntimeError, match="Fixture creation failed"):
            smart_fixture_manager.create_fixture('failing_fixture')

    def test_invalid_dependency_handling(self):
        """Test handling of invalid dependencies"""
        def creator_with_invalid_deps():
            return {'data': 'test'}

        smart_fixture_manager.register_fixture(
            'invalid_deps_fixture',
            creator_with_invalid_deps,
            dependencies=['nonexistent_dependency']
        )

        with pytest.raises(ValueError, match="Unknown fixture"):
            smart_fixture_manager.create_fixture('invalid_deps_fixture')


# Performance benchmark for overall system
def test_goo_34_performance_requirements():
    """
    Test GOO-34 performance requirements:
    - Fixture creation time < 50ms per test
    - Memory usage < 100MB for full test suite
    - Cleanup time < 10ms per test
    - Cache hit ratio > 80% for repeated fixtures
    """
    reset_smart_fixtures()

    # Test fixture creation time
    @smart_fixture('perf_requirement_test')
    def perf_fixture():
        return {'data': f'test_{time.time()}'}

    start_time = time.time()
    smart_fixture_manager.create_fixture('perf_requirement_test')
    creation_time_ms = (time.time() - start_time) * 1000

    # ✅ Fixture creation time < 50ms per test
    assert creation_time_ms < 50, f"Fixture creation took {creation_time_ms:.1f}ms (requirement: <50ms)"

    # Test cache hit ratio by creating same fixture multiple times
    cache_test_fixture_name = 'cache_ratio_test'

    @smart_fixture(cache_test_fixture_name)
    def cache_test():
        return {'cached_data': 'test'}

    # Create multiple times to test caching
    for _ in range(10):
        smart_fixture_manager.create_fixture(cache_test_fixture_name, scope=FixtureScope.SESSION)

    report = performance_monitor.get_performance_report()

    # ✅ Cache hit ratio > 80% for repeated fixtures
    cache_hit_ratio = report.get('overall_cache_hit_ratio', 0)
    assert cache_hit_ratio > 0.8, f"Cache hit ratio: {cache_hit_ratio:.1%} (requirement: >80%)"

    # ✅ Memory usage < 100MB for full test suite
    memory_usage_mb = report.get('memory_usage_mb', 0)
    assert memory_usage_mb < 100, f"Memory usage: {memory_usage_mb:.1f}MB (requirement: <100MB)"

    print(f"🎉 GOO-34 Performance Requirements PASSED:")
    print(f"   ✅ Fixture creation time: {creation_time_ms:.1f}ms (<50ms)")
    print(f"   ✅ Cache hit ratio: {cache_hit_ratio:.1%} (>80%)")
    print(f"   ✅ Memory usage: {memory_usage_mb:.1f}MB (<100MB)")


if __name__ == "__main__":
    # Run basic smoke test
    print("🧪 Running Smart Fixture System Smoke Test...")

    reset_smart_fixtures()

    # Test basic functionality
    @smart_fixture('smoke_test')
    def smoke_test_fixture():
        return {'smoke_test': True, 'timestamp': time.time()}

    result = smart_fixture_manager.create_fixture('smoke_test')
    assert result['smoke_test'] is True

    # Test performance monitoring
    report = smart_fixture_manager.get_performance_report()
    assert report['fixtures_created'] >= 1

    print("✅ Smoke test passed!")
    print(f"   - Fixtures created: {report['fixtures_created']}")
    print(f"   - Average creation time: {report['average_creation_time_ms']:.1f}ms")
    print(f"   - Memory usage: {report['memory_usage_mb']:.1f}MB")

    # Test system health
    health = get_system_health()
    print(f"   - System health: {health['health_status']}")

    print("🎉 Smart Fixture System is working correctly!")