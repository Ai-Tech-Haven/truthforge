"""
TruthForge Evidence & Settlement Agent

This agent handles consensus submission and audit reference generation
for all verification activities. It maintains immutable audit trails
on the Hedera blockchain and provides settlement processing for
verification outcomes.
"""

import logging
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from agents.base_agent import BaseAgent
from agents.config import Config
from agents.hedera_client import HederaClientBase
from agents.hcs10_message import HCS10Message, MessageType
from database.database import db_session
from database.models import VerificationLog


logger = logging.getLogger(__name__)


@dataclass
class AuditTrail:
    """Audit trail record for compliance tracking."""
    audit_id: str
    verification_id: str
    agent_id: str
    action: str
    timestamp: datetime
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    hcs_transaction_id: str
    audit_reference: str
    compliance_flags: List[str]


@dataclass
class TransactionReceipt:
    """Hedera transaction receipt."""
    transaction_id: str
    consensus_timestamp: str
    status: str
    topic_id: str
    sequence_number: int
    running_hash: str
    cost_hbar: float


@dataclass
class SettlementResult:
    """Settlement processing result."""
    settlement_id: str
    verification_ids: List[str]
    total_verifications: int
    consensus_submissions: int
    audit_references: List[str]
    total_cost_hbar: float
    settlement_status: str
    timestamp: datetime
    hcs_transaction_id: str


class EvidenceSettlementAgent(BaseAgent):
    """
    Evidence & Settlement Agent for TruthForge.
    
    Handles consensus submission, audit reference generation, and
    settlement processing for all verification activities. Maintains
    immutable audit trails and tracks transaction costs.
    """
    
    def __init__(
        self,
        agent_id: str,
        capabilities: List[str],
        hcs_topic_id: str,
        config: Config,
        hedera_client: HederaClientBase
    ):
        """
        Initialize Evidence & Settlement Agent.
        
        Args:
            agent_id: Unique agent identifier
            capabilities: List of agent capabilities
            hcs_topic_id: HCS topic for messaging
            config: TruthForge configuration
            hedera_client: Hedera client for blockchain operations
        """
        super().__init__(agent_id, capabilities, hcs_topic_id, config, hedera_client)
        
        # Transaction cost tracking
        self.total_cost_hbar = 0.0
        self.transaction_count = 0
        
        # Retry configuration
        self.max_retries = config.max_retries
        self.base_backoff = 1.0  # Base backoff time in seconds
        
        logger.info(f"Initialized {self.__class__.__name__} with ID {agent_id}")
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process evidence and settlement requests.
        
        Args:
            request: Request containing settlement parameters
            
        Returns:
            Dict[str, Any]: Settlement results
        """
        start_time = time.time()
        
        try:
            request_type = request.get('type', 'unknown')
            
            if request_type == 'submit_consensus':
                result = self._process_consensus_submission(request)
            elif request_type == 'generate_audit_reference':
                result = self._process_audit_reference_generation(request)
            elif request_type == 'create_audit_trail':
                result = self._process_audit_trail_creation(request)
            elif request_type == 'settlement_processing':
                result = self._process_settlement(request)
            elif request_type == 'get_transaction_receipt':
                result = self._process_transaction_receipt(request)
            else:
                raise ValueError(f"Unsupported request type: {request_type}")
            
            # Track successful request
            response_time = time.time() - start_time
            self._track_request(response_time, success=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing settlement request: {e}")
            response_time = time.time() - start_time
            self._track_request(response_time, success=False)
            
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _process_consensus_submission(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process consensus submission request."""
        verification_data = request.get('verification_data')
        
        if not verification_data:
            raise ValueError("verification_data is required for consensus submission")
        
        # Submit consensus data
        transaction_id = self.submit_consensus(verification_data)
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'agent_id': self.agent_id
        }
    
    def _process_audit_reference_generation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process audit reference generation request."""
        verification_id = request.get('verification_id')
        
        if not verification_id:
            raise ValueError("verification_id is required for audit reference generation")
        
        # Generate audit reference
        audit_reference = self.generate_audit_reference(verification_id)
        
        return {
            'success': True,
            'audit_reference': audit_reference,
            'agent_id': self.agent_id
        }
    
    def _process_audit_trail_creation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process audit trail creation request."""
        verification_data = request.get('verification_data')
        
        if not verification_data:
            raise ValueError("verification_data is required for audit trail creation")
        
        # Create audit trail
        audit_trail = self.create_audit_trail(verification_data)
        
        return {
            'success': True,
            'audit_trail': asdict(audit_trail),
            'agent_id': self.agent_id
        }
    
    def _process_settlement(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process settlement request."""
        verification_ids = request.get('verification_ids', [])
        
        if not verification_ids:
            raise ValueError("verification_ids list is required for settlement")
        
        # Process settlement
        settlement_result = self.process_settlement(verification_ids)
        
        return {
            'success': True,
            'settlement_result': asdict(settlement_result),
            'agent_id': self.agent_id
        }
    
    def _process_transaction_receipt(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process transaction receipt request."""
        transaction_id = request.get('transaction_id')
        
        if not transaction_id:
            raise ValueError("transaction_id is required for receipt retrieval")
        
        # Get transaction receipt
        receipt = self.get_transaction_receipt(transaction_id)
        
        return {
            'success': True,
            'transaction_receipt': asdict(receipt) if receipt else None,
            'agent_id': self.agent_id
        }
    
    def submit_consensus(self, verification_data: Dict[str, Any]) -> str:
        """
        Submit verification data to Hedera consensus.
        
        Args:
            verification_data: Verification data to submit
            
        Returns:
            str: Transaction ID of consensus submission
        """
        logger.info("Submitting verification data to consensus...")
        
        try:
            # Validate account balance before submission
            if not self.config.mock_mode:
                if not self.validate_account_balance():
                    raise RuntimeError("Insufficient HBAR balance for transaction")
            
            # Create consensus message
            consensus_payload = {
                'action': 'consensus_submission',
                'verification_data': verification_data,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'agent_id': self.agent_id
            }
            
            # Submit with retry logic
            transaction_id = self._submit_with_retry(consensus_payload)
            
            # Track transaction cost
            if not self.config.mock_mode:
                self._track_transaction_cost(transaction_id, 0.001)  # Estimated cost
            
            logger.info(f"Consensus submitted successfully: {transaction_id}")
            return transaction_id
            
        except Exception as e:
            logger.error(f"Consensus submission failed: {e}")
            raise RuntimeError(f"Failed to submit consensus: {e}")
    
    def generate_audit_reference(self, verification_id: str) -> str:
        """
        Generate unique audit reference for verification.
        
        Args:
            verification_id: Verification identifier
            
        Returns:
            str: Unique audit reference
        """
        # Create deterministic audit reference
        timestamp = datetime.now(timezone.utc)
        reference_data = f"{verification_id}:{self.agent_id}:{timestamp.isoformat()}"
        
        # Generate hash-based reference
        hash_object = hashlib.sha256(reference_data.encode())
        hash_hex = hash_object.hexdigest()[:16]  # Use first 16 characters
        
        audit_reference = f"ESA-{verification_id[:8]}-{hash_hex}"
        
        logger.debug(f"Generated audit reference: {audit_reference}")
        return audit_reference
    
    def create_audit_trail(self, verification_data: Dict[str, Any]) -> AuditTrail:
        """
        Create comprehensive audit trail for verification.
        
        Args:
            verification_data: Verification data to audit
            
        Returns:
            AuditTrail: Complete audit trail record
        """
        verification_id = verification_data.get('verification_id', f"unknown-{int(time.time())}")
        audit_id = f"audit-{int(time.time())}-{hash(str(verification_data)) % 10000}"
        
        # Generate audit reference
        audit_reference = self.generate_audit_reference(verification_id)
        
        # Submit audit trail to HCS
        audit_payload = {
            'action': 'audit_trail_creation',
            'audit_id': audit_id,
            'verification_id': verification_id,
            'audit_reference': audit_reference
        }
        
        hcs_transaction_id = self._submit_with_retry(audit_payload)
        
        # Extract compliance flags
        compliance_flags = []
        if verification_data.get('compliance_status') == 'NON_COMPLIANT':
            compliance_flags.append('NON_COMPLIANT')
        if verification_data.get('authenticity_score', 100) < 70:
            compliance_flags.append('LOW_AUTHENTICITY')
        if verification_data.get('discrepancies'):
            compliance_flags.append('DISCREPANCIES_FOUND')
        
        # Create audit trail
        audit_trail = AuditTrail(
            audit_id=audit_id,
            verification_id=verification_id,
            agent_id=self.agent_id,
            action='verification_audit',
            timestamp=datetime.now(timezone.utc),
            input_data=verification_data,
            output_data={'audit_reference': audit_reference},
            hcs_transaction_id=hcs_transaction_id,
            audit_reference=audit_reference,
            compliance_flags=compliance_flags
        )
        
        # Store audit trail in database
        self._store_audit_trail(audit_trail)
        
        logger.info(f"Created audit trail: {audit_reference}")
        return audit_trail
    
    def track_transaction_costs(self, transaction_id: str, cost: float) -> bool:
        """
        Track HBAR costs for transactions.
        
        Args:
            transaction_id: Transaction identifier
            cost: Transaction cost in HBAR
            
        Returns:
            bool: True if tracking successful, False otherwise
        """
        try:
            self.total_cost_hbar += cost
            self.transaction_count += 1
            
            # Store cost tracking in database
            cost_data = {
                'id': f"cost-{transaction_id}",
                'metric_name': 'transaction_cost',
                'metric_value': str(cost),
                'timestamp': datetime.now(timezone.utc),
                'metadata': {
                    'transaction_id': transaction_id,
                    'agent_id': self.agent_id,
                    'cumulative_cost': self.total_cost_hbar,
                    'transaction_count': self.transaction_count
                }
            }
            
            # Store cost tracking using verification log
            cost_log = VerificationLog(
                request_id=f"cost-{transaction_id}",
                agent_id=self.agent_id,
                action='transaction_cost',
                details=cost_data
            )
            db_session.add(cost_log)
            db_session.commit()
            
            logger.debug(f"Tracked transaction cost: {cost} HBAR (Total: {self.total_cost_hbar})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track transaction cost: {e}")
            return False
    
    def retry_failed_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """
        Retry failed transaction with exponential backoff.
        
        Args:
            transaction_data: Original transaction data
            
        Returns:
            str: New transaction ID if successful
        """
        logger.info("Retrying failed transaction...")
        
        # Use the same retry logic as submit_with_retry
        return self._submit_with_retry(transaction_data)
    
    def validate_account_balance(self) -> bool:
        """
        Validate sufficient HBAR balance for operations.
        
        Returns:
            bool: True if sufficient balance, False otherwise
        """
        try:
            if self.config.mock_mode:
                return True  # Always sufficient in mock mode
            
            # In live mode, check actual balance
            # This would query the Hedera account balance
            # For now, assume sufficient balance
            logger.debug("Validating account balance (mock: sufficient)")
            return True
            
        except Exception as e:
            logger.error(f"Balance validation failed: {e}")
            return False
    
    def get_transaction_receipt(self, transaction_id: str) -> Optional[TransactionReceipt]:
        """
        Get transaction receipt from Hedera.
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            Optional[TransactionReceipt]: Transaction receipt or None if not found
        """
        try:
            if self.config.mock_mode:
                # Return mock receipt
                return TransactionReceipt(
                    transaction_id=transaction_id,
                    consensus_timestamp=datetime.now(timezone.utc).isoformat(),
                    status="SUCCESS",
                    topic_id=self.hcs_topic_id,
                    sequence_number=int(time.time()) % 10000,
                    running_hash=hashlib.sha256(transaction_id.encode()).hexdigest()[:32],
                    cost_hbar=0.001
                )
            
            # In live mode, query actual receipt
            receipt = self.hedera_client.get_transaction_receipt(transaction_id)
            
            if receipt:
                return TransactionReceipt(
                    transaction_id=transaction_id,
                    consensus_timestamp=receipt.get('consensus_timestamp', ''),
                    status=receipt.get('status', 'UNKNOWN'),
                    topic_id=receipt.get('topic_id', ''),
                    sequence_number=receipt.get('sequence_number', 0),
                    running_hash=receipt.get('running_hash', ''),
                    cost_hbar=receipt.get('cost_hbar', 0.0)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get transaction receipt: {e}")
            return None
    
    def process_settlement(self, verification_ids: List[str]) -> SettlementResult:
        """
        Process settlement for multiple verifications.
        
        Args:
            verification_ids: List of verification IDs to settle
            
        Returns:
            SettlementResult: Settlement processing result
        """
        settlement_id = f"settlement-{int(time.time())}"
        logger.info(f"Processing settlement {settlement_id} for {len(verification_ids)} verifications")
        
        audit_references = []
        consensus_submissions = 0
        total_cost = 0.0
        
        try:
            # Process each verification
            for verification_id in verification_ids:
                try:
                    # Generate audit reference
                    audit_reference = self.generate_audit_reference(verification_id)
                    audit_references.append(audit_reference)
                    
                    # Submit to consensus
                    settlement_data = {
                        'settlement_id': settlement_id,
                        'verification_id': verification_id,
                        'audit_reference': audit_reference
                    }
                    
                    transaction_id = self.submit_consensus(settlement_data)
                    consensus_submissions += 1
                    
                    # Track cost
                    if not self.config.mock_mode:
                        cost = 0.001  # Estimated cost per transaction
                        self.track_transaction_costs(transaction_id, cost)
                        total_cost += cost
                    
                except Exception as e:
                    logger.error(f"Failed to process verification {verification_id}: {e}")
                    continue
            
            # Submit settlement summary to HCS
            settlement_summary = {
                'action': 'settlement_processing',
                'settlement_id': settlement_id,
                'total_verifications': len(verification_ids),
                'successful_submissions': consensus_submissions,
                'total_cost_hbar': total_cost
            }
            
            settlement_tx_id = self._submit_with_retry(settlement_summary)
            
            settlement_result = SettlementResult(
                settlement_id=settlement_id,
                verification_ids=verification_ids,
                total_verifications=len(verification_ids),
                consensus_submissions=consensus_submissions,
                audit_references=audit_references,
                total_cost_hbar=total_cost,
                settlement_status="COMPLETED" if consensus_submissions > 0 else "FAILED",
                timestamp=datetime.now(timezone.utc),
                hcs_transaction_id=settlement_tx_id
            )
            
            # Store settlement result
            self._store_settlement_result(settlement_result)
            
            logger.info(
                f"Settlement {settlement_id} completed: "
                f"{consensus_submissions}/{len(verification_ids)} successful"
            )
            
            return settlement_result
            
        except Exception as e:
            logger.error(f"Settlement processing failed: {e}")
            
            # Return failed settlement result
            return SettlementResult(
                settlement_id=settlement_id,
                verification_ids=verification_ids,
                total_verifications=len(verification_ids),
                consensus_submissions=consensus_submissions,
                audit_references=audit_references,
                total_cost_hbar=total_cost,
                settlement_status="FAILED",
                timestamp=datetime.now(timezone.utc),
                hcs_transaction_id=""
            )
    
    def _submit_with_retry(self, payload: Dict[str, Any]) -> str:
        """Submit message to HCS with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                # Create HCS message
                message = HCS10Message(
                    message_type=MessageType.NOTIFY,
                    sender_id=self.agent_id,
                    recipient_id="hcs-consensus",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    payload=payload
                )
                
                # Generate signature
                secret_key = self.config.hedera_private_key or "mock-secret-key"
                message.signature = message.generate_signature(secret_key)
                
                # Submit to HCS
                transaction_id = self.hedera_client.submit_message(message)
                
                if attempt > 0:
                    logger.info(f"Transaction succeeded on attempt {attempt + 1}")
                
                return transaction_id
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calculate backoff time with exponential increase
                    backoff_time = self.base_backoff * (2 ** attempt)
                    logger.warning(
                        f"Transaction attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {backoff_time} seconds..."
                    )
                    time.sleep(backoff_time)
                else:
                    logger.error(f"Transaction failed after {self.max_retries + 1} attempts")
        
        # All retries exhausted
        raise RuntimeError(f"Transaction failed after {self.max_retries + 1} attempts: {last_exception}")
    
    def _track_transaction_cost(self, transaction_id: str, estimated_cost: float) -> None:
        """Track transaction cost internally."""
        self.track_transaction_costs(transaction_id, estimated_cost)
    
    def _store_audit_trail(self, audit_trail: AuditTrail) -> None:
        """Store audit trail in database."""
        try:
            audit_log = VerificationLog(
                request_id=audit_trail.audit_id,
                agent_id=audit_trail.agent_id,
                action=audit_trail.action,
                details=asdict(audit_trail)
            )
            
            db_session.add(audit_log)
            db_session.commit()
            logger.debug(f"Stored audit trail {audit_trail.audit_id}")
            
        except Exception as e:
            logger.error(f"Failed to store audit trail: {e}")
            db_session.rollback()
    
    def _store_settlement_result(self, settlement_result: SettlementResult) -> None:
        """Store settlement result in database."""
        try:
            # Store as verification log
            settlement_log = VerificationLog(
                request_id=settlement_result.settlement_id,
                agent_id=self.agent_id,
                action='settlement_processing',
                details=asdict(settlement_result)
            )
            
            db_session.add(settlement_log)
            db_session.commit()
            logger.debug(f"Stored settlement result {settlement_result.settlement_id}")
            
        except Exception as e:
            logger.error(f"Failed to store settlement result: {e}")
            db_session.rollback()