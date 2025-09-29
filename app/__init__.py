from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from pymongo import MongoClient
import logging
from logging.handlers import RotatingFileHandler
import os

from config.settings import config

jwt = JWTManager()
mongo_client = None
mongo_db = None

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    jwt.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    init_db(app)
    init_logging(app)
    
    from app.core.controllers.auth_controller import auth_bp
    from app.core.controllers.user_controller import user_bp
    from app.preferences.controllers.preferences_controller import preferences_blueprint
    from app.social import register_social_module
    from app.games import create_games_blueprint, create_modes_blueprint, create_challenges_blueprint, create_teams_blueprint, init_games_module
    from app.donations.controllers import wallet_bp, donation_bp, rates_bp, payment_bp, batch_bp, compliance_bp, financial_admin_bp
    from app.onlus import register_onlus_blueprints

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(preferences_blueprint)

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

    # Register ONLUS module
    register_onlus_blueprints(app)

    # Initialize games module (create indexes and discover plugins)
    with app.app_context():
        init_games_module()
    
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

def get_db():
    return mongo_db