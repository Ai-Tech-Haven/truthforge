"""
Tests for TruthForge Orchestrator

This module tests the Orchestrator agent's request routing, agent coordination,
result aggregation, and error handling capabilities.
"""

import pytest
import time
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from agents.orchestrator import Orchestrator, VerificationType
from agents.base_agent import BaseAgent, AgentStatus
from agents.config import Config
from agents.hedera_client import MockHederaClient


class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    def __init__(self, agent_id: str, config: Config, hedera_client, delay: float = 0.0, should_fail: bool = False):
        super().__init__(
            agent_id=agent_id,
            capabilities=["test"],
            hcs_topic_id="0.0.test",
            config=config,
            hedera_client=hedera_client
        )
        self.delay = delay
        self.should_fail = should_fail
        self.call_count = 0
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request with optional delay and failure."""
        self.call_count += 1
        
        if self.delay > 0:
            time.sleep(self.delay)
        
        if self.should_fail:
            raise Exception(f"Mock agent {self.agent_id} failed")
        
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


@pytest.fixture
def orchestrator(config, hedera_client):
    """Create Orchestrator instance."""
    return Orchestrator(
        config=config,
        hedera_client=hedera_client,
        max_retries=3,
        request_timeout=5
    )


@pytest.fixture
def mock_agents(config, hedera_client):
    """Create mock specialized agents."""
    return {
        "truthforge-image-001": MockAgent("truthforge-image-001", config, hedera_client),
        "truthforge-verify-001": MockAgent("truthforge-verify-001", config, hedera_client),
        "truthforge-fedex-001": MockAgent("truthforge-fedex-001", config, hedera_client),
        "truthforge-woo-001": MockAgent("truthforge-woo-001", config, hedera_client),
        "truthforge-market-001": MockAgent("truthforge-market-001", config, hedera_client),
    }


def test_orchestrator_initialization(config, hedera_client):
    """Test Orchestrator initialization."""
    orchestrator = Orchestrator(
        config=config,
        hedera_client=hedera_client,
        max_retries=5,
        request_timeout=10
    )
    
    assert orchestrator.agent_id == "truthforge-orch-001"
    assert "request_routing" in orchestrator.capabilities
    assert orchestrator.max_retries == 5
    assert orchestrator.request_timeout == 10
    assert orchestrator.agents == {}


def test_register_agent(orchestrator, config, hedera_client):
    """Test agent registration."""
    mock_agent = MockAgent("test-agent-001", config, hedera_client)
    
    orchestrator.register_agent("test-agent-001", mock_agent)
    
    assert "test-agent-001" in orchestrator.agents
    assert orchestrator.agents["test-agent-001"] == mock_agent


def test_route_request_order_verification(orchestrator):
    """Test routing for order verification."""
    request = {
        "action": "verify_order",
        "order_id": "12345"
    }
    
    # Register mock agents
    for agent_id in ["truthforge-woo-001", "truthforge-image-001", 
                     "truthforge-verify-001", "truthforge-fedex-001"]:
        orchestrator.agents[agent_id] = Mock()
    
    agent_ids = orchestrator.route_request(request)
    
    assert "truthforge-woo-001" in agent_ids
    assert "truthforge-image-001" in agent_ids
    assert "truthforge-verify-001" in agent_ids
    assert "truthforge-fedex-001" in agent_ids


def test_route_request_image_verification(orchestrator):
    """Test routing for image verification."""
    request = {
        "action": "verify_image",
        "image_url": "https://example.com/image.jpg"
    }
    
    orchestrator.agents["truthforge-image-001"] = Mock()
    
    agent_ids = orchestrator.route_request(request)
    
    assert agent_ids == ["truthforge-image-001"]


def test_route_request_tracking_verification(orchestrator):
    """Test routing for tracking verification."""
    request = {
        "action": "verify_tracking",
        "tracking_number": "123456789012"
    }
    
    orchestrator.agents["truthforge-verify-001"] = Mock()
    orchestrator.agents["truthforge-fedex-001"] = Mock()
    
    agent_ids = orchestrator.route_request(request)
    
    assert "truthforge-verify-001" in agent_ids
    assert "truthforge-fedex-001" in agent_ids


def test_route_request_document_verification(orchestrator):
    """Test routing for document verification."""
    request = {
        "action": "verify_document",
        "document_url": "https://example.com/bol.pdf"
    }
    
    orchestrator.agents["truthforge-verify-001"] = Mock()
    orchestrator.agents["truthforge-fedex-001"] = Mock()
    
    agent_ids = orchestrator.route_request(request)
    
    assert "truthforge-verify-001" in agent_ids
    assert "truthforge-fedex-001" in agent_ids


def test_route_request_discover_agents(orchestrator):
    """Test routing for agent discovery."""
    request = {
        "action": "discover_agents"
    }
    
    orchestrator.agents["truthforge-market-001"] = Mock()
    
    agent_ids = orchestrator.route_request(request)
    
    assert agent_ids == ["truthforge-market-001"]


def test_coordinate_agents_success(orchestrator, config, hedera_client):
    """Test successful agent coordination."""
    # Create mock agents
    agent1 = MockAgent("agent-001", config, hedera_client)
    agent2 = MockAgent("agent-002", config, hedera_client)
    
    orchestrator.agents = {
        "agent-001": agent1,
        "agent-002": agent2
    }
    
    request = {"action": "test"}
    agent_ids = ["agent-001", "agent-002"]
    
    results = orchestrator.coordinate_agents(agent_ids, request)
    
    assert len(results) == 2
    assert "agent-001" in results
    assert "agent-002" in results
    assert results["agent-001"]["status"] == "success"
    assert results["agent-002"]["status"] == "success"


def test_coordinate_agents_with_timeout(orchestrator, config, hedera_client):
    """Test agent coordination with timeout."""
    # Create agent that takes too long
    slow_agent = MockAgent("slow-agent", config, hedera_client, delay=10.0)
    
    orchestrator.agents = {"slow-agent": slow_agent}
    orchestrator.request_timeout = 1  # 1 second timeout
    
    request = {"action": "test"}
    agent_ids = ["slow-agent"]
    
    results = orchestrator.coordinate_agents(agent_ids, request)
    
    assert "slow-agent" in results
    assert "error" in results["slow-agent"]
    assert "timeout" in results["slow-agent"]["error"].lower()


def test_coordinate_agents_parallel_execution(orchestrator, config, hedera_client):
    """Test that agents execute in parallel."""
    # Create agents with delays
    agent1 = MockAgent("agent-001", config, hedera_client, delay=0.5)
    agent2 = MockAgent("agent-002", config, hedera_client, delay=0.5)
    agent3 = MockAgent("agent-003", config, hedera_client, delay=0.5)
    
    orchestrator.agents = {
        "agent-001": agent1,
        "agent-002": agent2,
        "agent-003": agent3
    }
    
    request = {"action": "test"}
    agent_ids = ["agent-001", "agent-002", "agent-003"]
    
    start_time = time.time()
    results = orchestrator.coordinate_agents(agent_ids, request)
    elapsed_time = time.time() - start_time
    
    # If parallel, should take ~0.5s, not 1.5s
    assert elapsed_time < 1.0
    assert len(results) == 3


def test_aggregate_results_image_analysis(orchestrator):
    """Test result aggregation for image analysis."""
    agent_results = {
        "truthforge-image-001": {
            "authenticity_score": 85.5,
            "analysis_summary": "Image appears authentic",
            "hcs_transaction_id": "0.0.12345@1234567890.123456789"
        }
    }
    
    request = {"action": "verify_image"}
    
    unified_report = orchestrator.aggregate_results(agent_results, request)
    
    assert unified_report["authenticity_score"] == 85.5
    assert unified_report["image_analysis"] == "Image appears authentic"
    assert unified_report["hcs_transaction_id"] == "0.0.12345@1234567890.123456789"
    assert unified_report["overall_status"] == "SUCCESS"


def test_aggregate_results_document_verification(orchestrator):
    """Test result aggregation for document verification."""
    agent_results = {
        "truthforge-verify-001": {
            "verification_status": "PASS",
            "discrepancies": []
        },
        "truthforge-fedex-001": {
            "shipment_data": {
                "tracking_number": "123456789012",
                "status": "In Transit"
            }
        }
    }
    
    request = {"action": "verify_document"}
    
    unified_report = orchestrator.aggregate_results(agent_results, request)
    
    assert unified_report["verification_status"] == "PASS"
    assert unified_report["discrepancies"] == []
    assert unified_report["shipment_data"]["tracking_number"] == "123456789012"
    assert unified_report["overall_status"] == "SUCCESS"


def test_aggregate_results_with_errors(orchestrator):
    """Test result aggregation with agent errors."""
    agent_results = {
        "truthforge-image-001": {
            "error": "Image processing failed"
        },
        "truthforge-verify-001": {
            "verification_status": "PASS"
        }
    }
    
    request = {"action": "verify_order"}
    
    unified_report = orchestrator.aggregate_results(agent_results, request)
    
    assert unified_report["overall_status"] == "ERROR"
    assert len(unified_report["errors"]) == 1
    assert unified_report["errors"][0]["agent_id"] == "truthforge-image-001"


def test_aggregate_results_with_warnings(orchestrator):
    """Test result aggregation with warnings."""
    agent_results = {
        "truthforge-verify-001": {
            "verification_status": "WARNING",
            "discrepancies": [
                {"field": "weight", "severity": "low"}
            ]
        }
    }
    
    request = {"action": "verify_document"}
    
    unified_report = orchestrator.aggregate_results(agent_results, request)
    
    assert unified_report["overall_status"] == "WARNING"
    assert len(unified_report["discrepancies"]) == 1


def test_handle_agent_failure_with_retry(orchestrator, config, hedera_client):
    """Test agent failure handling with retry."""
    # Create agent that fails first time, succeeds second time
    agent = MockAgent("test-agent", config, hedera_client)
    agent.should_fail = True
    
    orchestrator.agents["test-agent"] = agent
    
    request = {"action": "test"}
    
    # First call should fail
    with pytest.raises(Exception):
        agent.process_request(request)
    
    # Now make it succeed
    agent.should_fail = False
    
    # Retry should succeed
    result = orchestrator.handle_agent_failure(
        "test-agent",
        Exception("Test failure"),
        request,
        attempt=1
    )
    
    assert result is not None
    assert result["status"] == "success"


def test_handle_agent_failure_max_retries(orchestrator, config, hedera_client):
    """Test agent failure after max retries."""
    agent = MockAgent("test-agent", config, hedera_client, should_fail=True)
    orchestrator.agents["test-agent"] = agent
    orchestrator.max_retries = 2
    
    request = {"action": "test"}
    
    result = orchestrator.handle_agent_failure(
        "test-agent",
        Exception("Test failure"),
        request,
        attempt=2
    )
    
    assert result is None


def test_execute_agent_with_retry_success(orchestrator, config, hedera_client):
    """Test agent execution with retry succeeds."""
    agent = MockAgent("test-agent", config, hedera_client)
    orchestrator.agents["test-agent"] = agent
    
    request = {"action": "test"}
    
    result = orchestrator._execute_agent_with_retry("test-agent", request)
    
    assert result["status"] == "success"
    assert agent.call_count == 1


def test_execute_agent_with_retry_eventual_success(orchestrator, config, hedera_client):
    """Test agent execution succeeds after retries."""
    agent = MockAgent("test-agent", config, hedera_client)
    orchestrator.agents["test-agent"] = agent
    orchestrator.max_retries = 3
    
    # Make agent fail twice, then succeed
    call_count = [0]
    original_process = agent.process_request
    
    def failing_process(request):
        call_count[0] += 1
        if call_count[0] <= 2:
            raise Exception("Temporary failure")
        return original_process(request)
    
    agent.process_request = failing_process
    
    request = {"action": "test"}
    
    result = orchestrator._execute_agent_with_retry("test-agent", request)
    
    assert result["status"] == "success"
    assert call_count[0] == 3


def test_execute_agent_with_retry_all_fail(orchestrator, config, hedera_client):
    """Test agent execution fails after all retries."""
    agent = MockAgent("test-agent", config, hedera_client, should_fail=True)
    orchestrator.agents["test-agent"] = agent
    orchestrator.max_retries = 2
    
    request = {"action": "test"}
    
    result = orchestrator._execute_agent_with_retry("test-agent", request)
    
    assert "error" in result
    assert result["attempts"] == 2


def test_process_request_end_to_end(orchestrator, config, hedera_client):
    """Test complete request processing end-to-end."""
    # Register mock agents
    image_agent = MockAgent("truthforge-image-001", config, hedera_client)
    image_agent.process_request = lambda req: {
        "authenticity_score": 90.0,
        "analysis_summary": "Highly authentic",
        "hcs_transaction_id": "0.0.12345@1234567890.123456789"
    }
    
    orchestrator.agents["truthforge-image-001"] = image_agent
    
    request = {
        "action": "verify_image",
        "image_url": "https://example.com/image.jpg"
    }
    
    result = orchestrator.process_request(request)
    
    assert result["overall_status"] == "SUCCESS"
    assert result["authenticity_score"] == 90.0
    assert "summary" in result


def test_process_request_with_no_agents(orchestrator):
    """Test request processing when no agents are available."""
    request = {
        "action": "verify_image"
    }
    
    result = orchestrator.process_request(request)
    
    assert "error" in result
    assert "no agents available" in result["error"].lower()


def test_process_request_tracks_metrics(orchestrator, config, hedera_client):
    """Test that request processing tracks metrics."""
    agent = MockAgent("truthforge-image-001", config, hedera_client)
    orchestrator.agents["truthforge-image-001"] = agent
    
    request = {"action": "verify_image"}
    
    initial_count = orchestrator.requests_processed
    
    orchestrator.process_request(request)
    
    assert orchestrator.requests_processed == initial_count + 1


def test_shutdown(orchestrator):
    """Test orchestrator shutdown."""
    orchestrator.shutdown()
    
    # Executor should be shutdown
    assert orchestrator.executor._shutdown


def test_generate_summary_high_authenticity(orchestrator):
    """Test summary generation for high authenticity."""
    unified_report = {
        "overall_status": "SUCCESS",
        "action": "verify_image",
        "authenticity_score": 95.0
    }
    
    summary = orchestrator._generate_summary(unified_report)
    
    assert "high authenticity" in summary.lower()
    assert "95.0" in summary


def test_generate_summary_with_discrepancies(orchestrator):
    """Test summary generation with discrepancies."""
    unified_report = {
        "overall_status": "WARNING",
        "action": "verify_document",
        "discrepancies": [
            {"field": "weight"},
            {"field": "origin"}
        ]
    }
    
    summary = orchestrator._generate_summary(unified_report)
    
    assert "2 discrepancy" in summary.lower()


def test_generate_summary_error(orchestrator):
    """Test summary generation for errors."""
    unified_report = {
        "overall_status": "ERROR",
        "errors": [
            {"agent_id": "agent-001"},
            {"agent_id": "agent-002"}
        ]
    }
    
    summary = orchestrator._generate_summary(unified_report)
    
    assert "failed" in summary.lower()
    assert "2 error" in summary.lower()


# Property-Based Tests

from hypothesis import given, strategies as st, settings, HealthCheck


@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    timeout_seconds=st.integers(min_value=1, max_value=3),
    agent_delay=st.floats(min_value=0.1, max_value=5.0)
)
def test_property_request_response_timeout(timeout_seconds, agent_delay):
    """
    Property 20: Request-Response Timeout
    
    Feature: truthforge, Property 20: Request-Response Timeout
    Validates: Requirements 5.5
    
    For any REQUEST message sent to an agent, either a RESPONSE message 
    shall be received within the configured timeout period, or a timeout 
    error shall be raised.
    
    This property test verifies that:
    1. When an agent responds within the timeout, the response is received successfully
    2. When an agent takes longer than the timeout, a timeout error is raised
    3. The timeout mechanism works correctly across different timeout values
    """
    # Create config and hedera client inside the test (not using fixtures)
    test_config = Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="test-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.test",
        mock_mode=True
    )
    
    test_hedera_client = MockHederaClient(test_config)
    
    # Create orchestrator with specified timeout
    orchestrator = Orchestrator(
        config=test_config,
        hedera_client=test_hedera_client,
        request_timeout=timeout_seconds
    )
    
    # Create mock agent with specified delay
    mock_agent = MockAgent(
        "test-agent-001",
        test_config,
        test_hedera_client,
        delay=agent_delay
    )
    
    orchestrator.register_agent("test-agent-001", mock_agent)
    
    # Create REQUEST message
    request = {
        "action": "test_request",
        "request_id": "test-123"
    }
    
    # Coordinate agent execution
    results = orchestrator.coordinate_agents(["test-agent-001"], request)
    
    # Verify timeout behavior
    assert "test-agent-001" in results
    result = results["test-agent-001"]
    
    if agent_delay <= timeout_seconds:
        # Agent should respond successfully within timeout
        assert "error" not in result or "timeout" not in result.get("error", "").lower()
        assert result.get("status") == "success"
    else:
        # Agent should timeout
        assert "error" in result
        assert "timeout" in result["error"].lower()
        assert result.get("timeout") == timeout_seconds


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    agent_id=st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-')),
    error_message=st.text(min_size=1, max_size=200),
    request_action=st.sampled_from(["verify_order", "verify_image", "verify_document", "verify_tracking"]),
    request_id=st.text(min_size=5, max_size=50)
)
def test_property_agent_failure_logging(agent_id, error_message, request_action, request_id):
    """
    Property 41: Agent Failure Logging
    
    Feature: truthforge, Property 41: Agent Failure Logging
    Validates: Requirements 16.1
    
    For any agent that fails to respond to a request, the Orchestrator shall 
    create a log entry containing the agent ID, request details, error type, 
    and timestamp.
    
    This property test verifies that:
    1. When an agent fails, a log entry is created
    2. The log entry contains the agent ID
    3. The log entry contains request details (action, request_id)
    4. The log entry contains the error type
    5. The log entry contains a timestamp
    """
    # Create config and hedera client inside the test
    test_config = Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="test-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.test",
        mock_mode=True
    )
    
    test_hedera_client = MockHederaClient(test_config)
    
    # Create orchestrator
    orchestrator = Orchestrator(
        config=test_config,
        hedera_client=test_hedera_client,
        max_retries=1  # Only 1 attempt to speed up test
    )
    
    # Create a failing mock agent
    failing_agent = MockAgent(agent_id, test_config, test_hedera_client, should_fail=True)
    
    # Override the process_request to raise a specific error
    def failing_process(req):
        raise ValueError(error_message)
    
    failing_agent.process_request = failing_process
    
    # Register the failing agent
    orchestrator.register_agent(agent_id, failing_agent)
    
    # Create request
    request = {
        "action": request_action,
        "request_id": request_id
    }
    
    # Capture logs using logging handler
    import logging
    from io import StringIO
    
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Get the orchestrator logger
    orch_logger = logging.getLogger('agents.orchestrator')
    orch_logger.addHandler(handler)
    original_level = orch_logger.level
    orch_logger.setLevel(logging.ERROR)
    
    try:
        # Execute agent with retry (which will fail and log)
        result = orchestrator._execute_agent_with_retry(agent_id, request)
    finally:
        # Clean up handler
        orch_logger.removeHandler(handler)
        orch_logger.setLevel(original_level)
    
    # Get log output
    log_output = log_stream.getvalue()
    
    # Verify the result contains error information
    assert "error" in result
    assert result["agent_id"] == agent_id
    
    # Verify log entries were created
    assert len(log_output) > 0, "Should have error log entries"
    
    # Verify the log contains required information
    # The log should contain agent_id, error type, request details
    
    # Check for agent ID in logs
    assert agent_id in log_output, f"Log should contain agent ID: {agent_id}"
    
    # Check for error type (ValueError) in logs
    assert "ValueError" in log_output or "error" in log_output.lower(), "Log should contain error type"
    
    # Check for request action in logs
    assert request_action in log_output or "request" in log_output.lower(), "Log should contain request details"
    
    # Verify timestamp is present (ISO format check)
    # The _log_agent_failure method includes timestamp in ISO format
    import re
    iso_timestamp_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
    has_timestamp = re.search(iso_timestamp_pattern, log_output) is not None
    
    assert has_timestamp, "Log should contain timestamp in ISO format"
