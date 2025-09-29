from .application_controller import application_bp
from .admin_application_controller import admin_application_bp
from .onlus_controller import onlus_bp
from .document_controller import document_bp
from .admin_onlus_controller import admin_onlus_bp

__all__ = [
    'application_bp',
    'admin_application_bp',
    'onlus_bp',
    'document_bp',
    'admin_onlus_bp'
]