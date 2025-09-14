from flask import jsonify
from typing import Any, Dict, Optional

def success_response(message: str, data: Any = None, status_code: int = 200):
    response = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code

def error_response(message: str, data: Any = None, status_code: int = 400):
    response = {
        'success': False,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code

def validation_error_response(errors: Dict[str, str], status_code: int = 422):
    return jsonify({
        'success': False,
        'message': 'Validation errors',
        'errors': errors
    }), status_code

def paginated_response(data: list, page: int, per_page: int, 
                      total: int, message: str = "Data retrieved successfully"):
    return jsonify({
        'success': True,
        'message': message,
        'data': data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    }), 200