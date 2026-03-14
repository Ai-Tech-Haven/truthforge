"""
API Keys Database Model for TruthForge

This module defines the database model for API key management,
supporting role-based access control for port authorities and enterprises.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from database.database import Base
import enum


class APIKeyRole(enum.Enum):
    """API key roles for access control"""
    PORT_AUTHORITY = "port_authority"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class APIKey(Base):
    """
    API Key model for authentication and authorization.
    
    Attributes:
        key: Unique API key string (hashed)
        name: Human-readable name for the key
        role: Role assigned to this key (port_authority, enterprise, admin)
        created_at: Timestamp when key was created
        last_used: Timestamp when key was last used
        is_active: Whether the key is currently active
        created_by: User or system that created the key
    """
    __tablename__ = 'api_keys'
    
    key = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(APIKeyRole), nullable=False, default=APIKeyRole.ENTERPRISE)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<APIKey(name='{self.name}', role='{self.role.value}', active={self.is_active})>"
    
    def to_dict(self):
        """Convert API key to dictionary representation"""
        return {
            "key": self.key,
            "name": self.name,
            "role": self.role.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "is_active": self.is_active,
            "created_by": self.created_by
        }
