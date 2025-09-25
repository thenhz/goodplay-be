# GOO-35 Testing Utilities - Developer Guide

**Version**: 1.0.0
**Last Updated**: December 2024

---

## 🚀 Quick Start Guide

### Installation & Setup

GOO-35 Testing Utilities are already integrated into the GoodPlay platform. No additional installation required!

### Basic Usage Pattern

```python
from tests.core.base_auth_test import BaseAuthTest
from app.core.services.auth_service import AuthService

class TestMyAuthFeature(BaseAuthTest):
    service_class = AuthService  # Set your service class

    def test_user_login(self):
        # Create test user with 1 line instead of 20+
        user = self.create_test_user(email='test@example.com', role='admin')

        # Mock successful login with 1 line instead of 10+
        self.mock_successful_login(user)

        # Test your service
        result = self.service.login(user['email'], 'password')

        # Validate with business-focused assertions
        self.assert_auth_response_success(result, expected_tokens=True)
```

**That's it!** You just reduced 40+ lines of boilerplate to 8 lines of focused business logic.

---

## 📚 Base Classes Reference

### Core Testing Classes

| Base Class | Purpose | Key Features | Boilerplate Reduction |
|------------|---------|--------------|----------------------|
| `BaseAuthTest` | Authentication & Users | JWT, bcrypt, user lifecycle | 85%+ |
| `BasePreferencesTest` | User Preferences | Sync, conflicts, defaults | 80%+ |
| `BaseGameTest` | Game Engine | Plugins, sessions, multiplayer | 90%+ |
| `BaseSocialTest` | Social Features | Friends, achievements, leaderboards | 85%+ |
| `BaseDonationTest` | Financial System | Wallets, payments, multi-currency | 90%+ |
| `BaseOnlusTest` | Non-Profit Orgs | ONLUS, campaigns, compliance | 85%+ |

---

## 🔧 Detailed Usage Examples

### 1. Authentication Testing (BaseAuthTest)

```python
from tests.core.base_auth_test import BaseAuthTest
from app.core.services.auth_service import AuthService

class TestAuthService(BaseAuthTest):
    service_class = AuthService

    def test_user_registration_success(self):
        """Test successful user registration"""
        # Create user data with realistic defaults
        user_data = self.create_test_user(
            email='newuser@example.com',
            role='user',
            preferences={'theme': 'dark'}
        )

        # Mock successful registration scenario
        self.mock_registration_scenario('success')

        # Execute service call
        success, message, result = self.service.register_user(user_data)

        # Business-focused validation
        self.assert_auth_response_success((success, message, result), expected_tokens=True)
        self.assert_user_valid(result['user'])

    def test_multiple_user_roles(self):
        """Test different user roles"""
        def role_test():
            user = self.create_test_user()
            return self.service.validate_permissions(user)

        # Test all roles automatically
        results = self.test_auth_scenarios(role_test, [
            'admin', 'user', 'premium_user', 'moderator'
        ])

        # All scenarios should succeed
        assert all(results.values())

    def test_jwt_token_lifecycle(self):
        """Test complete JWT token lifecycle"""
        user = self.create_test_user(role='admin')

        # Generate tokens
        tokens = self.mock_jwt_token_generation(user['_id'])

        # Validate token structure
        self.assert_jwt_tokens_valid(tokens)

        # Test token refresh
        new_tokens = self.mock_jwt_token_refresh(tokens['refresh_token'])
        self.assert_jwt_tokens_valid(new_tokens)
```

**Key Features:**
- **Automatic mocking**: User repository, JWT service, bcrypt
- **Role-based testing**: Admin, user, premium user scenarios
- **JWT utilities**: Token generation, validation, refresh
- **Business assertions**: `assert_auth_response_success()`, `assert_user_valid()`

### 2. Game Engine Testing (BaseGameTest)

```python
from tests.core.base_game_test import BaseGameTest
from app.games.core.plugin_manager import PluginManager

class TestGamePlugin(BaseGameTest):
    service_class = PluginManager

    def test_plugin_lifecycle(self):
        """Test complete plugin lifecycle"""
        # Create game plugin with realistic data
        plugin = self.create_test_game_plugin(
            name='Puzzle Master',
            category='puzzle',
            max_players=1
        )

        # Mock plugin registration
        self.mock_plugin_registration_success(plugin)

        # Test plugin loading
        self.mock_plugin_loading_success(plugin)

        # Validate plugin structure
        self.assert_game_plugin_valid(plugin)

    def test_multiplayer_session(self):
        """Test multiplayer game session"""
        # Create multiplayer game
        game = self.create_test_game(
            title='Battle Arena',
            category='action',
            max_players=4
        )

        # Create multiplayer session
        session = self.create_multiplayer_session(
            game_id=game['_id'],
            players=['user1', 'user2', 'user3'],
            max_players=4
        )

        # Test session state synchronization
        self.mock_state_synchronization_success(session['session_id'])

        # Validate multiplayer setup
        self.assert_game_session_valid(session)
        assert len(session['players']) == 3

    def test_enhanced_session_management(self):
        """Test Enhanced Session Management (GOO-9) features"""
        session = self.create_test_session(status='active')

        # Test precise time tracking
        time_data = {
            'play_duration_ms': 125750,  # 2 minutes, 5.75 seconds
            'pause_duration_ms': 15250,  # 15.25 seconds
            'precision': 'millisecond'
        }
        self.mock_precise_time_tracking(session['session_id'], time_data)

        # Test pause/resume cycle
        pause_data = {'status': 'paused', 'pause_reason': 'user_requested'}
        resume_data = {'status': 'active', 'pause_duration_ms': 300000}
        self.mock_session_pause_resume(session['session_id'], pause_data, resume_data)

        # Validate enhanced features
        assert time_data['precision'] == 'millisecond'
        assert resume_data['pause_duration_ms'] == 300000
```

**Key Features:**
- **Plugin system testing**: Registration, loading, lifecycle
- **Session management**: Single-player, multiplayer, state sync
- **Enhanced Session Management**: GOO-9 integration, precise timing
- **Performance testing**: Built-in load testing utilities

### 3. Financial Testing (BaseDonationTest)

```python
from tests.core.base_donation_test import BaseDonationTest, DonationLoadTestMixin
from app.donations.services.wallet_service import WalletService

class TestWalletOperations(DonationLoadTestMixin, BaseDonationTest):
    service_class = WalletService

    def test_multi_currency_donations(self):
        """Test multi-currency donation scenario"""
        # Create multi-currency scenario with 1 line
        scenario = self.create_multi_currency_scenario(['EUR', 'USD', 'GBP'])

        # Process donations in different currencies
        for currency, wallet in scenario['wallets'].items():
            donation = self.create_test_transaction(
                wallet_id=wallet['_id'],
                tx_type='donation',
                amount=50.0,
                currency=currency
            )

            # Validate transaction
            self.assert_transaction_valid(donation, 'donation', 50.0)
            self.assert_wallet_balance_valid(wallet)

    def test_payment_gateway_integration(self):
        """Test payment gateway integration"""
        # Mock PayPal payment
        paypal_result = self.mock_payment_gateway_success('paypal', 100.0)
        assert paypal_result['status'] == 'completed'
        assert paypal_result['gateway'] == 'paypal'

        # Mock Stripe payment
        stripe_result = self.mock_payment_gateway_success('stripe', 200.0)
        assert stripe_result['status'] == 'completed'

        # Test payment failure
        error = self.mock_payment_gateway_failure('paypal', 'insufficient_funds')
        assert error['error_code'] == 'insufficient_funds'

    def test_bulk_donation_processing(self):
        """Test high-volume donation processing"""
        # Create bulk scenario: 100 donors, 10 ONLUS
        bulk = self.create_bulk_donation_scenario(donor_count=100, onlus_count=10)

        # Validate bulk structure
        assert len(bulk['donors']) == 100
        assert len(bulk['donations']) == 100
        assert len(bulk['onlus_list']) == 10

        # Test concurrent donations (using mixin)
        concurrent = self.simulate_concurrent_donations(user_count=50, donation_amount=25.0)
        assert len(concurrent) == 50

    def test_transaction_history(self):
        """Test wallet with transaction history"""
        # Create wallet with complex history in 1 line
        wallet_with_history = self.create_wallet_with_history(
            user_id='user123',
            transactions_count=20
        )

        # Validate history structure
        assert 'transactions' in wallet_with_history
        assert len(wallet_with_history['transactions']) == 20

        # Check transaction types
        earnings = [tx for tx in wallet_with_history['transactions'] if tx['type'] == 'earning']
        donations = [tx for tx in wallet_with_history['transactions'] if tx['type'] == 'donation']

        assert len(earnings) == 10  # Half earnings
        assert len(donations) == 10  # Half donations
```

**Key Features:**
- **Multi-currency support**: EUR, USD, GBP, JPY, etc.
- **Payment gateways**: PayPal, Stripe integration mocking
- **Bulk operations**: High-volume donation scenarios
- **Load testing**: Concurrent operations with `DonationLoadTestMixin`
- **Financial assertions**: Balance validation, transaction verification

### 4. ONLUS Testing (BaseOnlusTest)

```python
from tests.core.base_onlus_test import BaseOnlusTest, OnlusComplianceMixin
from app.onlus.services.onlus_service import OnlusService

class TestOnlusManagement(OnlusComplianceMixin, BaseOnlusTest):
    service_class = OnlusService

    def test_onlus_verification_workflow(self):
        """Test complete ONLUS verification process"""
        # Create ONLUS with pending verification
        onlus = self.create_test_onlus(
            name='Charity Foundation',
            status='pending',
            verification_status='pending'
        )

        # Mock document verification
        docs = ['certificate.pdf', 'statute.pdf', 'tax_document.pdf']
        verification = self.mock_document_verification_success(onlus['_id'], docs)

        # Mock tax ID validation (Italian)
        tax_result = self.mock_tax_id_validation(onlus['tax_id'], valid=True)

        # Mock bank account validation (IBAN)
        bank_result = self.mock_bank_account_validation(onlus['bank_account']['iban'], valid=True)

        # Validate complete workflow
        self.assert_onlus_valid(onlus, 'pending')
        self.assert_verification_complete(verification)
        assert tax_result['valid'] is True
        assert bank_result['valid'] is True

    def test_campaign_lifecycle_management(self):
        """Test campaign from creation to completion"""
        onlus = self.create_test_onlus(status='active')

        # Create campaign lifecycle scenario
        lifecycle = self.create_campaign_lifecycle_scenario()

        # Test each stage
        for stage, campaign in lifecycle['campaigns'].items():
            self.assert_campaign_valid(campaign)
            assert campaign['status'] == stage

        # Test campaign completion
        completed_campaign = lifecycle['campaigns']['funded']
        assert completed_campaign['current_amount'] == completed_campaign['goal_amount']

    def test_gdpr_compliance(self):
        """Test GDPR compliance scenarios (using mixin)"""
        # Create GDPR compliance scenario
        gdpr = self.create_gdpr_compliance_scenario()

        # Validate data subjects
        assert len(gdpr['data_subjects']) == 5

        for subject in gdpr['data_subjects']:
            assert subject['consent_given'] is True
            assert 'email' in subject
            assert 'consent_date' in subject
            assert 'data_categories' in subject

        # Test tax reporting compliance
        onlus = gdpr['onlus']
        donations = [{'amount': 5000.0} for _ in range(10)]  # €50,000 total

        compliance = self.validate_tax_reporting_compliance(onlus, donations)
        assert compliance['requires_detailed_reporting'] is True
        assert compliance['total_donations'] == 50000.0

    def test_multi_campaign_onlus(self):
        """Test ONLUS with multiple campaigns"""
        # Create ONLUS with 5 campaigns in 1 line
        scenario = self.create_multi_campaign_onlus(campaign_count=5)

        onlus = scenario['onlus']
        campaigns = scenario['campaigns']

        # Validate structure
        assert len(campaigns) == 5
        assert scenario['active_campaigns'] == 5
        assert scenario['total_goal'] > 0

        # Each campaign should belong to the ONLUS
        for campaign in campaigns:
            assert campaign['onlus_id'] == onlus['_id']
            self.assert_campaign_valid(campaign, 'active')
```

**Key Features:**
- **Italian compliance**: Tax ID, IBAN validation, document verification
- **GDPR compliance**: Data subject management, consent tracking
- **Campaign management**: Complete lifecycle from creation to completion
- **Verification workflows**: Document, bank account, tax ID validation
- **Compliance mixins**: `OnlusComplianceMixin` for regulatory testing

---

## 🎯 Advanced Usage Patterns

### 1. Cross-Module Integration Testing

```python
from tests.core.base_auth_test import BaseAuthTest
from tests.core.base_donation_test import BaseDonationTest
from tests.core.base_onlus_test import BaseOnlusTest

class TestFullUserJourney(BaseAuthTest, BaseDonationTest, BaseOnlusTest):
    service_class = PlatformService

    def test_complete_donation_journey(self):
        """Test complete user journey: Auth → Earn Credits → Donate"""

        # 1. User Authentication
        user = self.create_test_user(email='donor@example.com', role='premium_user')
        self.mock_successful_login(user)

        # 2. User Earns Credits (from gaming)
        wallet = self.create_test_wallet(user_id=user['_id'], balance=0.0)
        earning = self.create_test_transaction(
            wallet_id=wallet['_id'],
            tx_type='earning',
            amount=100.0
        )

        # 3. Create ONLUS and Campaign
        onlus = self.create_test_onlus(name='Education Foundation', status='active')
        campaign = self.create_test_campaign(onlus_id=onlus['_id'], goal=10000.0)

        # 4. Process Donation
        donation = self.create_test_transaction(
            wallet_id=wallet['_id'],
            tx_type='donation',
            amount=50.0,
            onlus_id=onlus['_id']
        )

        # 5. Validate Complete Journey
        self.assert_user_valid(user)
        self.assert_wallet_balance_valid(wallet, 0.0)
        self.assert_transaction_valid(earning, 'earning', 100.0)
        self.assert_transaction_valid(donation, 'donation', 50.0)
        self.assert_onlus_valid(onlus, 'active')
        self.assert_campaign_valid(campaign, 'active', 10000.0)
```

### 2. Performance Testing with Mixins

```python
from tests.core.base_donation_test import BaseDonationTest, DonationLoadTestMixin
from tests.core.base_onlus_test import BaseOnlusTest, OnlusComplianceMixin

class TestHighVolumeOperations(DonationLoadTestMixin, OnlusComplianceMixin,
                               BaseDonationTest, BaseOnlusTest):
    service_class = BulkOperationService

    def test_platform_scale_operations(self):
        """Test platform at scale"""

        # Bulk donations: 1000 donors → 50 ONLUS
        bulk_donations = self.create_bulk_donation_scenario(
            donor_count=1000,
            onlus_count=50
        )

        # Concurrent operations: 200 simultaneous donations
        concurrent_ops = self.simulate_concurrent_donations(
            user_count=200,
            donation_amount=25.0
        )

        # ONLUS discovery: 500 organizations
        discovery = self.create_onlus_discovery_scenario(count=500)

        # Compliance testing at scale
        gdpr_scenario = self.create_gdpr_compliance_scenario()

        # Validate performance under load
        assert len(bulk_donations['donations']) == 1000
        assert len(concurrent_ops) == 200
        assert len(discovery['onlus_list']) == 500
        assert len(gdpr_scenario['data_subjects']) == 5

        # All operations should complete without errors
        print(f"✅ Processed {len(bulk_donations['donations']) + len(concurrent_ops)} operations successfully")
```

### 3. Custom Assertions and Utilities

```python
class TestCustomValidations(BaseAuthTest, BaseDonationTest):
    service_class = CustomService

    def test_custom_business_logic(self):
        """Test custom business logic with custom assertions"""

        # Create complex scenario
        user = self.create_test_user(role='premium_user')
        wallet = self.create_test_wallet(user_id=user['_id'], balance=500.0)

        # Custom validation method
        self.assert_premium_user_benefits(user, wallet)

    def assert_premium_user_benefits(self, user, wallet):
        """Custom assertion for premium user benefits"""
        # User should have premium role
        assert user['role'] == 'premium_user'

        # Wallet should have bonus balance
        assert float(wallet['balance']) >= 100.0

        # User should have premium preferences
        if 'preferences' in user:
            assert user['preferences'].get('premium_features', False)

        # Custom logging
        print(f"✅ Premium user {user['email']} validated with €{wallet['balance']} balance")
```

---

## 🛠️ Builder Pattern Deep Dive

### Available Builders

```python
from tests.utils.builders import UserBuilder, BaseBuilder

# User Builder with fluent interface
user = (UserBuilder()
        .with_email('advanced@example.com')
        .with_name('Advanced', 'User')
        .with_role('admin')
        .with_preferences({'theme': 'dark'})
        .build())

# Base Builder for custom objects
custom_object = (BaseBuilder()
                 .with_field('custom_field', 'custom_value')
                 .with_timestamps()
                 .with_id()  # Auto-generate ObjectId
                 .build())

# Batch operations
users = UserBuilder().build_batch(100)  # Create 100 users efficiently
```

### Factory-Boy Integration

```python
from tests.utils.builders import UserBuilder

# Use with Factory-Boy (if available)
user = (UserBuilder()
        .with_factory(UserFactory, 'premium', 'verified')  # Use factory with traits
        .with_email('factory@example.com')  # Override specific fields
        .build())
```

---

## 🔍 Debugging and Troubleshooting

### Common Issues and Solutions

#### 1. Service Class Not Injected
```python
class TestMyService(BaseAuthTest):
    service_class = None  # ❌ Wrong - service won't be injected

    # ✅ Correct
    service_class = MyService
```

#### 2. Missing Required Fields
```python
# ❌ Wrong - missing required fields
user = self.create_test_user()
result = self.service.register_user(user['email'])  # Missing password

# ✅ Correct - use complete user data
user = self.create_test_user(email='test@example.com')
result = self.service.register_user(user)  # Pass complete user object
```

#### 3. Assertion Method Not Found
```python
# ❌ Wrong - assertion method doesn't exist
self.assert_user_registration_valid(result)  # Method doesn't exist

# ✅ Correct - use available assertion
self.assert_auth_response_success(result, expected_tokens=True)
```

### Debug Mode

Enable debug logging to see what's happening:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

class TestWithDebug(BaseAuthTest):
    service_class = AuthService

    def test_with_debugging(self):
        # Enable debug output
        self.debug_mode = True  # If available

        user = self.create_test_user()
        print(f"Created user: {user}")  # Manual debugging

        result = self.service.login(user['email'], 'password')
        print(f"Login result: {result}")
```

---

## 📊 Performance Optimization Tips

### 1. Use Batch Operations

```python
# ❌ Slow - individual creation
users = []
for i in range(100):
    user = self.create_test_user(email=f'user{i}@example.com')
    users.append(user)

# ✅ Fast - batch creation
users = UserBuilder().build_batch(100)
```

### 2. Minimize Mock Setup

```python
# ❌ Excessive mocking
class TestWithTooManyMocks(BaseAuthTest):
    def setUp(self):
        super().setUp()
        # Don't add unnecessary mocks - base class handles it
        self.extra_mock1 = Mock()
        self.extra_mock2 = Mock()
        # ... etc

# ✅ Let base class handle mocking
class TestOptimized(BaseAuthTest):
    service_class = AuthService  # That's all you need!
```

### 3. Use Load Testing Mixins

```python
# ✅ Use mixins for performance testing
from tests.core.base_donation_test import DonationLoadTestMixin

class TestPerformance(DonationLoadTestMixin, BaseDonationTest):
    def test_high_volume(self):
        # Use built-in performance utilities
        concurrent_ops = self.simulate_concurrent_donations(user_count=1000)
        assert len(concurrent_ops) == 1000
```

---

## 📋 Best Practices Checklist

### ✅ Test Class Setup
- [ ] Inherit from appropriate base class
- [ ] Set `service_class` to your service
- [ ] Use descriptive class and method names
- [ ] Include docstrings for complex tests

### ✅ Test Data Creation
- [ ] Use `create_test_*` methods instead of manual data
- [ ] Leverage builder patterns for complex scenarios
- [ ] Use realistic test data (proper emails, names, etc.)
- [ ] Create minimal but sufficient test data

### ✅ Mocking and Assertions
- [ ] Use `mock_*` methods for scenario setup
- [ ] Use `assert_*` methods for business validation
- [ ] Test both success and failure scenarios
- [ ] Avoid testing implementation details

### ✅ Performance Considerations
- [ ] Use batch operations for large datasets
- [ ] Minimize unnecessary mocking
- [ ] Use load testing mixins for performance tests
- [ ] Clean up resources in tearDown if needed

### ✅ Code Organization
- [ ] Group related tests in the same class
- [ ] Use descriptive method names that explain what's being tested
- [ ] Keep tests focused on single responsibility
- [ ] Use helper methods for repeated logic

---

## 🆘 Need Help?

### Documentation Resources

1. **This Developer Guide** - Comprehensive usage examples
2. **Migration Report** - Technical details and architecture
3. **API Reference** - Complete method documentation
4. **Integration Tests** - Real examples in `/tests/integration/`

### Common Use Cases

- **Authentication Testing** → Use `BaseAuthTest`
- **Game Development** → Use `BaseGameTest`
- **Financial Features** → Use `BaseDonationTest`
- **Social Features** → Use `BaseSocialTest`
- **ONLUS Management** → Use `BaseOnlusTest`
- **User Preferences** → Use `BasePreferencesTest`

### Performance Expectations

- **Object Creation**: 40,000+ objects/second
- **Test Execution**: Sub-millisecond for simple tests
- **Memory Usage**: Optimized for large test suites
- **Concurrent Operations**: 200+ simultaneous operations supported

---

*Happy testing with GOO-35! 🚀*