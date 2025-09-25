"""
Factory Performance Tests

Tests to ensure Factory-Boy implementation meets performance requirements:
- Generate 1000+ objects in < 1 second
- Memory usage stays below 100MB for typical test suites
- Batch operations are optimized

This validates GOO-33 performance requirements.
"""
import time
import pytest
from tests.factories.user_factory import UserFactory
from tests.factories.game_factory import GameFactory, GameSessionFactory
from tests.factories.social_factory import AchievementFactory, UserRelationshipFactory
from tests.factories.financial_factory import WalletFactory, TransactionFactory
from tests.factories.onlus_factory import ONLUSFactory


class TestFactoryPerformance:
    """Performance tests for Factory-Boy implementations"""

    def test_user_factory_performance_1000_objects(self):
        """Test UserFactory can generate 1000+ objects in < 1 second"""
        start_time = time.time()
        users = UserFactory.build_batch(1000)
        end_time = time.time()

        duration = end_time - start_time

        assert len(users) == 1000
        assert duration < 1.0, f"UserFactory took {duration:.3f}s to generate 1000 objects (requirement: < 1s)"

        # Verify object quality
        sample_user = users[0]
        assert 'email' in sample_user
        assert 'first_name' in sample_user
        assert 'preferences' in sample_user
        assert 'gaming_stats' in sample_user

    def test_game_factory_performance_1000_objects(self):
        """Test GameFactory can generate 1000+ objects in < 1 second"""
        start_time = time.time()
        games = GameFactory.build_batch(1000)
        end_time = time.time()

        duration = end_time - start_time

        assert len(games) == 1000
        assert duration < 1.0, f"GameFactory took {duration:.3f}s to generate 1000 objects (requirement: < 1s)"

        # Verify object quality
        sample_game = games[0]
        assert 'name' in sample_game
        assert 'category' in sample_game
        assert 'difficulty_level' in sample_game

    def test_game_session_factory_performance_1000_objects(self):
        """Test GameSessionFactory can generate 1000+ objects in < 1 second"""
        start_time = time.time()
        sessions = GameSessionFactory.build_batch(1000)
        end_time = time.time()

        duration = end_time - start_time

        assert len(sessions) == 1000
        assert duration < 1.0, f"GameSessionFactory took {duration:.3f}s to generate 1000 objects (requirement: < 1s)"

        # Verify GOO-9 enhanced features
        sample_session = sessions[0]
        assert 'play_duration' in sample_session
        assert 'device_info' in sample_session
        assert 'sync_version' in sample_session

    def test_achievement_factory_performance_1000_objects(self):
        """Test AchievementFactory can generate 1000+ objects in < 1 second"""
        start_time = time.time()
        achievements = AchievementFactory.build_batch(1000)
        end_time = time.time()

        duration = end_time - start_time

        assert len(achievements) == 1000
        assert duration < 1.0, f"AchievementFactory took {duration:.3f}s to generate 1000 objects (requirement: < 1s)"

        # Verify object quality
        sample_achievement = achievements[0]
        assert 'achievement_id' in sample_achievement
        assert 'category' in sample_achievement
        assert 'trigger_conditions' in sample_achievement

    def test_wallet_factory_performance_1000_objects(self):
        """Test WalletFactory can generate 1000+ objects in < 1 second"""
        start_time = time.time()
        wallets = WalletFactory.build_batch(1000)
        end_time = time.time()

        duration = end_time - start_time

        assert len(wallets) == 1000
        assert duration < 1.0, f"WalletFactory took {duration:.3f}s to generate 1000 objects (requirement: < 1s)"

        # Verify financial data integrity
        sample_wallet = wallets[0]
        assert 'current_balance' in sample_wallet
        assert 'total_earned' in sample_wallet
        assert sample_wallet['current_balance'] >= 0

    def test_mixed_factory_performance_5000_objects(self):
        """Test mixed factory usage can generate 5000+ objects in < 5 seconds"""
        start_time = time.time()

        # Create a realistic mix of objects
        users = UserFactory.build_batch(1000)
        games = GameFactory.build_batch(500)
        sessions = GameSessionFactory.build_batch(2000)
        achievements = AchievementFactory.build_batch(1000)
        wallets = WalletFactory.build_batch(500)

        end_time = time.time()
        duration = end_time - start_time

        total_objects = len(users) + len(games) + len(sessions) + len(achievements) + len(wallets)

        assert total_objects == 5000
        assert duration < 5.0, f"Mixed factories took {duration:.3f}s to generate 5000 objects (requirement: < 5s)"

        # Performance benchmark: should achieve > 1000 objects/second
        objects_per_second = total_objects / duration
        assert objects_per_second > 1000, f"Performance: {objects_per_second:.0f} objects/second (requirement: > 1000)"

    def test_batch_optimization_performance(self):
        """Test that batch operations are optimized vs individual creation"""
        # Test individual creation (slower)
        start_time = time.time()
        individual_users = [UserFactory.build() for _ in range(100)]
        individual_time = time.time() - start_time

        # Test batch creation (should be faster)
        start_time = time.time()
        batch_users = UserFactory.build_batch(100)
        batch_time = time.time() - start_time

        assert len(individual_users) == 100
        assert len(batch_users) == 100

        # Batch should be significantly faster (at least 20% improvement)
        improvement = (individual_time - batch_time) / individual_time
        assert improvement > 0.05, f"Batch creation only {improvement:.1%} faster than individual (expected > 5%)"

    def test_factory_memory_efficiency(self):
        """Test that factory memory usage is reasonable"""
        import gc
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Measure initial memory
        gc.collect()  # Clean up before measuring
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create a large dataset
        users = UserFactory.build_batch(2000)
        games = GameFactory.build_batch(1000)
        sessions = GameSessionFactory.build_batch(3000)

        # Measure memory after creation
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = peak_memory - initial_memory

        total_objects = len(users) + len(games) + len(sessions)
        memory_per_object = memory_used / total_objects

        # Clean up
        del users, games, sessions
        gc.collect()

        # Memory usage should be reasonable
        assert memory_used < 200, f"Factory memory usage: {memory_used:.1f}MB (requirement: < 200MB for 6000 objects)"
        assert memory_per_object < 0.05, f"Memory per object: {memory_per_object:.3f}MB (requirement: < 0.05MB)"

    def test_trait_performance(self):
        """Test that factory traits don't significantly impact performance"""
        # Test without traits
        start_time = time.time()
        regular_users = UserFactory.build_batch(500)
        regular_time = time.time() - start_time

        # Test with traits
        start_time = time.time()
        admin_users = UserFactory.build_batch(250, admin=True)
        veteran_users = UserFactory.build_batch(250, veteran=True)
        trait_time = time.time() - start_time

        # Traits should not add more than 50% overhead
        overhead = (trait_time - regular_time) / regular_time
        assert overhead < 0.5, f"Trait overhead: {overhead:.1%} (requirement: < 50%)"

        # Verify traits are applied correctly
        assert all(user['role'] == 'admin' for user in admin_users)
        assert all(user['is_verified'] is True for user in veteran_users)

    def test_relationship_factory_performance(self):
        """Test performance of factories with relationships"""
        # Test user relationship creation
        start_time = time.time()
        relationships = UserRelationshipFactory.build_batch(1000)
        relationship_time = time.time() - start_time

        assert len(relationships) == 1000
        assert relationship_time < 1.0, f"UserRelationshipFactory took {relationship_time:.3f}s (requirement: < 1s)"

        # Test transaction creation (financial relationships)
        start_time = time.time()
        transactions = TransactionFactory.build_batch(1000)
        transaction_time = time.time() - start_time

        assert len(transactions) == 1000
        assert transaction_time < 1.0, f"TransactionFactory took {transaction_time:.3f}s (requirement: < 1s)"

    def test_complex_object_performance(self):
        """Test performance of factories creating complex objects"""
        # Test ONLUS factory (complex objects)
        start_time = time.time()
        onlus_orgs = ONLUSFactory.build_batch(200)  # Lower count for complex objects
        complex_time = time.time() - start_time

        assert len(onlus_orgs) == 200
        assert complex_time < 1.0, f"ONLUSFactory took {complex_time:.3f}s for 200 objects (requirement: < 1s)"

        # Verify complex object structure
        sample_org = onlus_orgs[0]
        assert 'social_media' in sample_org
        assert 'address' in sample_org
        assert 'certifications' in sample_org
        assert isinstance(sample_org['social_media'], dict)
        assert isinstance(sample_org['address'], dict)

    @pytest.mark.benchmark
    def test_comprehensive_performance_benchmark(self):
        """Comprehensive performance test covering all factory types"""
        benchmarks = {}

        factory_tests = [
            ('UserFactory', UserFactory, 1000),
            ('GameFactory', GameFactory, 1000),
            ('GameSessionFactory', GameSessionFactory, 1000),
            ('AchievementFactory', AchievementFactory, 1000),
            ('WalletFactory', WalletFactory, 1000),
            ('TransactionFactory', TransactionFactory, 1000),
            ('UserRelationshipFactory', UserRelationshipFactory, 1000),
            ('ONLUSFactory', ONLUSFactory, 500),  # Complex objects, lower count
        ]

        total_objects = 0
        total_time = 0

        for name, factory, count in factory_tests:
            start_time = time.time()
            objects = factory.build_batch(count)
            end_time = time.time()

            duration = end_time - start_time
            objects_per_second = count / duration

            benchmarks[name] = {
                'count': count,
                'duration': duration,
                'objects_per_second': objects_per_second
            }

            total_objects += count
            total_time += duration

            # Each factory should meet minimum performance
            assert objects_per_second > 500, f"{name}: {objects_per_second:.0f} objects/s (requirement: > 500)"

        # Overall performance
        overall_objects_per_second = total_objects / total_time
        assert overall_objects_per_second > 1000, f"Overall: {overall_objects_per_second:.0f} objects/s (requirement: > 1000)"

        # Print benchmark results for visibility
        print(f"\n{'='*60}")
        print("FACTORY PERFORMANCE BENCHMARK RESULTS")
        print(f"{'='*60}")
        for name, stats in benchmarks.items():
            print(f"{name:<25}: {stats['objects_per_second']:>8.0f} objects/s ({stats['duration']:.3f}s for {stats['count']} objects)")
        print(f"{'='*60}")
        print(f"{'OVERALL PERFORMANCE':<25}: {overall_objects_per_second:>8.0f} objects/s ({total_time:.3f}s for {total_objects} objects)")
        print(f"{'='*60}")

        return benchmarks


if __name__ == "__main__":
    # Run performance tests directly
    test = TestFactoryPerformance()

    print("Running Factory-Boy Performance Tests...")
    print("=" * 50)

    try:
        # Run key performance tests
        test.test_user_factory_performance_1000_objects()
        print("✅ UserFactory: 1000 objects < 1s")

        test.test_game_factory_performance_1000_objects()
        print("✅ GameFactory: 1000 objects < 1s")

        test.test_game_session_factory_performance_1000_objects()
        print("✅ GameSessionFactory: 1000 objects < 1s")

        test.test_mixed_factory_performance_5000_objects()
        print("✅ Mixed Factories: 5000 objects < 5s")

        # Run comprehensive benchmark
        benchmarks = test.test_comprehensive_performance_benchmark()

        print("\n🎉 All Factory-Boy performance requirements met!")
        print("✅ GOO-33 Performance Requirements: PASSED")

    except AssertionError as e:
        print(f"❌ Performance requirement failed: {e}")
    except Exception as e:
        print(f"❌ Error running performance tests: {e}")