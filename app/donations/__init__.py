from .controllers import wallet_bp, donation_bp, rates_bp, payment_bp, impact_bp

def register_blueprints(app):
    """Register donations module blueprints with the Flask app."""
    app.register_blueprint(wallet_bp)
    app.register_blueprint(donation_bp)
    app.register_blueprint(rates_bp)
    app.register_blueprint(payment_bp)

    # Register GOO-16 Impact Tracking blueprint
    app.register_blueprint(impact_bp)

__all__ = [
    'wallet_bp',
    'donation_bp',
    'rates_bp',
    'payment_bp',
    'impact_bp',
    'register_blueprints'
]