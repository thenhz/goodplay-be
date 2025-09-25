"""
Smart Cleanup and Rollback System for GOO-34

Automatic cleanup, rollback mechanisms, and resource management
for intelligent fixture system.
"""
import weakref
import threading
import time
import gc
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import logging

logger = logging.getLogger('smart_fixtures.cleanup')


class CleanupStrategy(Enum):
    """Different cleanup strategies for fixtures"""
    IMMEDIATE = "immediate"    # Clean up immediately after test
    LAZY = "lazy"             # Clean up when memory pressure detected
    SCOPE_BASED = "scope"     # Clean up when scope ends
    REFERENCE_BASED = "ref"   # Clean up when no references remain
    MANUAL = "manual"         # Manual cleanup only


class RollbackStrategy(Enum):
    """Rollback strategies for fixture state"""
    SNAPSHOT = "snapshot"     # Take snapshot and restore
    RECREATE = "recreate"     # Recreate fixture from scratch
    INCREMENTAL = "incremental"  # Track changes and reverse them
    NO_ROLLBACK = "none"      # No rollback capability


@dataclass
class CleanupAction:
    """Represents a cleanup action to be performed"""
    name: str
    action: Callable
    priority: int = 0  # Higher priority = executed first
    strategy: CleanupStrategy = CleanupStrategy.IMMEDIATE
    description: str = ""


@dataclass
class RollbackSnapshot:
    """Snapshot of fixture state for rollback"""
    fixture_name: str
    timestamp: float
    state_data: Any
    strategy: RollbackStrategy
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResourceTracker:
    """Track resource usage and cleanup requirements"""

    def __init__(self):
        self._tracked_resources: Dict[str, Dict[str, Any]] = {}
        self._resource_locks: Dict[str, threading.Lock] = {}
        self._lock = threading.RLock()

    def track_resource(
        self,
        fixture_name: str,
        resource_type: str,
        resource_id: Any,
        cleanup_func: Callable = None
    ):
        """Track a resource used by a fixture"""
        with self._lock:
            if fixture_name not in self._tracked_resources:
                self._tracked_resources[fixture_name] = {}

            self._tracked_resources[fixture_name][resource_type] = {
                'resource_id': resource_id,
                'cleanup_func': cleanup_func,
                'created_at': time.time(),
                'access_count': 0
            }

    def access_resource(self, fixture_name: str, resource_type: str):
        """Record resource access"""
        with self._lock:
            if (fixture_name in self._tracked_resources and
                resource_type in self._tracked_resources[fixture_name]):
                self._tracked_resources[fixture_name][resource_type]['access_count'] += 1

    def get_fixture_resources(self, fixture_name: str) -> Dict[str, Any]:
        """Get all resources for a fixture"""
        with self._lock:
            return self._tracked_resources.get(fixture_name, {}).copy()

    def cleanup_fixture_resources(self, fixture_name: str):
        """Clean up all resources for a fixture"""
        with self._lock:
            if fixture_name not in self._tracked_resources:
                return

            resources = self._tracked_resources[fixture_name]
            cleanup_errors = []

            for resource_type, resource_info in resources.items():
                cleanup_func = resource_info.get('cleanup_func')
                if cleanup_func:
                    try:
                        cleanup_func()
                        logger.debug(f"Cleaned up {resource_type} for {fixture_name}")
                    except Exception as e:
                        cleanup_errors.append(f"{resource_type}: {e}")

            del self._tracked_resources[fixture_name]

            if cleanup_errors:
                logger.warning(f"Cleanup errors for {fixture_name}: {cleanup_errors}")

    def get_resource_summary(self) -> Dict[str, Any]:
        """Get summary of tracked resources"""
        with self._lock:
            total_fixtures = len(self._tracked_resources)
            total_resources = sum(len(resources) for resources in self._tracked_resources.values())

            resource_types = {}
            for resources in self._tracked_resources.values():
                for resource_type in resources.keys():
                    resource_types[resource_type] = resource_types.get(resource_type, 0) + 1

            return {
                'total_fixtures_with_resources': total_fixtures,
                'total_resources': total_resources,
                'resource_type_breakdown': resource_types
            }


class SmartCleanupManager:
    """
    Intelligent cleanup and rollback management system
    """

    def __init__(self):
        self.resource_tracker = ResourceTracker()

        # Cleanup registry
        self._cleanup_actions: Dict[str, List[CleanupAction]] = {}
        self._global_cleanup_actions: List[CleanupAction] = []

        # Rollback system
        self._snapshots: Dict[str, RollbackSnapshot] = {}
        self._rollback_enabled_fixtures: Set[str] = set()

        # Weak references for automatic cleanup
        self._weak_references: Dict[str, weakref.ref] = {}

        # Configuration
        self.memory_pressure_threshold_mb = 80.0
        self.automatic_gc_enabled = True
        self.cleanup_batch_size = 10

        # State
        self._lock = threading.RLock()
        self._cleanup_in_progress = False

    def register_cleanup_action(
        self,
        fixture_name: str,
        action_name: str,
        cleanup_func: Callable,
        priority: int = 0,
        strategy: CleanupStrategy = CleanupStrategy.IMMEDIATE
    ):
        """Register a cleanup action for a fixture"""
        action = CleanupAction(
            name=action_name,
            action=cleanup_func,
            priority=priority,
            strategy=strategy,
            description=f"Cleanup action for {fixture_name}"
        )

        with self._lock:
            if fixture_name not in self._cleanup_actions:
                self._cleanup_actions[fixture_name] = []

            self._cleanup_actions[fixture_name].append(action)

            # Sort by priority (higher first)
            self._cleanup_actions[fixture_name].sort(key=lambda x: x.priority, reverse=True)

        logger.debug(f"Registered cleanup action '{action_name}' for '{fixture_name}'")

    def register_global_cleanup(
        self,
        action_name: str,
        cleanup_func: Callable,
        priority: int = 0
    ):
        """Register a global cleanup action"""
        action = CleanupAction(
            name=action_name,
            action=cleanup_func,
            priority=priority,
            description="Global cleanup action"
        )

        self._global_cleanup_actions.append(action)
        self._global_cleanup_actions.sort(key=lambda x: x.priority, reverse=True)

    def enable_rollback(
        self,
        fixture_name: str,
        strategy: RollbackStrategy = RollbackStrategy.SNAPSHOT
    ):
        """Enable rollback capability for a fixture"""
        with self._lock:
            self._rollback_enabled_fixtures.add(fixture_name)

        logger.debug(f"Enabled {strategy.value} rollback for '{fixture_name}'")

    def take_snapshot(self, fixture_name: str, fixture_value: Any) -> str:
        """Take a snapshot of fixture state for rollback"""
        if fixture_name not in self._rollback_enabled_fixtures:
            return None

        import copy

        try:
            # Deep copy the fixture value for snapshot
            state_data = copy.deepcopy(fixture_value)

            snapshot = RollbackSnapshot(
                fixture_name=fixture_name,
                timestamp=time.time(),
                state_data=state_data,
                strategy=RollbackStrategy.SNAPSHOT
            )

            snapshot_id = f"{fixture_name}_{snapshot.timestamp}"

            with self._lock:
                self._snapshots[snapshot_id] = snapshot

            logger.debug(f"Took snapshot '{snapshot_id}' for '{fixture_name}'")
            return snapshot_id

        except Exception as e:
            logger.warning(f"Failed to take snapshot for '{fixture_name}': {e}")
            return None

    def rollback_fixture(self, fixture_name: str, snapshot_id: str = None) -> Optional[Any]:
        """Rollback fixture to previous state"""
        with self._lock:
            if snapshot_id:
                if snapshot_id not in self._snapshots:
                    logger.error(f"Snapshot '{snapshot_id}' not found")
                    return None
                snapshot = self._snapshots[snapshot_id]
            else:
                # Find latest snapshot for fixture
                fixture_snapshots = [
                    snap for snap in self._snapshots.values()
                    if snap.fixture_name == fixture_name
                ]

                if not fixture_snapshots:
                    logger.error(f"No snapshots found for '{fixture_name}'")
                    return None

                snapshot = max(fixture_snapshots, key=lambda x: x.timestamp)

            logger.info(f"Rolling back '{fixture_name}' to snapshot from {snapshot.timestamp}")
            return snapshot.state_data

    def cleanup_fixture(
        self,
        fixture_name: str,
        strategy: CleanupStrategy = None
    ) -> Dict[str, Any]:
        """Clean up a specific fixture"""
        start_time = time.time()
        cleanup_results = {
            'fixture_name': fixture_name,
            'actions_executed': 0,
            'errors': [],
            'cleanup_time_ms': 0
        }

        with self._lock:
            if self._cleanup_in_progress:
                logger.warning(f"Cleanup already in progress, skipping {fixture_name}")
                return cleanup_results

            self._cleanup_in_progress = True

        try:
            # Get cleanup actions for fixture
            actions = self._cleanup_actions.get(fixture_name, [])

            if strategy:
                actions = [action for action in actions if action.strategy == strategy]

            # Execute cleanup actions
            for action in actions:
                try:
                    action.action()
                    cleanup_results['actions_executed'] += 1
                    logger.debug(f"Executed cleanup action '{action.name}' for '{fixture_name}'")
                except Exception as e:
                    error_msg = f"Action '{action.name}' failed: {e}"
                    cleanup_results['errors'].append(error_msg)
                    logger.error(error_msg)

            # Clean up tracked resources
            self.resource_tracker.cleanup_fixture_resources(fixture_name)

            # Remove snapshots
            snapshot_ids_to_remove = [
                snap_id for snap_id, snap in self._snapshots.items()
                if snap.fixture_name == fixture_name
            ]
            for snap_id in snapshot_ids_to_remove:
                del self._snapshots[snap_id]

            # Remove cleanup actions
            self._cleanup_actions.pop(fixture_name, None)

            # Remove weak reference
            self._weak_references.pop(fixture_name, None)

        finally:
            with self._lock:
                self._cleanup_in_progress = False

            cleanup_results['cleanup_time_ms'] = (time.time() - start_time) * 1000

        logger.debug(
            f"Cleaned up '{fixture_name}' in {cleanup_results['cleanup_time_ms']:.1f}ms "
            f"({cleanup_results['actions_executed']} actions)"
        )

        return cleanup_results

    def cleanup_scope(
        self,
        scope: str,
        fixture_names: List[str] = None
    ) -> Dict[str, Any]:
        """Clean up all fixtures in a scope"""
        if fixture_names is None:
            fixture_names = list(self._cleanup_actions.keys())

        start_time = time.time()
        total_results = {
            'scope': scope,
            'fixtures_cleaned': 0,
            'total_actions': 0,
            'total_errors': 0,
            'cleanup_time_ms': 0,
            'fixture_results': {}
        }

        # Batch cleanup for performance
        batches = [
            fixture_names[i:i + self.cleanup_batch_size]
            for i in range(0, len(fixture_names), self.cleanup_batch_size)
        ]

        for batch in batches:
            for fixture_name in batch:
                result = self.cleanup_fixture(fixture_name)
                total_results['fixture_results'][fixture_name] = result
                total_results['fixtures_cleaned'] += 1
                total_results['total_actions'] += result['actions_executed']
                total_results['total_errors'] += len(result['errors'])

        # Execute global cleanup actions
        for action in self._global_cleanup_actions:
            try:
                action.action()
                total_results['total_actions'] += 1
            except Exception as e:
                total_results['total_errors'] += 1
                logger.error(f"Global cleanup action '{action.name}' failed: {e}")

        # Force garbage collection if enabled
        if self.automatic_gc_enabled:
            gc.collect()

        total_results['cleanup_time_ms'] = (time.time() - start_time) * 1000

        logger.info(
            f"Scope cleanup '{scope}': {total_results['fixtures_cleaned']} fixtures, "
            f"{total_results['total_actions']} actions, "
            f"{total_results['cleanup_time_ms']:.1f}ms"
        )

        return total_results

    @contextmanager
    def cleanup_context(self, fixture_name: str):
        """Context manager for automatic cleanup"""
        try:
            yield
        finally:
            self.cleanup_fixture(fixture_name)

    def check_memory_pressure(self) -> bool:
        """Check if memory pressure cleanup is needed"""
        try:
            import psutil
            memory_usage_mb = psutil.Process().memory_info().rss / (1024 * 1024)
            return memory_usage_mb > self.memory_pressure_threshold_mb
        except:
            return False

    def emergency_cleanup(self):
        """Emergency cleanup when memory pressure is detected"""
        logger.warning("Memory pressure detected, performing emergency cleanup")

        # Clean up least recently used fixtures first
        fixture_names = list(self._cleanup_actions.keys())

        # Simple LRU cleanup - remove fixtures without recent snapshots
        fixtures_to_cleanup = []
        current_time = time.time()

        for fixture_name in fixture_names:
            # Check if fixture has recent snapshots
            recent_snapshots = [
                snap for snap in self._snapshots.values()
                if (snap.fixture_name == fixture_name and
                    current_time - snap.timestamp < 300)  # 5 minutes
            ]

            if not recent_snapshots:
                fixtures_to_cleanup.append(fixture_name)

        # Clean up identified fixtures
        for fixture_name in fixtures_to_cleanup:
            self.cleanup_fixture(fixture_name, CleanupStrategy.LAZY)

        # Force aggressive garbage collection
        gc.collect()

        logger.info(f"Emergency cleanup completed: {len(fixtures_to_cleanup)} fixtures cleaned")

    def get_cleanup_status(self) -> Dict[str, Any]:
        """Get cleanup system status"""
        with self._lock:
            return {
                'fixtures_with_cleanup': len(self._cleanup_actions),
                'total_cleanup_actions': sum(len(actions) for actions in self._cleanup_actions.values()),
                'global_cleanup_actions': len(self._global_cleanup_actions),
                'rollback_enabled_fixtures': len(self._rollback_enabled_fixtures),
                'snapshots_stored': len(self._snapshots),
                'tracked_resources': self.resource_tracker.get_resource_summary(),
                'memory_pressure_threshold_mb': self.memory_pressure_threshold_mb,
                'cleanup_in_progress': self._cleanup_in_progress
            }


# Global cleanup manager instance
cleanup_manager = SmartCleanupManager()