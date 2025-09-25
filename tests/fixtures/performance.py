"""
Performance Monitoring and Optimization for Smart Fixtures - GOO-34

Advanced performance monitoring, memory tracking, and optimization
capabilities for the intelligent fixture system.
"""
import time
import threading
import weakref

# Try to import psutil, fall back to basic memory tracking
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
from typing import Dict, List, Any, Optional, Callable, NamedTuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager
import logging
import os

logger = logging.getLogger('smart_fixtures.performance')


@dataclass
class PerformanceThresholds:
    """Performance thresholds for monitoring and alerting"""
    max_creation_time_ms: float = 50.0
    max_memory_usage_mb: float = 100.0
    max_cleanup_time_ms: float = 10.0
    min_cache_hit_ratio: float = 0.8
    max_parallel_fixtures: int = 10


@dataclass
class FixturePerformanceData:
    """Performance data for individual fixtures"""
    name: str
    creation_count: int = 0
    total_creation_time_ms: float = 0.0
    min_creation_time_ms: float = float('inf')
    max_creation_time_ms: float = 0.0
    memory_usage_bytes: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    last_created: Optional[datetime] = None
    dependency_count: int = 0

    @property
    def average_creation_time_ms(self) -> float:
        """Calculate average creation time"""
        return (self.total_creation_time_ms / self.creation_count
                if self.creation_count > 0 else 0.0)

    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio for this fixture"""
        total_accesses = self.cache_hits + self.cache_misses
        return (self.cache_hits / total_accesses) if total_accesses > 0 else 0.0


class MemoryTracker:
    """Memory usage tracking for fixtures"""

    def __init__(self):
        if HAS_PSUTIL:
            self._process = psutil.Process(os.getpid())
            self._baseline_memory = self._get_current_memory()
        else:
            self._process = None
            self._baseline_memory = 0

        self._peak_memory = self._baseline_memory
        self._fixture_memory: Dict[str, int] = {}
        self._lock = threading.RLock()

    def _get_current_memory(self) -> int:
        """Get current memory usage in bytes"""
        if HAS_PSUTIL and self._process:
            return self._process.memory_info().rss
        else:
            # Fallback: rough estimate based on tracked fixtures
            return sum(self._fixture_memory.values())

    def track_fixture_memory(self, fixture_name: str, memory_delta: int):
        """Track memory usage for a specific fixture"""
        with self._lock:
            self._fixture_memory[fixture_name] = memory_delta
            current_memory = self._get_current_memory()
            if current_memory > self._peak_memory:
                self._peak_memory = current_memory

    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        return self._get_current_memory() / (1024 * 1024)

    def get_peak_memory_mb(self) -> float:
        """Get peak memory usage in MB"""
        return self._peak_memory / (1024 * 1024)

    def get_memory_overhead_mb(self) -> float:
        """Get memory overhead from baseline in MB"""
        current = self._get_current_memory()
        return (current - self._baseline_memory) / (1024 * 1024)

    def get_fixture_memory_breakdown(self) -> Dict[str, float]:
        """Get memory breakdown by fixture in MB"""
        with self._lock:
            return {
                name: memory_bytes / (1024 * 1024)
                for name, memory_bytes in self._fixture_memory.items()
            }

    def reset_baseline(self):
        """Reset memory baseline"""
        self._baseline_memory = self._get_current_memory()


class PerformanceProfiler:
    """Profiling and timing utilities for fixtures"""

    def __init__(self):
        self._active_timers: Dict[str, float] = {}
        self._lock = threading.RLock()

    @contextmanager
    def time_operation(self, operation_name: str):
        """Context manager for timing operations"""
        start_time = time.perf_counter()
        with self._lock:
            self._active_timers[operation_name] = start_time

        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            with self._lock:
                self._active_timers.pop(operation_name, None)

            logger.debug(f"Operation '{operation_name}' took {duration_ms:.2f}ms")

    def profile_fixture_creation(self, fixture_name: str, creation_func: Callable) -> Any:
        """Profile fixture creation and return result with timing"""
        memory_before = 0
        if HAS_PSUTIL:
            memory_before = psutil.Process(os.getpid()).memory_info().rss

        start_time = time.perf_counter()

        try:
            result = creation_func()
            return result
        finally:
            end_time = time.perf_counter()
            memory_after = 0
            if HAS_PSUTIL:
                memory_after = psutil.Process(os.getpid()).memory_info().rss

            duration_ms = (end_time - start_time) * 1000
            memory_delta = memory_after - memory_before

            logger.debug(
                f"Fixture '{fixture_name}': {duration_ms:.2f}ms, "
                f"Memory delta: {memory_delta/1024 if memory_delta > 0 else 0:.1f}KB"
            )


class PerformanceOptimizer:
    """Automatic performance optimization for fixtures"""

    def __init__(self, thresholds: PerformanceThresholds):
        self.thresholds = thresholds
        self._optimization_suggestions: List[str] = []
        self._slow_fixtures: Dict[str, float] = {}

    def analyze_fixture_performance(
        self,
        performance_data: Dict[str, FixturePerformanceData]
    ) -> Dict[str, List[str]]:
        """Analyze fixture performance and suggest optimizations"""
        suggestions = {
            'slow_fixtures': [],
            'memory_heavy': [],
            'low_cache_hit': [],
            'optimization_tips': []
        }

        for name, data in performance_data.items():
            # Check creation time
            if data.average_creation_time_ms > self.thresholds.max_creation_time_ms:
                suggestions['slow_fixtures'].append(
                    f"{name}: {data.average_creation_time_ms:.1f}ms avg"
                )
                self._slow_fixtures[name] = data.average_creation_time_ms

            # Check memory usage
            memory_mb = data.memory_usage_bytes / (1024 * 1024)
            if memory_mb > 10:  # 10MB per fixture is quite heavy
                suggestions['memory_heavy'].append(f"{name}: {memory_mb:.1f}MB")

            # Check cache hit ratio
            if (data.cache_hits + data.cache_misses > 5 and
                data.cache_hit_ratio < self.thresholds.min_cache_hit_ratio):
                suggestions['low_cache_hit'].append(
                    f"{name}: {data.cache_hit_ratio:.1%} hit ratio"
                )

        # Generate optimization tips
        if suggestions['slow_fixtures']:
            suggestions['optimization_tips'].append(
                "Consider using lazy loading for slow fixtures"
            )
            suggestions['optimization_tips'].append(
                "Review Factory-Boy factory complexity"
            )

        if suggestions['memory_heavy']:
            suggestions['optimization_tips'].append(
                "Consider using function scope instead of session/module scope"
            )
            suggestions['optimization_tips'].append(
                "Implement memory cleanup for heavy fixtures"
            )

        if suggestions['low_cache_hit']:
            suggestions['optimization_tips'].append(
                "Review fixture dependencies and scoping"
            )
            suggestions['optimization_tips'].append(
                "Consider increasing cache scope for frequently used fixtures"
            )

        return suggestions

    def auto_optimize_fixture_scope(
        self,
        fixture_name: str,
        performance_data: FixturePerformanceData
    ) -> Optional[str]:
        """Suggest optimal scope for a fixture based on usage patterns"""
        if performance_data.creation_count < 2:
            return None  # Not enough data

        cache_ratio = performance_data.cache_hit_ratio
        creation_time = performance_data.average_creation_time_ms

        if cache_ratio > 0.8 and creation_time > 20:
            return "session"  # High reuse, slow creation -> session scope

        if cache_ratio < 0.5 and creation_time < 10:
            return "function"  # Low reuse, fast creation -> function scope

        if 0.5 <= cache_ratio <= 0.8:
            return "class"  # Medium reuse -> class scope

        return None  # Current scope is probably fine


class SmartFixturePerformanceMonitor:
    """
    Comprehensive performance monitoring for smart fixtures
    """

    def __init__(self, thresholds: PerformanceThresholds = None):
        self.thresholds = thresholds or PerformanceThresholds()
        self.memory_tracker = MemoryTracker()
        self.profiler = PerformanceProfiler()
        self.optimizer = PerformanceOptimizer(self.thresholds)

        self._fixture_data: Dict[str, FixturePerformanceData] = {}
        self._session_start_time = time.time()
        self._lock = threading.RLock()

        # Alerts and warnings
        self._alerts: List[str] = []
        self._performance_warnings = 0

    def start_fixture_creation(self, fixture_name: str) -> str:
        """Start monitoring fixture creation"""
        operation_id = f"{fixture_name}_{time.time()}"

        with self._lock:
            if fixture_name not in self._fixture_data:
                self._fixture_data[fixture_name] = FixturePerformanceData(name=fixture_name)

        return operation_id

    def end_fixture_creation(
        self,
        fixture_name: str,
        operation_id: str,
        creation_time_ms: float,
        memory_delta: int = 0,
        was_cache_hit: bool = False
    ):
        """End monitoring fixture creation and record metrics"""
        with self._lock:
            data = self._fixture_data[fixture_name]
            data.last_created = datetime.now(timezone.utc)

            if was_cache_hit:
                data.cache_hits += 1
            else:
                data.cache_misses += 1
                data.creation_count += 1
                data.total_creation_time_ms += creation_time_ms
                data.memory_usage_bytes += memory_delta

                # Update min/max times
                data.min_creation_time_ms = min(data.min_creation_time_ms, creation_time_ms)
                data.max_creation_time_ms = max(data.max_creation_time_ms, creation_time_ms)

                # Track memory
                if memory_delta > 0:
                    self.memory_tracker.track_fixture_memory(fixture_name, memory_delta)

                # Performance warnings
                if creation_time_ms > self.thresholds.max_creation_time_ms:
                    self._add_performance_warning(
                        f"Fixture '{fixture_name}' creation took {creation_time_ms:.1f}ms "
                        f"(threshold: {self.thresholds.max_creation_time_ms}ms)"
                    )

    def record_dependency(self, fixture_name: str, dependency_name: str):
        """Record a dependency relationship"""
        with self._lock:
            if fixture_name in self._fixture_data:
                self._fixture_data[fixture_name].dependency_count += 1

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        with self._lock:
            total_fixtures = len(self._fixture_data)
            total_creations = sum(data.creation_count for data in self._fixture_data.values())
            total_cache_hits = sum(data.cache_hits for data in self._fixture_data.values())
            total_cache_misses = sum(data.cache_misses for data in self._fixture_data.values())

            overall_cache_ratio = (
                total_cache_hits / (total_cache_hits + total_cache_misses)
                if (total_cache_hits + total_cache_misses) > 0 else 0.0
            )

            # Get optimization suggestions
            suggestions = self.optimizer.analyze_fixture_performance(self._fixture_data)

            # Performance status
            performance_status = self._get_performance_status()

            session_duration = time.time() - self._session_start_time

            return {
                'session_duration_seconds': session_duration,
                'total_fixtures_registered': total_fixtures,
                'total_fixture_creations': total_creations,
                'overall_cache_hit_ratio': overall_cache_ratio,
                'cache_hits': total_cache_hits,
                'cache_misses': total_cache_misses,
                'memory_usage_mb': self.memory_tracker.get_memory_usage_mb(),
                'peak_memory_mb': self.memory_tracker.get_peak_memory_mb(),
                'memory_overhead_mb': self.memory_tracker.get_memory_overhead_mb(),
                'performance_warnings': self._performance_warnings,
                'performance_status': performance_status,
                'alerts': self._alerts,
                'optimization_suggestions': suggestions,
                'fixture_breakdown': {
                    name: {
                        'creation_count': data.creation_count,
                        'avg_creation_time_ms': data.average_creation_time_ms,
                        'cache_hit_ratio': data.cache_hit_ratio,
                        'memory_usage_mb': data.memory_usage_bytes / (1024 * 1024),
                        'dependency_count': data.dependency_count
                    }
                    for name, data in self._fixture_data.items()
                },
                'thresholds': {
                    'max_creation_time_ms': self.thresholds.max_creation_time_ms,
                    'max_memory_usage_mb': self.thresholds.max_memory_usage_mb,
                    'min_cache_hit_ratio': self.thresholds.min_cache_hit_ratio
                }
            }

    def _get_performance_status(self) -> str:
        """Get overall performance status"""
        memory_mb = self.memory_tracker.get_memory_usage_mb()

        if memory_mb > self.thresholds.max_memory_usage_mb:
            return "MEMORY_WARNING"

        if self._performance_warnings > 5:
            return "PERFORMANCE_WARNING"

        total_cache_hits = sum(data.cache_hits for data in self._fixture_data.values())
        total_cache_misses = sum(data.cache_misses for data in self._fixture_data.values())
        cache_ratio = (total_cache_hits / (total_cache_hits + total_cache_misses)
                      if (total_cache_hits + total_cache_misses) > 0 else 1.0)

        if cache_ratio < self.thresholds.min_cache_hit_ratio:
            return "CACHE_WARNING"

        return "OPTIMAL"

    def _add_performance_warning(self, message: str):
        """Add a performance warning"""
        self._performance_warnings += 1
        self._alerts.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        logger.warning(message)

        # Keep only last 20 alerts to prevent memory bloat
        if len(self._alerts) > 20:
            self._alerts = self._alerts[-20:]

    def reset_metrics(self):
        """Reset all performance metrics"""
        with self._lock:
            self._fixture_data.clear()
            self._alerts.clear()
            self._performance_warnings = 0
            self._session_start_time = time.time()
            self.memory_tracker.reset_baseline()

    def export_performance_data(self, format: str = 'json') -> str:
        """Export performance data in specified format"""
        report = self.get_performance_report()

        if format.lower() == 'json':
            import json
            return json.dumps(report, indent=2, default=str)

        elif format.lower() == 'csv':
            import io
            import csv

            output = io.StringIO()
            writer = csv.writer(output)

            # Write headers
            writer.writerow([
                'fixture_name', 'creation_count', 'avg_creation_time_ms',
                'cache_hit_ratio', 'memory_usage_mb', 'dependency_count'
            ])

            # Write data
            for name, data in report['fixture_breakdown'].items():
                writer.writerow([
                    name, data['creation_count'], data['avg_creation_time_ms'],
                    data['cache_hit_ratio'], data['memory_usage_mb'], data['dependency_count']
                ])

            return output.getvalue()

        else:
            raise ValueError(f"Unsupported format: {format}")


# Global performance monitor instance
performance_monitor = SmartFixturePerformanceMonitor()