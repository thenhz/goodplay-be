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
    from app.games import create_games_blueprint, init_games_module

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(preferences_blueprint)

    # Register social module
    register_social_module(app)

    # Register games module
    games_bp = create_games_blueprint()
    app.register_blueprint(games_bp)

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

            user_repo = UserRepository()
            user_repo.create_indexes()

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