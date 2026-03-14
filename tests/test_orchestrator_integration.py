"""
Integration tests for TruthForge Orchestrator

This module contains integration tests for the complete verification flow,
testing end-to-end request processing through multiple agents.
"""

import pytest
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from agents.orchestrator import Orchestrator
from agents.base_agent import BaseAgent
from agents.config import Config
from agents.hedera_client import MockHederaClient


logger = logging.getLogger(__name__)


class MockAgent(BaseAgent):
    """Mock agent for integration testing."""
    
    def __init__(self, agent_id: str, config: Config, hedera_client, delay: float = 0.0):
        super().__init__(
            agent_id=agent_id,
            capabilities=["test"],
            hcs_topic_id="0.0.test",
            config=config,
            hedera_client=hedera_client
        )
        self.delay = delay
        self.call_count = 0
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request."""
        self.call_count += 1
        
        if self.delay > 0:
            import time
            time.sleep(self.delay)
        
        return {
            "agent_id": self.agent_id,
            "status": "success",
            "data": f"Result from {self.agent_id}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@pytest.fixture
def config():
    """Create test configuration."""
    return Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="test-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.test",
        mock_mode=True
    )


@pytest.fixture
def hedera_client(config):
    """Create mock Hedera client."""
    return MockHederaClient(config)


def test_complete_verification_flow_integration(config, hedera_client):
    """
    Integration test for complete verification flow.
    
    Tests end-to-end: request → routing → agents → aggregation → response
    Verifies all agents are called correctly and results are properly aggregated.
    
    Requirements: 6.1, 6.2, 6.3, 6.5, 6.6
    """
    # Create orchestrator
    orchestrator = Orchestrator(
        config=config,
        hedera_client=hedera_client,
        max_retries=3,
        request_timeout=10
    )
    
    # Track agent calls
    agent_calls = {
        "truthforge-woo-001": [],
        "truthforge-image-001": [],
        "truthforge-verify-001": [],
        "truthforge-fedex-001": []
    }
    
    # Create mock WooCommerce adapter
    woo_agent = MockAgent("truthforge-woo-001", config, hedera_client)
    def woo_process(req):
        agent_calls["truthforge-woo-001"].append(req)
        return {
            "status": "success",
            "order_data": {
                "order_id": "12345",
                "customer_name": "John Doe",
                "items": ["Widget A", "Widget B"],
                "cargo_photo_urls": ["https://example.com/photo1.jpg"]
            }
        }
    woo_agent.process_request = woo_process
    
    # Create mock Reality Engine
    image_agent = MockAgent("truthforge-image-001", config, hedera_client)
    def image_process(req):
        agent_calls["truthforge-image-001"].append(req)
        return {
            "status": "success",
            "authenticity_score": 87.5,
            "analysis_summary": "Image shows high authenticity with minor lighting inconsistencies",
            "hcs_transaction_id": "0.0.12345@1234567890.123456789",
            "exif_report": {
                "has_exif_data": True,
                "camera_make": "Canon",
                "confidence_score": 90.0
            },
            "lighting_report": {
                "lighting_consistency": 85.0,
                "confidence_score": 85.0
            },
            "artifact_report": {
                "ai_artifacts_detected": False,
                "generation_probability": 10.0,
                "confidence_score": 90.0
            },
            "metadata_report": {
                "metadata_consistent": True,
                "confidence_score": 95.0
            }
        }
    image_agent.process_request = image_process
    
    # Create mock Document Verifier
    verify_agent = MockAgent("truthforge-verify-001", config, hedera_client)
    def verify_process(req):
        agent_calls["truthforge-verify-001"].append(req)
        return {
            "status": "success",
            "verification_status": "PASS",
            "discrepancies": [],
            "confidence_level": 95.0,
            "hcs_transaction_id": "0.0.12346@1234567890.123456789"
        }
    verify_agent.process_request = verify_process
    
    # Create mock FedEx adapter
    fedex_agent = MockAgent("truthforge-fedex-001", config, hedera_client)
    def fedex_process(req):
        agent_calls["truthforge-fedex-001"].append(req)
        return {
            "status": "success",
            "shipment_data": {
                "tracking_number": "123456789012",
                "current_status": "In Transit",
                "origin": "Los Angeles, CA",
                "destination": "New York, NY",
                "estimated_delivery": "2026-02-25"
            }
        }
    fedex_agent.process_request = fedex_process
    
    # Register all agents with orchestrator
    orchestrator.register_agent("truthforge-woo-001", woo_agent)
    orchestrator.register_agent("truthforge-image-001", image_agent)
    orchestrator.register_agent("truthforge-verify-001", verify_agent)
    orchestrator.register_agent("truthforge-fedex-001", fedex_agent)
    
    # Create verification request for full order verification
    request = {
        "action": "verify_order",
        "order_id": "12345",
        "request_id": "test-request-001"
    }
    
    # Execute complete verification flow
    result = orchestrator.process_request(request)
    
    # Verify request was routed correctly (Requirement 6.1)
    # For order verification, should route to all 4 agents
    assert len(agent_calls["truthforge-woo-001"]) == 1, "WooCommerce agent should be called once"
    assert len(agent_calls["truthforge-image-001"]) == 1, "Reality Engine should be called once"
    assert len(agent_calls["truthforge-verify-001"]) == 1, "Document Verifier should be called once"
    assert len(agent_calls["truthforge-fedex-001"]) == 1, "FedEx adapter should be called once"
    
    # Verify all agents received the correct request (Requirement 6.2)
    for agent_id, calls in agent_calls.items():
        assert calls[0]["action"] == "verify_order", f"{agent_id} should receive verify_order action"
        assert calls[0]["order_id"] == "12345", f"{agent_id} should receive correct order_id"
    
    # Verify results were properly aggregated (Requirement 6.3, 6.5)
    assert result["overall_status"] == "SUCCESS", "Overall status should be SUCCESS"
    assert result["request_id"] == "test-request-001", "Request ID should be preserved"
    assert result["action"] == "verify_order", "Action should be preserved"
    
    # Verify order data from WooCommerce adapter is included
    assert "order_data" in result, "Order data should be in result"
    assert result["order_data"]["order_id"] == "12345"
    assert result["order_data"]["customer_name"] == "John Doe"
    
    # Verify image analysis from Reality Engine is included
    assert "authenticity_score" in result, "Authenticity score should be in result"
    assert result["authenticity_score"] == 87.5
    assert "image_analysis" in result, "Image analysis should be in result"
    assert "hcs_transaction_id" in result, "HCS transaction ID should be in result"
    
    # Verify document verification results are included
    assert "verification_status" in result, "Verification status should be in result"
    assert result["verification_status"] == "PASS"
    assert "discrepancies" in result, "Discrepancies should be in result"
    assert len(result["discrepancies"]) == 0, "Should have no discrepancies"
    
    # Verify shipment data from FedEx adapter is included
    assert "shipment_data" in result, "Shipment data should be in result"
    assert result["shipment_data"]["tracking_number"] == "123456789012"
    assert result["shipment_data"]["current_status"] == "In Transit"
    
    # Verify unified report structure (Requirement 6.6)
    assert "timestamp" in result, "Timestamp should be in result"
    assert "summary" in result, "Summary should be in result"
    assert "agent_results" in result, "Agent results should be in result"
    
    # Verify all agent results are present in agent_results
    assert "truthforge-woo-001" in result["agent_results"]
    assert "truthforge-image-001" in result["agent_results"]
    assert "truthforge-verify-001" in result["agent_results"]
    assert "truthforge-fedex-001" in result["agent_results"]
    
    # Verify no errors occurred
    assert "errors" in result, "Errors list should be present"
    assert len(result["errors"]) == 0, "Should have no errors"
    
    logger.info("Complete verification flow integration test passed successfully")
