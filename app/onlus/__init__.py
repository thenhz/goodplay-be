from flask import Blueprint
from .controllers import (
    application_bp,
    admin_application_bp,
    onlus_bp,
    document_bp,
    admin_onlus_bp
)

def register_onlus_blueprints(app):
    """Register ONLUS module blueprints with the Flask app."""
    # Public ONLUS endpoints
    app.register_blueprint(onlus_bp, url_prefix='/api/onlus')

    # User application management
    app.register_blueprint(application_bp, url_prefix='/api/onlus')

    # Document management
    app.register_blueprint(document_bp, url_prefix='/api/onlus')

    # Admin application review
    app.register_blueprint(admin_application_bp, url_prefix='/api/admin/onlus')

    # Admin ONLUS management
    app.register_blueprint(admin_onlus_bp, url_prefix='/api/admin/onlus')

__all__ = [
    'register_onlus_blueprints',
    'application_bp',
    'admin_application_bp',
    'onlus_bp',
    'document_bp',
    'admin_onlus_bp'
]