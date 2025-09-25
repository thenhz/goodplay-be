"""
SmartFixtureManager - Core System for GOO-34

Intelligent fixture management system with automatic dependency resolution,
caching, performance monitoring, and resource optimization.
"""
import time
import threading
import weakref
from typing import Dict, List, Any, Optional, Callable, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timezone

# Configure logging for smart fixture system
logger = logging.getLogger('smart_fixtures')


class FixtureScope(Enum):
    """Fixture scope types for intelligent caching"""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    SESSION = "session"
    LAZY = "lazy"


class FixtureStatus(Enum):
    """Fixture lifecycle status"""
    PENDING = "pending"
    CREATING = "creating"
    READY = "ready"
    CACHED = "cached"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass
class FixtureMetadata:
    """Metadata for fixture tracking and optimization"""
    name: str
    scope: FixtureScope
    dependencies: List[str] = field(default_factory=list)
    creation_time: Optional[float] = None
    access_count: int = 0
    memory_usage: int = 0
    last_accessed: Optional[datetime] = None
    status: FixtureStatus = FixtureStatus.PENDING
    factory_class: Optional[str] = None
    preset_type: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance tracking for fixture operations"""
    total_fixtures_created: int = 0
    total_creation_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    memory_peak_usage: int = 0
    cleanup_time: float = 0.0

    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        total_accesses = self.cache_hits + self.cache_misses
        return (self.cache_hits / total_accesses) if total_accesses > 0 else 0.0

    @property
    def average_creation_time(self) -> float:
        """Calculate average fixture creation time"""
        return (self.total_creation_time / self.total_fixtures_created
                if self.total_fixtures_created > 0 else 0.0)


class DependencyGraph:
    """Dependency graph for automatic fixture resolution"""

    def __init__(self):
        self._graph: Dict[str, Set[str]] = {}
        self._reverse_graph: Dict[str, Set[str]] = {}
        self._lock = threading.RLock()

    def add_dependency(self, fixture_name: str, depends_on: str):
        """Add a dependency relationship"""
        with self._lock:
            if fixture_name not in self._graph:
                self._graph[fixture_name] = set()
            if depends_on not in self._reverse_graph:
                self._reverse_graph[depends_on] = set()

            self._graph[fixture_name].add(depends_on)
            self._reverse_graph[depends_on].add(fixture_name)

    def get_dependencies(self, fixture_name: str) -> List[str]:
        """Get direct dependencies for a fixture"""
        return list(self._graph.get(fixture_name, set()))

    def get_dependents(self, fixture_name: str) -> List[str]:
        """Get fixtures that depend on this one"""
        return list(self._reverse_graph.get(fixture_name, set()))

    def resolve_order(self, fixture_names: List[str]) -> List[str]:
        """Resolve optimal creation order for fixtures"""
        visited = set()
        temp_visited = set()
        result = []

        def visit(name: str):
            if name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {name}")
            if name in visited:
                return

            temp_visited.add(name)
            for dep in self.get_dependencies(name):
                if dep in fixture_names:
                    visit(dep)
            temp_visited.remove(name)
            visited.add(name)
            result.append(name)

        for fixture_name in fixture_names:
            if fixture_name not in visited:
                visit(fixture_name)

        return result

    def detect_conflicts(self, fixture_names: List[str]) -> List[str]:
        """Detect potential conflicts between fixtures"""
        conflicts = []
        # Implementation for conflict detection
        # For now, return empty list - will be enhanced in later phases
        return conflicts


class SmartFixtureCache:
    """Intelligent caching system for fixtures"""

    def __init__(self, max_memory_mb: int = 100):
        self._caches: Dict[FixtureScope, Dict[str, Any]] = {
            scope: {} for scope in FixtureScope
        }
        self._metadata: Dict[str, FixtureMetadata] = {}
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._current_memory = 0
        self._lock = threading.RLock()

    def get(self, name: str, scope: FixtureScope) -> Optional[Any]:
        """Get cached fixture if available"""
        with self._lock:
            cache = self._caches.get(scope, {})
            if name in cache:
                # Update access tracking
                if name in self._metadata:
                    self._metadata[name].access_count += 1
                    self._metadata[name].last_accessed = datetime.now(timezone.utc)
                return cache[name]
            return None

    def set(self, name: str, value: Any, metadata: FixtureMetadata):
        """Cache a fixture with metadata"""
        with self._lock:
            scope = metadata.scope
            if scope not in self._caches:
                self._caches[scope] = {}

            # Estimate memory usage (simplified)
            estimated_size = len(str(value)) * 8  # Rough estimate

            # Check memory limits
            if self._current_memory + estimated_size > self._max_memory_bytes:
                self._cleanup_expired()

            self._caches[scope][name] = value
            metadata.status = FixtureStatus.CACHED
            metadata.memory_usage = estimated_size
            self._metadata[name] = metadata
            self._current_memory += estimated_size

    def invalidate(self, name: str, scope: FixtureScope = None):
        """Invalidate cached fixture"""
        with self._lock:
            if scope:
                cache = self._caches.get(scope, {})
                if name in cache:
                    del cache[name]
            else:
                # Invalidate from all scopes
                for cache in self._caches.values():
                    cache.pop(name, None)

            if name in self._metadata:
                self._current_memory -= self._metadata[name].memory_usage
                del self._metadata[name]

    def clear_scope(self, scope: FixtureScope):
        """Clear all fixtures in a specific scope"""
        with self._lock:
            cache = self._caches.get(scope, {})
            for name in list(cache.keys()):
                self.invalidate(name, scope)
            cache.clear()

    def _cleanup_expired(self):
        """Internal cleanup of expired fixtures"""
        # Simple LRU cleanup - remove least recently accessed
        if not self._metadata:
            return

        # Sort by last accessed time
        sorted_items = sorted(
            self._metadata.items(),
            key=lambda x: x[1].last_accessed or datetime.min.replace(tzinfo=timezone.utc)
        )

        # Remove oldest 25% of items
        items_to_remove = len(sorted_items) // 4
        for name, _ in sorted_items[:items_to_remove]:
            for scope in FixtureScope:
                self.invalidate(name, scope)

    def get_memory_usage(self) -> int:
        """Get current memory usage in bytes"""
        return self._current_memory

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_items = sum(len(cache) for cache in self._caches.values())
            scope_stats = {
                scope.value: len(cache) for scope, cache in self._caches.items()
            }

            return {
                'total_items': total_items,
                'memory_usage_mb': self._current_memory / (1024 * 1024),
                'scope_breakdown': scope_stats,
                'metadata_count': len(self._metadata)
            }


class SmartFixtureManager:
    """
    Core intelligent fixture management system for GOO-34

    Provides automatic dependency resolution, intelligent caching,
    performance monitoring, and resource optimization.
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        """Singleton pattern for global fixture management"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # Core components
        self.dependency_graph = DependencyGraph()
        self.cache = SmartFixtureCache()
        self.performance_metrics = PerformanceMetrics()

        # Registry of fixture creators
        self._fixture_registry: Dict[str, Callable] = {}
        self._factory_registry: Dict[str, Any] = {}

        # Configuration
        self.max_creation_time_ms = 50.0
        self.enable_parallel_creation = True
        self.enable_lazy_loading = True

        # Internal state
        self._creating_fixtures: Set[str] = set()
        self._creation_lock = threading.RLock()

        logger.info("SmartFixtureManager initialized")

    def register_fixture(
        self,
        name: str,
        creator: Callable,
        scope: FixtureScope = FixtureScope.FUNCTION,
        dependencies: List[str] = None,
        factory_class: str = None
    ):
        """Register a fixture with the smart manager"""
        dependencies = dependencies or []

        # Register the creator
        self._fixture_registry[name] = creator

        # Add dependencies to graph
        for dep in dependencies:
            self.dependency_graph.add_dependency(name, dep)

        # Create metadata
        metadata = FixtureMetadata(
            name=name,
            scope=scope,
            dependencies=dependencies,
            factory_class=factory_class
        )

        logger.debug(f"Registered fixture '{name}' with {len(dependencies)} dependencies")

    def register_factory(self, name: str, factory_class: Any):
        """Register a Factory-Boy factory"""
        self._factory_registry[name] = factory_class
        logger.debug(f"Registered factory '{name}': {factory_class.__name__}")

    def create_fixture(
        self,
        name: str,
        scope: FixtureScope = FixtureScope.FUNCTION,
        force_recreate: bool = False,
        **kwargs
    ) -> Any:
        """
        Create or retrieve a fixture with smart caching and dependency resolution
        """
        start_time = time.time()

        # Import performance monitor here to avoid circular import
        from .performance import performance_monitor

        # Start performance monitoring
        operation_id = performance_monitor.start_fixture_creation(name)

        try:
            # Check cache first (unless forcing recreation)
            if not force_recreate:
                cached_value = self.cache.get(name, scope)
                if cached_value is not None:
                    self.performance_metrics.cache_hits += 1
                    creation_time_ms = (time.time() - start_time) * 1000
                    performance_monitor.end_fixture_creation(
                        name, operation_id, creation_time_ms, was_cache_hit=True
                    )
                    logger.debug(f"Cache hit for fixture '{name}'")
                    return cached_value

            self.performance_metrics.cache_misses += 1

            # Check if fixture is currently being created (avoid infinite loops)
            with self._creation_lock:
                if name in self._creating_fixtures:
                    raise ValueError(f"Circular dependency detected: '{name}' is already being created")
                self._creating_fixtures.add(name)

            try:
                # Resolve and create dependencies first
                dependencies = self.dependency_graph.get_dependencies(name)
                dependency_values = {}

                if dependencies:
                    logger.debug(f"Resolving {len(dependencies)} dependencies for '{name}'")
                    creation_order = self.dependency_graph.resolve_order(dependencies)

                    for dep_name in creation_order:
                        if dep_name not in dependency_values:
                            dependency_values[dep_name] = self.create_fixture(
                                dep_name, scope, force_recreate
                            )

                # Create the fixture
                if name in self._fixture_registry:
                    creator = self._fixture_registry[name]
                    fixture_value = creator(**kwargs, **dependency_values)
                elif name in self._factory_registry:
                    factory = self._factory_registry[name]
                    fixture_value = factory.build(**kwargs)
                else:
                    raise ValueError(f"Unknown fixture '{name}'. Register it first.")

                # Create metadata and cache
                creation_time = (time.time() - start_time) * 1000  # Convert to ms
                metadata = FixtureMetadata(
                    name=name,
                    scope=scope,
                    dependencies=dependencies,
                    creation_time=creation_time,
                    status=FixtureStatus.READY,
                    factory_class=self._factory_registry.get(name, {}).get('__class__', {}).get('__name__')
                )

                self.cache.set(name, fixture_value, metadata)

                # Update performance metrics
                self.performance_metrics.total_fixtures_created += 1
                self.performance_metrics.total_creation_time += creation_time / 1000

                # Update performance monitor
                performance_monitor.end_fixture_creation(
                    name, operation_id, creation_time, was_cache_hit=False
                )

                # Performance warning if creation took too long
                if creation_time > self.max_creation_time_ms:
                    logger.warning(
                        f"Fixture '{name}' creation took {creation_time:.1f}ms "
                        f"(target: <{self.max_creation_time_ms}ms)"
                    )

                logger.debug(f"Created fixture '{name}' in {creation_time:.1f}ms")
                return fixture_value

            finally:
                # Remove from creating set
                with self._creation_lock:
                    self._creating_fixtures.discard(name)

        except Exception as e:
            logger.error(f"Failed to create fixture '{name}': {e}")
            # Update metadata for failed creation
            if name not in self.cache._metadata:
                failed_metadata = FixtureMetadata(
                    name=name,
                    scope=scope,
                    status=FixtureStatus.FAILED
                )
                self.cache._metadata[name] = failed_metadata
            raise

    def create_fixtures(self, names: List[str], **kwargs) -> Dict[str, Any]:
        """Create multiple fixtures with optimal ordering"""
        if not names:
            return {}

        # Resolve creation order
        ordered_names = self.dependency_graph.resolve_order(names)
        results = {}

        for name in ordered_names:
            results[name] = self.create_fixture(name, **kwargs)

        return results

    def cleanup_scope(self, scope: FixtureScope):
        """Clean up all fixtures in a specific scope"""
        start_time = time.time()

        self.cache.clear_scope(scope)

        cleanup_time = time.time() - start_time
        self.performance_metrics.cleanup_time += cleanup_time

        logger.debug(f"Cleaned up scope '{scope.value}' in {cleanup_time*1000:.1f}ms")

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        cache_stats = self.cache.get_cache_stats()

        return {
            'fixtures_created': self.performance_metrics.total_fixtures_created,
            'average_creation_time_ms': self.performance_metrics.average_creation_time * 1000,
            'cache_hit_ratio': self.performance_metrics.cache_hit_ratio,
            'cache_hits': self.performance_metrics.cache_hits,
            'cache_misses': self.performance_metrics.cache_misses,
            'memory_usage_mb': cache_stats['memory_usage_mb'],
            'cleanup_time_ms': self.performance_metrics.cleanup_time * 1000,
            'registered_fixtures': len(self._fixture_registry),
            'registered_factories': len(self._factory_registry),
            'dependency_relationships': len(self.dependency_graph._graph),
            'cache_stats': cache_stats
        }

    def reset(self):
        """Reset the fixture manager (useful for testing)"""
        self.cache = SmartFixtureCache()
        self.performance_metrics = PerformanceMetrics()
        self._fixture_registry.clear()
        self._factory_registry.clear()
        self.dependency_graph = DependencyGraph()
        self._creating_fixtures.clear()

        logger.info("SmartFixtureManager reset")


# Global instance for easy access
smart_fixture_manager = SmartFixtureManager()