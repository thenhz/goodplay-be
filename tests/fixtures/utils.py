"""
Smart Fixture Utilities for GOO-34

Utility functions, helpers, and integrations for the intelligent fixture system.
"""
import inspect
import functools
from typing import Dict, List, Any, Optional, Callable, Type, get_type_hints
import pytest
from .smart_manager import smart_fixture_manager, FixtureScope
from .performance import performance_monitor
from .cleanup import cleanup_manager


def auto_detect_dependencies(func: Callable) -> List[str]:
    """
    Auto-detect fixture dependencies from function signature

    Args:
        func: Function to analyze

    Returns:
        List of parameter names that could be fixtures
    """
    sig = inspect.signature(func)
    dependencies = []

    for param_name, param in sig.parameters.items():
        # Skip special pytest parameters
        if param_name in ['request', 'monkeypatch', 'tmpdir', 'tmp_path']:
            continue

        # Skip parameters with default values that aren't None
        if param.default is not inspect.Parameter.empty and param.default is not None:
            continue

        dependencies.append(param_name)

    return dependencies


def validate_fixture_function(func: Callable) -> Dict[str, Any]:
    """
    Validate fixture function for common issues

    Args:
        func: Function to validate

    Returns:
        Validation report with warnings and suggestions
    """
    report = {
        'valid': True,
        'warnings': [],
        'suggestions': [],
        'function_name': func.__name__
    }

    # Check function signature
    sig = inspect.signature(func)

    # Check for too many parameters (might indicate complex dependencies)
    if len(sig.parameters) > 10:
        report['warnings'].append(
            f"Function has {len(sig.parameters)} parameters - consider breaking into smaller fixtures"
        )

    # Check for type hints
    try:
        type_hints = get_type_hints(func)
        if not type_hints:
            report['suggestions'].append("Add type hints for better IDE support")
    except:
        pass

    # Check docstring
    if not func.__doc__:
        report['suggestions'].append("Add docstring to explain fixture purpose")

    # Check for potential expensive operations
    source_lines = inspect.getsourcelines(func)[0]
    source_code = ''.join(source_lines)

    expensive_patterns = [
        ('time.sleep', 'Contains time.sleep - consider mocking'),
        ('requests.', 'Makes HTTP requests - consider mocking'),
        ('open(', 'File I/O operations - ensure cleanup'),
        ('subprocess.', 'Subprocess calls - ensure cleanup')
    ]

    for pattern, warning in expensive_patterns:
        if pattern in source_code:
            report['warnings'].append(warning)

    return report


def migrate_legacy_fixture(
    legacy_fixture_func: Callable,
    scope: FixtureScope = FixtureScope.FUNCTION,
    dependencies: List[str] = None
) -> Callable:
    """
    Migrate a legacy pytest fixture to smart fixture system

    Args:
        legacy_fixture_func: Existing pytest fixture function
        scope: Smart fixture scope
        dependencies: Explicit dependencies

    Returns:
        Smart fixture wrapper
    """
    fixture_name = legacy_fixture_func.__name__
    detected_deps = auto_detect_dependencies(legacy_fixture_func)
    all_deps = list(set((dependencies or []) + detected_deps))

    # Register with smart fixture manager
    smart_fixture_manager.register_fixture(
        name=fixture_name,
        creator=legacy_fixture_func,
        scope=scope,
        dependencies=all_deps
    )

    @functools.wraps(legacy_fixture_func)
    def smart_wrapper(*args, **kwargs):
        return smart_fixture_manager.create_fixture(fixture_name, scope=scope)

    # Preserve pytest fixture decorator
    return pytest.fixture(scope=scope.value, name=fixture_name)(smart_wrapper)


def create_fixture_factory(factory_class: Type) -> Callable:
    """
    Create a fixture function from a Factory-Boy factory class

    Args:
        factory_class: Factory-Boy factory class

    Returns:
        Fixture function that creates instances using the factory
    """
    fixture_name = factory_class.__name__.lower().replace('factory', '')

    def factory_fixture(**kwargs):
        return factory_class.build(**kwargs)

    factory_fixture.__name__ = fixture_name
    factory_fixture.__doc__ = f"Auto-generated fixture for {factory_class.__name__}"

    return factory_fixture


def benchmark_fixture(
    fixture_func: Callable,
    iterations: int = 100,
    warmup_iterations: int = 10
) -> Dict[str, Any]:
    """
    Benchmark fixture performance

    Args:
        fixture_func: Fixture function to benchmark
        iterations: Number of benchmark iterations
        warmup_iterations: Number of warmup iterations

    Returns:
        Benchmark results
    """
    import time
    import statistics

    # Warmup
    for _ in range(warmup_iterations):
        try:
            fixture_func()
        except:
            pass

    # Benchmark
    times = []
    errors = 0

    for _ in range(iterations):
        start_time = time.perf_counter()
        try:
            fixture_func()
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)  # Convert to ms
        except Exception:
            errors += 1

    if not times:
        return {
            'fixture_name': fixture_func.__name__,
            'error': 'All iterations failed',
            'errors': errors,
            'iterations': iterations
        }

    return {
        'fixture_name': fixture_func.__name__,
        'iterations': len(times),
        'errors': errors,
        'min_time_ms': min(times),
        'max_time_ms': max(times),
        'mean_time_ms': statistics.mean(times),
        'median_time_ms': statistics.median(times),
        'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0.0,
        'total_time_ms': sum(times),
        'success_rate': len(times) / iterations
    }


class FixtureDebugger:
    """Debug and analyze fixture behavior"""

    def __init__(self):
        self._debug_traces: Dict[str, List[str]] = {}

    def trace_fixture_creation(self, fixture_name: str):
        """Enable tracing for fixture creation"""
        if fixture_name not in self._debug_traces:
            self._debug_traces[fixture_name] = []

        def trace_func(frame, event, arg):
            if event == 'call':
                filename = frame.f_code.co_filename
                function_name = frame.f_code.co_name
                line_number = frame.f_lineno

                if 'fixtures' in filename or 'factories' in filename:
                    trace_info = f"{function_name}:{line_number} in {filename}"
                    self._debug_traces[fixture_name].append(trace_info)

            return trace_func

        import sys
        old_trace = sys.gettrace()

        try:
            sys.settrace(trace_func)
            smart_fixture_manager.create_fixture(fixture_name)
        finally:
            sys.settrace(old_trace)

    def get_fixture_trace(self, fixture_name: str) -> List[str]:
        """Get creation trace for a fixture"""
        return self._debug_traces.get(fixture_name, [])

    def analyze_fixture_dependencies(self, fixture_name: str) -> Dict[str, Any]:
        """Analyze fixture dependency graph"""
        dependencies = smart_fixture_manager.dependency_graph.get_dependencies(fixture_name)
        dependents = smart_fixture_manager.dependency_graph.get_dependents(fixture_name)

        return {
            'fixture_name': fixture_name,
            'direct_dependencies': dependencies,
            'dependents': dependents,
            'dependency_depth': self._calculate_dependency_depth(fixture_name),
            'circular_dependencies': self._detect_circular_deps(fixture_name)
        }

    def _calculate_dependency_depth(self, fixture_name: str, visited: set = None) -> int:
        """Calculate maximum dependency depth"""
        if visited is None:
            visited = set()

        if fixture_name in visited:
            return 0  # Circular dependency

        visited.add(fixture_name)
        dependencies = smart_fixture_manager.dependency_graph.get_dependencies(fixture_name)

        if not dependencies:
            return 0

        max_depth = 0
        for dep in dependencies:
            depth = 1 + self._calculate_dependency_depth(dep, visited.copy())
            max_depth = max(max_depth, depth)

        return max_depth

    def _detect_circular_deps(self, fixture_name: str) -> List[List[str]]:
        """Detect circular dependencies"""
        # Implementation for circular dependency detection
        # This is a simplified version - could be enhanced
        try:
            dependencies = smart_fixture_manager.dependency_graph.get_dependencies(fixture_name)
            smart_fixture_manager.dependency_graph.resolve_order([fixture_name] + dependencies)
            return []  # No circular dependencies
        except ValueError as e:
            if "Circular dependency" in str(e):
                return [["Circular dependency detected"]]
            return []


def generate_fixture_documentation() -> str:
    """Generate documentation for all registered fixtures"""
    report = smart_fixture_manager.get_performance_report()

    doc_lines = [
        "# Smart Fixture System Documentation",
        "",
        "## Registered Fixtures",
        ""
    ]

    # Get all registered fixtures
    registry = smart_fixture_manager._fixture_registry
    factory_registry = smart_fixture_manager._factory_registry

    for fixture_name in sorted(registry.keys()):
        func = registry[fixture_name]
        doc_lines.extend([
            f"### {fixture_name}",
            "",
            f"**Function**: `{func.__name__}`",
            f"**Docstring**: {func.__doc__ or 'No documentation'}",
            ""
        ])

        # Add dependencies
        deps = smart_fixture_manager.dependency_graph.get_dependencies(fixture_name)
        if deps:
            doc_lines.extend([
                f"**Dependencies**: {', '.join(deps)}",
                ""
            ])

    # Add Factory-Boy factories
    if factory_registry:
        doc_lines.extend([
            "## Factory-Boy Integration",
            ""
        ])

        for factory_name, factory_class in factory_registry.items():
            doc_lines.extend([
                f"### {factory_name}",
                f"**Factory Class**: `{factory_class.__name__}`",
                ""
            ])

    # Add performance summary
    doc_lines.extend([
        "## Performance Summary",
        "",
        f"- Total fixtures: {report['registered_fixtures']}",
        f"- Total factories: {report['registered_factories']}",
        f"- Cache hit ratio: {report['cache_hit_ratio']:.1%}",
        f"- Average creation time: {report['average_creation_time_ms']:.1f}ms",
        ""
    ])

    return '\n'.join(doc_lines)


# Global utilities
fixture_debugger = FixtureDebugger()


# Convenience functions
def smart_fixture_from_factory(factory_class: Type, **default_kwargs):
    """
    Quick helper to create smart fixture from Factory-Boy factory

    Usage:
        user_fixture = smart_fixture_from_factory(UserFactory, role='user')
    """
    fixture_name = factory_class.__name__.lower().replace('factory', '')

    def factory_creator(**kwargs):
        merged_kwargs = {**default_kwargs, **kwargs}
        return factory_class.build(**merged_kwargs)

    smart_fixture_manager.register_fixture(
        name=fixture_name,
        creator=factory_creator,
        scope=FixtureScope.FUNCTION,
        factory_class=factory_class.__name__
    )

    return fixture_name


def reset_smart_fixtures():
    """Reset the entire smart fixture system (useful for testing)"""
    smart_fixture_manager.reset()
    performance_monitor.reset_metrics()
    cleanup_manager.resource_tracker._tracked_resources.clear()


def get_system_health() -> Dict[str, Any]:
    """Get overall health status of the smart fixture system"""
    perf_report = performance_monitor.get_performance_report()
    cleanup_status = cleanup_manager.get_cleanup_status()

    # Determine health status
    health_issues = []
    health_score = 100

    # Check performance
    if perf_report['performance_status'] != 'OPTIMAL':
        health_issues.append(f"Performance: {perf_report['performance_status']}")
        health_score -= 20

    # Check memory usage
    if perf_report['memory_usage_mb'] > 150:  # 150MB threshold
        health_issues.append(f"High memory usage: {perf_report['memory_usage_mb']:.1f}MB")
        health_score -= 15

    # Check cache performance
    if perf_report['overall_cache_hit_ratio'] < 0.7:
        health_issues.append(f"Low cache hit ratio: {perf_report['overall_cache_hit_ratio']:.1%}")
        health_score -= 10

    health_status = "HEALTHY"
    if health_score < 70:
        health_status = "UNHEALTHY"
    elif health_score < 85:
        health_status = "WARNING"

    return {
        'health_status': health_status,
        'health_score': health_score,
        'issues': health_issues,
        'performance_summary': {
            'total_fixtures': perf_report['total_fixtures_registered'],
            'memory_usage_mb': perf_report['memory_usage_mb'],
            'cache_hit_ratio': perf_report['overall_cache_hit_ratio'],
            'performance_warnings': perf_report['performance_warnings']
        },
        'cleanup_summary': {
            'fixtures_with_cleanup': cleanup_status['fixtures_with_cleanup'],
            'snapshots_stored': cleanup_status['snapshots_stored']
        },
        'recommendations': _generate_health_recommendations(health_issues)
    }


def _generate_health_recommendations(issues: List[str]) -> List[str]:
    """Generate health improvement recommendations"""
    recommendations = []

    for issue in issues:
        if "memory usage" in issue.lower():
            recommendations.extend([
                "Consider using function scope instead of session scope for large fixtures",
                "Enable automatic cleanup for unused fixtures",
                "Review fixture factory complexity"
            ])

        if "cache hit ratio" in issue.lower():
            recommendations.extend([
                "Review fixture scoping strategy",
                "Consider increasing cache scope for frequently used fixtures",
                "Check for unnecessary fixture recreations"
            ])

        if "performance" in issue.lower():
            recommendations.extend([
                "Profile slow fixture creation functions",
                "Consider lazy loading for expensive operations",
                "Review Factory-Boy factory optimization"
            ])

    return list(set(recommendations))  # Remove duplicates