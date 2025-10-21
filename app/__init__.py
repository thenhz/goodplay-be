from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from pymongo import MongoClient
import logging
from logging.handlers import RotatingFileHandler
import os

from config.settings import config

jwt = JWTManager()
socketio = SocketIO()
mongo_client = None
mongo_db = None

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    jwt.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])

    # Initialize SocketIO with threading mode (recommended for 2025)
    socketio.init_app(
        app,
        cors_allowed_origins=app.config['CORS_ORIGINS'],
        logger=app.debug,
        engineio_logger=False,
        ping_timeout=app.config.get('SOCKETIO_PING_TIMEOUT', 60),
        ping_interval=app.config.get('SOCKETIO_PING_INTERVAL', 25),
        max_http_buffer_size=app.config.get('SOCKETIO_MAX_MESSAGE_SIZE', 1000000)
    )

    init_db(app)
    init_logging(app)
    
    from app.core.controllers.auth_controller import auth_bp
    from app.core.controllers.user_controller import user_bp
    from app.core.controllers.device_controller import device_bp
    from app.core.controllers.notification_controller import notification_bp
    from app.core.controllers.notification_preferences_controller import preferences_bp as notification_preferences_bp
    from app.preferences.controllers.preferences_controller import preferences_blueprint
    from app.social import register_social_module
    from app.games import create_games_blueprint, create_modes_blueprint, create_challenges_blueprint, create_teams_blueprint, init_games_module
    from app.donations.controllers import wallet_bp, donation_bp, rates_bp, payment_bp, batch_bp, compliance_bp, financial_admin_bp
    from app.onlus import register_onlus_blueprints
    from app.admin.controllers import admin_bp, dashboard_bp, user_mgmt_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(preferences_blueprint)

    # Register notification system blueprints
    app.register_blueprint(device_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(notification_preferences_bp)

    # Register social module
    register_social_module(app)

    # Register games module
    games_bp = create_games_blueprint()
    app.register_blueprint(games_bp)

    # Register modes module
    modes_bp = create_modes_blueprint()
    app.register_blueprint(modes_bp)

    # Register challenges module
    challenges_bp = create_challenges_blueprint()
    app.register_blueprint(challenges_bp)

    # Register teams module
    teams_bp = create_teams_blueprint()
    app.register_blueprint(teams_bp)

    # Register donations module
    app.register_blueprint(wallet_bp)
    app.register_blueprint(donation_bp)
    app.register_blueprint(rates_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(batch_bp)
    app.register_blueprint(compliance_bp)
    app.register_blueprint(financial_admin_bp)

    # Register admin module
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(user_mgmt_bp)

    # Initialize games module (create indexes and discover plugins)
    with app.app_context():
        init_games_module()

    # Register multiplayer module (WebSocket + REST API)
    from app.games.multiplayer import register_multiplayer_module
    register_multiplayer_module(app, socketio)

    # Initialize scheduler and register scheduled tasks
    init_scheduler(app)

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {'status': 'healthy', 'message': 'API is running'}, 200

    return app

def init_db(app):
    global mongo_client, mongo_db

    if os.environ.get('SKIP_DB_INIT') == '1':
        app.logger.info('Skipping database initialization')
        return

    try:
        mongo_client = MongoClient(app.config['MONGO_URI'])
        mongo_db = mongo_client[app.config['MONGO_DB_NAME']]

        with app.app_context():
            from app.core.repositories.user_repository import UserRepository
            from app.donations.repositories.wallet_repository import WalletRepository
            from app.donations.repositories.transaction_repository import TransactionRepository
            from app.donations.repositories.conversion_rate_repository import ConversionRateRepository
            from app.donations.repositories.payment_provider_repository import PaymentProviderRepository
            from app.donations.repositories.payment_intent_repository import PaymentIntentRepository
            from app.donations.repositories.batch_operation_repository import BatchOperationRepository
            from app.donations.repositories.batch_donation_repository import BatchDonationRepository
            from app.donations.repositories.impact_story_repository import ImpactStoryRepository
            from app.donations.repositories.impact_metric_repository import ImpactMetricRepository
            from app.donations.repositories.impact_update_repository import ImpactUpdateRepository
            from app.donations.repositories.community_report_repository import CommunityReportRepository
            from app.onlus.repositories.onlus_category_repository import ONLUSCategoryRepository
            from app.onlus.repositories.onlus_document_repository import ONLUSDocumentRepository
            from app.onlus.repositories.verification_check_repository import VerificationCheckRepository
            from app.onlus.repositories.onlus_application_repository import ONLUSApplicationRepository
            from app.onlus.repositories.onlus_organization_repository import ONLUSOrganizationRepository

            user_repo = UserRepository()
            user_repo.create_indexes()

            # Initialize donations module indexes
            wallet_repo = WalletRepository()
            transaction_repo = TransactionRepository()
            conversion_rate_repo = ConversionRateRepository()
            payment_provider_repo = PaymentProviderRepository()
            payment_intent_repo = PaymentIntentRepository()
            batch_operation_repo = BatchOperationRepository()
            batch_donation_repo = BatchDonationRepository()
            impact_story_repo = ImpactStoryRepository()
            impact_metric_repo = ImpactMetricRepository()
            impact_update_repo = ImpactUpdateRepository()
            community_report_repo = CommunityReportRepository()

            wallet_repo.create_indexes()
            transaction_repo.create_indexes()
            conversion_rate_repo.create_indexes()
            payment_provider_repo.create_indexes()
            payment_intent_repo.create_indexes()
            batch_operation_repo.create_indexes()
            batch_donation_repo.create_indexes()
            impact_story_repo.create_indexes()
            impact_metric_repo.create_indexes()
            impact_update_repo.create_indexes()
            community_report_repo.create_indexes()

            # Initialize ONLUS module indexes
            category_repo = ONLUSCategoryRepository()
            document_repo = ONLUSDocumentRepository()
            verification_repo = VerificationCheckRepository()
            application_repo = ONLUSApplicationRepository()
            organization_repo = ONLUSOrganizationRepository()

            category_repo.create_indexes()
            document_repo.create_indexes()
            verification_repo.create_indexes()
            application_repo.create_indexes()
            organization_repo.create_indexes()

            # Initialize admin module indexes
            from app.admin.repositories.admin_repository import AdminRepository
            from app.admin.repositories.metrics_repository import MetricsRepository
            from app.admin.repositories.audit_repository import AuditRepository

            admin_repo = AdminRepository()
            metrics_repo = MetricsRepository()
            audit_repo = AuditRepository()

            admin_repo.create_indexes()
            metrics_repo.create_indexes()
            audit_repo.create_indexes()

            # Initialize notification system indexes
            from app.core.repositories.device_token_repository import DeviceTokenRepository
            from app.core.repositories.notification_repository import NotificationRepository
            from app.core.repositories.notification_preferences_repository import NotificationPreferencesRepository

            device_token_repo = DeviceTokenRepository()
            notification_repo = NotificationRepository()
            notification_prefs_repo = NotificationPreferencesRepository()

            device_token_repo.create_indexes()
            notification_repo.create_indexes()
            notification_prefs_repo.create_indexes()

            app.logger.info('Database initialized successfully')
    except Exception as e:
        app.logger.warning(f'Database initialization failed: {str(e)}')

def init_logging(app):
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            f'logs/{app.config["LOG_FILE"]}', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.info('Application startup')

def init_scheduler(app):
    """Initialize APScheduler and register background tasks"""
    try:
        from app.core.services.scheduler_service import scheduler_service
        from app.games.multiplayer.tasks.invitation_warning_tasks import (
            send_expiry_warnings,
            cleanup_expired_invitations,
            cleanup_old_invitations,
            cleanup_old_notifications,
            cleanup_expired_device_tokens
        )

        # Helper function to wrap tasks with app context
        def wrap_with_app_context(task_func):
            def wrapper():
                with app.app_context():
                    return task_func()
            return wrapper

        with app.app_context():
            # Initialize scheduler
            scheduler_service.initialize()

            # Register scheduled tasks with app context wrapper
            # Run expiry warnings every 2 minutes
            scheduler_service.add_interval_job(
                func=wrap_with_app_context(send_expiry_warnings),
                job_id='send_expiry_warnings',
                minutes=2
            )

            # Run expired invitations cleanup every 5 minutes
            scheduler_service.add_interval_job(
                func=wrap_with_app_context(cleanup_expired_invitations),
                job_id='cleanup_expired_invitations',
                minutes=5
            )

            # Run old invitations cleanup daily at 3 AM
            scheduler_service.add_cron_job(
                func=wrap_with_app_context(cleanup_old_invitations),
                job_id='cleanup_old_invitations',
                hour=3,
                minute=0
            )

            # Run old notifications cleanup daily at 3 AM
            scheduler_service.add_cron_job(
                func=wrap_with_app_context(cleanup_old_notifications),
                job_id='cleanup_old_notifications',
                hour=3,
                minute=15
            )

            # Run expired device tokens cleanup daily at 3 AM
            scheduler_service.add_cron_job(
                func=wrap_with_app_context(cleanup_expired_device_tokens),
                job_id='cleanup_expired_device_tokens',
                hour=3,
                minute=30
            )

            # Start scheduler
            scheduler_service.start()

            app.logger.info('Scheduler initialized with 5 tasks')

            # Register shutdown handler
            import atexit
            atexit.register(lambda: scheduler_service.shutdown())

    except Exception as e:
        app.logger.error(f'Scheduler initialization failed: {str(e)}', exc_info=True)

def get_db():
    return mongo_db