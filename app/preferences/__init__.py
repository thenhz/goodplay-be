from flask import Blueprint
from .controllers.preferences_controller import preferences_blueprint

def create_preferences_module(app):
    app.register_blueprint(preferences_blueprint)
    return preferences_blueprint