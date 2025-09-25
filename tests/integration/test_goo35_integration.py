"""
GOO-35 Integration Test Suite - FASE 5.1
Comprehensive integration testing for all base test classes
Tests cross-module functionality and ecosystem stability
"""
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.core.base_auth_test import BaseAuthTest
from tests.core.base_preferences_test import BasePreferencesTest
from tests.core.base_game_test import BaseGameTest
from tests.core.base_social_test import BaseSocialTest
from tests.core.base_donation_test import BaseDonationTest, DonationLoadTestMixin
from tests.core.base_onlus_test import BaseOnlusTest, OnlusComplianceMixin


class TestGOO35IntegrationSuite:
    """Master integration test suite for all GOO-35 base classes"""

    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.integration_errors = []
        self.start_time = None
        self.end_time = None

    def run_integration_suite(self):
        """Run complete integration test suite"""
        print("🚀 Starting GOO-35 Integration Test Suite (FASE 5.1)")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        self.start_time = time.time()

        # Test individual base classes
        individual_tests = [
            ("BaseAuthTest", self._test_auth_integration),
            ("BasePreferencesTest", self._test_preferences_integration),
            ("BaseGameTest", self._test_game_integration),
            ("BaseSocialTest", self._test_social_integration),
            ("BaseDonationTest", self._test_donation_integration),
            ("BaseOnlusTest", self._test_onlus_integration),
        ]

        print("\n📊 Testing Individual Base Classes:")
        for test_name, test_func in individual_tests:
            try:
                start = time.time()
                result = test_func()
                duration = time.time() - start

                self.test_results[test_name] = result
                self.performance_metrics[test_name] = {
                    'duration': duration,
                    'objects_created': result.get('objects_created', 0),
                    'assertions_run': result.get('assertions_run', 0),
                    'throughput': result.get('objects_created', 0) / duration if duration > 0 else 0
                }

                status = "✅" if result['success'] else "❌"
                print(f"  {status} {test_name}: {duration:.3f}s ({result.get('objects_created', 0)} objects)")

            except Exception as e:
                print(f"  ❌ {test_name}: FAILED - {str(e)}")
                self.integration_errors.append(f"{test_name}: {str(e)}")
                self.test_results[test_name] = {'success': False, 'error': str(e)}

        # Test cross-module integrations
        print("\n🔗 Testing Cross-Module Integrations:")
        cross_module_tests = [
            ("Auth + Preferences", self._test_auth_preferences_integration),
            ("Games + Social", self._test_games_social_integration),
            ("Donations + ONLUS", self._test_donations_onlus_integration),
            ("Full Platform", self._test_full_platform_integration),
        ]

        for test_name, test_func in cross_module_tests:
            try:
                start = time.time()
                result = test_func()
                duration = time.time() - start

                self.test_results[f"Integration_{test_name.replace(' ', '_')}"] = result
                status = "✅" if result['success'] else "❌"
                print(f"  {status} {test_name}: {duration:.3f}s")

            except Exception as e:
                print(f"  ❌ {test_name}: FAILED - {str(e)}")
                self.integration_errors.append(f"{test_name}: {str(e)}")

        self.end_time = time.time()
        return self._generate_integration_report()

    def _test_auth_integration(self):
        """Test BaseAuthTest integration"""
        class TestAuth(BaseAuthTest):
            service_class = Mock

            def integration_test(self):
                # Create user with various scenarios
                user_scenarios = [
                    self.create_test_user(email='admin@test.com', role='admin'),
                    self.create_test_user(email='user@test.com', role='user'),
                    self.create_test_user(email='premium@test.com', role='premium_user')
                ]

                # Test auth scenarios
                for user in user_scenarios:
                    self.mock_successful_login(user)
                    login_tokens = self.mock_jwt_token_generation(user['_id'])

                    # Validate each scenario
                    self.assert_user_valid(user)
                    assert login_tokens['access_token']
                    assert login_tokens['refresh_token']

                return {
                    'success': True,
                    'objects_created': len(user_scenarios) * 3,  # user + 2 tokens each
                    'assertions_run': len(user_scenarios) * 3
                }

        test = TestAuth()
        test.setUp()
        result = test.integration_test()
        test.tearDown()
        return result

    def _test_preferences_integration(self):
        """Test BasePreferencesTest integration"""
        class TestPreferences(BasePreferencesTest):
            service_class = Mock

            def integration_test(self):
                # Create users with different preference patterns
                preference_scenarios = [
                    self.create_test_user_with_preferences(
                        gaming_difficulty='easy',
                        notifications_enabled=True
                    ),
                    self.create_test_user_with_preferences(
                        gaming_difficulty='hard',
                        notifications_enabled=False
                    ),
                    self.create_test_user_with_preferences(
                        theme='dark',
                        privacy_public=True
                    )
                ]

                objects_created = 0
                assertions_run = 0

                for user_data in preference_scenarios:
                    # Test preference operations
                    preferences = self.create_test_preferences(
                        theme='dark',
                        notifications={'email': True, 'sms': False}
                    )

                    # Test preference synchronization
                    sync_result = self.mock_preference_sync_success(
                        user_data['_id'],
                        preferences
                    )

                    # Validations
                    self.assert_preferences_valid(preferences)
                    assert sync_result['synchronized'] is True

                    objects_created += 2  # user + preferences
                    assertions_run += 2

                return {
                    'success': True,
                    'objects_created': objects_created,
                    'assertions_run': assertions_run
                }

        test = TestPreferences()
        test.setUp()
        result = test.integration_test()
        test.tearDown()
        return result

    def _test_game_integration(self):
        """Test BaseGameTest integration"""
        class TestGames(BaseGameTest):
            service_class = Mock

            def integration_test(self):
                # Create diverse game scenarios
                game_scenarios = [
                    self.create_test_game(title='Puzzle Master', category='puzzle', max_players=1),
                    self.create_test_game(title='Battle Arena', category='action', max_players=4),
                    self.create_test_game(title='Strategy Empire', category='strategy', max_players=8)
                ]

                objects_created = len(game_scenarios)
                assertions_run = 0

                for game in game_scenarios:
                    # Create game sessions
                    session = self.create_test_session(
                        game_id=game['_id'],
                        status='active'
                    )

                    # Test multiplayer if applicable
                    if game['max_players'] > 1:
                        mp_session = self.create_multiplayer_session(
                            game_id=game['_id'],
                            players=[str(i) for i in range(min(3, game['max_players']))],
                            max_players=game['max_players']
                        )
                        objects_created += 1
                        self.assert_game_session_valid(mp_session)
                        assertions_run += 1

                    # Test game plugins
                    plugin = self.create_test_game_plugin(
                        name=f"Plugin for {game['title']}",
                        category=game['category']
                    )

                    # Validations
                    self.assert_game_valid(game)
                    self.assert_game_session_valid(session)

                    objects_created += 2  # session + plugin
                    assertions_run += 2

                return {
                    'success': True,
                    'objects_created': objects_created,
                    'assertions_run': assertions_run
                }

        test = TestGames()
        test.setUp()
        result = test.integration_test()
        test.tearDown()
        return result

    def _test_social_integration(self):
        """Test BaseSocialTest integration"""
        class TestSocial(BaseSocialTest):
            service_class = Mock

            def integration_test(self):
                # Create social network scenario
                users = []
                for i in range(5):
                    user = self.create_test_social_user(
                        display_name=f'User {i+1}',
                        level=i + 1
                    )
                    users.append(user)

                objects_created = len(users)
                assertions_run = 0

                # Create friend relationships
                for i in range(len(users)-1):
                    friend_request = self.create_test_friend_request(
                        sender_id=users[i]['_id'],
                        target_id=users[i+1]['_id']
                    )
                    objects_created += 1

                    self.assert_friend_request_valid(friend_request)
                    assertions_run += 1

                # Create achievements
                for user in users:
                    achievement = self.create_test_achievement(
                        name=f'Achievement for {user["display_name"]}',
                        category='social'
                    )
                    objects_created += 1

                    self.assert_achievement_valid(achievement)
                    assertions_run += 1

                # Test social scenarios
                social_scenario = self.create_social_network_scenario(user_count=5)
                self.assert_social_network_valid(social_scenario)
                assertions_run += 1

                return {
                    'success': True,
                    'objects_created': objects_created,
                    'assertions_run': assertions_run
                }

        test = TestSocial()
        test.setUp()
        result = test.integration_test()
        test.tearDown()
        return result

    def _test_donation_integration(self):
        """Test BaseDonationTest integration"""
        class TestDonations(DonationLoadTestMixin, BaseDonationTest):
            service_class = Mock

            def integration_test(self):
                # Create financial ecosystem
                wallets = []
                for i in range(3):
                    wallet = self.create_test_wallet(
                        balance=100.0 + (i * 50),
                        currency='EUR' if i % 2 == 0 else 'USD'
                    )
                    wallets.append(wallet)

                objects_created = len(wallets)
                assertions_run = 0

                # Create transactions for each wallet
                for wallet in wallets:
                    # Earning transaction
                    earning = self.create_test_transaction(
                        wallet_id=wallet['_id'],
                        tx_type='earning',
                        amount=25.0
                    )

                    # Donation transaction
                    donation = self.create_test_transaction(
                        wallet_id=wallet['_id'],
                        tx_type='donation',
                        amount=15.0
                    )

                    objects_created += 2

                    # Validate transactions
                    self.assert_transaction_valid(earning, 'earning', 25.0)
                    self.assert_transaction_valid(donation, 'donation', 15.0)
                    assertions_run += 2

                # Test multi-currency scenario
                multi_currency = self.create_multi_currency_scenario(['EUR', 'USD'])
                objects_created += len(multi_currency['wallets'])

                # Test bulk operations
                bulk_scenario = self.create_bulk_donation_scenario(donor_count=5, onlus_count=2)
                objects_created += len(bulk_scenario['donors']) + len(bulk_scenario['donations'])

                # Test payment gateways
                paypal_payment = self.mock_payment_gateway_success('paypal', 100.0)
                assert paypal_payment['status'] == 'completed'
                assertions_run += 1

                return {
                    'success': True,
                    'objects_created': objects_created,
                    'assertions_run': assertions_run
                }

        test = TestDonations()
        test.setUp()
        result = test.integration_test()
        test.tearDown()
        return result

    def _test_onlus_integration(self):
        """Test BaseOnlusTest integration"""
        class TestOnlus(OnlusComplianceMixin, BaseOnlusTest):
            service_class = Mock

            def integration_test(self):
                # Create ONLUS ecosystem
                onlus_orgs = []
                for i in range(3):
                    onlus = self.create_test_onlus(
                        name=f'ONLUS {i+1}',
                        status='active',
                        categories=['education', 'health'][i % 2:i % 2 + 1]
                    )
                    onlus_orgs.append(onlus)

                objects_created = len(onlus_orgs)
                assertions_run = 0

                # Create campaigns for each ONLUS
                for onlus in onlus_orgs:
                    campaigns = []
                    for j in range(2):  # 2 campaigns per ONLUS
                        campaign = self.create_test_campaign(
                            onlus_id=onlus['_id'],
                            title=f'Campaign {j+1} for {onlus["name"]}',
                            goal=1000.0 + (j * 500)
                        )
                        campaigns.append(campaign)
                        objects_created += 1

                    # Validate ONLUS and campaigns
                    self.assert_onlus_valid(onlus, 'active')
                    assertions_run += 1

                    for campaign in campaigns:
                        self.assert_campaign_valid(campaign, 'active', 1000.0)
                        assertions_run += 1

                # Test verification workflows
                verification_scenario = self.create_verification_scenario('verified')
                verification_result = self.mock_document_verification_success(
                    onlus_orgs[0]['_id'],
                    ['certificate.pdf', 'statute.pdf']
                )

                self.assert_verification_complete(verification_result)
                assertions_run += 1

                # Test compliance
                gdpr_scenario = self.create_gdpr_compliance_scenario()
                assert len(gdpr_scenario['data_subjects']) == 5
                assertions_run += 1

                return {
                    'success': True,
                    'objects_created': objects_created,
                    'assertions_run': assertions_run
                }

        test = TestOnlus()
        test.setUp()
        result = test.integration_test()
        test.tearDown()
        return result

    def _test_auth_preferences_integration(self):
        """Test Auth + Preferences cross-module integration"""
        class TestAuthPrefs(BaseAuthTest, BasePreferencesTest):
            service_class = Mock

            def cross_integration_test(self):
                # Create user with auth and preferences
                user = self.create_test_user(email='integrated@test.com', role='user')

                # Setup authentication
                self.mock_successful_login(user)
                tokens = self.mock_jwt_token_generation(user['_id'])

                # Create user preferences
                preferences = self.create_test_preferences(
                    theme='dark',
                    gaming={'difficulty': 'medium'},
                    notifications={'email_enabled': True}
                )

                # Test preference synchronization with auth
                sync_result = self.mock_preference_sync_success(user['_id'], preferences)

                # Validations
                self.assert_user_valid(user)
                self.assert_preferences_valid(preferences)
                assert tokens['access_token']
                assert sync_result['synchronized'] is True

                return {'success': True, 'cross_module_operations': 4}

        test = TestAuthPrefs()
        test.setUp()
        result = test.cross_integration_test()
        test.tearDown()
        return result

    def _test_games_social_integration(self):
        """Test Games + Social cross-module integration"""
        class TestGamesSocial(BaseGameTest, BaseSocialTest):
            service_class = Mock

            def cross_integration_test(self):
                # Create social users who play games
                users = []
                for i in range(3):
                    user = self.create_test_social_user(
                        display_name=f'Gamer {i+1}',
                        level=i + 1
                    )
                    users.append(user)

                # Create multiplayer game
                game = self.create_test_game(
                    title='Social Multiplayer Game',
                    category='social',
                    max_players=4
                )

                # Create multiplayer session with social users
                session = self.create_multiplayer_session(
                    game_id=game['_id'],
                    players=[user['_id'] for user in users],
                    max_players=4
                )

                # Create social achievements for game completion
                for user in users:
                    achievement = self.create_test_achievement(
                        name=f'Game Master for {user["display_name"]}',
                        category='gaming',
                        user_id=user['_id']
                    )

                # Validations
                self.assert_game_valid(game)
                self.assert_game_session_valid(session)

                for user in users:
                    self.assert_social_user_valid(user)

                return {'success': True, 'cross_module_operations': len(users) + 2}

        test = TestGamesSocial()
        test.setUp()
        result = test.cross_integration_test()
        test.tearDown()
        return result

    def _test_donations_onlus_integration(self):
        """Test Donations + ONLUS cross-module integration"""
        class TestDonationsOnlus(BaseDonationTest, BaseOnlusTest):
            service_class = Mock

            def cross_integration_test(self):
                # Create ONLUS organization
                onlus = self.create_test_onlus(
                    name='Charity Integration Test',
                    status='active',
                    categories=['education']
                )

                # Create campaign
                campaign = self.create_test_campaign(
                    onlus_id=onlus['_id'],
                    title='Help Build Schools',
                    goal=5000.0
                )

                # Create donor wallets
                donors = []
                for i in range(3):
                    wallet = self.create_test_wallet(
                        balance=200.0,
                        currency='EUR'
                    )
                    donors.append(wallet)

                # Process donations to campaign
                total_donated = 0.0
                for wallet in donors:
                    donation = self.create_test_transaction(
                        wallet_id=wallet['_id'],
                        tx_type='donation',
                        amount=50.0,
                        onlus_id=onlus['_id']
                    )

                    # Mock campaign donation processing
                    self.mock_campaign_donation(campaign['_id'], 50.0, wallet['user_id'])
                    total_donated += 50.0

                # Update campaign with donations
                updated_campaign = self.create_test_campaign(
                    onlus_id=onlus['_id'],
                    title='Help Build Schools',
                    goal=5000.0,
                    current_amount=total_donated
                )

                # Validations
                self.assert_onlus_valid(onlus, 'active')
                self.assert_campaign_valid(updated_campaign, 'active', 5000.0)

                for wallet in donors:
                    self.assert_wallet_balance_valid(wallet, 200.0)

                progress = (total_donated / 5000.0) * 100
                assert progress == 3.0  # 150/5000 = 3%

                return {'success': True, 'cross_module_operations': len(donors) + 2}

        test = TestDonationsOnlus()
        test.setUp()
        result = test.cross_integration_test()
        test.tearDown()
        return result

    def _test_full_platform_integration(self):
        """Test full platform integration with all modules"""
        class TestFullPlatform(BaseAuthTest, BasePreferencesTest, BaseGameTest,
                               BaseSocialTest, BaseDonationTest, BaseOnlusTest):
            service_class = Mock

            def full_platform_test(self):
                # Create a user journey across all modules

                # 1. User Authentication
                user = self.create_test_user(email='fulltest@goodplay.com', role='premium_user')
                self.mock_successful_login(user)
                tokens = self.mock_jwt_token_generation(user['_id'])

                # 2. Set User Preferences
                preferences = self.create_test_preferences(
                    theme='dark',
                    gaming={'difficulty': 'hard'},
                    donations={'auto_donate': True}
                )
                self.mock_preference_sync_success(user['_id'], preferences)

                # 3. Create Social Profile
                social_user = self.create_test_social_user(
                    display_name=user['first_name'] + ' ' + user['last_name'],
                    level=5,
                    user_id=user['_id']
                )

                # 4. Play Games
                game = self.create_test_game(title='Full Platform Game', category='adventure')
                session = self.create_test_session(
                    game_id=game['_id'],
                    user_id=user['_id'],
                    status='completed'
                )

                # 5. Earn Credits
                wallet = self.create_test_wallet(
                    user_id=user['_id'],
                    balance=0.0,
                    currency='EUR'
                )

                earning = self.create_test_transaction(
                    wallet_id=wallet['_id'],
                    tx_type='earning',
                    amount=100.0,
                    source='game_completion'
                )

                # 6. Make Donation
                onlus = self.create_test_onlus(
                    name='Full Integration Charity',
                    status='active'
                )

                campaign = self.create_test_campaign(
                    onlus_id=onlus['_id'],
                    title='Full Platform Campaign',
                    goal=10000.0
                )

                donation = self.create_test_transaction(
                    wallet_id=wallet['_id'],
                    tx_type='donation',
                    amount=50.0,
                    onlus_id=onlus['_id']
                )

                # 7. Earn Social Achievement
                achievement = self.create_test_achievement(
                    name='Charitable Gamer',
                    category='special',
                    user_id=user['_id']
                )

                # Cross-module validations
                operations_count = 0

                self.assert_user_valid(user)
                operations_count += 1

                self.assert_preferences_valid(preferences)
                operations_count += 1

                self.assert_social_user_valid(social_user)
                operations_count += 1

                self.assert_game_session_valid(session)
                operations_count += 1

                self.assert_wallet_balance_valid(wallet, 0.0)  # Initial balance
                self.assert_transaction_valid(earning, 'earning', 100.0)
                self.assert_transaction_valid(donation, 'donation', 50.0)
                operations_count += 3

                self.assert_onlus_valid(onlus, 'active')
                self.assert_campaign_valid(campaign, 'active', 10000.0)
                operations_count += 2

                self.assert_achievement_valid(achievement)
                operations_count += 1

                return {
                    'success': True,
                    'cross_module_operations': operations_count,
                    'modules_integrated': 6,
                    'user_journey_complete': True
                }

        test = TestFullPlatform()
        test.setUp()
        result = test.full_platform_test()
        test.tearDown()
        return result

    def _generate_integration_report(self):
        """Generate comprehensive integration test report"""
        total_duration = self.end_time - self.start_time
        successful_tests = len([r for r in self.test_results.values() if r.get('success', False)])
        total_tests = len(self.test_results)

        report = {
            'summary': {
                'total_duration': total_duration,
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                'integration_errors': len(self.integration_errors)
            },
            'performance_metrics': self.performance_metrics,
            'test_results': self.test_results,
            'errors': self.integration_errors
        }

        return report


# Performance Testing Suite
class GOO35PerformanceSuite:
    """Performance benchmarking for GOO-35 Testing Utilities"""

    def __init__(self):
        self.performance_results = {}

    def run_performance_benchmarks(self):
        """Run comprehensive performance benchmarks"""
        print("\n🏃‍♂️ Running Performance Benchmarks (FASE 5.2)")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        benchmarks = [
            ("Object Creation Speed", self._benchmark_object_creation),
            ("Memory Usage", self._benchmark_memory_usage),
            ("Concurrent Operations", self._benchmark_concurrent_operations),
            ("Bulk Operations", self._benchmark_bulk_operations),
            ("Builder Performance", self._benchmark_builder_performance)
        ]

        for benchmark_name, benchmark_func in benchmarks:
            print(f"\n📊 {benchmark_name}:")
            try:
                result = benchmark_func()
                self.performance_results[benchmark_name] = result

                if 'operations_per_second' in result:
                    print(f"  ⚡ {result['operations_per_second']:.0f} ops/sec")
                if 'avg_time_ms' in result:
                    print(f"  ⏱️  {result['avg_time_ms']:.2f}ms average")
                if 'memory_mb' in result:
                    print(f"  💾 {result['memory_mb']:.1f}MB memory")

            except Exception as e:
                print(f"  ❌ {benchmark_name} failed: {str(e)}")
                self.performance_results[benchmark_name] = {'error': str(e)}

        return self.performance_results

    def _benchmark_object_creation(self):
        """Benchmark object creation speed across all base classes"""
        operations = 0
        start_time = time.time()

        # Test each base class
        test_classes = [
            (BaseAuthTest, Mock),
            (BasePreferencesTest, Mock),
            (BaseGameTest, Mock),
            (BaseSocialTest, Mock),
            (BaseDonationTest, Mock),
            (BaseOnlusTest, Mock)
        ]

        for base_class, service_class in test_classes:
            class TestClass(base_class):
                service_class = service_class

                def create_objects(self):
                    count = 0
                    if hasattr(self, 'create_test_user'):
                        for i in range(50):
                            self.create_test_user(email=f'perf{i}@test.com')
                            count += 1

                    if hasattr(self, 'create_test_game'):
                        for i in range(50):
                            self.create_test_game(title=f'Game {i}')
                            count += 1

                    if hasattr(self, 'create_test_wallet'):
                        for i in range(50):
                            self.create_test_wallet(balance=float(i * 10))
                            count += 1

                    return count

            test = TestClass()
            test.setUp()
            operations += test.create_objects()
            test.tearDown()

        duration = time.time() - start_time
        ops_per_second = operations / duration if duration > 0 else 0

        return {
            'total_operations': operations,
            'duration': duration,
            'operations_per_second': ops_per_second,
            'avg_time_ms': (duration / operations) * 1000 if operations > 0 else 0
        }

    def _benchmark_memory_usage(self):
        """Benchmark memory usage of base classes"""
        import psutil
        import gc

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create large number of objects
        class TestMemory(BaseDonationTest, BaseOnlusTest):
            service_class = Mock

            def create_many_objects(self):
                objects = []

                # Create 1000 wallets
                for i in range(1000):
                    wallet = self.create_test_wallet(balance=float(i))
                    objects.append(wallet)

                # Create 1000 ONLUS
                for i in range(1000):
                    onlus = self.create_test_onlus(name=f'ONLUS {i}')
                    objects.append(onlus)

                return objects

        test = TestMemory()
        test.setUp()
        objects = test.create_many_objects()

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = peak_memory - initial_memory

        # Cleanup
        del objects
        test.tearDown()
        gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_freed = peak_memory - final_memory

        return {
            'initial_memory_mb': initial_memory,
            'peak_memory_mb': peak_memory,
            'memory_used_mb': memory_used,
            'memory_freed_mb': memory_freed,
            'memory_efficiency': (memory_freed / memory_used) * 100 if memory_used > 0 else 0
        }

    def _benchmark_concurrent_operations(self):
        """Benchmark concurrent operations"""
        def create_objects_concurrently(thread_id):
            class ConcurrentTest(BaseDonationTest):
                service_class = Mock

                def create_batch(self):
                    results = []
                    for i in range(10):
                        wallet = self.create_test_wallet(
                            balance=float(i * 10),
                            currency='EUR'
                        )
                        transaction = self.create_test_transaction(
                            wallet_id=wallet['_id'],
                            amount=float(i * 5)
                        )
                        results.extend([wallet, transaction])
                    return len(results)

            test = ConcurrentTest()
            test.setUp()
            count = test.create_batch()
            test.tearDown()
            return count

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_objects_concurrently, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]

        duration = time.time() - start_time
        total_operations = sum(results)
        ops_per_second = total_operations / duration if duration > 0 else 0

        return {
            'concurrent_threads': 10,
            'total_operations': total_operations,
            'duration': duration,
            'operations_per_second': ops_per_second,
            'thread_efficiency': ops_per_second / 10  # ops per thread per second
        }

    def _benchmark_bulk_operations(self):
        """Benchmark bulk operations"""
        class BulkTest(BaseDonationTest):
            service_class = Mock

            def bulk_operations(self):
                start = time.time()

                # Bulk donation scenario
                bulk_scenario = self.create_bulk_donation_scenario(
                    donor_count=100,
                    onlus_count=10
                )

                bulk_time = time.time() - start

                # Multi-currency scenario
                start = time.time()
                multi_currency = self.create_multi_currency_scenario(
                    ['EUR', 'USD', 'GBP', 'JPY', 'CHF']
                )
                currency_time = time.time() - start

                return {
                    'bulk_donations': len(bulk_scenario['donations']),
                    'bulk_time': bulk_time,
                    'currency_wallets': len(multi_currency['wallets']),
                    'currency_time': currency_time
                }

        test = BulkTest()
        test.setUp()
        results = test.bulk_operations()
        test.tearDown()

        total_time = results['bulk_time'] + results['currency_time']
        total_objects = results['bulk_donations'] + results['currency_wallets']

        return {
            'total_objects_created': total_objects,
            'total_time': total_time,
            'objects_per_second': total_objects / total_time if total_time > 0 else 0,
            'bulk_scenario_efficiency': results['bulk_donations'] / results['bulk_time'] if results['bulk_time'] > 0 else 0
        }

    def _benchmark_builder_performance(self):
        """Benchmark builder pattern performance"""
        from tests.utils.builders import UserBuilder, BaseBuilder

        start_time = time.time()

        # Test builder creation speed
        builders_created = 0
        for i in range(1000):
            builder = UserBuilder()
            user = builder.with_email(f'user{i}@test.com').with_name(f'User', f'{i}').build()
            builders_created += 1

        duration = time.time() - start_time
        builders_per_second = builders_created / duration if duration > 0 else 0

        return {
            'builders_created': builders_created,
            'duration': duration,
            'builders_per_second': builders_per_second,
            'avg_build_time_ms': (duration / builders_created) * 1000 if builders_created > 0 else 0
        }


if __name__ == "__main__":
    # Run Integration Suite
    integration_suite = TestGOO35IntegrationSuite()
    integration_report = integration_suite.run_integration_suite()

    # Run Performance Benchmarks
    performance_suite = GOO35PerformanceSuite()
    performance_results = performance_suite.run_performance_benchmarks()

    # Combined Results Summary
    print("\n" + "="*80)
    print("🎯 FASE 5.1 & 5.2 RESULTS SUMMARY")
    print("="*80)

    print(f"\n📊 Integration Test Results:")
    summary = integration_report['summary']
    print(f"  ✅ Success Rate: {summary['success_rate']:.1f}% ({summary['successful_tests']}/{summary['total_tests']})")
    print(f"  ⏱️  Total Duration: {summary['total_duration']:.2f}s")
    print(f"  🔗 Integration Errors: {summary['integration_errors']}")

    print(f"\n🏃‍♂️ Performance Benchmark Results:")
    for benchmark_name, results in performance_results.items():
        if 'error' not in results:
            if 'operations_per_second' in results:
                print(f"  ⚡ {benchmark_name}: {results['operations_per_second']:.0f} ops/sec")

    print(f"\n🏆 FASE 5.1 & 5.2: INTEGRATION & PERFORMANCE TESTING COMPLETED!")