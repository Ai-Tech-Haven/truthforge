"""
TruthForge Webhook Handler Tests

This module tests the WebhookHandler class functionality including
signature validation, order event processing, and verification queueing.
"""

import pytest
import json
import hmac
import hashlib
import base64
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings

from agents.webhook_handler import WebhookHandler, WebhookEvent
from agents.config import Config


@pytest.fixture
def config():
    """Create test configuration."""
    config = Config()
    config.mock_mode = True
    config.woocommerce_webhook_secret = "test_webhook_secret"
    return config


@pytest.fixture
def webhook_handler(config):
    """Create WebhookHandler instance."""
    return WebhookHandler(config)


@pytest.fixture
def sample_order_payload():
    """Create sample order webhook payload."""
    return {
        "id": "12345",
        "number": "ORD-12345",
        "status": "processing",
        "billing": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com"
        },
        "shipping": {
            "address_1": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "postcode": "94102",
            "country": "USA"
        },
        "line_items": [
            {
                "product_id": "101",
                "name": "Test Product",
                "quantity": 2,
                "price": "99.99",
                "total": "199.98"
            }
        ],
        "total": "199.98"
    }


class TestWebhookHandlerInit:
    """Tests for WebhookHandler initialization."""
    
    def test_init_with_config(self, config):
        """Test WebhookHandler initialization with config."""
        handler = WebhookHandler(config)
        
        assert handler.config == config
        assert handler.webhook_secret == "test_webhook_secret"
        assert handler.verification_queue == []
    
    def test_init_mock_mode(self, config):
        """Test WebhookHandler initialization in mock mode."""
        config.mock_mode = True
        handler = WebhookHandler(config)
        
        assert handler.config.mock_mode is True


class TestValidateSignature:
    """Tests for webhook signature validation."""
    
    def test_validate_signature_mock_mode(self, webhook_handler, sample_order_payload):
        """Test signature validation in mock mode always succeeds."""
        webhook_handler.config.mock_mode = True
        
        result = webhook_handler.validate_signature(sample_order_payload, "any_signature")
        
        assert result is True
    
    def test_validate_signature_no_secret(self, config, sample_order_payload):
        """Test signature validation without webhook secret."""
        config.mock_mode = False
        config.woocommerce_webhook_secret = ""
        handler = WebhookHandler(config)
        
        result = handler.validate_signature(sample_order_payload, "signature")
        
        assert result is False
    
    def test_validate_signature_no_signature_provided(self, config, sample_order_payload):
        """Test signature validation without signature."""
        config.mock_mode = False
        handler = WebhookHandler(config)
        
        result = handler.validate_signature(sample_order_payload, "")
        
        assert result is False
    
    def test_validate_signature_valid(self, config, sample_order_payload):
        """Test signature validation with valid signature."""
        config.mock_mode = False
        config.woocommerce_webhook_secret = "test_secret"
        handler = WebhookHandler(config)
        
        # Compute valid signature
        import json
        import hmac
        import hashlib
        import base64
        
        payload_str = json.dumps(sample_order_payload, separators=(',', ':'), sort_keys=True)
        valid_signature = base64.b64encode(
            hmac.new(
                b"test_secret",
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        result = handler.validate_signature(sample_order_payload, valid_signature)
        
        assert result is True
    
    def test_validate_signature_invalid(self, config, sample_order_payload):
        """Test signature validation with invalid signature."""
        config.mock_mode = False
        config.woocommerce_webhook_secret = "test_secret"
        handler = WebhookHandler(config)
        
        result = handler.validate_signature(sample_order_payload, "invalid_signature")
        
        assert result is False


class TestHandleOrderCreated:
    """Tests for order.created webhook handling."""
    
    def test_handle_order_created_success(self, webhook_handler, sample_order_payload):
        """Test successful order.created webhook handling."""
        webhook_event = WebhookEvent(
            event_type="order.created",
            order_id="12345",
            payload=sample_order_payload,
            timestamp=datetime.now(timezone.utc),
            verified=True
        )
        
        result = webhook_handler.handle_order_created(webhook_event)
        
        assert result["status"] == "success"
        assert result["action"] == "queued_verification"
        assert result["order_id"] == "12345"
        
        # Verify request was queued
        assert webhook_handler.get_queue_size() == 1
        queued = webhook_handler.get_queued_requests()[0]
        assert queued["order_id"] == "12345"
        assert queued["action"] == "verify_order"
        assert queued["event_type"] == "order.created"
    
    def test_handle_order_created_extracts_order_info(self, webhook_handler, sample_order_payload):
        """Test order.created extracts order information."""
        webhook_event = WebhookEvent(
            event_type="order.created",
            order_id="12345",
            payload=sample_order_payload,
            timestamp=datetime.now(timezone.utc),
            verified=True
        )
        
        result = webhook_handler.handle_order_created(webhook_event)
        
        assert result["status"] == "success"
        
        # Check queued request contains order info
        queued = webhook_handler.get_queued_requests()[0]
        order_info = queued["order_info"]
        
        assert order_info["order_id"] == "12345"
        assert order_info["order_number"] == "ORD-12345"
        assert order_info["status"] == "processing"
        assert order_info["customer_email"] == "john.doe@example.com"
        assert order_info["customer_name"] == "John Doe"


class TestHandleOrderUpdated:
    """Tests for order.updated webhook handling."""
    
    def test_handle_order_updated_needs_reverification(self, webhook_handler, sample_order_payload):
        """Test order.updated that needs re-verification."""
        # Set status to trigger re-verification
        sample_order_payload["status"] = "processing"
        
        webhook_event = WebhookEvent(
            event_type="order.updated",
            order_id="12345",
            payload=sample_order_payload,
            timestamp=datetime.now(timezone.utc),
            verified=True
        )
        
        result = webhook_handler.handle_order_updated(webhook_event)
        
        assert result["status"] == "success"
        assert result["action"] == "queued_reverification"
        assert result["order_id"] == "12345"
        
        # Verify request was queued
        assert webhook_handler.get_queue_size() == 1
        queued = webhook_handler.get_queued_requests()[0]
        assert queued["reverification"] is True
    
    def test_handle_order_updated_no_reverification(self, webhook_handler, sample_order_payload):
        """Test order.updated that doesn't need re-verification."""
        # Set status that doesn't trigger re-verification
        sample_order_payload["status"] = "pending"
        
        webhook_event = WebhookEvent(
            event_type="order.updated",
            order_id="12345",
            payload=sample_order_payload,
            timestamp=datetime.now(timezone.utc),
            verified=True
        )
        
        result = webhook_handler.handle_order_updated(webhook_event)
        
        assert result["status"] == "success"
        assert result["action"] == "no_action_needed"
        assert result["order_id"] == "12345"
        
        # Verify nothing was queued
        assert webhook_handler.get_queue_size() == 0
    
    def test_handle_order_updated_with_cargo_photo_metadata(self, webhook_handler, sample_order_payload):
        """Test order.updated with cargo photo metadata triggers re-verification."""
        sample_order_payload["status"] = "pending"
        sample_order_payload["meta_data"] = [
            {"key": "cargo_photo_1", "value": "https://example.com/photo.jpg"}
        ]
        
        webhook_event = WebhookEvent(
            event_type="order.updated",
            order_id="12345",
            payload=sample_order_payload,
            timestamp=datetime.now(timezone.utc),
            verified=True
        )
        
        result = webhook_handler.handle_order_updated(webhook_event)
        
        assert result["status"] == "success"
        assert result["action"] == "queued_reverification"


class TestQueueVerification:
    """Tests for verification request queueing."""
    
    def test_queue_verification_success(self, webhook_handler):
        """Test successful verification queueing."""
        verification_request = {
            "action": "verify_order",
            "order_id": "12345",
            "source": "test"
        }
        
        result = webhook_handler.queue_verification(verification_request)
        
        assert result is True
        assert webhook_handler.get_queue_size() == 1
    
    def test_queue_verification_missing_order_id(self, webhook_handler):
        """Test queueing without order_id fails."""
        verification_request = {
            "action": "verify_order"
        }
        
        result = webhook_handler.queue_verification(verification_request)
        
        assert result is False
        assert webhook_handler.get_queue_size() == 0
    
    def test_queue_verification_missing_action(self, webhook_handler):
        """Test queueing without action fails."""
        verification_request = {
            "order_id": "12345"
        }
        
        result = webhook_handler.queue_verification(verification_request)
        
        assert result is False
        assert webhook_handler.get_queue_size() == 0
    
    def test_queue_multiple_requests(self, webhook_handler):
        """Test queueing multiple verification requests."""
        for i in range(5):
            verification_request = {
                "action": "verify_order",
                "order_id": f"order_{i}",
                "source": "test"
            }
            webhook_handler.queue_verification(verification_request)
        
        assert webhook_handler.get_queue_size() == 5


class TestProcessWebhook:
    """Tests for main webhook processing."""
    
    def test_process_webhook_order_created(self, webhook_handler, sample_order_payload):
        """Test processing order.created webhook."""
        result = webhook_handler.process_webhook(
            payload=sample_order_payload,
            signature="test_signature",
            event_type="order.created"
        )
        
        assert result["status"] == "success"
        assert result["action"] == "queued_verification"
        assert result["order_id"] == "12345"
    
    def test_process_webhook_order_updated(self, webhook_handler, sample_order_payload):
        """Test processing order.updated webhook."""
        sample_order_payload["status"] = "processing"
        
        result = webhook_handler.process_webhook(
            payload=sample_order_payload,
            signature="test_signature",
            event_type="order.updated"
        )
        
        assert result["status"] == "success"
        assert result["action"] == "queued_reverification"
    
    def test_process_webhook_invalid_signature(self, config, sample_order_payload):
        """Test processing webhook with invalid signature."""
        config.mock_mode = False
        config.woocommerce_webhook_secret = "test_secret"
        handler = WebhookHandler(config)
        
        with pytest.raises(ValueError, match="Invalid webhook signature"):
            handler.process_webhook(
                payload=sample_order_payload,
                signature="invalid_signature",
                event_type="order.created"
            )
    
    def test_process_webhook_missing_order_id(self, webhook_handler):
        """Test processing webhook without order ID."""
        payload = {"status": "processing"}
        
        with pytest.raises(ValueError, match="order_id not found"):
            webhook_handler.process_webhook(
                payload=payload,
                signature="test_signature",
                event_type="order.created"
            )
    
    def test_process_webhook_unsupported_event_type(self, webhook_handler, sample_order_payload):
        """Test processing webhook with unsupported event type."""
        result = webhook_handler.process_webhook(
            payload=sample_order_payload,
            signature="test_signature",
            event_type="order.deleted"
        )
        
        assert result["status"] == "ignored"
        assert "Unsupported event type" in result["reason"]
    
    def test_process_webhook_auto_detect_event_type(self, webhook_handler, sample_order_payload):
        """Test processing webhook with auto-detected event type."""
        sample_order_payload["event"] = "order.created"
        
        result = webhook_handler.process_webhook(
            payload=sample_order_payload,
            signature="test_signature"
        )
        
        assert result["status"] == "success"
        assert result["action"] == "queued_verification"


class TestQueueManagement:
    """Tests for queue management methods."""
    
    def test_get_queue_size(self, webhook_handler):
        """Test getting queue size."""
        assert webhook_handler.get_queue_size() == 0
        
        webhook_handler.queue_verification({
            "action": "verify_order",
            "order_id": "12345"
        })
        
        assert webhook_handler.get_queue_size() == 1
    
    def test_get_queued_requests(self, webhook_handler):
        """Test getting queued requests."""
        request1 = {"action": "verify_order", "order_id": "12345"}
        request2 = {"action": "verify_order", "order_id": "67890"}
        
        webhook_handler.queue_verification(request1)
        webhook_handler.queue_verification(request2)
        
        queued = webhook_handler.get_queued_requests()
        
        assert len(queued) == 2
        assert queued[0]["order_id"] == "12345"
        assert queued[1]["order_id"] == "67890"
    
    def test_clear_queue(self, webhook_handler):
        """Test clearing the queue."""
        for i in range(3):
            webhook_handler.queue_verification({
                "action": "verify_order",
                "order_id": f"order_{i}"
            })
        
        assert webhook_handler.get_queue_size() == 3
        
        cleared = webhook_handler.clear_queue()
        
        assert cleared == 3
        assert webhook_handler.get_queue_size() == 0


class TestHelperMethods:
    """Tests for helper methods."""
    
    def test_extract_order_id_from_id_field(self, webhook_handler):
        """Test extracting order ID from 'id' field."""
        payload = {"id": 12345}
        
        order_id = webhook_handler._extract_order_id(payload)
        
        assert order_id == "12345"
    
    def test_extract_order_id_from_order_id_field(self, webhook_handler):
        """Test extracting order ID from 'order_id' field."""
        payload = {"order_id": "67890"}
        
        order_id = webhook_handler._extract_order_id(payload)
        
        assert order_id == "67890"
    
    def test_extract_order_id_from_nested_order(self, webhook_handler):
        """Test extracting order ID from nested 'order' object."""
        payload = {"order": {"id": 99999}}
        
        order_id = webhook_handler._extract_order_id(payload)
        
        assert order_id == "99999"
    
    def test_extract_order_id_not_found(self, webhook_handler):
        """Test extracting order ID when not present."""
        payload = {"status": "processing"}
        
        order_id = webhook_handler._extract_order_id(payload)
        
        assert order_id is None
    
    def test_extract_event_type_from_event_field(self, webhook_handler):
        """Test extracting event type from 'event' field."""
        payload = {"event": "order.created"}
        
        event_type = webhook_handler._extract_event_type(payload)
        
        assert event_type == "order.created"
    
    def test_extract_event_type_from_action_field(self, webhook_handler):
        """Test extracting event type from 'action' field."""
        payload = {"action": "updated"}
        
        event_type = webhook_handler._extract_event_type(payload)
        
        assert event_type == "order.updated"
    
    def test_extract_event_type_default(self, webhook_handler):
        """Test extracting event type defaults to order.updated."""
        payload = {"id": 12345}
        
        event_type = webhook_handler._extract_event_type(payload)
        
        assert event_type == "order.updated"
    
    def test_check_reverification_processing_status(self, webhook_handler):
        """Test re-verification check for processing status."""
        payload = {"status": "processing"}
        
        needs_reverification = webhook_handler._check_reverification_needed(payload)
        
        assert needs_reverification is True
    
    def test_check_reverification_completed_status(self, webhook_handler):
        """Test re-verification check for completed status."""
        payload = {"status": "completed"}
        
        needs_reverification = webhook_handler._check_reverification_needed(payload)
        
        assert needs_reverification is True
    
    def test_check_reverification_pending_status(self, webhook_handler):
        """Test re-verification check for pending status."""
        payload = {"status": "pending"}
        
        needs_reverification = webhook_handler._check_reverification_needed(payload)
        
        assert needs_reverification is False
    
    def test_check_reverification_cargo_photo_metadata(self, webhook_handler):
        """Test re-verification check with cargo photo metadata."""
        payload = {
            "status": "pending",
            "meta_data": [
                {"key": "cargo_photo_url", "value": "https://example.com/photo.jpg"}
            ]
        }
        
        needs_reverification = webhook_handler._check_reverification_needed(payload)
        
        assert needs_reverification is True


class TestWebhookEvent:
    """Tests for WebhookEvent dataclass."""
    
    def test_webhook_event_creation(self):
        """Test creating WebhookEvent."""
        event = WebhookEvent(
            event_type="order.created",
            order_id="12345",
            payload={"test": "data"},
            signature="test_signature",
            timestamp=datetime.now(timezone.utc),
            verified=True
        )
        
        assert event.event_type == "order.created"
        assert event.order_id == "12345"
        assert event.payload == {"test": "data"}
        assert event.signature == "test_signature"
        assert event.verified is True
    
    def test_webhook_event_to_dict(self):
        """Test converting WebhookEvent to dictionary."""
        timestamp = datetime.now(timezone.utc)
        event = WebhookEvent(
            event_type="order.created",
            order_id="12345",
            payload={"test": "data"},
            signature="test_signature",
            timestamp=timestamp,
            verified=True
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "order.created"
        assert event_dict["order_id"] == "12345"
        assert event_dict["payload"] == {"test": "data"}
        assert event_dict["signature"] == "test_signature"
        assert event_dict["timestamp"] == timestamp.isoformat()
        assert event_dict["verified"] is True



# Property-Based Tests


class TestWebhookSignatureValidationProperties:
    """Property-based tests for webhook signature validation."""
    
    @given(
        webhook_scenario=st.sampled_from([
            # Valid signature scenarios
            {"secret": "test_secret_123", "payload": {"id": "12345", "status": "processing"}, "valid": True},
            {"secret": "another_secret", "payload": {"id": "67890", "number": "ORD-001"}, "valid": True},
            {"secret": "complex!@#$%^&*()_+", "payload": {"id": "99999", "total": "199.99"}, "valid": True},
            # Invalid signature scenarios - wrong secret
            {"secret": "test_secret_123", "payload": {"id": "12345", "status": "processing"}, "valid": False, "wrong_secret": "wrong_secret"},
            {"secret": "another_secret", "payload": {"id": "67890", "number": "ORD-001"}, "valid": False, "wrong_secret": "different"},
            # Invalid signature scenarios - tampered payload
            {"secret": "test_secret_123", "payload": {"id": "12345", "status": "processing"}, "valid": False, "tamper": True},
            {"secret": "another_secret", "payload": {"id": "67890", "number": "ORD-001"}, "valid": False, "tamper": True},
            # Missing signature scenarios
            {"secret": "test_secret_123", "payload": {"id": "12345", "status": "processing"}, "valid": False, "missing_signature": True},
            # Empty signature scenarios
            {"secret": "test_secret_123", "payload": {"id": "12345", "status": "processing"}, "valid": False, "empty_signature": True},
        ])
    )
    @settings(max_examples=100, deadline=None)
    def test_property_34_webhook_signature_validation(self, webhook_scenario):
        """
        Feature: truthforge, Property 34: Webhook Signature Validation
        
        For any incoming WooCommerce webhook, webhooks with invalid or missing 
        signatures shall be rejected with a 401 status code.
        
        Validates: Requirements 14.1, 14.2
        
        This property test verifies that:
        1. Valid signatures are accepted (return True)
        2. Invalid signatures are rejected (return False)
        3. Missing signatures are rejected (return False)
        4. Empty signatures are rejected (return False)
        5. Tampered payloads are rejected (return False)
        6. Wrong secrets produce invalid signatures (return False)
        """
        # Setup configuration
        config = Config()
        config.mock_mode = False  # Must be in production mode to test signature validation
        config.woocommerce_webhook_secret = webhook_scenario["secret"]
        
        handler = WebhookHandler(config)
        
        payload = webhook_scenario["payload"]
        expected_valid = webhook_scenario["valid"]
        
        # Compute the correct signature for the payload
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        correct_signature = base64.b64encode(
            hmac.new(
                webhook_scenario["secret"].encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        # Determine what signature to use based on scenario
        if webhook_scenario.get("missing_signature"):
            # Test with None signature
            signature = None
        elif webhook_scenario.get("empty_signature"):
            # Test with empty string signature
            signature = ""
        elif webhook_scenario.get("wrong_secret"):
            # Compute signature with wrong secret
            wrong_secret = webhook_scenario["wrong_secret"]
            signature = base64.b64encode(
                hmac.new(
                    wrong_secret.encode('utf-8'),
                    payload_str.encode('utf-8'),
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')
        elif webhook_scenario.get("tamper"):
            # Use correct signature but tamper with payload
            signature = correct_signature
            payload = {"id": "tampered", "status": "hacked"}
        else:
            # Use correct signature
            signature = correct_signature
        
        # Validate signature
        result = handler.validate_signature(payload, signature or "")
        
        # Property: Signature validation result must match expected validity
        assert result == expected_valid, \
            f"Expected signature validation to return {expected_valid}, got {result}. " \
            f"Scenario: valid={expected_valid}, missing={webhook_scenario.get('missing_signature')}, " \
            f"empty={webhook_scenario.get('empty_signature')}, wrong_secret={webhook_scenario.get('wrong_secret')}, " \
            f"tamper={webhook_scenario.get('tamper')}"
        
        # Additional property: Invalid signatures should prevent webhook processing
        if not expected_valid:
            # Attempting to process webhook with invalid signature should raise ValueError
            with pytest.raises(ValueError, match="Invalid webhook signature"):
                handler.process_webhook(
                    payload=payload,
                    signature=signature,
                    event_type="order.created"
                )
    
    @given(
        payload=st.fixed_dictionaries({
            "id": st.integers(min_value=1, max_value=999999).map(str),
            "status": st.sampled_from(["pending", "processing", "completed", "cancelled"]),
            "total": st.floats(min_value=0.01, max_value=10000.0).map(lambda x: f"{x:.2f}")
        }),
        secret=st.text(min_size=8, max_size=64, alphabet=st.characters(min_codepoint=33, max_codepoint=126))
    )
    @settings(max_examples=50, deadline=None)
    def test_property_34_valid_signature_always_accepted(self, payload, secret):
        """
        Property: For any payload and secret, a correctly computed signature 
        must always be accepted.
        
        This tests that the signature validation algorithm is consistent and 
        deterministic - the same payload and secret always produce the same 
        valid signature.
        """
        # Setup configuration
        config = Config()
        config.mock_mode = False
        config.woocommerce_webhook_secret = secret
        
        handler = WebhookHandler(config)
        
        # Compute correct signature
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        correct_signature = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        # Property: Correct signature must always be accepted
        result = handler.validate_signature(payload, correct_signature)
        assert result is True, \
            f"Valid signature was rejected. Payload: {payload}, Secret length: {len(secret)}"
    
    @given(
        payload=st.fixed_dictionaries({
            "id": st.integers(min_value=1, max_value=999999).map(str),
            "status": st.sampled_from(["pending", "processing", "completed"]),
        }),
        correct_secret=st.text(min_size=8, max_size=32),
        wrong_secret=st.text(min_size=8, max_size=32)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_34_wrong_secret_always_rejected(self, payload, correct_secret, wrong_secret):
        """
        Property: For any payload, a signature computed with a different secret 
        must always be rejected.
        
        This tests that signature validation properly detects when the wrong 
        secret is used.
        """
        # Skip if secrets happen to be the same
        if correct_secret == wrong_secret:
            return
        
        # Setup configuration with correct secret
        config = Config()
        config.mock_mode = False
        config.woocommerce_webhook_secret = correct_secret
        
        handler = WebhookHandler(config)
        
        # Compute signature with wrong secret
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        wrong_signature = base64.b64encode(
            hmac.new(
                wrong_secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        # Property: Signature with wrong secret must always be rejected
        result = handler.validate_signature(payload, wrong_signature)
        assert result is False, \
            f"Signature with wrong secret was accepted. Correct secret length: {len(correct_secret)}, " \
            f"Wrong secret length: {len(wrong_secret)}"
    
    @given(
        original_payload=st.fixed_dictionaries({
            "id": st.integers(min_value=1, max_value=999999).map(str),
            "status": st.sampled_from(["pending", "processing", "completed"]),
            "total": st.floats(min_value=0.01, max_value=10000.0).map(lambda x: f"{x:.2f}")
        }),
        secret=st.text(min_size=8, max_size=32)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_34_tampered_payload_always_rejected(self, original_payload, secret):
        """
        Property: For any payload, if the payload is modified after signature 
        computation, the signature must be rejected.
        
        This tests that signature validation detects payload tampering.
        """
        # Setup configuration
        config = Config()
        config.mock_mode = False
        config.woocommerce_webhook_secret = secret
        
        handler = WebhookHandler(config)
        
        # Compute signature for original payload
        payload_str = json.dumps(original_payload, separators=(',', ':'), sort_keys=True)
        signature = base64.b64encode(
            hmac.new(
                secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        # Tamper with payload
        tampered_payload = original_payload.copy()
        tampered_payload["id"] = "999999"  # Change the ID
        
        # Property: Signature for original payload must be rejected when used with tampered payload
        result = handler.validate_signature(tampered_payload, signature)
        assert result is False, \
            f"Tampered payload was accepted with original signature. " \
            f"Original ID: {original_payload['id']}, Tampered ID: {tampered_payload['id']}"
    
    def test_property_34_mock_mode_bypasses_validation(self):
        """
        Property: In mock mode, all signatures (valid or invalid) must be accepted.
        
        This tests that mock mode properly bypasses signature validation for 
        development and testing purposes.
        """
        # Setup configuration in mock mode
        config = Config()
        config.mock_mode = True
        config.woocommerce_webhook_secret = "test_secret"
        
        handler = WebhookHandler(config)
        
        payload = {"id": "12345", "status": "processing"}
        
        # Property: Mock mode accepts any signature
        assert handler.validate_signature(payload, "any_signature") is True
        assert handler.validate_signature(payload, "invalid_signature") is True
        assert handler.validate_signature(payload, "") is True
        assert handler.validate_signature(payload, None) is True
        
        # Property: Mock mode allows webhook processing without valid signature
        result = handler.process_webhook(
            payload=payload,
            signature="invalid_signature",
            event_type="order.created"
        )
        assert result["status"] == "success"


class TestWebhookOrderIDExtractionProperties:
    """Property-based tests for webhook order ID extraction."""
    
    @given(
        webhook_scenario=st.sampled_from([
            # Order ID in 'id' field (most common)
            {"payload": {"id": 12345, "status": "processing"}, "expected_order_id": "12345"},
            {"payload": {"id": "67890", "status": "completed"}, "expected_order_id": "67890"},
            {"payload": {"id": 999, "number": "ORD-999"}, "expected_order_id": "999"},
            
            # Order ID in 'order_id' field
            {"payload": {"order_id": "54321", "status": "pending"}, "expected_order_id": "54321"},
            {"payload": {"order_id": 11111, "total": "99.99"}, "expected_order_id": "11111"},
            
            # Order ID in nested 'order' object
            {"payload": {"order": {"id": 77777, "status": "processing"}}, "expected_order_id": "77777"},
            {"payload": {"order": {"order_id": "88888", "number": "ORD-888"}}, "expected_order_id": "88888"},
            
            # Mixed integer and string IDs
            {"payload": {"id": 123456789, "status": "processing"}, "expected_order_id": "123456789"},
            {"payload": {"id": "ABC-12345", "status": "processing"}, "expected_order_id": "ABC-12345"},
            
            # Both 'id' and 'order_id' present (id takes precedence)
            {"payload": {"id": "11111", "order_id": "22222", "status": "processing"}, "expected_order_id": "11111"},
        ])
    )
    @settings(max_examples=100, deadline=None)
    def test_property_35_webhook_order_id_extraction(self, webhook_scenario):
        """
        Feature: truthforge, Property 35: Webhook Order ID Extraction
        
        For any valid order.created or order.updated webhook, the Webhook_Handler 
        shall extract the order ID and include it in the queued verification request.
        
        Validates: Requirements 14.3
        
        This property test verifies that:
        1. Order IDs are correctly extracted from various payload structures
        2. Order IDs from 'id' field are extracted
        3. Order IDs from 'order_id' field are extracted
        4. Order IDs from nested 'order' objects are extracted
        5. Both integer and string order IDs are handled
        6. Extracted order IDs are included in queued verification requests
        """
        # Setup configuration
        config = Config()
        config.mock_mode = True
        
        handler = WebhookHandler(config)
        
        payload = webhook_scenario["payload"]
        expected_order_id = webhook_scenario["expected_order_id"]
        
        # Test order.created event
        result_created = handler.process_webhook(
            payload=payload,
            signature="test_signature",
            event_type="order.created"
        )
        
        # Property 1: Order ID must be extracted and included in result
        assert "order_id" in result_created, \
            f"order_id not found in result for order.created. Result: {result_created}"
        assert result_created["order_id"] == expected_order_id, \
            f"Expected order_id '{expected_order_id}', got '{result_created['order_id']}'"
        
        # Property 2: Order ID must be included in queued verification request
        queued_requests = handler.get_queued_requests()
        assert len(queued_requests) > 0, "No verification request was queued"
        
        queued_request = queued_requests[-1]  # Get the last queued request
        assert "order_id" in queued_request, \
            f"order_id not found in queued request. Request: {queued_request}"
        assert queued_request["order_id"] == expected_order_id, \
            f"Expected queued order_id '{expected_order_id}', got '{queued_request['order_id']}'"
        
        # Clear queue for next test
        handler.clear_queue()
        
        # Test order.updated event (if status triggers re-verification)
        payload_updated = payload.copy()
        payload_updated["status"] = "processing"  # Status that triggers re-verification
        
        result_updated = handler.process_webhook(
            payload=payload_updated,
            signature="test_signature",
            event_type="order.updated"
        )
        
        # Property 3: Order ID must be extracted for order.updated events
        assert "order_id" in result_updated, \
            f"order_id not found in result for order.updated. Result: {result_updated}"
        assert result_updated["order_id"] == expected_order_id, \
            f"Expected order_id '{expected_order_id}' for order.updated, got '{result_updated['order_id']}'"
        
        # Property 4: If re-verification is triggered, order ID must be in queued request
        if result_updated.get("action") == "queued_reverification":
            queued_requests = handler.get_queued_requests()
            assert len(queued_requests) > 0, "No verification request was queued for order.updated"
            
            queued_request = queued_requests[-1]
            assert queued_request["order_id"] == expected_order_id, \
                f"Expected queued order_id '{expected_order_id}' for order.updated, " \
                f"got '{queued_request['order_id']}'"
    
    @given(
        order_id=st.one_of(
            st.integers(min_value=1, max_value=999999),
            st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=48, max_codepoint=122))
        ),
        event_type=st.sampled_from(["order.created", "order.updated"])
    )
    @settings(max_examples=100, deadline=None)
    def test_property_35_order_id_always_extracted_and_queued(self, order_id, event_type):
        """
        Property: For any order ID (integer or string) and event type, the order ID 
        must be extracted and included in the queued verification request.
        
        This tests that order ID extraction is consistent across different ID formats 
        and event types.
        """
        # Setup configuration
        config = Config()
        config.mock_mode = True
        
        handler = WebhookHandler(config)
        
        # Create payload with order ID
        payload = {
            "id": order_id,
            "status": "processing",  # Status that triggers verification/re-verification
            "number": f"ORD-{order_id}",
            "total": "99.99"
        }
        
        # Process webhook
        result = handler.process_webhook(
            payload=payload,
            signature="test_signature",
            event_type=event_type
        )
        
        # Convert order_id to string for comparison (handler converts to string)
        expected_order_id = str(order_id)
        
        # Property: Order ID must be in result
        assert "order_id" in result, \
            f"order_id not found in result. Event: {event_type}, Order ID: {order_id}"
        assert result["order_id"] == expected_order_id, \
            f"Expected order_id '{expected_order_id}', got '{result['order_id']}'"
        
        # Property: Order ID must be in queued request
        queued_requests = handler.get_queued_requests()
        
        # For order.created, always queued
        # For order.updated, only queued if re-verification is needed
        if event_type == "order.created" or result.get("action") == "queued_reverification":
            assert len(queued_requests) > 0, \
                f"No verification request queued. Event: {event_type}, Order ID: {order_id}"
            
            queued_request = queued_requests[-1]
            assert queued_request["order_id"] == expected_order_id, \
                f"Expected queued order_id '{expected_order_id}', got '{queued_request['order_id']}'"
    
    @given(
        payload_structure=st.sampled_from([
            "id_field",
            "order_id_field",
            "nested_order_id",
            "nested_order_order_id"
        ]),
        order_id_value=st.integers(min_value=1, max_value=999999)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_35_extraction_from_various_structures(self, payload_structure, order_id_value):
        """
        Property: Order ID extraction must work correctly regardless of payload structure.
        
        This tests that the handler can extract order IDs from different payload 
        structures commonly used by WooCommerce webhooks.
        """
        # Setup configuration
        config = Config()
        config.mock_mode = True
        
        handler = WebhookHandler(config)
        
        # Create payload based on structure type
        if payload_structure == "id_field":
            payload = {"id": order_id_value, "status": "processing"}
        elif payload_structure == "order_id_field":
            payload = {"order_id": order_id_value, "status": "processing"}
        elif payload_structure == "nested_order_id":
            payload = {"order": {"id": order_id_value}, "status": "processing"}
        elif payload_structure == "nested_order_order_id":
            payload = {"order": {"order_id": order_id_value}, "status": "processing"}
        
        # Process webhook
        result = handler.process_webhook(
            payload=payload,
            signature="test_signature",
            event_type="order.created"
        )
        
        expected_order_id = str(order_id_value)
        
        # Property: Order ID must be extracted regardless of structure
        assert result["order_id"] == expected_order_id, \
            f"Failed to extract order ID from {payload_structure}. " \
            f"Expected '{expected_order_id}', got '{result.get('order_id')}'"
        
        # Property: Extracted order ID must be in queued request
        queued_requests = handler.get_queued_requests()
        assert len(queued_requests) > 0
        assert queued_requests[-1]["order_id"] == expected_o
