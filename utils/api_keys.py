"""
API Key Generation and Validation Utilities

This module provides functions for generating, hashing, and validating API keys
for TruthForge authentication and authorization.
"""
import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple
from database.api_keys import APIKey, APIKeyRole
from database.database import db_session


def generate_api_key() -> str:
    """
    Generate a secure random API key.
    
    Returns:
        str: A 32-character hexadecimal API key
    """
    return secrets.token_hex(32)


def hash_api_key(key: str) -> str:
    """
    Hash an API key using SHA-256.
    
    Args:
        key: The plain text API key
        
    Returns:
        str: The hashed API key (64 characters)
    """
    return hashlib.sha256(key.encode()).hexdigest()


def create_api_key(
    name: str,
    role: APIKeyRole,
    created_by: Optional[str] = None
) -> Tuple[str, APIKey]:
    """
    Create a new API key and store it in the database.
    
    Args:
        name: Human-readable name for the key
        role: Role to assign to the key
        created_by: User or system that created the key
        
    Returns:
        Tuple[str, APIKey]: The plain text key and the database record
    """
    # Generate plain text key
    plain_key = generate_api_key()
    
    # Hash the key for storage
    hashed_key = hash_api_key(plain_key)
    
    # Create database record
    api_key = APIKey(
        key=hashed_key,
        name=name,
        role=role,
        created_by=created_by,
        is_active=True
    )
    
    # Save to database
    db_session.add(api_key)
    db_session.commit()
    
    return plain_key, api_key


def validate_api_key(key: str) -> Optional[APIKey]:
    """
    Validate an API key and return the associated record if valid.
    
    Args:
        key: The plain text API key to validate
        
    Returns:
        Optional[APIKey]: The API key record if valid and active, None otherwise
    """
    # Hash the provided key
    hashed_key = hash_api_key(key)
    
    # Query database
    api_key = db_session.query(APIKey).filter_by(
        key=hashed_key,
        is_active=True
    ).first()
    
    if api_key:
        # Update last_used timestamp
        api_key.last_used = datetime.now(timezone.utc)
        db_session.commit()
    
    return api_key


def revoke_api_key(key: str) -> bool:
    """
    Revoke an API key by marking it as inactive.
    
    Args:
        key: The plain text API key to revoke
        
    Returns:
        bool: True if key was revoked, False if not found
    """
    hashed_key = hash_api_key(key)
    
    api_key = db_session.query(APIKey).filter_by(key=hashed_key).first()
    
    if api_key:
        api_key.is_active = False
        db_session.commit()
        return True
    
    return False


def list_api_keys(role: Optional[APIKeyRole] = None, active_only: bool = True) -> list:
    """
    List API keys, optionally filtered by role and active status.
    
    Args:
        role: Optional role filter
        active_only: If True, only return active keys
        
    Returns:
        list: List of APIKey records
    """
    query = db_session.query(APIKey)
    
    if role:
        query = query.filter_by(role=role)
    
    if active_only:
        query = query.filter_by(is_active=True)
    
    return query.all()
