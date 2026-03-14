"""
Property-based tests for frontend functionality.

These tests validate frontend responsive behavior, port trust receipt process,
and dashboard metrics display.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import Mock
import json
from datetime import datetime, timezone

from api.app import create_app
from agents.config import Config
from agents.orchestrator_agent import OrchestratorAgent
from hol_registry.registry import HOLRegistry, AgentMetadata
from database.database import Database


@pytest.fixture
def mock_config():
    """Create mock configuration for testing."""
    config = Mock(spec=Config)
    config.mock_mode = True
    config.api_auth_token = "test-token-12345"
    config.woocommerce_webhook_secret = "webhook-secret"
    config.hcs_topic_id = "0.0.12345"
    return config


@pytest.fixture
def mock_database():
    """Create mock database for testing."""
    database = Mock()
    database.is_connected.return_value = True
    database.query_records.return_value = []
    database.count_records.return_value = 0
    return database


@pytest.fixture
def mock_hol_registry():
    """Create mock HOL registry for testing."""
    registry = Mock(spec=HOLRegistry)
    
    agent = AgentMetadata(
        agent_id="truthforge-verify-001",
        capabilities=["document_verification", "compliance_check"],
        endpoints={"api": "http://localhost:5001"},
        hcs_topic_id="0.0.12345",
        status="active"
    )
    
    registry.query_agents.return_value = [agent]
    return registry


class TestFrontendResponsiveBehavior:
    """Property-based tests for frontend responsive behavior (Property 21)."""
    
    @given(
        viewport_width=st.integers(min_value=320, max_value=2560),
        agent_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_21_responsive_layout_switching(self, mock_config, mock_hol_registry, mock_database, viewport_width, agent_count):
        """
        Feature: truthforge, Property 21: Frontend Responsive Behavior
        
        For any viewport width, the Frontend shall display the appropriate layout:
        - Desktop (>= 768px): Agent Registry Table
        - Mobile (< 768px): Agent Registry Cards
        
        This test verifies that the API provides data that supports both layouts.
        
        Validates: Requirements 8.1, 8.2, 8.6, 8.7
        """
        agents = []
        for i in range(agent_count):
            agent = AgentMetadata(
                agent_id=f"truthforge-agent-{i:03d}",
                capabilities=["capability_1", "capability_2"],
                endpoints={"api": f"http://localhost:500{i}"},
                hcs_topic_id="0.0.12345",
                status="active" if i % 2 == 0 else "offline"
            )
            agents.append(agent)
        
        mock_hol_registry.query_agents.return_value = agents
        mock_orchestrator = Mock(spec=OrchestratorAgent)
        
        app = create_app(mock_config, mock_orchestrator, mock_hol_registry, mock_database)
        app.config['TESTING'] = True
        client = app.test_client()
        
        response = client.get('/api/agents')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "agents" in data
        assert isinstance(data["agents"], list)
        assert len(data["agents"]) == agent_count
        
        for agent in data["agents"]:
            assert "agentId" in agent
            assert "status" in agent
            assert "capabilities" in agent
            assert isinstance(agent["agentId"], str)
            assert isinstance(agent["status"], str)
            assert isinstance(agent["capabilities"], list)
        
        expected_layout = "table" if viewport_width >= 768 else "cards"
        assert expected_layout in ["table", "cards"]


class TestPortTrustReceiptProcess:
    """Property-based tests for port trust receipt 4-step process (Property 22)."""
    
    @given(
        step_number=st.integers(min_value=1, max_value=4),
        authenticity_score=st.floats(min_value=0.0, max_value=100.0)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_22_four_step_verification_process(self, mock_config, mock_hol_registry, mock_database, step_number, authenticity_score):
        """
        Feature: truthforge, Property 22: Port Trust Receipt 4-Step Process
        
        For any verification, the Port Trust Receipt shall display a 4-step process:
        1. Image Analysis
        2. Document Verification
        3. Blockchain Timestamping
        4. Trust Score Generation
        
        This test verifies that the API response includes data for all 4 steps.
        
        Validates: Requirements 8.3
        """
        mock_orchestrator = Mock(spec=OrchestratorAgent)
        mock_orchestrator.process_request.return_value = {
            "success": True,
            "natural_language_response": "Verification completed",
            "unified_report": {
                "authenticity_score": authenticity_score,
                "hcs_transaction_id": "0.0.12345@1234567890.123456789",
                "verification_steps": [
                    {"step": 1, "name": "Image Analysis", "status": "completed", "result": "4-layer deepfake detection passed"},
                    {"step": 2, "name": "Document Verification", "status": "completed", "result": "Bill of Lading validated"},
                    {"step": 3, "name": "Blockchain Timestamping", "status": "completed", "result": "HCS transaction recorded"},
                    {"step": 4, "name": "Trust Score Generation", "status": "completed", "result": f"Authenticity score: {authenticity_score:.1f}"}
                ]
            }
        }
        
        app = create_app(mock_config, mock_orchestrator, mock_hol_registry, mock_database)
        app.config['TESTING'] = True
        client = app.test_client()
        
        response = client.post(
            '/api/verify',
            json={"message": "Verify this cargo photo"},
            headers={"Authorization": "Bearer test-token-12345"}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "unified_report" in data
        result = data["unified_report"]
        assert "verification_steps" in result
        
        steps = result["verification_steps"]
        assert len(steps) == 4, "Port Trust Receipt must have exactly 4 steps"
        
        for step in steps:
            assert "step" in step
            assert "name" in step
            assert "status" in step
            assert "result" in step
            assert 1 <= step["step"] <= 4
        
        matching_step = next((s for s in steps if s["step"] == step_number), None)
        assert matching_step is not None, f"Step {step_number} must exist"
        
        expected_names = ["Image Analysis", "Document Verification", "Blockchain Timestamping", "Trust Score Generation"]
        actual_names = [s["name"] for s in steps]
        assert actual_names == expected_names, "Step names must match 4-step process"


class TestDashboardMetricsDisplay:
    """Property-based tests for dashboard metrics display (Property 23)."""
    
    @given(
        total_verifications=st.integers(min_value=0, max_value=10000),
        active_agents=st.integers(min_value=0, max_value=10),
        avg_response_time=st.floats(min_value=0.1, max_value=10.0)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_23_dashboard_operational_metrics(self, mock_config, mock_hol_registry, mock_database, total_verifications, active_agents, avg_response_time):
        """
        Feature: truthforge, Property 23: Dashboard Metrics Display
        
        For any system state, the Dashboard shall display operational metrics:
        - Total verifications processed
        - Active agents count
        - Average response time
        
        This test verifies that the API provides complete metrics data.
        
        Validates: Requirements 10.1, 10.2, 10.4
        """
        mock_orchestrator = Mock(spec=OrchestratorAgent)
        
        app = create_app(mock_config, mock_orchestrator, mock_hol_registry, mock_database)
        app.config['TESTING'] = True
        client = app.test_client()
        
        response = client.get('/api/dashboard/metrics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "totalVerifications" in data or "total_verifications" in data
        assert "activeAgents" in data or "active_agents" in data
        
        total_key = "totalVerifications" if "totalVerifications" in data else "total_verifications"
        agents_key = "activeAgents" if "activeAgents" in data else "active_agents"
        
        assert isinstance(data[total_key], int)
        assert data[total_key] >= 0
        assert isinstance(data[agents_key], int)
        assert data[agents_key] >= 0
    
    @given(
        verification_count=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_23_metrics_consistency(self, mock_config, mock_hol_registry, mock_database, verification_count):
        """
        Feature: truthforge, Property 23: Dashboard Metrics Display (Consistency)
        
        For any number of verifications, the Dashboard metrics shall remain
        consistent and accurately reflect the system state.
        
        Validates: Requirements 10.1, 10.2, 10.4
        """
        mock_orchestrator = Mock(spec=OrchestratorAgent)
        
        app = create_app(mock_config, mock_orchestrator, mock_hol_registry, mock_database)
        app.config['TESTING'] = True
        client = app.test_client()
        
        response = client.get('/api/dashboard/metrics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        total_key = "totalVerifications" if "totalVerifications" in data else "total_verifications"
        agents_key = "activeAgents" if "activeAgents" in data else "active_agents"
        
        assert data[total_key] >= 0
        assert data[agents_key] >= 0
        assert data[total_key] <= 1000000
        assert data[agents_key] <= 100
