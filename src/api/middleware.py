"""
API Middleware Module

This module provides middleware for the healthcare management system API,
including authentication, CORS, error handling, and request logging.
"""

import time
import json
import logging
from functools import wraps
from typing import Callable, Optional
from flask import request, jsonify, current_app, g
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

def setup_middleware(app):
    """Setup all middleware for the Flask application"""
    
    # CORS middleware
    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers to all responses"""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    # Request logging middleware
    @app.before_request
    def log_request():
        """Log incoming requests"""
        g.start_time = time.time()
        
        # Log request details
        logger.info(f"Request: {request.method} {request.path} - IP: {request.remote_addr}")
        
        # Log request body for non-GET requests
        if request.method != 'GET' and request.is_json:
            try:
                # Mask sensitive data
                body = request.get_json()
                masked_body = mask_sensitive_data(body)
                logger.debug(f"Request body: {json.dumps(masked_body, indent=2)}")
            except Exception as e:
                logger.warning(f"Failed to log request body: {str(e)}")
    
    # Response logging middleware
    @app.after_request
    def log_response(response):
        """Log response details"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            logger.info(f"Response: {response.status_code} - Duration: {duration:.3f}s")
        return response
    
    # Error handling middleware
    @app.errorhandler(Exception)
    def handle_exceptions(error):
        """Handle all exceptions and return appropriate responses"""
        logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        
        if isinstance(error, HTTPException):
            return jsonify({
                'success': False,
                'error': error.description,
                'status_code': error.code,
                'timestamp': time.time()
            }), error.code
        
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'status_code': 500,
            'timestamp': time.time()
        }), 500
    
    # Database connection middleware
    @app.before_request
    def check_database_connection():
        """Check database connection before each request"""
        try:
            from database.connection import check_database_health
            if not check_database_health():
                logger.error("Database connection is unhealthy")
                return jsonify({
                    'success': False,
                    'error': 'Database connection failed',
                    'status_code': 503,
                    'timestamp': time.time()
                }), 503
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Database health check failed',
                'status_code': 503,
                'timestamp': time.time()
            }), 503

def mask_sensitive_data(data: dict) -> dict:
    """Mask sensitive data in request/response bodies"""
    if not isinstance(data, dict):
        return data
    
    sensitive_fields = [
        'password', 'token', 'api_key', 'secret', 'ssn', 'credit_card',
        'insurance_number', 'medical_record_number'
    ]
    
    masked_data = data.copy()
    
    for field in sensitive_fields:
        if field in masked_data:
            if isinstance(masked_data[field], str):
                masked_data[field] = '*' * len(masked_data[field])
            else:
                masked_data[field] = '***'
    
    # Recursively mask nested dictionaries
    for key, value in masked_data.items():
        if isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value)
        elif isinstance(value, list):
            masked_data[key] = [
                mask_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
    
    return masked_data

def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'Authorization header required',
                'status_code': 401
            }), 401
        
        # Validate token (implement your authentication logic here)
        token = auth_header.replace('Bearer ', '')
        
        if not validate_token(token):
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token',
                'status_code': 401
            }), 401
        
        # Add user info to request context
        g.user = get_user_from_token(token)
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_role(required_role: str) -> Callable:
    """Decorator to require specific role for endpoints"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'status_code': 401
                }), 401
            
            # Check if user has required role
            user_roles = getattr(g.user, 'roles', [])
            if required_role not in user_roles:
                return jsonify({
                    'success': False,
                    'error': f'Role {required_role} required',
                    'status_code': 403
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit(max_requests: int = 100, window: int = 3600) -> Callable:
    """Decorator to implement rate limiting"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.remote_addr
            
            # Check rate limit (implement your rate limiting logic here)
            if is_rate_limited(client_ip, max_requests, window):
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'status_code': 429
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_token(token: str) -> bool:
    """Validate authentication token"""
    # Implement your token validation logic here
    # This is a placeholder implementation
    if not token:
        return False
    
    # Add your JWT validation, database lookup, etc.
    # For now, just check if token exists and has minimum length
    return len(token) >= 10

def get_user_from_token(token: str) -> Optional[dict]:
    """Get user information from token"""
    # Implement your token decoding logic here
    # This is a placeholder implementation
    try:
        # Add your JWT decoding, database lookup, etc.
        # For now, return a mock user
        return {
            'id': 'user123',
            'username': 'healthcare_user',
            'roles': ['nurse', 'doctor'],
            'permissions': ['read_patients', 'write_vitals']
        }
    except Exception as e:
        logger.error(f"Failed to decode token: {str(e)}")
        return None

def is_rate_limited(client_ip: str, max_requests: int, window: int) -> bool:
    """Check if client is rate limited"""
    # Implement your rate limiting logic here
    # This is a placeholder implementation
    # You could use Redis, database, or in-memory storage
    
    # For now, always return False (no rate limiting)
    return False

class RequestValidator:
    """Request validation middleware"""
    
    @staticmethod
    def validate_json_content_type():
        """Validate that request has JSON content type"""
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Content-Type must be application/json',
                    'status_code': 400
                }), 400
        return None
    
    @staticmethod
    def validate_required_fields(required_fields: list) -> Optional[tuple]:
        """Validate that required fields are present in request"""
        if request.is_json:
            data = request.get_json()
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            
            if missing_fields:
                return jsonify({
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}',
                    'status_code': 400
                }), 400
        return None

def setup_error_handlers(app):
    """Setup specific error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad request',
            'details': str(error),
            'status_code': 400
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 'Method not allowed',
            'status_code': 405
        }), 405
    
    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'status_code': 500
        }), 500

def setup_security_headers(app):
    """Setup security headers"""
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers to responses"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response
