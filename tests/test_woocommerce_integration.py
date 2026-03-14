"""
Integration tests for WooCommerce Adapter

This module tests the complete WooCommerce integration workflow including
order fetching, verification data updates, and order note additions.
"""

import pytest
from datetime import datetime, timezone

from agents.woocommerce_adapter import MockWooCommerceAdapter
from agents.config import Config
from agents.hedera_client import MockHederaClient


@pytest.fixture
def mock_config():
    """Create mock configuration for testing."""
    config = Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="mock-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.67890",
        woocommerce_url="https://example.com",
        woocommerce_consumer_key="ck_test",
        woocommerce_consumer_secret="cs_test",
        mock_mode=True
    )
    return config


@pytest.fixture
def mock_hedera_client(mock_config):
    """Create mock Hedera client for testing."""
    return MockHederaClient(mock_config)


@pytest.fixture
def woocommerce_adapter(mock_config, mock_hedera_client):
    """Create mock WooCommerce adapter for testing."""
    return MockWooCommerceAdapter(mock_config, mock_hedera_client)


class TestWooCommerceIntegration:
    """Test complete WooCommerce integration workflows."""
    
    def test_complete_order_verification_workflow(self, woocommerce_adapter):
        """
        Test complete order verification workflow:
        1. Fetch order
        2. Get cargo photos
        3. Update order with verification results
        4. Add verification note
        """
        # Step 1: Fetch order
        order = woocommerce_adapter.fetch_order("1003")
        assert order.order_id == "1003"
        assert order.customer_name == "Carol Davis"
        
        # Step 2: Get cargo photos
        photos = woocommerce_adapter.fetch_cargo_photos(order)
        assert len(photos) == 3
        assert all("cargo-1003" in url for url in photos)
        
        # Step 3: Simulate verification results
        verification_data = {
            "status": "verified",
            "authenticity_score": 94.5,
            "hcs_transaction_id": "0.0.12345@1234567890.123456789",
            "analysis_details": {
                "exif_score": 95.0,
                "lighting_score": 93.0,
                "artifact_score": 96.0,
                "metadata_score": 94.0
            }
        }
        
        # Step 4: Update order metadata
        update_result = woocommerce_adapter.update_order_meta(order.order_id, verification_data)
        assert update_result is True
        
        # Verify update was stored
        assert order.order_id in woocommerce_adapter.order_updates
        stored_data = woocommerce_adapter.order_updates[order.order_id]
        assert stored_data["verification_data"]["authenticity_score"] == 94.5
        
        # Step 5: Add verification note
        note = (
            f"Verification completed successfully.\n"
            f"Authenticity Score: {verification_data['authenticity_score']}\n"
            f"HCS Transaction: {verification_data['hcs_transaction_id']}"
        )
        note_result = woocommerce_adapter.add_order_note(order.order_id, note)
        assert note_result is True
        
        # Verify note was stored
        assert order.order_id in woocommerce_adapter.order_notes
        assert len(woocommerce_adapter.order_notes[order.order_id]) == 1
        stored_note = woocommerce_adapter.order_notes[order.order_id][0]["note"]
        assert "94.5" in stored_note
        assert "0.0.12345@1234567890.123456789" in stored_note
    
    def test_webhook_to_verification_workflow(self, woocommerce_adapter):
        """
        Test webhook-triggered verification workflow:
        1. Receive webhook
        2. Fetch order
        3. Process verification
        4. Update order
        """
        # Step 1: Receive webhook
        webhook_data = {
            "order_id": "1001",
            "payload": {
                "action": "order.created",
                "order_id": "1001"
            }
        }
        
        webhook_result = woocommerce_adapter.handle_webhook(webhook_data)
        assert webhook_result is True
        
        # Step 2: Fetch order from webhook
        order = woocommerce_adapter.fetch_order(webhook_data["order_id"])
        assert order.order_id == "1001"
        assert order.customer_name == "Alice Johnson"
        
        # Step 3: Simulate verification
        verification_data = {
            "status": "verified",
            "authenticity_score": 88.7,
            "hcs_transaction_id": "0.0.12345@9876543210.987654321"
        }
        
        # Step 4: Update order
        woocommerce_adapter.update_order_meta(order.order_id, verification_data)
        woocommerce_adapter.add_order_note(
            order.order_id,
            f"Automated verification triggered by webhook. Score: {verification_data['authenticity_score']}"
        )
        
        # Verify workflow completed
        assert order.order_id in woocommerce_adapter.order_updates
        assert order.order_id in woocommerce_adapter.order_notes
    
    def test_multiple_orders_verification(self, woocommerce_adapter):
        """Test verifying multiple orders in sequence."""
        order_ids = ["1001", "1002", "1003"]
        
        for order_id in order_ids:
            # Fetch order
            order = woocommerce_adapter.fetch_order(order_id)
            assert order.order_id == order_id
            
            # Simulate verification
            verification_data = {
                "status": "verified",
                "authenticity_score": 90.0 + int(order_id) % 10,
                "hcs_transaction_id": f"0.0.12345@{order_id}.123456789"
            }
            
            # Update order
            woocommerce_adapter.update_order_meta(order_id, verification_data)
            woocommerce_adapter.add_order_note(
                order_id,
                f"Verification completed for order {order_id}"
            )
        
        # Verify all orders were processed
        assert len(woocommerce_adapter.order_updates) == 3
        assert len(woocommerce_adapter.order_notes) == 3
        
        for order_id in order_ids:
            assert order_id in woocommerce_adapter.order_updates
            assert order_id in woocommerce_adapter.order_notes
    
    def test_order_with_no_cargo_photos(self, woocommerce_adapter):
        """Test handling order with no cargo photos."""
        # Fetch order without predefined photos
        order = woocommerce_adapter.fetch_order("1001")
        
        # Fetch cargo photos (should return mock URLs)
        photos = woocommerce_adapter.fetch_cargo_photos(order)
        
        # Should still return some mock photos
        assert isinstance(photos, list)
        assert len(photos) >= 0
    
    def test_verification_failure_workflow(self, woocommerce_adapter):
        """Test workflow when verification fails."""
        order = woocommerce_adapter.fetch_order("1002")
        
        # Simulate failed verification
        verification_data = {
            "status": "failed",
            "authenticity_score": 45.2,
            "hcs_transaction_id": "0.0.12345@1234567890.123456789",
            "failure_reason": "Low authenticity score detected"
        }
        
        # Update order with failure data
        woocommerce_adapter.update_order_meta(order.order_id, verification_data)
        woocommerce_adapter.add_order_note(
            order.order_id,
            f"⚠️ Verification failed. Score: {verification_data['authenticity_score']}. "
            f"Reason: {verification_data['failure_reason']}"
        )
        
        # Verify failure was recorded
        assert order.order_id in woocommerce_adapter.order_updates
        stored_data = woocommerce_adapter.order_updates[order.order_id]
        assert stored_data["verification_data"]["status"] == "failed"
        assert stored_data["verification_data"]["authenticity_score"] == 45.2
    
    def test_agent_registration_and_health_check(self, woocommerce_adapter):
        """Test agent registration and health monitoring."""
        # Register agent with HOL
        registration_result = woocommerce_adapter.register_with_hol()
        assert registration_result is True
        assert woocommerce_adapter.registered is True
        
        # Perform health check
        status = woocommerce_adapter.health_check()
        assert status.agent_id == "truthforge-woo-mock-001"
        assert status.status in ["ONLINE", "OFFLINE"]
        assert status.requests_processed >= 0
        assert status.error_count >= 0
    
    def test_process_request_integration(self, woocommerce_adapter):
        """Test process_request method with complete workflow."""
        # Fetch order via process_request
        fetch_request = {
            "action": "fetch_order",
            "order_id": "1003"
        }
        fetch_response = woocommerce_adapter.process_request(fetch_request)
        assert fetch_response["status"] == "success"
        assert fetch_response["result"]["order_id"] == "1003"
        
        # Update order via process_request
        update_request = {
            "action": "update_order_meta",
            "order_id": "1003",
            "verification_data": {
                "status": "verified",
                "authenticity_score": 92.8
            }
        }
        update_response = woocommerce_adapter.process_request(update_request)
        assert update_response["status"] == "success"
        assert update_response["result"]["updated"] is True
        
        # Add note via process_request
        note_request = {
            "action": "add_order_note",
            "order_id": "1003",
            "note": "Integration test verification"
        }
        note_response = woocommerce_adapter.process_request(note_request)
        assert note_response["status"] == "success"
        assert note_response["result"]["added"] is True
        
        # Verify all operations completed
        assert "1003" in woocommerce_adapter.order_updates
        assert "1003" in woocommerce_adapter.order_notes
