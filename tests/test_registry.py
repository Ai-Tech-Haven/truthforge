"""
Unit tests for HOL Registry

Tests agent registration, discovery, and status management functionality.
"""

import pytest
from datetime import datetime, timezone
from hypothesis import given, strategies as st
from hol_registry.registry import HOLRegistry, AgentMetadata


class TestHOLRegistry:
    """Test suite for HOL Registry functionality."""
    
    def test_six_agent_registration(self):
        """
        Test that system can register exactly 6 agents with expected IDs.
        
        Validates Requirements 1.1, 1.2:
        - System initializes with exactly 6 registered agents
        - All agent IDs match expected values
        """
        # Initialize registry
        registry = HOLRegistry()
        
        # Define the 6 expected agents with their capabilities
        expected_agents = [
            {
                "agent_id": "truthforge-orch-001",
                "capabilities": ["routing", "coordination", "intent-parsing"]
            },
            {
                "agent_id": "truthforge-image-001",
                "capabilities": ["deepfake-detection", "exif-analysis", "lighting-analysis", "ai-artifact-detection"]
            },
            {
                "agent_id": "truthforge-verify-001",
                "capabilities": ["bol-verification", "document-validation", "discrepancy-detection"]
            },
            {
                "agent_id": "truthforge-fedex-001",
                "capabilities": ["shipment-tracking", "fedex-integration", "logistics-data"]
            },
            {
                "agent_id": "truthforge-woo-001",
                "capabilities": ["woocommerce-integration", "order-management", "photo-retrieval"]
            },
            {
                "agent_id": "truthforge-market-001",
                "capabilities": ["agent-discovery", "capability-filtering", "registry-management"]
            }
        ]
        
        # Register all 6 agents
        for agent_data in expected_agents:
            result = registry.register_agent(
                agent_id=agent_data["agent_id"],
                capabilities=agent_data["capabilities"],
                hcs_topic_id=f"0.0.{hash(agent_data['agent_id']) % 1000000}"
            )
            assert result is True, f"Failed to register agent {agent_data['agent_id']}"
        
        # Verify exactly 6 agents are registered
        agent_count = registry.count_agents()
        assert agent_count == 6, f"Expected 6 agents, but found {agent_count}"
        
        # Verify all expected agent IDs are present
        expected_ids = [agent["agent_id"] for agent in expected_agents]
        registered_agents = registry.get_all_agents()
        registered_ids = [agent.agent_id for agent in registered_agents]
        
        for expected_id in expected_ids:
            assert expected_id in registered_ids, f"Agent {expected_id} not found in registry"
        
        # Verify no unexpected agents are registered
        for registered_id in registered_ids:
            assert registered_id in expected_ids, f"Unexpected agent {registered_id} found in registry"
        
        # Verify each agent has correct capabilities
        for agent_data in expected_agents:
            agent = registry.get_agent(agent_data["agent_id"])
            assert agent is not None, f"Agent {agent_data['agent_id']} not found"
            assert agent.capabilities == agent_data["capabilities"], \
                f"Agent {agent_data['agent_id']} has incorrect capabilities"
    
    def test_agent_registration_basic(self):
        """Test basic agent registration functionality."""
        registry = HOLRegistry()
        
        result = registry.register_agent(
            agent_id="test-agent-001",
            capabilities=["test-capability"],
            hcs_topic_id="0.0.12345"
        )
        
        assert result is True
        assert registry.count_agents() == 1
        
        agent = registry.get_agent("test-agent-001")
        assert agent is not None
        assert agent.agent_id == "test-agent-001"
        assert agent.capabilities == ["test-capability"]
        assert agent.hcs_topic_id == "0.0.12345"
    
    def test_agent_registration_with_metadata(self):
        """Test agent registration with additional metadata."""
        registry = HOLRegistry()
        
        metadata = {"version": "1.0.0", "network": "testnet"}
        endpoints = {"api": "http://localhost:5000"}
        
        result = registry.register_agent(
            agent_id="test-agent-002",
            capabilities=["capability-1", "capability-2"],
            endpoints=endpoints,
            hcs_topic_id="0.0.12346",
            metadata=metadata
        )
        
        assert result is True
        
        agent = registry.get_agent("test-agent-002")
        assert agent is not None
        assert agent.metadata == metadata
        assert agent.endpoints == endpoints
    
    def test_agent_registration_validation(self):
        """Test that registration validates required parameters."""
        registry = HOLRegistry()
        
        # Test missing agent_id
        with pytest.raises(ValueError, match="agent_id is required"):
            registry.register_agent(
                agent_id="",
                capabilities=["test"]
            )
        
        # Test empty capabilities
        with pytest.raises(ValueError, match="capabilities list cannot be empty"):
            registry.register_agent(
                agent_id="test-agent",
                capabilities=[]
            )
    
    def test_agent_re_registration_idempotence(self):
        """Test that re-registering an agent updates the registration."""
        registry = HOLRegistry()
        
        # Initial registration
        registry.register_agent(
            agent_id="test-agent-003",
            capabilities=["capability-1"],
            hcs_topic_id="0.0.12347"
        )
        
        # Re-register with updated capabilities
        result = registry.register_agent(
            agent_id="test-agent-003",
            capabilities=["capability-1", "capability-2"],
            hcs_topic_id="0.0.12347"
        )
        
        assert result is True
        assert registry.count_agents() == 1  # Still only 1 agent
        
        agent = registry.get_agent("test-agent-003")
        assert agent is not None
        assert len(agent.capabilities) == 2
        assert "capability-2" in agent.capabilities
    
    def test_query_agents_no_filter(self):
        """Test querying all agents without filters."""
        registry = HOLRegistry()
        
        # Register multiple agents
        registry.register_agent("agent-1", ["cap-1"])
        registry.register_agent("agent-2", ["cap-2"])
        registry.register_agent("agent-3", ["cap-3"])
        
        results = registry.query_agents()
        assert len(results) == 3
    
    def test_query_agents_with_capability_filter(self):
        """Test querying agents with capability filtering."""
        registry = HOLRegistry()
        
        # Register agents with different capabilities
        registry.register_agent("agent-1", ["deepfake-detection", "exif-analysis"])
        registry.register_agent("agent-2", ["bol-verification", "document-validation"])
        registry.register_agent("agent-3", ["deepfake-detection", "lighting-analysis"])
        
        # Query for deepfake-detection capability
        results = registry.query_agents(capability_filter=["deepfake-detection"])
        assert len(results) == 2
        
        agent_ids = [agent.agent_id for agent in results]
        assert "agent-1" in agent_ids
        assert "agent-3" in agent_ids
        assert "agent-2" not in agent_ids
    
    def test_query_agents_with_status_filter(self):
        """Test querying agents with status filtering."""
        registry = HOLRegistry()
        
        # Register agents
        registry.register_agent("agent-1", ["cap-1"])
        registry.register_agent("agent-2", ["cap-2"])
        registry.register_agent("agent-3", ["cap-3"])
        
        # Update status of one agent
        registry.update_agent_status("agent-2", "OFFLINE")
        
        # Query for ONLINE agents
        results = registry.query_agents(status_filter="ONLINE")
        assert len(results) == 2
        
        # Query for OFFLINE agents
        results = registry.query_agents(status_filter="OFFLINE")
        assert len(results) == 1
        assert results[0].agent_id == "agent-2"
    
    def test_get_agent_status(self):
        """Test getting agent status."""
        registry = HOLRegistry()
        
        registry.register_agent("agent-1", ["cap-1"])
        
        status = registry.get_agent_status("agent-1")
        assert status == "ONLINE"
        
        # Test non-existent agent
        status = registry.get_agent_status("non-existent")
        assert status is None
    
    def test_update_agent_status(self):
        """Test updating agent status."""
        registry = HOLRegistry()
        
        registry.register_agent("agent-1", ["cap-1"])
        
        result = registry.update_agent_status("agent-1", "BUSY")
        assert result is True
        
        status = registry.get_agent_status("agent-1")
        assert status == "BUSY"
        
        # Test updating non-existent agent
        result = registry.update_agent_status("non-existent", "OFFLINE")
        assert result is False
    
    def test_unregister_agent(self):
        """Test unregistering an agent."""
        registry = HOLRegistry()
        
        registry.register_agent("agent-1", ["cap-1"])
        assert registry.count_agents() == 1
        
        result = registry.unregister_agent("agent-1")
        assert result is True
        assert registry.count_agents() == 0
        
        # Test unregistering non-existent agent
        result = registry.unregister_agent("non-existent")
        assert result is False
    
    def test_agent_metadata_to_dict(self):
        """Test AgentMetadata to_dict conversion."""
        metadata = AgentMetadata(
            agent_id="test-agent",
            capabilities=["cap-1", "cap-2"],
            hcs_topic_id="0.0.12345",
            status="ONLINE"
        )
        
        result = metadata.to_dict()
        
        assert result["agent_id"] == "test-agent"
        assert result["capabilities"] == ["cap-1", "cap-2"]
        assert result["hcs_topic_id"] == "0.0.12345"
        assert result["status"] == "ONLINE"
        assert "registered_at" in result
        assert "last_updated" in result
    
    @given(
        agent_ids=st.lists(
            st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-"),
                min_size=5,
                max_size=30
            ).filter(lambda x: x and not x.startswith("-") and not x.endswith("-")),
            min_size=1,
            max_size=20,
            unique=True
        )
    )
    def test_property_agent_registration_uniqueness(self, agent_ids):
        """
        Property Test: Agent Registration Uniqueness
        
        Property 1: For any set of agent registration attempts, all successfully
        registered agent IDs must be unique and no duplicate IDs shall be accepted
        by the HOL registry.
        
        Validates: Requirements 1.2
        
        **Validates: Requirements 1.2**
        """
        registry = HOLRegistry()
        
        # Register all agents with unique IDs
        for agent_id in agent_ids:
            result = registry.register_agent(
                agent_id=agent_id,
                capabilities=["test-capability"]
            )
            assert result is True, f"Failed to register agent {agent_id}"
        
        # Verify the number of registered agents matches the number of unique IDs
        assert registry.count_agents() == len(agent_ids), \
            f"Expected {len(agent_ids)} agents, but found {registry.count_agents()}"
        
        # Verify all agent IDs are present and unique
        registered_agents = registry.get_all_agents()
        registered_ids = [agent.agent_id for agent in registered_agents]
        
        # Check that all registered IDs are in the original list
        for registered_id in registered_ids:
            assert registered_id in agent_ids, \
                f"Unexpected agent ID {registered_id} found in registry"
        
        # Check that all original IDs are registered
        for agent_id in agent_ids:
            assert agent_id in registered_ids, \
                f"Agent ID {agent_id} not found in registry"
        
        # Verify no duplicates in registered IDs
        assert len(registered_ids) == len(set(registered_ids)), \
            "Duplicate agent IDs found in registry"
        
        # Attempt to register duplicate IDs (should update, not create duplicates)
        for agent_id in agent_ids[:min(3, len(agent_ids))]:  # Test first 3 or fewer
            result = registry.register_agent(
                agent_id=agent_id,
                capabilities=["updated-capability"]
            )
            assert result is True, f"Failed to re-register agent {agent_id}"
        
        # Verify count remains the same (no duplicates created)
        assert registry.count_agents() == len(agent_ids), \
            f"Re-registration created duplicates: expected {len(agent_ids)}, found {registry.count_agents()}"
