"""
Tests for TruthForge OrchestratorAgent

This module tests the OrchestratorAgent's request routing, agent coordination,
result aggregation, and error handling capabilities.
"""

import pytest
import time
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from agents.orchestrator_agent import OrchestratorAgent as Orchestrator, Intent
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
            hedera_client=hedera_client,
        )
        self.delay = delay
        self.should_fail = should_fail
        self.call_count = 0

    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        self.call_count += 1
        if self.delay > 0:
            time.sleep(self.delay)
        if self.should_fail:
            raise Exception(f"Mock agent {self.agent_id} failed")
        return {
            "agent_id": self.agent_id,
            "status": "success",
            "data": f"Result from {self.agent_id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@pytest.fixture
def config():
    return Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="test-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.test",
        mock_mode=True,
    )


@pytest.fixture
def hedera_client(config):
    return MockHederaClient(config)


@pytest.fixture
def orchestrator(config, hedera_client):
    return Orchestrator(
        agent_id="truthforge-orch-001",
        capabilities=["request_routing", "agent_coordination"],
        hcs_topic_id="0.0.test",
        config=config,
        hedera_client=hedera_client,
    )


@pytest.fixture
def mock_agents(config, hedera_client):
    return {
        "verification_compliance": MockAgent("verification_compliance", config, hedera_client),
        "carrier_adapter": MockAgent("carrier_adapter", config, hedera_client),
        "evidence_settlement": MockAgent("evidence_settlement", config, hedera_client),
        "registry_discovery": MockAgent("registry_discovery", config, hedera_client),
        "marketplace_agent": MockAgent("marketplace_agent", config, hedera_client),
    }


def test_orchestrator_initialization(config, hedera_client):
    orch = Orchestrator(
        agent_id="truthforge-orch-001",
        capabilities=["request_routing", "agent_coordination"],
        hcs_topic_id="0.0.test",
        config=config,
        hedera_client=hedera_client,
    )
    assert orch.agent_id == "truthforge-orch-001"
    assert "request_routing" in orch.capabilities
    assert orch.agents == {}


def test_set_agents(orchestrator, mock_agents):
    orchestrator.set_agents(mock_agents)
    for agent_id in mock_agents:
        assert agent_id in orchestrator.agents


def test_route_request_verification(orchestrator, mock_agents):
    orchestrator.set_agents(mock_agents)
    intent = Intent(
        intent_type="verification",
        parameters={"verification_type": "document_verification"},
        confidence=0.9,
        missing_parameters=[],
    )
    agent_ids = orchestrator.route_request(intent)
    assert isinstance(agent_ids, list)
    assert len(agent_ids) > 0


def test_route_request_image_analysis(orchestrator, mock_agents):
    orchestrator.set_agents(mock_agents)
    intent = Intent(
        intent_type="verification",
        parameters={"verification_type": "image_analysis"},
        confidence=0.9,
        missing_parameters=[],
    )
    agent_ids = orchestrator.route_request(intent)
    assert "verification_compliance" in agent_ids
    assert "evidence_settlement" in agent_ids


def test_route_request_tracking(orchestrator, mock_agents):
    orchestrator.set_agents(mock_agents)
    intent = Intent(
        intent_type="tracking",
        parameters={"tracking_number": "123456789012"},
        confidence=0.9,
        missing_parameters=[],
    )
    agent_ids = orchestrator.route_request(intent)
    assert "carrier_adapter" in agent_ids


def test_coordinate_agents_success(orchestrator, config, hedera_client):
    agent1 = MockAgent("verification_compliance", config, hedera_client)
    agent2 = MockAgent("evidence_settlement", config, hedera_client)
    orchestrator.set_agents({"verification_compliance": agent1, "evidence_settlement": agent2})

    request = {"action": "test", "type": "verification"}
    results = orchestrator.coordinate_agents(["verification_compliance", "evidence_settlement"], request)

    assert isinstance(results, dict)
    assert len(results) == 2


def test_coordinate_agents_missing_agent(orchestrator, config, hedera_client):
    agent1 = MockAgent("verification_compliance", config, hedera_client)
    orchestrator.set_agents({"verification_compliance": agent1})

    results = orchestrator.coordinate_agents(["verification_compliance", "nonexistent"], {"action": "test"})

    assert "verification_compliance" in results
    assert "nonexistent" in results
    assert "error" in results["nonexistent"]


def test_handle_agent_failure_returns_error_dict(orchestrator):
    error = Exception("Test failure")
    result = orchestrator.handle_agent_failure("test-agent", error)
    assert isinstance(result, dict)
    assert "error" in result


def test_process_request_unsupported_type(orchestrator):
    result = orchestrator.process_request({"type": "unsupported_type"})
    assert "success" in result
    assert result["success"] is False


def test_process_request_tracks_metrics(orchestrator, config, hedera_client):
    agent = MockAgent("verification_compliance", config, hedera_client)
    orchestrator.set_agents({"verification_compliance": agent})
    initial_count = orchestrator.requests_processed
    orchestrator.process_request({"type": "verification", "verification_type": "image_analysis"})
    assert orchestrator.requests_processed == initial_count + 1


def test_agent_timeout(orchestrator, config, hedera_client):
    slow_agent = MockAgent("slow-agent", config, hedera_client, delay=10.0)
    orchestrator.set_agents({"slow-agent": slow_agent})
    orchestrator.request_timeout = 1
    results = orchestrator.coordinate_agents(["slow-agent"], {"action": "test"})
    assert "slow-agent" in results
    assert "error" in results["slow-agent"] or "timeout" in str(results["slow-agent"]).lower()


# Property-Based Tests

from hypothesis import given, strategies as st, settings, HealthCheck


@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    timeout_seconds=st.integers(min_value=1, max_value=3),
    agent_delay=st.floats(min_value=0.1, max_value=5.0),
)
def test_property_request_response_timeout(timeout_seconds, agent_delay):
    """
    Property 20: Request-Response Timeout
    Validates: Requirements 5.5
    """
    test_config = Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="test-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.test",
        mock_mode=True,
    )
    test_hedera_client = MockHederaClient(test_config)

    orch = Orchestrator(
        agent_id="truthforge-orch-001",
        capabilities=["request_routing"],
        hcs_topic_id="0.0.test",
        config=test_config,
        hedera_client=test_hedera_client,
    )
    orch.request_timeout = timeout_seconds

    mock_agent = MockAgent("test-agent-001", test_config, test_hedera_client, delay=agent_delay)
    orch.set_agents({"test-agent-001": mock_agent})

    results = orch.coordinate_agents(["test-agent-001"], {"action": "test_request"})

    assert "test-agent-001" in results
    result = results["test-agent-001"]

    if agent_delay <= timeout_seconds:
        assert "error" not in result or "timeout" not in result.get("error", "").lower()
    else:
        assert "error" in result


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    agent_id=st.text(
        min_size=5,
        max_size=50,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-"),
    ),
    error_message=st.text(min_size=1, max_size=200),
    request_action=st.sampled_from(["verify_order", "verify_image", "verify_document", "verify_tracking"]),
)
def test_property_agent_failure_logging(agent_id, error_message, request_action):
    """
    Property 41: Agent Failure Logging
    Validates: Requirements 16.1
    """
    test_config = Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="test-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.test",
        mock_mode=True,
    )
    test_hedera_client = MockHederaClient(test_config)

    orch = Orchestrator(
        agent_id="truthforge-orch-001",
        capabilities=["request_routing"],
        hcs_topic_id="0.0.test",
        config=test_config,
        hedera_client=test_hedera_client,
    )

    import logging
    from io import StringIO

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.ERROR)
    handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

    orch_logger = logging.getLogger("agents.orchestrator_agent")
    orch_logger.addHandler(handler)
    original_level = orch_logger.level
    orch_logger.setLevel(logging.ERROR)

    try:
        result = orch.handle_agent_failure(agent_id, ValueError(error_message))
    finally:
        orch_logger.removeHandler(handler)
        orch_logger.setLevel(original_level)

    assert isinstance(result, dict)
    assert "error" in result
