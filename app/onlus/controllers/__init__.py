from .application_controller import application_bp
from .admin_application_controller import admin_application_bp
from .onlus_controller import onlus_bp
from .document_controller import document_bp
from .admin_onlus_controller import admin_onlus_bp

# GOO-19 Smart Allocation & Financial Control controllers
from .allocation_controller import allocation_bp
from .financial_controller import financial_bp
from .compliance_controller import compliance_bp

__all__ = [
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