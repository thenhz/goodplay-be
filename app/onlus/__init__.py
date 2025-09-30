from flask import Blueprint
from .controllers import (
    application_bp,
    admin_application_bp,
    onlus_bp,
    document_bp,
    admin_onlus_bp,
    # GOO-19 controllers
    allocation_bp,
    financial_bp,
    compliance_bp
)

def register_onlus_blueprints(app):
    """Register ONLUS module blueprints with the Flask app."""
    # Public ONLUS endpoints
    app.register_blueprint(onlus_bp)

    # User application management
    app.register_blueprint(application_bp)

    # Document management
    app.register_blueprint(document_bp)

    # Admin application review
    app.register_blueprint(admin_application_bp)

    # Admin ONLUS management
    app.register_blueprint(admin_onlus_bp)

    # GOO-19 Smart Allocation & Financial Control endpoints
    app.register_blueprint(allocation_bp)      # /api/onlus/allocations/*
    app.register_blueprint(financial_bp)       # /api/onlus/financial/*
    app.register_blueprint(compliance_bp)      # /api/onlus/compliance/*

__all__ = [
    'register_onlus_blueprints',
    'application_bp',
    'admin_application_bp',
    'onlus_bp',
    'document_bp',
    'admin_onlus_bp',
    # GOO-19 controllers
    'allocation_bp',
    'financial_bp',
    'compliance_bp'
]