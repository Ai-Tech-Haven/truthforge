"""
Database service layer for TruthForge
Provides high-level database operations for live mode
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database.database import db_session
from database.models import (
    Verification, AgentStatus, Shipment, PortTrustReceipt,
    AuditTrail, DashboardMetrics
)

logger = logging.getLogger(__name__)


class VerificationService:
    """Service for verification operations"""
    
    @staticmethod
    def create_verification(
        request_id: str,
        verification_type: str,
        order_id: Optional[str] = None,
        tracking_number: Optional[str] = None,
        shipment_id: Optional[str] = None,
        mock_mode: bool = False
    ) -> Verification:
        """Create a new verification record"""
        verification = Verification(
            id=str(uuid.uuid4()),
            request_id=request_id,
            verification_type=verification_type,
            status='pending',
            order_id=order_id,
            tracking_number=tracking_number,
            shipment_id=shipment_id,
            mock_mode=mock_mode
        )
        
        db_session.add(verification)
        db_session.commit()
        
        logger.info(f"Created verification: {verification.id}")
        return verification
    
    @staticmethod
    def update_verification(
        verification_id: str,
        status: Optional[str] = None,
        authenticity_score: Optional[float] = None,
        compliance_score: Optional[float] = None,
        verification_result: Optional[Dict] = None,
        hcs_transaction_id: Optional[str] = None,
        consensus_timestamp: Optional[str] = None,
        audit_reference: Optional[str] = None
    ) -> Optional[Verification]:
        """Update verification record"""
        verification = db_session.query(Verification).filter_by(id=verification_id).first()
        
        if not verification:
            logger.warning(f"Verification not found: {verification_id}")
            return None
        
        if status:
            verification.status = status
        if authenticity_score is not None:
            verification.authenticity_score = authenticity_score
        if compliance_score is not None:
            verification.compliance_score = compliance_score
        if verification_result:
            verification.verification_result = verification_result
        if hcs_transaction_id:
            verification.hcs_transaction_id = hcs_transaction_id
        if consensus_timestamp:
            verification.consensus_timestamp = consensus_timestamp
        if audit_reference:
            verification.audit_reference = audit_reference
        
        if status in ['completed', 'error', 'failed']:
            verification.completed_at = datetime.now(timezone.utc)
        
        verification.updated_at = datetime.now(timezone.utc)
        
        db_session.commit()
        logger.info(f"Updated verification: {verification_id}")
        
        return verification
    
    @staticmethod
    def get_verification(verification_id: str) -> Optional[Verification]:
        """Get verification by ID"""
        return db_session.query(Verification).filter_by(id=verification_id).first()
    
    @staticmethod
    def get_verification_by_request_id(request_id: str) -> Optional[Verification]:
        """Get verification by request ID"""
        return db_session.query(Verification).filter_by(request_id=request_id).first()
    
    @staticmethod
    def list_verifications(limit: int = 50, offset: int = 0, shipment_id: Optional[str] = None) -> tuple:
        """List verifications with pagination"""
        query = db_session.query(Verification)
        
        if shipment_id:
            query = query.filter_by(shipment_id=shipment_id)
        
        total = query.count()
        verifications = query.order_by(desc(Verification.created_at)).limit(limit).offset(offset).all()
        
        return verifications, total


class AgentService:
    """Service for agent operations"""
    
    @staticmethod
    def upsert_agent(
        agent_id: str,
        agent_name: str,
        status: str = 'online',
        hol_uaid: Optional[str] = None,
        hcs_topic_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None
    ) -> AgentStatus:
        """Create or update agent status"""
        agent = db_session.query(AgentStatus).filter_by(agent_id=agent_id).first()
        
        if agent:
            # Update existing
            agent.agent_name = agent_name
            agent.status = status
            agent.last_heartbeat = datetime.now(timezone.utc)
            if hol_uaid:
                agent.hol_uaid = hol_uaid
            if hcs_topic_id:
                agent.hcs_topic_id = hcs_topic_id
            if capabilities:
                agent.capabilities = capabilities
            agent.updated_at = datetime.now(timezone.utc)
        else:
            # Create new
            agent = AgentStatus(
                agent_id=agent_id,
                agent_name=agent_name,
                status=status,
                hol_uaid=hol_uaid,
                hcs_topic_id=hcs_topic_id,
                capabilities=capabilities,
                last_heartbeat=datetime.now(timezone.utc)
            )
            db_session.add(agent)
        
        db_session.commit()
        logger.info(f"Upserted agent: {agent_id}")
        
        return agent
    
    @staticmethod
    def update_agent_metrics(
        agent_id: str,
        requests_processed: Optional[int] = None,
        average_response_time: Optional[float] = None,
        success_rate: Optional[float] = None,
        error_count: Optional[int] = None,
        health_score: Optional[int] = None
    ) -> Optional[AgentStatus]:
        """Update agent metrics"""
        agent = db_session.query(AgentStatus).filter_by(agent_id=agent_id).first()
        
        if not agent:
            return None
        
        if requests_processed is not None:
            agent.requests_processed = requests_processed
        if average_response_time is not None:
            agent.average_response_time = average_response_time
        if success_rate is not None:
            agent.success_rate = success_rate
        if error_count is not None:
            agent.error_count = error_count
        if health_score is not None:
            agent.health_score = health_score
        
        agent.last_heartbeat = datetime.now(timezone.utc)
        agent.updated_at = datetime.now(timezone.utc)
        
        db_session.commit()
        return agent
    
    @staticmethod
    def list_agents() -> List[AgentStatus]:
        """List all agents"""
        return db_session.query(AgentStatus).all()
    
    @staticmethod
    def get_agent(agent_id: str) -> Optional[AgentStatus]:
        """Get agent by ID"""
        return db_session.query(AgentStatus).filter_by(agent_id=agent_id).first()


class ShipmentService:
    """Service for shipment operations"""
    
    @staticmethod
    def create_shipment(
        shipment_id: str,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None,
        vessel_name: Optional[str] = None,
        origin_port: Optional[str] = None,
        destination_port: Optional[str] = None,
        estimated_arrival: Optional[datetime] = None,
        order_id: Optional[str] = None
    ) -> Shipment:
        """Create a new shipment"""
        shipment = Shipment(
            id=str(uuid.uuid4()),
            shipment_id=shipment_id,
            tracking_number=tracking_number,
            carrier=carrier,
            vessel_name=vessel_name,
            origin_port=origin_port,
            destination_port=destination_port,
            estimated_arrival=estimated_arrival,
            order_id=order_id
        )
        
        db_session.add(shipment)
        db_session.commit()
        
        logger.info(f"Created shipment: {shipment_id}")
        return shipment
    
    @staticmethod
    def update_shipment(
        shipment_id: str,
        clearance_status: Optional[str] = None,
        verification_status: Optional[str] = None,
        current_location: Optional[str] = None,
        actual_arrival: Optional[datetime] = None,
        clearance_time: Optional[float] = None
    ) -> Optional[Shipment]:
        """Update shipment"""
        shipment = db_session.query(Shipment).filter_by(shipment_id=shipment_id).first()
        
        if not shipment:
            return None
        
        if clearance_status:
            shipment.clearance_status = clearance_status
        if verification_status:
            shipment.verification_status = verification_status
        if current_location:
            shipment.current_location = current_location
        if actual_arrival:
            shipment.actual_arrival = actual_arrival
        if clearance_time is not None:
            shipment.clearance_time = clearance_time
        
        shipment.updated_at = datetime.now(timezone.utc)
        
        db_session.commit()
        return shipment
    
    @staticmethod
    def list_shipments(limit: int = 50, offset: int = 0) -> tuple:
        """List shipments with pagination"""
        query = db_session.query(Shipment)
        total = query.count()
        shipments = query.order_by(desc(Shipment.created_at)).limit(limit).offset(offset).all()
        
        return shipments, total
    
    @staticmethod
    def get_shipment(shipment_id: str) -> Optional[Shipment]:
        """Get shipment by ID"""
        return db_session.query(Shipment).filter_by(shipment_id=shipment_id).first()


class MetricsService:
    """Service for dashboard metrics"""
    
    @staticmethod
    def get_latest_metrics() -> Optional[DashboardMetrics]:
        """Get latest dashboard metrics"""
        return db_session.query(DashboardMetrics).order_by(desc(DashboardMetrics.timestamp)).first()
    
    @staticmethod
    def calculate_and_store_metrics() -> DashboardMetrics:
        """Calculate current metrics and store"""
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Calculate metrics from database
        total_verifications = db_session.query(func.count(Verification.id)).scalar() or 0
        
        # Get completed verifications for clearance time
        completed = db_session.query(Verification).filter_by(status='completed').all()
        avg_clearance_time = 0.0
        if completed:
            times = [(v.completed_at - v.created_at).total_seconds() / 60 for v in completed if v.completed_at]
            avg_clearance_time = sum(times) / len(times) if times else 0.0
        
        # Active agents
        active_agents = db_session.query(func.count(AgentStatus.id)).filter_by(status='online').scalar() or 0
        
        # Success rate
        success_count = db_session.query(func.count(Verification.id)).filter_by(status='completed').scalar() or 0
        success_rate = (success_count / total_verifications * 100) if total_verifications > 0 else 0.0
        
        # Shipments today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        shipments_today = db_session.query(func.count(Shipment.id)).filter(
            Shipment.created_at >= today_start
        ).scalar() or 0
        
        # Pre-cleared shipments
        shipments_pre_cleared = db_session.query(func.count(Shipment.id)).filter_by(
            clearance_status='cleared'
        ).scalar() or 0
        
        # Documents pre-arrival (verifications completed before arrival)
        documents_pre_arrival = db_session.query(func.count(Verification.id)).filter_by(
            status='completed'
        ).scalar() or 0
        
        # Cost savings (mock calculation: $350 per verification)
        cost_savings = total_verifications * 350.0
        
        # Create metrics record
        metrics = DashboardMetrics(
            total_verifications=total_verifications,
            avg_clearance_time=avg_clearance_time,
            cost_savings=cost_savings,
            active_agents=active_agents,
            success_rate=success_rate,
            shipments_today=shipments_today,
            documents_pre_arrival=documents_pre_arrival,
            shipments_pre_cleared=shipments_pre_cleared,
            date=today
        )
        
        db_session.add(metrics)
        db_session.commit()
        
        logger.info(f"Calculated and stored metrics for {today}")
        return metrics


class AuditService:
    """Service for audit trail operations"""
    
    @staticmethod
    def create_audit_trail(
        verification_id: str,
        agent_id: str,
        action: str,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        hcs_transaction_id: Optional[str] = None,
        audit_reference: Optional[str] = None,
        compliance_flags: Optional[List[str]] = None
    ) -> AuditTrail:
        """Create audit trail entry"""
        audit = AuditTrail(
            audit_id=f"audit_{uuid.uuid4().hex[:12]}",
            verification_id=verification_id,
            agent_id=agent_id,
            action=action,
            input_data=input_data,
            output_data=output_data,
            hcs_transaction_id=hcs_transaction_id,
            audit_reference=audit_reference,
            compliance_flags=compliance_flags
        )
        
        db_session.add(audit)
        db_session.commit()
        
        logger.info(f"Created audit trail: {audit.audit_id}")
        return audit
