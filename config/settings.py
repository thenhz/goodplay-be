import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30)))
    
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/goodplay')
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'goodplay')
    
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')

    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS', 12))

    # WebSocket Configuration (Flask-SocketIO with threading mode)
    SOCKETIO_PING_TIMEOUT = int(os.environ.get('SOCKETIO_PING_TIMEOUT', 60))
    SOCKETIO_PING_INTERVAL = int(os.environ.get('SOCKETIO_PING_INTERVAL', 25))
    SOCKETIO_MAX_MESSAGE_SIZE = int(os.environ.get('SOCKETIO_MAX_MESSAGE_SIZE', 1000000))  # 1MB

    # Multiplayer Configuration
    MAX_PLAYERS_PER_ROOM = int(os.environ.get('MAX_PLAYERS_PER_ROOM', 8))
    MAX_ROOMS_PER_USER = int(os.environ.get('MAX_ROOMS_PER_USER', 3))
    ROOM_TIMEOUT_SECONDS = int(os.environ.get('ROOM_TIMEOUT_SECONDS', 3600))  # 1 hour
    ROOM_CODE_LENGTH = int(os.environ.get('ROOM_CODE_LENGTH', 6))

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    TESTING = True
    MONGO_DB_NAME = 'goodplay_test_db'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}