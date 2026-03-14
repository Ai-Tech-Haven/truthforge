"""
Authentication and Authorization Module for TruthForge API

This module provides decorators and utilities for API authentication
and role-based access control.
"""
import logging
from functools import wraps
from datetime import datetime, timezone
from flask import request, jsonify, current_app
from utils.api_keys import validate_api_key
from database.api_keys import APIKeyRole


logger = logging.getLogger(__name__)


def require_role(*allowed_roles):
    """
    Decorator to require specific roles for API endpoints.
    
    Usage:
        @require_role(APIKeyRole.PORT_AUTHORITY, APIKeyRole.ADMIN)
        def my_endpoint():
            ...
    
    Args:
        *allowed_roles: Variable number of APIKeyRole enum values
        
    Returns:
        Decorated function that validates API key and role
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get authorization header
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({
                    "error": {
                        "code": "MISSING_AUTH_TOKEN",
                        "message": "Authorization header is required",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }), 401
            
            # Extract token (format: "Bearer <token>")
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({
                    "error": {
                        "code": "INVALID_AUTH_FORMAT",
                        "message": "Authorization header must be in format: Bearer <token>",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }), 401
            
            token = parts[1]
            
            # Validate API key
            api_key = validate_api_key(token)
            
            if not api_key:
                return jsonify({
                    "error": {
                        "code": "INVALID_API_KEY",
                        "message": "Invalid or inactive API key",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }), 401
            
            # Check role authorization
            if allowed_roles and api_key.role not in allowed_roles:
                return jsonify({
                    "error": {
                        "code": "INSUFFICIENT_PERMISSIONS",
                        "message": f"This endpoint requires one of the following roles: {', '.join(r.value for r in allowed_roles)}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "details": {
                            "your_role": api_key.role.value,
                            "required_roles": [r.value for r in allowed_roles]
                        }
                    }
                }), 403
            
            # Store API key info in request context for use in endpoint
            request.api_key = api_key
            
            logger.info(f"Authenticated request from {api_key.name} (role: {api_key.role.value})")
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def optional_auth(f):
    """
    Decorator for endpoints that support optional authentication.
    
    If a valid API key is provided, it will be validated and stored in request.api_key.
    If no API key is provided or it's invalid, the request continues without authentication.
    
    Usage:
        @optional_auth
        def my_endpoint():
            if hasattr(request, 'api_key'):
                # Authenticated request
                ...
            else:
                # Unauthenticated request
                ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                api_key = validate_api_key(token)
                
                if api_key:
                    request.api_key = api_key
                    logger.info(f"Authenticated request from {api_key.name} (role: {api_key.role.value})")
        
        return f(*args, **kwargs)
    
    return decorated_function
