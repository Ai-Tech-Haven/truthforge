"""
TruthForge HCS-10 Messaging Protocol

This module implements the HCS-10 messaging protocol for agent-to-agent communication
on the Hedera network. It provides message structure, serialization, and signature
validation for secure and standardized agent interactions.
"""

import json
import hashlib
import hmac
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class MessageType(Enum):
    """
    HCS-10 message types for agent communication.
    
    Attributes:
        REQUEST: Request for an agent to perform an action
        RESPONSE: Response to a previous REQUEST message
        QUERY: Query for information without state changes
        NOTIFY: One-way notification message
        DISCOVER: Discovery request to find agents by capabilities
    """
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    QUERY = "QUERY"
    NOTIFY = "NOTIFY"
    DISCOVER = "DISCOVER"


@dataclass
class HCS10Message:
    """
    HCS-10 message structure for agent-to-agent communication.
    
    All messages exchanged between TruthForge agents follow this standardized
    structure to ensure interoperability and security.
    
    Attributes:
        message_type: Type of message (REQUEST, RESPONSE, QUERY, NOTIFY, DISCOVER)
        sender_id: Unique identifier of the sending agent
        recipient_id: Unique identifier of the recipient agent
        timestamp: ISO 8601 formatted timestamp of message creation
        payload: Message-specific data as a dictionary
        signature: HMAC signature for message authenticity validation
    """
    message_type: MessageType
    sender_id: str
    recipient_id: str
    timestamp: str
    payload: Dict[str, Any]
    signature: str = ""
    
    def __post_init__(self):
        """
        Validate message fields after initialization.
        
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Convert string to MessageType enum if needed
        if isinstance(self.message_type, str):
            try:
                self.message_type = MessageType(self.message_type)
            except ValueError:
                raise ValueError(
                    f"Invalid message_type: {self.message_type}. "
                    f"Must be one of: {', '.join([t.value for t in MessageType])}"
                )
        elif not isinstance(self.message_type, MessageType):
            # Reject non-string, non-MessageType values
            raise ValueError(
                f"Invalid message_type: {self.message_type}. "
                f"Must be a string or MessageType enum, got {type(self.message_type).__name__}"
            )
        
        # Validate required fields
        if not self.sender_id:
            raise ValueError("sender_id is required")
        
        if not self.recipient_id:
            raise ValueError("recipient_id is required")
        
        if not self.timestamp:
            raise ValueError("timestamp is required")
        
        if self.payload is None:
            raise ValueError("payload is required")
        
        # Validate timestamp format
        try:
            datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError(
                f"Invalid timestamp format: {self.timestamp}. "
                "Expected ISO 8601 format (e.g., 2026-01-15T10:30:00Z)"
            )
    
    def generate_signature(self, secret_key: str) -> str:
        """
        Generate HMAC signature for the message.
        
        Creates a cryptographic signature using HMAC-SHA256 to ensure message
        authenticity and integrity. The signature is computed over all message
        fields except the signature itself.
        
        Args:
            secret_key: Secret key for HMAC signature generation
            
        Returns:
            str: Hexadecimal HMAC signature
            
        Raises:
            ValueError: If secret_key is empty
        """
        if not secret_key:
            raise ValueError("secret_key is required for signature generation")
        
        # Create canonical message representation for signing
        message_data = {
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "timestamp": self.timestamp,
            "payload": self.payload
        }
        
        # Serialize to JSON with sorted keys for consistent hashing
        message_json = json.dumps(message_data, sort_keys=True, separators=(',', ':'))
        
        # Generate HMAC signature
        signature = hmac.new(
            secret_key.encode('utf-8'),
            message_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def validate_signature(self, secret_key: str) -> bool:
        """
        Validate the message signature.
        
        Verifies that the message signature matches the expected signature
        computed from the message contents. This ensures the message has not
        been tampered with and comes from a trusted source.
        
        Args:
            secret_key: Secret key for signature validation
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not self.signature:
            return False
        
        if not secret_key:
            return False
        
        expected_signature = self.generate_signature(secret_key)
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(self.signature, expected_signature)
    
    def to_hcs_format(self) -> bytes:
        """
        Serialize message to HCS-compatible format.
        
        Converts the message to a JSON byte string suitable for submission
        to Hedera Consensus Service topics.
        
        Returns:
            bytes: JSON-encoded message as bytes
        """
        message_dict = {
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "signature": self.signature
        }
        
        return json.dumps(message_dict, separators=(',', ':')).encode('utf-8')
    
    @classmethod
    def from_hcs_format(cls, data: bytes) -> "HCS10Message":
        """
        Deserialize message from HCS format.
        
        Parses a JSON byte string received from Hedera Consensus Service
        and reconstructs an HCS10Message object.
        
        Args:
            data: JSON-encoded message as bytes
            
        Returns:
            HCS10Message: Deserialized message object
            
        Raises:
            ValueError: If data is invalid or cannot be parsed
        """
        if not data:
            raise ValueError("data cannot be empty")
        
        try:
            message_dict = json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to parse message data: {e}")
        
        # Validate that parsed data is a dictionary
        if not isinstance(message_dict, dict):
            raise ValueError(
                f"Invalid message format: expected JSON object, got {type(message_dict).__name__}"
            )
        
        # Validate required fields are present
        required_fields = ["message_type", "sender_id", "recipient_id", "timestamp", "payload"]
        missing_fields = [field for field in required_fields if field not in message_dict]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Create message instance
        return cls(
            message_type=MessageType(message_dict["message_type"]),
            sender_id=message_dict["sender_id"],
            recipient_id=message_dict["recipient_id"],
            timestamp=message_dict["timestamp"],
            payload=message_dict["payload"],
            signature=message_dict.get("signature", "")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all message fields
        """
        return {
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "signature": self.signature
        }
    
    def __repr__(self) -> str:
        """
        String representation of the message.
        
        Returns:
            str: Human-readable message representation
        """
        return (
            f"HCS10Message("
            f"type={self.message_type.value}, "
            f"from={self.sender_id}, "
            f"to={self.recipient_id}, "
            f"timestamp={self.timestamp})"
        )
