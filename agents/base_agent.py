"""
TruthForge Base Agent

This module provides the abstract base class for all TruthForge agents.
All specialized agents (Orchestrator, Document Verifier, etc.) inherit
from BaseAgent to ensure consistent behavior and HOL integration.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from agents.config import Config
from agents.hedera_client import HederaClientBase
from agents.hcs10_message import HCS10Message, MessageType


logger = logging.getLogger(__name__)


@dataclass
class AgentStatus:
    """
    Agent health and status information.
    
    Provides real-time status data for agent monitoring and discovery.
    
    Attributes:
        agent_id: Unique identifier for the agent
        status: Current status (ONLINE, OFFLINE, BUSY, ERROR)
        last_heartbeat: Timestamp of last health check
        requests_processed: Total number of requests processed
        average_response_time: Average response time in seconds
        error_count: Total number of errors encountered
    """
    agent_id: str
    status: str  # "ONLINE", "OFFLINE", "BUSY", "ERROR"
    last_heartbeat: datetime
    requests_processed: int
    average_response_time: float
    error_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert status to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all status fields
        """
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "requests_processed": self.requests_processed,
            "average_response_time": self.average_response_time,
            "error_count": self.error_count
        }


class BaseAgent(ABC):
    """
    Abstract base class for all TruthForge agents.
    
    Provides common functionality for agent registration, messaging,
    health monitoring, and HOL integration. All specialized agents
    must inherit from this class and implement the abstract methods.
    
    Attributes:
        agent_id: Unique HOL identifier for this agent
        capabilities: List of capabilities this agent provides
        hcs_topic_id: HCS topic ID for agent messaging
        config: TruthForge configuration object
        hedera_client: Hedera client for blockchain operations
        registered: Whether agent is registered with HOL
        requests_processed: Counter for processed requests
        total_response_time: Cumulative response time for averaging
        error_count: Counter for errors encountered
        last_heartbeat: Timestamp of last health check
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
        Initialize base agent with required parameters.
        
        Args:
            agent_id: Unique identifier for this agent (e.g., "truthforge-orch-001")
            capabilities: List of capabilities this agent provides
            hcs_topic_id: HCS topic ID for messaging
            config: TruthForge configuration object
            hedera_client: Hedera client for blockchain operations
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if not agent_id:
            raise ValueError("agent_id is required")
        
        if not capabilities:
            raise ValueError("capabilities list cannot be empty")
        
        # In mock mode, hcs_topic_id is optional
        if not config.mock_mode and not hcs_topic_id:
            raise ValueError("hcs_topic_id is required in production mode")
        
        if not config:
            raise ValueError("config is required")
        
        if not hedera_client:
            raise ValueError("hedera_client is required")
        
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.hcs_topic_id = hcs_topic_id or "mock-topic-id"
        self.config = config
        self.hedera_client = hedera_client
        
        # Agent state
        self.registered = False
        self.requests_processed = 0
        self.total_response_time = 0.0
        self.error_count = 0
        self.last_heartbeat = datetime.now(timezone.utc)
        
        logger.info(
            f"Initialized agent {self.agent_id} with capabilities: "
            f"{', '.join(self.capabilities)}"
        )
    
    def register_with_hol(self) -> bool:
        """
        Register this agent with Hedera's Hashgraph Online (HOL) registry.
        
        Submits agent metadata including ID, capabilities, and endpoints
        to the HOL registry for discovery by other agents. This method
        is idempotent - calling it multiple times will update the registration.
        
        Returns:
            bool: True if registration successful, False otherwise
            
        Raises:
            RuntimeError: If registration fails after retries
        """
        try:
            logger.info(f"Registering agent {self.agent_id} with HOL...")
            
            # Ensure Hedera client is authenticated
            if not self.hedera_client.authenticated:
                logger.info("Authenticating Hedera client...")
                self.hedera_client.authenticate()
            
            # Create registration message
            registration_payload = {
                "action": "register",
                "agent_id": self.agent_id,
                "capabilities": self.capabilities,
                "hcs_topic_id": self.hcs_topic_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "version": "1.0.0",
                    "network": self.config.hedera_network
                }
            }
            
            # Create HCS-10 message for registration
            registration_message = HCS10Message(
                message_type=MessageType.NOTIFY,
                sender_id=self.agent_id,
                recipient_id="hol-registry",
                timestamp=datetime.now(timezone.utc).isoformat(),
                payload=registration_payload
            )
            
            # Generate signature
            secret_key = self.config.hedera_private_key or "mock-secret-key"
            registration_message.signature = registration_message.generate_signature(secret_key)
            
            # Submit registration to HCS
            transaction_id = self.hedera_client.submit_message(registration_message)
            
            logger.info(
                f"Agent {self.agent_id} registered with HOL. "
                f"Transaction ID: {transaction_id}"
            )
            
            self.registered = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {self.agent_id} with HOL: {e}")
            raise RuntimeError(f"Agent registration failed: {e}")
    
    def send_message(self, recipient_id: str, message: HCS10Message) -> str:
        """
        Send a message to another agent via HCS.
        
        Submits the message to the HCS topic for immutable recording
        and delivery to the recipient agent.
        
        Args:
            recipient_id: ID of the recipient agent
            message: HCS10Message to send
            
        Returns:
            str: Transaction ID of the submitted message
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If message submission fails
        """
        if not recipient_id:
            raise ValueError("recipient_id is required")
        
        if not message:
            raise ValueError("message is required")
        
        try:
            # Ensure message has correct sender
            if message.sender_id != self.agent_id:
                logger.warning(
                    f"Message sender_id ({message.sender_id}) does not match "
                    f"agent_id ({self.agent_id}). Updating sender_id."
                )
                message.sender_id = self.agent_id
            
            # Ensure message has correct recipient
            if message.recipient_id != recipient_id:
                logger.warning(
                    f"Message recipient_id ({message.recipient_id}) does not match "
                    f"provided recipient_id ({recipient_id}). Updating recipient_id."
                )
                message.recipient_id = recipient_id
            
            # Generate signature if not present
            if not message.signature:
                secret_key = self.config.hedera_private_key or "mock-secret-key"
                message.signature = message.generate_signature(secret_key)
            
            # Submit message to HCS
            transaction_id = self.hedera_client.submit_message(message)
            
            logger.info(
                f"Agent {self.agent_id} sent message to {recipient_id}. "
                f"Transaction ID: {transaction_id}"
            )
            
            return transaction_id
            
        except Exception as e:
            logger.error(f"Failed to send message from {self.agent_id} to {recipient_id}: {e}")
            self.error_count += 1
            raise RuntimeError(f"Message sending failed: {e}")
    
    def receive_message(self) -> Optional[HCS10Message]:
        """
        Receive a message from the HCS topic.
        
        This is a placeholder implementation. In a production system,
        this would poll the HCS topic or use a subscription mechanism
        to receive messages addressed to this agent.
        
        Returns:
            Optional[HCS10Message]: Received message, or None if no messages available
            
        Note:
            This method requires HCS topic subscription functionality which
            is not fully implemented in this version. It serves as an interface
            for future implementation.
        """
        # TODO: Implement HCS topic subscription and message polling
        # This would require:
        # 1. Subscribe to HCS topic
        # 2. Filter messages by recipient_id == self.agent_id
        # 3. Validate message signatures
        # 4. Return next available message
        
        logger.debug(f"Agent {self.agent_id} checking for messages (not implemented)")
        return None
    
    @abstractmethod
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming request.
        
        This abstract method must be implemented by all specialized agents
        to handle their specific request types and perform their core functionality.
        
        Args:
            request: Request data as a dictionary
            
        Returns:
            Dict[str, Any]: Response data as a dictionary
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement process_request()")
    
    def health_check(self) -> AgentStatus:
        """
        Perform health check and return agent status.
        
        Provides current status information including uptime, request counts,
        performance metrics, and error rates for monitoring and discovery.
        
        Returns:
            AgentStatus: Current agent status and health metrics
        """
        # Update heartbeat timestamp
        self.last_heartbeat = datetime.now(timezone.utc)
        
        # Calculate average response time
        average_response_time = 0.0
        if self.requests_processed > 0:
            average_response_time = self.total_response_time / self.requests_processed
        
        # Determine status
        if self.requests_processed > 0:
            # Calculate error rate
            error_rate = self.error_count / self.requests_processed
            if error_rate > 0.5:
                status = "ERROR"
            elif self.registered:
                status = "ONLINE"
            else:
                status = "OFFLINE"
        elif self.registered:
            status = "ONLINE"
        else:
            status = "OFFLINE"
        
        agent_status = AgentStatus(
            agent_id=self.agent_id,
            status=status,
            last_heartbeat=self.last_heartbeat,
            requests_processed=self.requests_processed,
            average_response_time=average_response_time,
            error_count=self.error_count
        )
        
        logger.debug(
            f"Health check for {self.agent_id}: status={status}, "
            f"requests={self.requests_processed}, errors={self.error_count}"
        )
        
        return agent_status
    
    def _track_request(self, response_time: float, success: bool = True) -> None:
        """
        Track request metrics for monitoring.
        
        Internal method to update request counters and performance metrics.
        
        Args:
            response_time: Time taken to process request in seconds
            success: Whether the request was successful
        """
        self.requests_processed += 1
        self.total_response_time += response_time
        
        if not success:
            self.error_count += 1
    
    def __repr__(self) -> str:
        """
        String representation of the agent.
        
        Returns:
            str: Human-readable agent representation
        """
        return (
            f"{self.__class__.__name__}("
            f"id={self.agent_id}, "
            f"capabilities={self.capabilities}, "
            f"registered={self.registered})"
        )
