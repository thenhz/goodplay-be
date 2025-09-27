from .controllers import wallet_bp, donation_bp, rates_bp, payment_bp

def register_blueprints(app):
    """Register donations module blueprints with the Flask app."""
    app.register_blueprint(wallet_bp)
    app.register_blueprint(donation_bp)
    app.register_blueprint(rates_bp)
    app.register_blueprint(payment_bp)

__all__ = [
    'wallet_bp',
    'donation_bp',
    'rates_bp',
    'payment_bp',
    'register_blueprints'
]