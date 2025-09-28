# 🏗️ GoodPlay Backend Architecture Documentation

## 📋 Overview

The GoodPlay Backend is a Flask-based REST API using MongoDB, designed with a modular architecture following Repository Pattern, Service Layer, and Event-Driven design principles. This document provides a comprehensive technical overview of the system architecture, initialization flow, and component interactions.

## 🚀 Application Startup Sequence

### 1. **Entry Point** (`app.py`)

```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
```

### 2. **Application Factory** (`app/__init__.py`)

The startup follows this precise sequence:

#### 2.1 **Core Flask Setup**
```python
def create_app(config_name=None):
    # 1. Environment detection
    config_name = os.environ.get('FLASK_ENV', 'default')

    # 2. Flask app instantiation
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 3. JWT initialization
    jwt.init_app(app)

    # 4. CORS configuration
    CORS(app, origins=app.config['CORS_ORIGINS'])
```

#### 2.2 **Database Initialization**
```python
def init_db(app):
    # 1. MongoDB client connection
    mongo_client = MongoClient(app.config['MONGO_URI'])
    mongo_db = mongo_client[app.config['MONGO_DB_NAME']]

    # 2. Core repository index creation
    user_repo = UserRepository()
    user_repo.create_indexes()
```

#### 2.3 **Logging Setup**
```python
def init_logging(app):
    # 1. File handler configuration (production)
    # 2. Log level setting
    # 3. Formatter application
```

### 3. **Module Registration Sequence**

The modules are registered in this specific order to handle dependencies:

#### 3.1 **Core Modules** (No dependencies)
```python
# Auth and User management
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(preferences_blueprint)  # User preferences
```

#### 3.2 **Social Module** (Depends on Core)
```python
# Social features and Impact Score system
register_social_module(app)
```

**Social Module Initialization** (`app/social/__init__.py`):
1. **Blueprint Registration**:
   - `social_bp` → `/api/social`
   - `leaderboards_bp` → `/api/social`
   - `social_challenges_bp` → `/api/social/challenges`

2. **Achievement System**:
   - `achievement_bp` → `/api/achievements`
   - Default achievements initialization
   - Achievement repository indexes

3. **Database Index Creation**:
   - RelationshipRepository
   - ImpactScoreRepository
   - LeaderboardRepository
   - Social challenge repositories (4 total)

4. **Event Hook Registration**:
   ```python
   from .leaderboards.integration.hooks import register_integration_hooks
   with app.app_context():
       register_integration_hooks()
   ```

#### 3.3 **Games Module** (Depends on Core + Social for hooks)
```python
# Game engine and session management
games_bp = create_games_blueprint()
app.register_blueprint(games_bp)

# Game modes system
modes_bp = create_modes_blueprint()
app.register_blueprint(modes_bp)

# Challenge system
challenges_bp = create_challenges_blueprint()
app.register_blueprint(challenges_bp)

# Teams and tournaments
teams_bp = create_teams_blueprint()
app.register_blueprint(teams_bp)
```

**Games Module Initialization** (`app/games/__init__.py`):
```python
def init_games_module():
    # 1. Database indexes
    game_repo = GameRepository()
    session_repo = GameSessionRepository()
    game_repo.create_indexes()
    session_repo.create_indexes()

    # 2. Mode system initialization
    mode_manager = ModeManager()
    mode_manager.initialize_system()

    # 3. Plugin discovery and loading
    discovered_plugins = plugin_manager.discover_plugins()
```

#### 3.4 **Health Check Registration**
```python
@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'healthy', 'message': 'API is running'}, 200
```

## 🏛️ Modular Architecture

### 📊 Module Structure

Each module follows the same architectural pattern:

```
app/{module}/
├── models/          # Data models and validation
├── repositories/    # Data access layer
├── services/        # Business logic layer
├── controllers/     # HTTP request handlers
└── __init__.py      # Module registration
```

### 🔗 Dependency Hierarchy

```mermaid
graph TD
    A[Core Module] --> B[Social Module]
    A --> C[Preferences Module]
    B --> D[Games Module]
    A --> D
    B --> E[Donations Module]
    A --> E
    D --> E
    B --> F[ONLUS Module]
    A --> F
    E --> F
    A --> G[Admin Module]
    B --> G
    D --> G
    E --> G
```

### 📋 Module Responsibilities

#### **Core Module** (`app/core/`)
- **Purpose**: Foundation services and authentication
- **Components**:
  - User management and authentication
  - JWT token handling
  - Base repository and service classes
  - Utility functions and decorators
- **Database Collections**: `users`, `configs`
- **Dependencies**: None (foundation layer)

#### **Social Module** (`app/social/`)
- **Purpose**: Social features and gamification
- **Components**:
  - User relationships and friendships
  - Impact Score system and leaderboards
  - Achievement engine and badge system
  - Social challenges and competitions
- **Database Collections**:
  - `user_relationships`
  - `user_impact_scores`
  - `leaderboards`
  - `achievements`, `user_achievements`
  - `social_challenges`
- **Dependencies**: Core (for users and auth)

#### **Games Module** (`app/games/`)
- **Purpose**: Game engine and session management
- **Components**:
  - Game plugin system
  - Session management with sync
  - Game modes and scheduling
  - Direct challenges (1v1, NvN)
  - Global teams and tournaments
  - Universal scoring system
- **Database Collections**:
  - `games`, `game_sessions`
  - `game_modes`, `mode_schedules`
  - `challenges`, `challenge_participants`
  - `global_teams`, `team_members`, `tournaments`
- **Dependencies**: Core (users), Social (impact score hooks)

#### **Donations Module** (`app/donations/`) - **GOO-15 Implementation**
- **Purpose**: Virtual wallet, payment processing, and donation management
- **Components**:
  - Virtual wallet system with credit conversion
  - Payment processing and provider integration
  - Donation workflow and receipt generation
  - Transaction reconciliation and compliance
  - Financial analytics and admin dashboard
  - Batch processing for high-volume operations
- **Database Collections**:
  - `wallets` - User virtual wallets and balances
  - `transactions` - Financial transaction records
  - `conversion_rates` - Credit conversion rates and multipliers
  - `payment_providers` - External payment provider configs
  - `payment_intents` - Payment processing records
  - `batch_operations` - Batch processing operations
  - `batch_donations` - Batch donation records
- **Dependencies**: Core (users, auth), Social (credit earning hooks)

#### **Other Modules** (Future implementation)
- **ONLUS**: Charity organization management
- **Admin**: Administrative interface and controls

## 🎯 Design Patterns

### 🏗️ Repository Pattern

**Base Repository** (`app/core/repositories/base_repository.py`):
```python
class BaseRepository:
    def __init__(self, collection_name: str)
    def find_by_id(self, id: str) → Optional[Dict]
    def find_all(self, filter: Dict = None) → List[Dict]
    def create(self, data: Dict) → str
    def update(self, id: str, data: Dict) → bool
    def delete(self, id: str) → bool
    def create_indexes(self) → None  # Abstract method
```

**Implementation Example**:
```python
class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__('users')

    def find_by_email(self, email: str) → Optional[User]
    def create_indexes(self):
        # MongoDB index creation
        self.collection.create_index([('email', 1)], unique=True)
```

### 🔧 Service Layer Pattern

**Base Service Structure**:
```python
class BaseService:
    def __init__(self, repository: BaseRepository)

    # Standard return format: Tuple[bool, str, Optional[Dict]]
    def method_name(self, params) → Tuple[bool, str, Optional[Dict]]:
        try:
            # 1. Validation
            validation_error = self._validate_input(params)
            if validation_error:
                return False, validation_error, None

            # 2. Business logic
            result = self._execute_business_logic(params)

            # 3. Logging
            current_app.logger.info(f"Operation successful")
            return True, "SUCCESS_MESSAGE", result

        except Exception as e:
            current_app.logger.error(f"Operation failed: {str(e)}")
            return False, "ERROR_MESSAGE", None
```

### 🎮 Controller Pattern

**Base Controller Structure**:
```python
@blueprint.route('/endpoint', methods=['POST'])
@auth_required
def endpoint_handler(current_user):
    try:
        # 1. Input validation
        data = request.get_json()
        if not data:
            return error_response("DATA_REQUIRED")

        # 2. Service call
        success, message, result = service.method(data)

        # 3. Response formatting
        if success:
            return success_response(message, result)
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f"Endpoint error: {str(e)}")
        return error_response("INTERNAL_SERVER_ERROR", status_code=500)
```

### 🪝 Event-Driven Pattern

**Hook System Architecture**:
```python
# 1. Event Registration (at startup)
hook_manager.register_hook('event_name', handler_function)

# 2. Event Triggering (in controllers)
trigger_event_name(user_id, event_data)

# 3. Event Processing (automatic)
def handler_function(user_id, event_data):
    # Process event and update systems
    return success_status
```

## 🎯 Cross-Module Integration

### 📡 Event Hook System

The event hook system enables loose coupling between modules:

#### **Registration Phase** (Startup)
```python
# In app/social/__init__.py
from .leaderboards.integration.hooks import register_integration_hooks

with app.app_context():
    register_integration_hooks()
```

**Registered Events**:
- `game_session_complete` - Game sessions ending
- `social_activity` - Social interactions
- `donation_complete` - Payment completions
- `achievement_unlock` - Achievement unlocks
- `user_login` - User login events
- `weekly_reset` - Periodic system resets
- `tournament_complete` - Tournament endings

#### **Triggering Phase** (Runtime)
```python
# In games controller
from app.social.leaderboards.integration.hooks import trigger_game_session_complete

success, message, result = session_service.end_game_session(session_id, reason)
if success:
    trigger_game_session_complete(
        str(session_data['user_id']),
        session_data
    )
```

#### **Processing Phase** (Automatic)
```python
# In event handler
def handle_game_session_complete(user_id: str, session_data: Dict):
    # Update Impact Score
    ranking_engine.trigger_user_score_update(user_id, 'gaming', activity_data)
    return True
```

### 🔄 Data Flow

```mermaid
graph LR
    A[Controller] --> B[Service]
    B --> C[Repository]
    C --> D[MongoDB]
    B --> E[Event Hook]
    E --> F[Cross-Module Service]
    F --> G[Cross-Module Repository]
    G --> D
```

## 📊 Database Architecture

### 🏗️ MongoDB Collections Structure

#### **Core Collections**
- `users` - User accounts and authentication
  - Indexes: `email` (unique), `created_at`
- `configs` - System configuration
  - Indexes: `key` (unique)

#### **Social Collections**
- `user_relationships` - Friend connections
  - Indexes: `user_id`, `friend_id`, `status`
- `user_impact_scores` - Gamification scores
  - Indexes: `user_id` (unique), `impact_score`, `rank_global`
- `leaderboards` - Ranking tables
  - Indexes: `leaderboard_type`, `time_period`, `rank`
- `achievements` - Achievement definitions
  - Indexes: `achievement_id` (unique), `category`, `is_active`
- `user_achievements` - User progress tracking
  - Indexes: `user_id`, `achievement_id`, `completed_at`

#### **Games Collections**
- `games` - Game definitions
  - Indexes: `game_id` (unique), `is_active`
- `game_sessions` - Active game sessions
  - Indexes: `user_id`, `game_id`, `status`, `created_at`
- `game_modes` - Temporary game modes
  - Indexes: `name` (unique), `is_active`, `start_date`, `end_date`
- `challenges` - Direct player challenges
  - Indexes: `challenger_id`, `status`, `game_id`, `created_at`
- `global_teams` - Team definitions
  - Indexes: `team_id` (unique), `is_active`
- `team_members` - Team membership
  - Indexes: `user_id`, `team_id`, `role`

#### **Donations Collections** (GOO-15)
- `wallets` - Virtual wallet management
  - Indexes: `user_id` (unique), `balance`, `total_earned`
- `transactions` - Financial transaction records
  - Indexes: `user_id`, `transaction_type`, `status`, `created_at`
- `conversion_rates` - Credit conversion rates
  - Indexes: `rate_type`, `is_active`, `effective_date`
- `payment_providers` - Payment provider configurations
  - Indexes: `provider_name` (unique), `is_active`
- `payment_intents` - Payment processing records
  - Indexes: `payment_intent_id` (unique), `user_id`, `status`
- `batch_operations` - Batch processing operations
  - Indexes: `operation_type`, `status`, `created_at`
- `batch_donations` - Batch donation records
  - Indexes: `batch_id`, `user_id`, `status`

### 📈 Index Strategy

**Performance Considerations**:
1. **Query Pattern Analysis**: Indexes based on common query patterns
2. **Compound Indexes**: Multi-field indexes for complex queries
3. **Unique Constraints**: Data integrity enforcement
4. **TTL Indexes**: Automatic data cleanup (sessions, temporary data)

**Index Creation Timing**:
- **Startup**: All indexes created during module initialization
- **Testing Mode**: Index creation skipped to prevent DB connection requirements

## 🔧 Configuration Management

### 🌍 Environment-Based Configuration

**Configuration Structure** (`config/settings.py`):
```python
class Config:
    # Base configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    MONGO_URI = os.environ.get('MONGO_URI')

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'INFO'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

### 🔐 Security Configuration

**JWT Settings**:
- Access token expiration: 1 hour
- Refresh token expiration: 30 days
- Token blacklisting support

**CORS Configuration**:
- Environment-specific origins
- Development: `http://localhost:3000`
- Production: Configured domains only

## 🧪 Testing Architecture

### 🔬 Testing Strategy

**Test Structure**:
```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_core_auth.py        # Core authentication tests (47 tests)
├── test_preferences.py      # Preferences module tests (35 tests)
├── test_social.py          # Social features tests (28 tests)
├── test_games.py           # Game engine tests (32 tests)
└── test_integration.py     # Cross-module integration tests
```

**Testing Patterns**:
- **Service Tests**: Mock repository dependencies
- **Controller Tests**: Mock services, test API contracts
- **Repository Tests**: Mock database operations
- **Integration Tests**: Test full request/response cycles

**Mock Strategy**:
```python
# Database mocking
@pytest.fixture
def mock_db(monkeypatch):
    mock_collection = MagicMock()
    monkeypatch.setattr('app.core.database.get_db', lambda: mock_db)

# Service mocking
@pytest.fixture
def mock_user_service(monkeypatch):
    mock_service = MagicMock()
    monkeypatch.setattr('app.core.services.user_service', mock_service)
```

### 📊 Testing Configuration

**Environment Variables**:
```python
# In conftest.py
os.environ['TESTING'] = 'true'
os.environ['SKIP_DB_INIT'] = '1'
```

**Index Creation Control**:
```python
def create_indexes(self):
    if os.getenv('TESTING') == 'true':
        return  # Skip index creation in tests
    # Normal index creation
```

## 🚀 Performance Considerations

### ⚡ Optimization Strategies

**Database Optimization**:
- Compound indexes for complex queries
- Query result pagination
- Connection pooling
- Index usage monitoring

**Application Optimization**:
- Service layer caching
- Lazy loading for related data
- Async processing for heavy operations
- Event hook non-blocking execution

**Memory Management**:
- Repository instance reuse
- Service singleton pattern
- Connection pool optimization

### 📈 Scalability Design

**Horizontal Scaling Readiness**:
- Stateless service design
- Database connection abstraction
- Event-driven architecture
- Load balancer friendly

**Monitoring Integration Points**:
- Request/response timing
- Database query performance
- Event processing metrics
- Error rate tracking

## 🔮 Future Architecture Evolution

### 🎯 Planned Improvements

**Event System Enhancement**:
- Redis/Kafka integration for distributed events
- Event sourcing implementation
- Replay capability for debugging

**Microservices Migration Path**:
- Module extraction strategy
- API gateway implementation
- Service mesh integration

**Performance Enhancements**:
- Caching layer (Redis)
- Background job processing (Celery)
- Real-time features (WebSocket)

**Development Experience**:
- Auto-generated API documentation
- Development tooling integration
- Enhanced debugging capabilities

---

## 💰 GOO-15: Donation Processing Engine Architecture

### 🏗️ Donations Module Architecture

The GOO-15 implementation introduces a comprehensive donation processing system with the following architectural components:

#### **Service Layer Architecture**

```mermaid
graph TD
    A[WalletService] --> B[ConversionRateService]
    A --> C[TransactionService]
    A --> D[FraudDetectionService]

    E[DonationService] --> A
    E --> F[PaymentService]
    E --> G[ReceiptGenerationService]
    E --> H[TaxComplianceService]

    I[BatchProcessingService] --> A
    I --> E
    I --> J[ComplianceService]

    K[ReconciliationService] --> C
    K --> F

    L[FinancialAnalyticsService] --> C
    L --> A
    L --> E
```

#### **Core Service Responsibilities**

**WalletService** (`app/donations/services/wallet_service.py`):
- Virtual wallet management and balance tracking
- Credit conversion from game sessions
- Auto-donation configuration and processing
- Transaction validation and security checks

**PaymentService** (`app/donations/services/payment_service.py`):
- Payment provider integration (Stripe, PayPal, etc.)
- Payment intent creation and processing
- Payment method validation and security
- Webhook handling for payment updates

**DonationService** (`app/donations/services/donation_service.py`):
- Donation workflow orchestration
- ONLUS validation and verification
- Donation receipt generation coordination
- Tax deductibility calculations

**BatchProcessingService** (`app/donations/services/batch_processing_service.py`):
- High-volume donation processing
- Batch operation management
- Progress tracking and status updates
- Error handling and retry mechanisms

**ComplianceService** (`app/donations/services/compliance_service.py`):
- AML (Anti-Money Laundering) checks
- KYC (Know Your Customer) verification
- Sanctions screening
- Regulatory compliance reporting

**ReconciliationService** (`app/donations/services/reconciliation_service.py`):
- Transaction matching between internal and external systems
- Discrepancy detection and resolution
- Financial reconciliation reporting
- Data integrity validation

**FinancialAnalyticsService** (`app/donations/services/financial_analytics_service.py`):
- Real-time financial dashboard generation
- Donation trends and forecasting
- User behavior analytics
- System performance metrics

#### **Data Flow Architecture**

```mermaid
sequenceDiagram
    participant User
    participant WalletController
    participant WalletService
    participant TransactionService
    participant FraudDetection
    participant PaymentService
    participant DonationService
    participant ComplianceService

    User->>WalletController: Convert game session to credits
    WalletController->>WalletService: process_session_conversion()
    WalletService->>FraudDetection: validate_conversion()
    FraudDetection->>WalletService: validation_result
    WalletService->>TransactionService: create_transaction()
    TransactionService->>WalletService: transaction_created
    WalletService->>WalletController: conversion_success

    User->>WalletController: Create donation
    WalletController->>DonationService: process_donation()
    DonationService->>PaymentService: create_payment_intent()
    PaymentService->>DonationService: payment_intent_created
    DonationService->>ComplianceService: perform_compliance_check()
    ComplianceService->>DonationService: compliance_approved
    DonationService->>TransactionService: record_donation()
    TransactionService->>DonationService: transaction_recorded
    DonationService->>WalletController: donation_success
```

#### **Controller Layer Organization**

The donations module exposes 7 specialized controllers:

1. **WalletController** (`/api/wallet/*`) - Virtual wallet operations
2. **DonationController** (`/api/donations/*`) - Donation processing
3. **ConversionRatesController** (`/api/conversion-rates/*`) - Rate management
4. **PaymentController** (`/api/payments/*`) - Payment processing
5. **BatchController** (`/api/batch/*`) - Batch operations (admin)
6. **ComplianceController** (`/api/compliance/*`) - Compliance management (admin)
7. **FinancialAdminController** (`/api/admin/financial/*`) - Financial analytics (admin)

#### **Security Architecture**

**Multi-Layer Security Approach**:

1. **Input Validation Layer**:
   - Request data sanitization
   - Parameter type validation
   - Business rule validation

2. **Authentication Layer**:
   - JWT token verification
   - User session validation
   - Admin role verification for sensitive operations

3. **Authorization Layer**:
   - Resource access control
   - Operation-level permissions
   - Admin-only endpoint protection

4. **Transaction Security Layer**:
   - Optimistic locking for wallet operations
   - Transaction integrity validation
   - Fraud detection algorithms

5. **Compliance Layer**:
   - AML/KYC verification
   - Sanctions screening
   - Regulatory compliance checks

#### **Event Integration Architecture**

**Credit Earning Events**:
```python
# Game session completion triggers credit conversion
trigger_session_complete(user_id, session_data)
  ↓
WalletService.process_session_conversion()
  ↓
Apply dynamic multipliers (tournament, streak, weekend)
  ↓
Create transaction record
  ↓
Update wallet balance
  ↓
Check auto-donation settings
  ↓
Trigger auto-donation if threshold met
```

**Donation Events**:
```python
# Donation completion triggers multiple systems
trigger_donation_complete(user_id, donation_data)
  ↓
Update Impact Score (social module)
  ↓
Generate receipt (tax compliance)
  ↓
Update financial analytics
  ↓
Check achievement unlocks
  ↓
Update leaderboards
```

#### **Error Handling Architecture**

**Standardized Error Response Pattern**:
```python
# Service Layer Error Handling
try:
    validation_result = self._validate_input(data)
    if validation_result:
        return False, validation_result, None

    business_result = self._execute_business_logic(data)

    current_app.logger.info(f"Operation successful: {operation_info}")
    return True, "SUCCESS_CONSTANT", business_result

except ValidationError as e:
    current_app.logger.warning(f"Validation failed: {str(e)}")
    return False, "VALIDATION_ERROR_CONSTANT", None

except BusinessLogicError as e:
    current_app.logger.error(f"Business logic error: {str(e)}")
    return False, "BUSINESS_ERROR_CONSTANT", None

except Exception as e:
    current_app.logger.error(f"Unexpected error: {str(e)}")
    return False, "INTERNAL_SERVER_ERROR", None
```

**Controller Layer Error Handling**:
```python
# Standardized controller error responses
try:
    success, message, result = service.method(data)

    if success:
        return success_response(message, result)
    else:
        return error_response(message)

except Exception as e:
    current_app.logger.error(f"Controller error: {str(e)}")
    return error_response("INTERNAL_SERVER_ERROR", status_code=500)
```

#### **Performance Optimization Architecture**

**Caching Strategy**:
- Conversion rates cached for 1 hour
- Financial analytics cached for 15 minutes
- User wallet data cached for 5 minutes
- Payment provider configs cached for 24 hours

**Database Optimization**:
- Compound indexes for complex queries
- Transaction aggregation pipelines
- Batch processing for high-volume operations
- Connection pooling and query optimization

**Concurrent Processing**:
- Optimistic locking for wallet updates
- Async processing for non-critical operations
- Queue-based batch processing
- Background reconciliation jobs

### 🔄 GOO-15 Integration Points

#### **Games Module Integration**:
- Session completion triggers credit conversion
- Multiplier calculation based on game type and mode
- Tournament participation bonus calculations

#### **Social Module Integration**:
- Donation activities update Impact Score
- Achievement unlocks for donation milestones
- Leaderboard updates for charitable contributions

#### **Core Module Integration**:
- User authentication for all financial operations
- User preferences for auto-donation settings
- Admin role verification for sensitive operations

---

## 🎨 GOO-16: Impact Tracking & Reporting System Architecture

### 🏗️ System Overview

The GOO-16 Impact Tracking & Reporting System completes the donation platform by providing real-time impact visualization, progressive story unlocking, and community transparency features. Building on the foundation of GOO-14 (Virtual Wallet) and GOO-15 (Donation Processing), GOO-16 creates direct connections between donations and their real-world impact.

### 📊 Module Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DONATIONS MODULE ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GOO-14: Virtual Wallet System (Foundation)                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │     Wallet      │  │   Transaction   │  │    Credit Conversion        │ │
│  │     Model       │  │     Model       │  │       Service               │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│                                                                             │
│  GOO-15: Donation Processing Engine                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │  PaymentIntent  │  │ BatchOperation  │  │    Compliance & Receipt     │ │
│  │     Model       │  │     Model       │  │       Services              │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│                                                                             │
│  GOO-16: Impact Tracking & Reporting (NEW)                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │  ImpactStory    │  │  ImpactMetric   │  │    Progressive Unlocking    │ │
│  │     Model       │  │     Model       │  │       System                │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │  ImpactUpdate   │  │ CommunityReport │  │    Real-time Impact         │ │
│  │     Model       │  │     Model       │  │      Visualization          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 🔄 Integration Workflow

```mermaid
graph TD
    A[User Makes Donation] --> B[GOO-15: Process Payment]
    B --> C[GOO-14: Update Wallet]
    C --> D[GOO-16: Track Impact]

    D --> E[Update ONLUS Metrics]
    D --> F[Check Story Unlocks]
    D --> G[Update Community Stats]

    E --> H[Efficiency Calculations]
    F --> I[Progressive Content Reveal]
    G --> J[Platform Analytics]

    H --> K[ONLUS Dashboard]
    I --> L[User Engagement]
    J --> M[Community Reports]
```

### 🎯 Core Components

#### **Impact Models** (`app/donations/models/`)

**ImpactStory** (`impact_story.py`):
- Progressive story unlocking system
- Milestone-based content revelation (€10 → €10,000)
- Multiple unlock conditions (total donated, donation count, ONLUS diversity)
- User progress tracking and API response formatting

**ImpactMetric** (`impact_metric.py`):
- Aggregated ONLUS impact metrics
- Efficiency ratio calculations (impact per euro)
- Time-series trend analysis
- Verification and dispute resolution system

**ImpactUpdate** (`impact_update.py`):
- Real-time updates from ONLUS organizations
- Engagement tracking (views, likes, shares, comments)
- Priority-based publishing system
- Media attachments and related metrics

**CommunityReport** (`community_report.py`):
- Platform-wide aggregated reports
- Growth metrics and statistical analysis
- Monthly/annual reporting cycles
- Community milestone tracking

#### **Repository Layer** (`app/donations/repositories/`)

**Advanced MongoDB Aggregations**:
```python
# Trend analysis pipeline
def get_metric_trends(self, onlus_id: str, metric_name: str, days: int = 30):
    pipeline = [
        {"$match": {"onlus_id": onlus_id, "metric_name": metric_name}},
        {"$group": {
            "_id": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$collection_date"}}},
            "avg_value": {"$avg": "$current_value"},
            "efficiency_ratio": {"$avg": {"$divide": ["$current_value", "$related_donations_amount"]}}
        }},
        {"$sort": {"_id.date": 1}}
    ]

# Community growth analysis
def get_platform_growth_trends(self, months: int = 12):
    pipeline = [
        {"$match": {"report_type": "monthly", "status": "published"}},
        {"$group": {
            "_id": {"year": {"$year": "$period_start"}, "month": {"$month": "$period_start"}},
            "total_donations": {"$sum": "$total_donations"},
            "growth_rate": {"$avg": "$growth_metrics.donations_growth"}
        }}
    ]
```

**Performance Indexes**:
```javascript
// High-performance indexes for story unlocking
{onlus_id: 1, is_active: 1, story_type: 1}
{unlock_condition_type: 1, unlock_condition_value: 1, is_active: 1}
{title: "text", content: "text", tags: "text"}

// Metrics aggregation optimization
{onlus_id: 1, metric_name: 1, collection_date: -1}
{metric_type: 1, efficiency_ratio: -1}

// Community reporting performance
{report_type: 1, period_start: -1, status: 1}
```

#### **Service Layer** (`app/donations/services/`)

**ImpactTrackingService** (`impact_tracking_service.py`):
- Core donation→impact workflow coordination
- User statistics aggregation and caching
- Cross-service integration with GOO-14/GOO-15
- Impact milestone detection and user level progression

**StoryUnlockingService** (`story_unlocking_service.py`):
- Progressive unlock algorithm implementation
- Milestone achievement tracking
- User progress calculation and API responses
- Content availability management based on donation history

**ImpactVisualizationService** (`impact_visualization_service.py`):
- Dashboard data aggregation and formatting
- ONLUS impact visualization preparation
- Trend analysis and efficiency calculations
- Real-time metrics compilation for frontend

**CommunityImpactService** (`community_impact_service.py`):
- Platform-wide statistics generation
- Community leaderboards and ranking systems
- Growth rate calculations and projections
- Real-time report generation and caching

#### **API Layer** (`app/donations/controllers/`)

**ImpactController** (`impact_controller.py`):
- 15+ REST endpoints with constant message responses
- User impact summaries and timeline visualization
- Story unlock progress and availability
- Community statistics and leaderboards
- ONLUS metrics and real-time updates
- Monthly/annual reporting endpoints
- Admin metrics and update management

**Endpoint Categories**:
```python
# User Impact Endpoints
GET  /api/impact/user/{user_id}                    # Impact summary
GET  /api/impact/user/{user_id}/timeline           # Donation timeline
GET  /api/impact/donation/{donation_id}            # Donation details

# Story System Endpoints
GET  /api/impact/stories/available                 # Available stories
GET  /api/impact/stories/{story_id}                # Story details
GET  /api/impact/stories/progress                  # Unlock progress

# Community Endpoints
GET  /api/impact/community/statistics              # Platform stats
GET  /api/impact/community/leaderboard             # Leaderboards
GET  /api/impact/dashboard                         # Dashboard data

# ONLUS Endpoints
GET  /api/impact/onlus/{onlus_id}/metrics          # ONLUS metrics
GET  /api/impact/onlus/{onlus_id}/updates          # ONLUS updates

# Reporting Endpoints
GET  /api/impact/reports/monthly/{year}/{month}    # Monthly reports
GET  /api/impact/reports/annual/{year}             # Annual reports

# Admin Endpoints (Admin Required)
POST /api/impact/admin/metrics                     # Create metrics
POST /api/impact/admin/updates                     # Create updates
POST /api/impact/admin/reports/generate            # Generate reports
```

### 🎮 Gamification System

#### **Progressive Milestone System**:
```python
MILESTONE_LEVELS = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

# Example progression:
€10   → "First Impact" story unlock
€25   → "Growing Difference" story + basic metrics access
€50   → "Community Builder" story + trend data
€100  → "Changemaker" story + detailed analytics
€250  → "Impact Champion" story + ONLUS direct updates
€500  → "Philanthropist" story + community leaderboard
€1000 → "Major Donor" story + platform insights
€2500 → "Community Leader" story + admin dashboards
€5000 → "Impact Hero" story + advanced reporting
€10000→ "Transformation Leader" story + all features
```

#### **Unlock Conditions**:
- **Total Donated**: Cumulative donation amount across all ONLUS
- **Donation Count**: Number of separate donation transactions
- **ONLUS Diversity**: Number of different organizations supported
- **Impact Score**: Calculated efficiency and engagement metric
- **Special Events**: Holiday campaigns, emergency responses, community goals

### 📊 Database Collections

#### **New Collections Added**:

**impact_stories** Collection:
```javascript
{
  "_id": ObjectId,
  "onlus_id": "uuid",                    // ONLUS organization ID
  "title": "Your First Impact Story",    // Display title
  "content": "Full story content...",    // Revealed when unlocked
  "story_type": "milestone",             // milestone|progress|featured|special
  "unlock_condition_type": "total_donated",  // unlock trigger type
  "unlock_condition_value": 100.0,      // threshold amount/count
  "category": "education",               // impact category
  "priority": 5,                         // display priority 1-10
  "media_urls": ["https://..."],         // photos, videos, documents
  "tags": ["education", "children"],     // searchable tags
  "featured_until": null,                // featured expiration
  "is_active": true,                     // visibility control
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**impact_metrics** Collection:
```javascript
{
  "_id": ObjectId,
  "onlus_id": "uuid",                    // ONLUS organization ID
  "metric_name": "children_helped",      // metric identifier
  "metric_type": "beneficiaries",        // financial|beneficiaries|projects|etc
  "current_value": 150,                  // current metric value
  "previous_value": 120,                 // previous period value
  "unit": "people",                      // measurement unit
  "related_donations_amount": 2500.0,    // associated donation total
  "efficiency_ratio": 0.06,              // calculated efficiency
  "collection_period": "month",          // data collection period
  "collection_date": ISODate,            // when metric was recorded
  "verification_status": "verified",     // verified|pending|disputed
  "is_active": true,
  "created_at": ISODate
}
```

**impact_updates** Collection:
```javascript
{
  "_id": ObjectId,
  "onlus_id": "uuid",                    // ONLUS organization ID
  "title": "New School Completed",       // update title
  "content": "Full update content...",   // update details
  "update_type": "milestone_reached",    // update category
  "priority": "high",                    // low|normal|high|urgent|critical
  "status": "published",                 // draft|scheduled|published|featured
  "tags": ["construction", "education"], // categorization tags
  "media_urls": ["https://..."],         // attached media
  "related_metrics": {                   // related metric updates
    "schools_built": 1,
    "children_capacity": 200
  },
  "engagement_metrics": {                // user engagement tracking
    "views": 1250,
    "likes": 45,
    "shares": 12,
    "comments": 8
  },
  "featured_until": null,                // featured expiration
  "created_at": ISODate,
  "published_at": ISODate
}
```

**community_reports** Collection:
```javascript
{
  "_id": ObjectId,
  "report_type": "monthly",              // daily|weekly|monthly|quarterly|annual
  "title": "Sept 2024 Impact Report",    // report title
  "summary": "Community achievements...", // executive summary
  "period_start": ISODate("2024-09-01"), // reporting period start
  "period_end": ISODate("2024-09-30"),   // reporting period end
  "total_donations": 45000.0,            // period donation total
  "total_donors": 320,                   // active donor count
  "active_onlus_count": 15,              // participating organizations
  "detailed_metrics": {                  // comprehensive statistics
    "donations_by_category": {
      "education": 18000.0,
      "health": 15000.0,
      "environment": 12000.0
    },
    "user_engagement": {
      "stories_unlocked": 180,
      "avg_session_duration": 420,
      "return_rate": 0.75
    }
  },
  "growth_metrics": {                    // period-over-period growth
    "donations_growth": 15.5,
    "users_growth": 8.2,
    "engagement_growth": 12.3
  },
  "status": "published",                 // draft|published|archived
  "created_at": ISODate,
  "published_at": ISODate
}
```

### 🔗 Integration Points

#### **GOO-16 → GOO-15 Integration**:
```python
# Donation completion triggers impact tracking
@donation_bp.route('/process', methods=['POST'])
def process_donation():
    # GOO-15: Process payment
    success, message, donation_data = donation_service.process_donation(data)

    if success:
        # GOO-16: Track impact
        impact_service.track_donation_impact(
            donation_data['donation_id'],
            donation_data['user_id'],
            donation_data['amount'],
            donation_data['onlus_id']
        )

    return success_response(message, donation_data)
```

#### **GOO-16 → GOO-14 Integration**:
```python
# Credit conversion includes impact milestone checks
def convert_session_to_credits(session_data):
    # GOO-14: Convert credits
    credits_earned = credit_service.calculate_credits(session_data)

    # GOO-16: Check if credit earnings unlock stories
    user_total = wallet_service.get_user_total_earned(user_id)
    unlocked_stories = story_service.check_and_unlock_stories(user_id, user_total)

    return {
        'credits_earned': credits_earned,
        'stories_unlocked': unlocked_stories,
        'new_milestone_reached': len(unlocked_stories) > 0
    }
```

### 📈 Performance Considerations

#### **Caching Strategy**:
```python
# Redis caching for frequently accessed data
CACHE_KEYS = {
    'user_impact_summary': 'impact:user:{user_id}:summary',      # TTL: 10 minutes
    'dashboard_data': 'impact:user:{user_id}:dashboard',         # TTL: 15 minutes
    'community_stats': 'impact:community:stats',                # TTL: 30 minutes
    'onlus_metrics': 'impact:onlus:{onlus_id}:metrics',         # TTL: 5 minutes
    'story_unlocks': 'impact:user:{user_id}:unlocks'            # TTL: 60 minutes
}
```

#### **Database Query Optimization**:
```python
# Efficient aggregation pipeline for user impact
def get_user_impact_summary(user_id):
    # Single aggregation query across multiple collections
    pipeline = [
        {"$lookup": {"from": "transactions", "localField": "user_id", "foreignField": "user_id"}},
        {"$lookup": {"from": "impact_stories", "localField": "unlock_level", "foreignField": "unlock_condition_value"}},
        {"$group": {"_id": "$user_id", "total_donated": {"$sum": "$amount"}, "stories_unlocked": {"$addToSet": "$story_id"}}}
    ]
```

#### **Scalability Features**:
- Background task queues for report generation
- Incremental aggregation updates
- Partitioned collections for historical data
- Read replicas for analytics queries

### 🧪 Testing Architecture

#### **Test Structure (99 Test Methods)**:
```
tests/test_goo16_models.py        (25 tests) - Model validation & business logic
tests/test_goo16_repositories.py  (28 tests) - Database operations & aggregations
tests/test_goo16_services.py      (18 tests) - Service layer business logic
tests/test_goo16_controllers.py   (21 tests) - API endpoints & auth validation
tests/test_goo16_integration.py   (7 tests)  - End-to-end workflow testing
```

#### **Coverage Requirements**:
- Models: >95% line coverage
- Repositories: >90% line coverage
- Services: >88% line coverage
- Controllers: >92% line coverage
- Integration: >85% line coverage
- **Overall Target**: >90% coverage

### 📱 Frontend Integration

#### **API Response Constants**:
All responses use constant message keys for UI internationalization:
```python
# Success constants
"USER_IMPACT_SUMMARY_SUCCESS", "STORIES_RETRIEVED_SUCCESS",
"COMMUNITY_STATS_SUCCESS", "LEADERBOARD_SUCCESS",
"DASHBOARD_DATA_SUCCESS", "MONTHLY_REPORT_SUCCESS"

# Error constants
"STORY_NOT_FOUND", "REPORT_NOT_FOUND", "ACCESS_DENIED",
"INVALID_MONTH", "ONLUS_ID_REQUIRED"
```

#### **Real-time Updates**:
```javascript
// WebSocket integration for live updates
const impactSocket = io('/impact');

impactSocket.on('story_unlocked', (data) => {
    // Show unlock notification
    showStoryUnlockNotification(data.story);
    // Refresh user progress
    refreshUserProgress();
});

impactSocket.on('community_milestone', (data) => {
    // Show platform achievement
    showCommunityMilestone(data.milestone);
});
```

### 🚀 Deployment Considerations

#### **Environment Variables**:
```bash
# GOO-16 specific configuration
IMPACT_STORY_CACHE_TTL=600
METRIC_UPDATE_FREQUENCY=300
COMMUNITY_REPORT_SCHEDULE="0 0 1 * *"
TRENDING_UPDATE_WINDOW=24
MAX_STORIES_PER_USER=50
REPORT_GENERATION_TIMEOUT=300
```

#### **Background Jobs**:
```python
# Scheduled tasks for GOO-16
@scheduler.task('cron', hour=0, minute=0, day=1)  # Monthly reports
def generate_monthly_reports():
    CommunityImpactService().generate_monthly_report()

@scheduler.task('interval', minutes=5)  # Metric updates
def update_trending_metrics():
    ImpactVisualizationService().refresh_trending_updates()

@scheduler.task('interval', minutes=10)  # Cache warming
def warm_dashboard_cache():
    CacheService().warm_dashboard_data()
```

#### **Monitoring & Alerts**:
```python
# Key metrics to monitor
MONITORING_METRICS = {
    'story_unlock_latency': {'threshold': '500ms', 'alert': 'high'},
    'dashboard_load_time': {'threshold': '2s', 'alert': 'medium'},
    'report_generation_time': {'threshold': '5min', 'alert': 'high'},
    'daily_story_unlocks': {'threshold': '> 0', 'alert': 'low'},
    'api_error_rate': {'threshold': '< 1%', 'alert': 'critical'}
}
```

---

*Architecture documentation - GoodPlay Backend v1.2*
*Last updated: September 27, 2025*
*Includes GOO-14 Virtual Wallet, GOO-15 Donation Processing, and GOO-16 Impact Tracking*