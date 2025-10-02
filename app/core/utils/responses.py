from flask import jsonify
from typing import Any, Dict, Optional
from app.core.utils.json_encoder import serialize_model_dates


def success_response(message: str, data: Any = None, status_code: int = 200):
    """
    Standard success response with automatic datetime serialization to ISO 8601.

    Args:
        message: Constant message key for UI localization
        data: Response data (will be serialized with ISO 8601 dates)
        status_code: HTTP status code (default: 200)

    Returns:
        Flask JSON response with all datetime fields in ISO 8601 format
    """
    response = {
        'success': True,
        'message': message
    }

    if data is not None:
        # Ensure all datetime fields are in ISO 8601 format
        response['data'] = serialize_model_dates(data)

    return jsonify(response), status_code


def error_response(message: str, data: Any = None, status_code: int = 400):
    """
    Standard error response with automatic datetime serialization to ISO 8601.

    Args:
        message: Constant message key for UI localization
        data: Additional error data (will be serialized with ISO 8601 dates)
        status_code: HTTP status code (default: 400)

    Returns:
        Flask JSON response with all datetime fields in ISO 8601 format
    """
    response = {
        'success': False,
        'message': message
    }

    if data is not None:
        # Ensure all datetime fields are in ISO 8601 format
        response['data'] = serialize_model_dates(data)

    return jsonify(response), status_code


def validation_error_response(errors: Dict[str, str], status_code: int = 422):
    """
    Validation error response.

    Args:
        errors: Dictionary of validation errors
        status_code: HTTP status code (default: 422)

    Returns:
        Flask JSON response
    """
    return jsonify({
        'success': False,
        'message': 'Validation errors',
        'errors': errors
    }), status_code


def paginated_response(data: list, page: int, per_page: int,
                      total: int, message: str = "Data retrieved successfully"):
    """
    Paginated response with automatic datetime serialization to ISO 8601.

    Args:
        data: List of items (will be serialized with ISO 8601 dates)
        page: Current page number
        per_page: Items per page
        total: Total number of items
        message: Response message

    Returns:
        Flask JSON response with pagination metadata and ISO 8601 dates
    """
    return jsonify({
        'success': True,
        'message': message,
        'data': serialize_model_dates(data),
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }), 200