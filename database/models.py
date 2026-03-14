"""
Database models for TruthForge - Production Ready
Supports both PostgreSQL (live) and SQLite (fallback)
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database.database import Base


class Verification(Base):
    """Verification requests and results"""
    __tablename__ = 'verifications'
    
    id = Column(String(36), primary_key=True)
    request_id = Column(String(36), unique=True, nullable=False, index=True)
    verification_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    
    # Request data
    order_id = Column(String(100), nullable=True, index=True)
    tracking_number = Column(String(100), nullable=True, index=True)
    shipment_id = Column(String(100), nullable=True, index=True)
    
    # Results
    authenticity_score = Column(Float, nullable=True)
    compliance_score = Column(Float, nullable=True)
    verification_result = Column(JSON, nullable=True)
    
    # Blockchain references
    hcs_transaction_id = Column(String(100), nullable=True)
    consensus_timestamp = Column(String(50), nullable=True)
    audit_reference = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    
    # Mode tracking
    mock_mode = Column(Boolean, default=False, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'verification_type': self.verification_type,
            'status': self.status,
            'order_id': self.order_id,
            'tracking_number': self.tracking_number,
            'shipment_id': self.shipment_id,
            'authenticity_score': self.authenticity_score,
            'compliance_score': self.compliance_score,
            'verification_result': self.verification_result,
            'hcs_transaction_id': self.hcs_transaction_id,
            'consensus_timestamp': self.consensus_timestamp,
            'audit_reference': self.audit_reference,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'mock_mode': self.mock_mode
        }


class AgentStatus(Base):
    """Agent health and status tracking"""
    __tablename__ = 'agent_status'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(200), nullable=False)
    
    # Status
    status = Column(String(20), nullable=False, default='offline')
    health_score = Column(Integer, default=0)
    
    # HOL Registration
    hol_uaid = Column(String(100), nullable=True)
    hcs_topic_id = Column(String(50), nullable=True)
    capabilities = Column(JSON, nullable=True)
    
    # Metrics
    requests_processed = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    error_count = Column(Integer, default=0)
    
    # Timestamps
    last_heartbeat = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'status': self.status,
            'health_score': self.health_score,
            'hol_uaid': self.hol_uaid,
            'hcs_topic_id': self.hcs_topic_id,
            'capabilities': self.capabilities,
            'requests_processed': self.requests_processed,
            'average_response_time': self.average_response_time,
            'success_rate': self.success_rate,
            'error_count': self.error_count,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Shipment(Base):
    """Shipment tracking data"""
    __tablename__ = 'shipments'
    
    id = Column(String(36), primary_key=True)
    shipment_id = Column(String(100), unique=True, nullable=False, index=True)
    tracking_number = Column(String(100), nullable=True, index=True)
    
    # Carrier info
    carrier = Column(String(50), nullable=True)
    vessel_name = Column(String(200), nullable=True)
    
    # Locations
    origin_port = Column(String(200), nullable=True)
    destination_port = Column(String(200), nullable=True)
    current_location = Column(String(200), nullable=True)
    
    # Status
    clearance_status = Column(String(50), default='pending')
    verification_status = Column(String(50), default='pending')
    priority = Column(String(20), default='medium')
    
    # Timing
    estimated_arrival = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    clearance_time = Column(Float, nullable=True)  # in hours
    
    # References
    order_id = Column(String(100), nullable=True)
    verification_id = Column(String(36), ForeignKey('verifications.id'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    verification = relationship("Verification", backref="shipments")
    
    def to_dict(self):
        return {
            'id': self.id,
            'shipment_id': self.shipment_id,
            'tracking_number': self.tracking_number,
            'carrier': self.carrier,
            'vessel_name': self.vessel_name,
            'origin_port': self.origin_port,
            'destination_port': self.destination_port,
            'current_location': self.current_location,
            'clearance_status': self.clearance_status,
            'verification_status': self.verification_status,
            'priority': self.priority,
            'estimated_arrival': self.estimated_arrival.isoformat() if self.estimated_arrival else None,
            'actual_arrival': self.actual_arrival.isoformat() if self.actual_arrival else None,
            'clearance_time': self.clearance_time,
            'order_id': self.order_id,
            'verification_id': self.verification_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PortTrustReceipt(Base):
    """Port trust receipts for clearance"""
    __tablename__ = 'port_trust_receipts'
    
    id = Column(String(36), primary_key=True)
    receipt_id = Column(String(100), unique=True, nullable=False, index=True)
    shipment_id = Column(String(36), ForeignKey('shipments.id'), nullable=False)
    
    # Receipt details
    clearance_status = Column(String(50), default='pending')
    agent_signatures = Column(JSON, nullable=True)  # List of agent signatures
    
    # Blockchain proof
    hedera_tx_ref = Column(String(100), nullable=True)
    consensus_timestamp = Column(String(50), nullable=True)
    
    # Port details
    vessel_name = Column(String(200), nullable=True)
    port_name = Column(String(200), nullable=True)
    
    # Timestamps
    issued_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    shipment = relationship("Shipment", backref="port_receipts")
    
    def to_dict(self):
        return {
            'id': self.id,
            'receipt_id': self.receipt_id,
            'shipment_id': self.shipment_id,
            'clearance_status': self.clearance_status,
            'agent_signatures': self.agent_signatures,
            'hedera_tx_ref': self.hedera_tx_ref,
            'consensus_timestamp': self.consensus_timestamp,
            'vessel_name': self.vessel_name,
            'port_name': self.port_name,
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AuditTrail(Base):
    """Audit trail for compliance"""
    __tablename__ = 'audit_trails'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # References
    verification_id = Column(String(36), ForeignKey('verifications.id'), nullable=True)
    agent_id = Column(String(100), nullable=False)
    
    # Action details
    action = Column(String(100), nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    # Blockchain proof
    hcs_transaction_id = Column(String(100), nullable=True)
    audit_reference = Column(String(100), nullable=True)
    
    # Compliance
    compliance_flags = Column(JSON, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    verification = relationship("Verification", backref="audit_trails")
    
    def to_dict(self):
        return {
            'id': self.id,
            'audit_id': self.audit_id,
            'verification_id': self.verification_id,
            'agent_id': self.agent_id,
            'action': self.action,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'hcs_transaction_id': self.hcs_transaction_id,
            'audit_reference': self.audit_reference,
            'compliance_flags': self.compliance_flags,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class DashboardMetrics(Base):
    """Dashboard operational metrics"""
    __tablename__ = 'dashboard_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Metrics
    total_verifications = Column(Integer, default=0)
    avg_clearance_time = Column(Float, default=0.0)  # in minutes
    cost_savings = Column(Float, default=0.0)  # in USD
    active_agents = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    shipments_today = Column(Integer, default=0)
    documents_pre_arrival = Column(Integer, default=0)
    shipments_pre_cleared = Column(Integer, default=0)
    
    # Timestamp
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    
    def to_dict(self):
        return {
            'totalVerifications': self.total_verifications,
            'avgClearanceTime': f"{self.avg_clearance_time:.1f} min",
            'costSavings': f"${self.cost_savings/1000000:.1f}M" if self.cost_savings >= 1000000 else f"${self.cost_savings/1000:.1f}K",
            'activeAgents': self.active_agents,
            'successRate': self.success_rate,
            'shipmentsToday': self.shipments_today,
            'documentsPreArrival': self.documents_pre_arrival,
            'shipmentsPreCleared': self.shipments_pre_cleared,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON
from sqlalchemy.sql import func
from database.database import Base

class VerificationRequest(Base):
    """Model for verification requests"""
    __tablename__ = 'verification_requests'
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(255), unique=True, index=True)
    user_id = Column(String(255), index=True)
    image_url = Column(Text)
    document_url = Column(Text)
    shipment_id = Column(String(255))
    status = Column(String(50), default='pending')
    authenticity_score = Column(Float)
    analysis_results = Column(JSON)
    hcs_transaction_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Agent(Base):
    """Model for registered agents"""
    __tablename__ = 'agents'
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(255), unique=True, index=True)
    uaid = Column(String(255), unique=True)
    hcs_topic_id = Column(String(255))
    status = Column(String(50), default='active')
    last_heartbeat = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class VerificationLog(Base):
    """Model for verification logs"""
    __tablename__ = 'verification_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(255), index=True)
    agent_id = Column(String(255))
    action = Column(String(100))
    details = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ShipmentData(Base):
    """Model for shipment data"""
    __tablename__ = 'shipment_data'
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(String(255), unique=True, index=True)
    carrier = Column(String(100))
    tracking_number = Column(String(255))
    origin = Column(String(255))
    destination = Column(String(255))
    status = Column(String(100))
    estimated_delivery = Column(DateTime(timezone=True))
    shipment_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())