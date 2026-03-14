"""
Unit tests for HCS-10 messaging protocol.

Tests the HCS10Message class including message creation, validation,
serialization, and signature generation/validation.
"""

import pytest
import json
from datetime import datetime, timezone
from hypothesis import given, strategies as st
from agents.hcs10_message import HCS10Message, MessageType


class TestMessageType:
    """Tests for MessageType enum."""
    
    def test_message_type_values(self):
        """Test that all message types have correct values."""
        assert MessageType.REQUEST.value == "REQUEST"
        assert MessageType.RESPONSE.value == "RESPONSE"
        assert MessageType.QUERY.value == "QUERY"
        assert MessageType.NOTIFY.value == "NOTIFY"
        assert MessageType.DISCOVER.value == "DISCOVER"


class TestHCS10Message:
    """Tests for HCS10Message class."""
    
    @pytest.fixture
    def valid_message_data(self):
        """Fixture providing valid message data."""
        return {
            "message_type": MessageType.REQUEST,
            "sender_id": "truthforge-orch-001",
            "recipient_id": "truthforge-image-001",
            "timestamp": "2026-02-21T10:30:00Z",
            "payload": {"action": "analyze_image", "image_id": "img_123"}
        }
    
    @pytest.fixture
    def secret_key(self):
        """Fixture providing a test secret key."""
        return "test_secret_key_12345"
    
    def test_create_message_with_enum(self, valid_message_data):
        """Test creating a message with MessageType enum."""
        message = HCS10Message(**valid_message_data)
        
        assert message.message_type == MessageType.REQUEST
        assert message.sender_id == "truthforge-orch-001"
        assert message.recipient_id == "truthforge-image-001"
        assert message.timestamp == "2026-02-21T10:30:00Z"
        assert message.payload == {"action": "analyze_image", "image_id": "img_123"}
        assert message.signature == ""
    
    def test_create_message_with_string_type(self, valid_message_data):
        """Test creating a message with string message type (auto-converted to enum)."""
        valid_message_data["message_type"] = "RESPONSE"
        message = HCS10Message(**valid_message_data)
        
        assert message.message_type == MessageType.RESPONSE
    
    def test_invalid_message_type_raises_error(self, valid_message_data):
        """Test that invalid message type raises ValueError."""
        valid_message_data["message_type"] = "INVALID_TYPE"
        
        with pytest.raises(ValueError, match="Invalid message_type"):
            HCS10Message(**valid_message_data)
    
    def test_missing_sender_id_raises_error(self, valid_message_data):
        """Test that missing sender_id raises ValueError."""
        valid_message_data["sender_id"] = ""
        
        with pytest.raises(ValueError, match="sender_id is required"):
            HCS10Message(**valid_message_data)
    
    def test_missing_recipient_id_raises_error(self, valid_message_data):
        """Test that missing recipient_id raises ValueError."""
        valid_message_data["recipient_id"] = ""
        
        with pytest.raises(ValueError, match="recipient_id is required"):
            HCS10Message(**valid_message_data)
    
    def test_missing_timestamp_raises_error(self, valid_message_data):
        """Test that missing timestamp raises ValueError."""
        valid_message_data["timestamp"] = ""
        
        with pytest.raises(ValueError, match="timestamp is required"):
            HCS10Message(**valid_message_data)
    
    def test_invalid_timestamp_format_raises_error(self, valid_message_data):
        """Test that invalid timestamp format raises ValueError."""
        valid_message_data["timestamp"] = "not-a-valid-timestamp"
        
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            HCS10Message(**valid_message_data)
    
    def test_missing_payload_raises_error(self, valid_message_data):
        """Test that missing payload raises ValueError."""
        valid_message_data["payload"] = None
        
        with pytest.raises(ValueError, match="payload is required"):
            HCS10Message(**valid_message_data)
    
    def test_generate_signature(self, valid_message_data, secret_key):
        """Test signature generation."""
        message = HCS10Message(**valid_message_data)
        signature = message.generate_signature(secret_key)
        
        assert signature
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest length
    
    def test_generate_signature_without_secret_raises_error(self, valid_message_data):
        """Test that generating signature without secret key raises error."""
        message = HCS10Message(**valid_message_data)
        
        with pytest.raises(ValueError, match="secret_key is required"):
            message.generate_signature("")
    
    def test_validate_signature_success(self, valid_message_data, secret_key):
        """Test successful signature validation."""
        message = HCS10Message(**valid_message_data)
        message.signature = message.generate_signature(secret_key)
        
        assert message.validate_signature(secret_key) is True
    
    def test_validate_signature_failure_wrong_key(self, valid_message_data, secret_key):
        """Test signature validation fails with wrong key."""
        message = HCS10Message(**valid_message_data)
        message.signature = message.generate_signature(secret_key)
        
        assert message.validate_signature("wrong_key") is False
    
    def test_validate_signature_failure_tampered_message(self, valid_message_data, secret_key):
        """Test signature validation fails when message is tampered."""
        message = HCS10Message(**valid_message_data)
        message.signature = message.generate_signature(secret_key)
        
        # Tamper with the message
        message.payload["action"] = "malicious_action"
        
        assert message.validate_signature(secret_key) is False
    
    def test_validate_signature_failure_no_signature(self, valid_message_data, secret_key):
        """Test signature validation fails when no signature present."""
        message = HCS10Message(**valid_message_data)
        
        assert message.validate_signature(secret_key) is False
    
    def test_to_hcs_format(self, valid_message_data, secret_key):
        """Test serialization to HCS format."""
        message = HCS10Message(**valid_message_data)
        message.signature = message.generate_signature(secret_key)
        
        hcs_data = message.to_hcs_format()
        
        assert isinstance(hcs_data, bytes)
        
        # Verify it's valid JSON
        parsed = json.loads(hcs_data.decode('utf-8'))
        assert parsed["message_type"] == "REQUEST"
        assert parsed["sender_id"] == "truthforge-orch-001"
        assert parsed["recipient_id"] == "truthforge-image-001"
        assert parsed["timestamp"] == "2026-02-21T10:30:00Z"
        assert parsed["payload"] == {"action": "analyze_image", "image_id": "img_123"}
        assert parsed["signature"] == message.signature
    
    def test_from_hcs_format(self, valid_message_data, secret_key):
        """Test deserialization from HCS format."""
        # Create and serialize a message
        original_message = HCS10Message(**valid_message_data)
        original_message.signature = original_message.generate_signature(secret_key)
        hcs_data = original_message.to_hcs_format()
        
        # Deserialize
        deserialized_message = HCS10Message.from_hcs_format(hcs_data)
        
        assert deserialized_message.message_type == original_message.message_type
        assert deserialized_message.sender_id == original_message.sender_id
        assert deserialized_message.recipient_id == original_message.recipient_id
        assert deserialized_message.timestamp == original_message.timestamp
        assert deserialized_message.payload == original_message.payload
        assert deserialized_message.signature == original_message.signature
    
    def test_from_hcs_format_empty_data_raises_error(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="data cannot be empty"):
            HCS10Message.from_hcs_format(b"")
    
    def test_from_hcs_format_invalid_json_raises_error(self):
        """Test that invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse message data"):
            HCS10Message.from_hcs_format(b"not valid json")
    
    def test_from_hcs_format_missing_fields_raises_error(self):
        """Test that missing required fields raises ValueError."""
        incomplete_data = json.dumps({
            "message_type": "REQUEST",
            "sender_id": "agent-001"
            # Missing other required fields
        }).encode('utf-8')
        
        with pytest.raises(ValueError, match="Missing required fields"):
            HCS10Message.from_hcs_format(incomplete_data)
    
    def test_to_dict(self, valid_message_data):
        """Test conversion to dictionary."""
        message = HCS10Message(**valid_message_data)
        message.signature = "test_signature"
        
        message_dict = message.to_dict()
        
        assert message_dict["message_type"] == "REQUEST"
        assert message_dict["sender_id"] == "truthforge-orch-001"
        assert message_dict["recipient_id"] == "truthforge-image-001"
        assert message_dict["timestamp"] == "2026-02-21T10:30:00Z"
        assert message_dict["payload"] == {"action": "analyze_image", "image_id": "img_123"}
        assert message_dict["signature"] == "test_signature"
    
    def test_repr(self, valid_message_data):
        """Test string representation."""
        message = HCS10Message(**valid_message_data)
        repr_str = repr(message)
        
        assert "HCS10Message" in repr_str
        assert "REQUEST" in repr_str
        assert "truthforge-orch-001" in repr_str
        assert "truthforge-image-001" in repr_str
        assert "2026-02-21T10:30:00Z" in repr_str
    
    def test_signature_consistency(self, valid_message_data, secret_key):
        """Test that same message produces same signature."""
        message1 = HCS10Message(**valid_message_data)
        message2 = HCS10Message(**valid_message_data)
        
        sig1 = message1.generate_signature(secret_key)
        sig2 = message2.generate_signature(secret_key)
        
        assert sig1 == sig2
    
    def test_all_message_types(self):
        """Test creating messages with all message types."""
        base_data = {
            "sender_id": "agent-001",
            "recipient_id": "agent-002",
            "timestamp": "2026-02-21T10:30:00Z",
            "payload": {}
        }
        
        for msg_type in MessageType:
            message = HCS10Message(message_type=msg_type, **base_data)
            assert message.message_type == msg_type
    
    def test_round_trip_serialization(self, valid_message_data, secret_key):
        """Test that serialization and deserialization preserve message data."""
        original = HCS10Message(**valid_message_data)
        original.signature = original.generate_signature(secret_key)
        
        # Serialize and deserialize
        serialized = original.to_hcs_format()
        restored = HCS10Message.from_hcs_format(serialized)
        
        # Verify signature is still valid
        assert restored.validate_signature(secret_key) is True
        
        # Verify all fields match
        assert restored.message_type == original.message_type
        assert restored.sender_id == original.sender_id
        assert restored.recipient_id == original.recipient_id
        assert restored.timestamp == original.timestamp
        assert restored.payload == original.payload
        assert restored.signature == original.signature


class TestHCS10MessageProperties:
    """Property-based tests for HCS10Message using Hypothesis."""
    
    @given(
        msg_type=st.sampled_from(MessageType),
        sender=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters=['\x00', '\n', '\r'])),
        recipient=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters=['\x00', '\n', '\r'])),
        payload=st.dictionaries(
            keys=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=['\x00', '\n', '\r'])),
            values=st.one_of(
                st.text(max_size=100, alphabet=st.characters(blacklist_characters=['\x00', '\n', '\r'])),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans()
            ),
            min_size=0,
            max_size=10
        )
    )
    def test_property_17_hcs10_message_structure(self, msg_type, sender, recipient, payload):
        """
        Feature: truthforge, Property 17: HCS-10 Message Structure
        
        For any message sent between agents, the message shall contain all required 
        HCS-10 fields: message_type, sender_id, recipient_id, timestamp, payload, 
        and signature.
        
        Validates: Requirements 5.2
        """
        # Generate a valid ISO 8601 timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Create message with generated data
        message = HCS10Message(
            message_type=msg_type,
            sender_id=sender,
            recipient_id=recipient,
            timestamp=timestamp,
            payload=payload
        )
        
        # Property: All required fields must be present and non-None
        assert message.message_type is not None, "message_type must not be None"
        assert message.sender_id is not None, "sender_id must not be None"
        assert message.recipient_id is not None, "recipient_id must not be None"
        assert message.timestamp is not None, "timestamp must not be None"
        assert message.payload is not None, "payload must not be None"
        assert message.signature is not None, "signature must not be None (can be empty string)"
        
        # Property: message_type must be a valid MessageType enum
        assert isinstance(message.message_type, MessageType), "message_type must be MessageType enum"
        
        # Property: sender_id and recipient_id must be non-empty strings
        assert isinstance(message.sender_id, str), "sender_id must be a string"
        assert len(message.sender_id) > 0, "sender_id must not be empty"
        assert isinstance(message.recipient_id, str), "recipient_id must be a string"
        assert len(message.recipient_id) > 0, "recipient_id must not be empty"
        
        # Property: timestamp must be a valid ISO 8601 string
        assert isinstance(message.timestamp, str), "timestamp must be a string"
        # Verify timestamp can be parsed
        datetime.fromisoformat(message.timestamp.replace('Z', '+00:00'))
        
        # Property: payload must be a dictionary
        assert isinstance(message.payload, dict), "payload must be a dictionary"
        
        # Property: signature must be a string (can be empty initially)
        assert isinstance(message.signature, str), "signature must be a string"
        
        # Property: Message can be serialized to HCS format
        hcs_data = message.to_hcs_format()
        assert isinstance(hcs_data, bytes), "to_hcs_format() must return bytes"
        
        # Property: Serialized message can be deserialized
        deserialized = HCS10Message.from_hcs_format(hcs_data)
        assert deserialized.message_type == message.message_type
        assert deserialized.sender_id == message.sender_id
        assert deserialized.recipient_id == message.recipient_id
        assert deserialized.timestamp == message.timestamp
        assert deserialized.payload == message.payload
        
        # Property: Message can be converted to dictionary with all fields
        msg_dict = message.to_dict()
        assert "message_type" in msg_dict
        assert "sender_id" in msg_dict
        assert "recipient_id" in msg_dict
        assert "timestamp" in msg_dict
        assert "payload" in msg_dict
        assert "signature" in msg_dict
    
    @given(
        invalid_type=st.one_of(
            st.text(min_size=1, max_size=50).filter(lambda x: x not in ["REQUEST", "RESPONSE", "QUERY", "NOTIFY", "DISCOVER"]),
            st.integers()
        )
    )
    def test_property_19_invalid_message_rejection_invalid_type(self, invalid_type):
        """
        Feature: truthforge, Property 19: Invalid Message Rejection (Part 1 - Invalid Type)
        
        For any received message with malformed structure, missing required fields, 
        or invalid signature, the message validation shall reject the message and 
        return a structured error.
        
        Validates: Requirements 5.4
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Property: Messages with invalid message_type must be rejected
        with pytest.raises((ValueError, TypeError, AttributeError)):
            HCS10Message(
                message_type=invalid_type,
                sender_id="agent-001",
                recipient_id="agent-002",
                timestamp=timestamp,
                payload={"test": "data"}
            )
    
    @given(
        missing_field=st.sampled_from(["sender_id", "recipient_id", "timestamp", "payload"])
    )
    def test_property_19_invalid_message_rejection_missing_fields(self, missing_field):
        """
        Feature: truthforge, Property 19: Invalid Message Rejection (Part 2 - Missing Fields)
        
        For any received message with malformed structure, missing required fields, 
        or invalid signature, the message validation shall reject the message and 
        return a structured error.
        
        Validates: Requirements 5.4
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Build message data with one field missing or invalid
        message_data = {
            "message_type": MessageType.REQUEST,
            "sender_id": "agent-001",
            "recipient_id": "agent-002",
            "timestamp": timestamp,
            "payload": {"test": "data"}
        }
        
        # Set the missing field to an invalid value
        if missing_field == "payload":
            message_data[missing_field] = None
        else:
            message_data[missing_field] = ""
        
        # Property: Messages with missing required fields must be rejected
        with pytest.raises(ValueError):
            HCS10Message(**message_data)
    
    @given(
        invalid_timestamp=st.one_of(
            st.text(min_size=1, max_size=50).filter(lambda x: x not in ["2026-02-21T10:30:00Z"]),
            st.integers().map(str),
            st.just("not-a-timestamp"),
            st.just("2026-13-45T99:99:99Z"),  # Invalid date/time values
            st.just("2026/02/21 10:30:00")  # Wrong format
        )
    )
    def test_property_19_invalid_message_rejection_invalid_timestamp(self, invalid_timestamp):
        """
        Feature: truthforge, Property 19: Invalid Message Rejection (Part 3 - Invalid Timestamp)
        
        For any received message with malformed structure, missing required fields, 
        or invalid signature, the message validation shall reject the message and 
        return a structured error.
        
        Validates: Requirements 5.4
        """
        # Property: Messages with invalid timestamp format must be rejected
        with pytest.raises(ValueError):
            HCS10Message(
                message_type=MessageType.REQUEST,
                sender_id="agent-001",
                recipient_id="agent-002",
                timestamp=invalid_timestamp,
                payload={"test": "data"}
            )
    
    @given(
        tampered_field=st.sampled_from(["sender_id", "recipient_id", "payload"]),
        secret_key=st.text(min_size=1, max_size=100)
    )
    def test_property_19_invalid_message_rejection_invalid_signature(self, tampered_field, secret_key):
        """
        Feature: truthforge, Property 19: Invalid Message Rejection (Part 4 - Invalid Signature)
        
        For any received message with malformed structure, missing required fields, 
        or invalid signature, the message validation shall reject the message and 
        return a structured error.
        
        Validates: Requirements 5.4
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Create a valid message with signature
        message = HCS10Message(
            message_type=MessageType.REQUEST,
            sender_id="agent-001",
            recipient_id="agent-002",
            timestamp=timestamp,
            payload={"test": "data"}
        )
        message.signature = message.generate_signature(secret_key)
        
        # Tamper with the message after signing
        if tampered_field == "sender_id":
            message.sender_id = "malicious-agent"
        elif tampered_field == "recipient_id":
            message.recipient_id = "wrong-recipient"
        elif tampered_field == "payload":
            message.payload = {"malicious": "payload"}
        
        # Property: Messages with invalid signatures must fail validation
        assert message.validate_signature(secret_key) is False, \
            f"Tampered message (field: {tampered_field}) should fail signature validation"
    
    @given(
        malformed_json=st.one_of(
            st.just(b"not json at all"),
            st.just(b"{incomplete json"),
            st.just(b"[1, 2, 3]"),  # Valid JSON but not an object
            st.just(b'{"only": "partial"'),  # Incomplete JSON
            st.binary(min_size=1, max_size=100).filter(lambda x: x not in [b"{}", b"[]"])
        )
    )
    def test_property_19_invalid_message_rejection_malformed_data(self, malformed_json):
        """
        Feature: truthforge, Property 19: Invalid Message Rejection (Part 5 - Malformed Data)
        
        For any received message with malformed structure, missing required fields, 
        or invalid signature, the message validation shall reject the message and 
        return a structured error.
        
        Validates: Requirements 5.4
        """
        # Property: Malformed JSON data must be rejected during deserialization
        with pytest.raises(ValueError):
            HCS10Message.from_hcs_format(malformed_json)
    
    @given(
        missing_serialized_field=st.sampled_from(["message_type", "sender_id", "recipient_id", "timestamp", "payload"])
    )
    def test_property_19_invalid_message_rejection_missing_serialized_fields(self, missing_serialized_field):
        """
        Feature: truthforge, Property 19: Invalid Message Rejection (Part 6 - Missing Serialized Fields)
        
        For any received message with malformed structure, missing required fields, 
        or invalid signature, the message validation shall reject the message and 
        return a structured error.
        
        Validates: Requirements 5.4
        """
        # Create incomplete message data missing one required field
        incomplete_data = {
            "message_type": "REQUEST",
            "sender_id": "agent-001",
            "recipient_id": "agent-002",
            "timestamp": "2026-02-21T10:30:00Z",
            "payload": {"test": "data"}
        }
        
        # Remove the specified field
        del incomplete_data[missing_serialized_field]
        
        serialized = json.dumps(incomplete_data).encode('utf-8')
        
        # Property: Deserialization must reject messages missing required fields
        with pytest.raises(ValueError, match="Missing required fields"):
            HCS10Message.from_hcs_format(serialized)
