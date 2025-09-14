import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(app):
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        
        file_handler = logging.handlers.RotatingFileHandler(
            f'logs/{app.config["LOG_FILE"]}', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.info('Application logging configured')
    
    else:
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        )
        console_handler.setFormatter(formatter)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.DEBUG)

def log_request(request, response_status=None):
    """Log delle richieste HTTP"""
    logger = logging.getLogger(__name__)
    
    log_data = {
        'method': request.method,
        'path': request.path,
        'remote_addr': request.environ.get('REMOTE_ADDR'),
        'user_agent': request.headers.get('User-Agent'),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if response_status:
        log_data['status'] = response_status
    
    logger.info(f"HTTP Request: {log_data}")

def log_auth_event(event_type, user_email=None, user_id=None, success=True, details=None):
    """Log degli eventi di autenticazione"""
    logger = logging.getLogger(__name__)
    
    log_data = {
        'event': event_type,
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if user_email:
        log_data['user_email'] = user_email
    if user_id:
        log_data['user_id'] = user_id
    if details:
        log_data['details'] = details
    
    level = logging.INFO if success else logging.WARNING
    logger.log(level, f"Auth Event: {log_data}")

def log_database_operation(operation, collection, success=True, details=None):
    """Log delle operazioni sul database"""
    logger = logging.getLogger(__name__)
    
    log_data = {
        'operation': operation,
        'collection': collection,
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details:
        log_data['details'] = details
    
    level = logging.DEBUG if success else logging.ERROR
    logger.log(level, f"DB Operation: {log_data}")