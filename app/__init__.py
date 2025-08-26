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
    
    from app.controllers.auth_controller import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {'status': 'healthy', 'message': 'API is running'}, 200
    
    return app

def init_db(app):
    global mongo_client, mongo_db
    mongo_client = MongoClient(app.config['MONGO_URI'])
    mongo_db = mongo_client[app.config['MONGO_DB_NAME']]
    
    with app.app_context():
        from app.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        user_repo.create_indexes()

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