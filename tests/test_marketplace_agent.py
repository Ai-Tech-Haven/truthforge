"""
Tests for TruthForge Marketplace Agent

This module tests the Marketplace Agent's discovery, filtering, and caching
functionality.
"""

import pytest
import time
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock

from agents.marketplace_agent import MarketplaceAgent
from agents.config import Config
from agents.hedera_client import MockHederaClient
from agents.hcs10_message import MessageType
from hol_registry.registry import HOLRegistry, AgentMetadata


@pytest.fixture
def config():
    """Create test configuration."""
    return Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="test-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.67890",
        mock_mode=True
    )


@pytest.fixture
def hedera_client(config):
    """Create mock Hedera client."""
    return MockHederaClient(config)


@pytest.fixture
def hol_registry():
    """Create HOL registry with test agents."""
    registry = HOLRegistry()
    
    # Register test agents
    registry.register_agent(
        agent_id="truthforge-image-001",
        capabilities=["deepfake_detection", "image_analysis"],
        hcs_topic_id="0.0.67890"
    )
    
    registry.register_agent(
        agent_id="truthforge-verify-001",
        capabilities=["document_verification", "bol_validation"],
        hcs_topic_id="0.0.67890"
    )
    
    registry.register_agent(
        agent_id="truthforge-fedex-001",
        capabilities=["shipment_tracking", "fedex_integration"],
        hcs_topic_id="0.0.67890"
    )
    
    # Set one agent to offline
    registry.update_agent_status("truthforge-fedex-001", "OFFLINE")
    
    return registry


@pytest.fixture
def marketplace_agent(config, hedera_client, hol_registry):
    """Create Marketplace Agent instance."""
    return MarketplaceAgent(
        config=config,
        hedera_client=hedera_client,
        hol_registry=hol_registry,
        cache_ttl=2  # Short TTL for testing
    )


class TestMarketplaceAgentInitialization:
    """Test Marketplace Agent initialization."""
    
    def test_initialization_success(self, config, hedera_client, hol_registry):
        """Test successful agent initialization."""
        agent = MarketplaceAgent(
            config=config,
            hedera_client=hedera_client,
            hol_registry=hol_registry
        )
        
        assert agent.agent_id == "truthforge-market-001"
        assert "agent_discovery" in agent.capabilities
        assert agent.hol_registry == hol_registry
        assert agent.cache_ttl == 300  # Default TTL
    
    def test_initialization_with_custom_ttl(self, config, hedera_client, hol_registry):
        """Test initialization with custom cache TTL."""
        agent = MarketplaceAgent(
            config=config,
            hedera_client=hedera_client,
            hol_registry=hol_registry,
            cache_ttl=600
        )
        
        assert agent.cache_ttl == 600
    
    def test_initialization_without_registry_fails(self, config, hedera_client):
        """Test that initialization fails without HOL registry."""
        with pytest.raises(ValueError, match="hol_registry is required"):
            MarketplaceAgent(
                config=config,
                hedera_client=hedera_client,
                hol_registry=None
            )


class TestHandleDiscover:
    """Test DISCOVER message handling."""
    
    def test_discover_all_agents(self, marketplace_agent):
        """Test discovering all agents without filters."""
        payload = {}
        
        result = marketplace_agent.handle_discover(payload)
        
        assert "agents" in result
        assert "count" in result
        assert result["count"] == 3
        assert len(result["agents"]) == 3
    
    def test_discover_with_capability_filter(self, marketplace_agent):
        """Test discovering agents with capability filter."""
        payload = {
            "capability_filter": ["deepfake_detection"]
        }
        
        result = marketplace_agent.handle_discover(payload)
        
        assert result["count"] == 1
        assert result["agents"][0]["agent_id"] == "truthforge-image-001"
        assert "deepfake_detection" in result["agents"][0]["capabilities"]
    
    def test_discover_with_multiple_capability_filters(self, marketplace_agent):
        """Test discovering agents with multiple capability filters."""
        payload = {
            "capability_filter": ["deepfake_detection", "document_verification"]
        }
        
        result = marketplace_agent.handle_discover(payload)
        
        assert result["count"] == 2
        agent_ids = [agent["agent_id"] for agent in result["agents"]]
        assert "truthforge-image-001" in agent_ids
        assert "truthforge-verify-001" in agent_ids
    
    def test_discover_with_status_filter(self, marketplace_agent):
        """Test discovering agents with status filter."""
        payload = {
            "status_filter": "ONLINE"
        }
        
        result = marketplace_agent.handle_discover(payload)
        
        assert result["count"] == 2
        for agent in result["agents"]:
            assert agent["status"] == "ONLINE"
    
    def test_discover_offline_agents(self, marketplace_agent):
        """Test discovering offline agents."""
        payload = {
            "status_filter": "OFFLINE"
        }
        
        result = marketplace_agent.handle_discover(payload)
        
        assert result["count"] == 1
        assert result["agents"][0]["agent_id"] == "truthforge-fedex-001"
        assert result["agents"][0]["status"] == "OFFLINE"
    
    def test_discover_response_includes_all_fields(self, marketplace_agent):
        """Test that discovery response includes all required fields."""
        payload = {}
        
        result = marketplace_agent.handle_discover(payload)
        
        assert "agents" in result
        assert "count" in result
        assert "timestamp" in result
        
        # Check agent fields
        for agent in result["agents"]:
            assert "agent_id" in agent
            assert "capabilities" in agent
            assert "endpoints" in agent
            assert "status" in agent
            assert "hcs_topic_id" in agent


class TestQueryHOLRegistry:
    """Test HOL registry querying."""
    
    def test_query_all_agents(self, marketplace_agent):
        """Test querying all agents from registry."""
        agents = marketplace_agent.query_hol_registry()
        
        assert len(agents) == 3
    
    def test_query_with_capability_filter(self, marketplace_agent):
        """Test querying with capability filter."""
        agents = marketplace_agent.query_hol_registry(
            capability_filter=["deepfake_detection"]
        )
        
        assert len(agents) == 1
        assert agents[0].agent_id == "truthforge-image-001"
    
    def test_query_with_status_filter(self, marketplace_agent):
        """Test querying with status filter."""
        agents = marketplace_agent.query_hol_registry(
            status_filter="ONLINE"
        )
        
        assert len(agents) == 2


class TestFilterByCapabilities:
    """Test capability filtering."""
    
    def test_filter_by_single_capability(self, marketplace_agent, hol_registry):
        """Test filtering agents by single capability."""
        all_agents = hol_registry.get_all_agents()
        
        filtered = marketplace_agent.filter_by_capabilities(
            all_agents,
            ["deepfake_detection"]
        )
        
        assert len(filtered) == 1
        assert filtered[0].agent_id == "truthforge-image-001"
    
    def test_filter_by_multiple_capabilities(self, marketplace_agent, hol_registry):
        """Test filtering agents by multiple capabilities."""
        all_agents = hol_registry.get_all_agents()
        
        filtered = marketplace_agent.filter_by_capabilities(
            all_agents,
            ["deepfake_detection", "document_verification"]
        )
        
        assert len(filtered) == 2
    
    def test_filter_with_no_matches(self, marketplace_agent, hol_registry):
        """Test filtering with no matching capabilities."""
        all_agents = hol_registry.get_all_agents()
        
        filtered = marketplace_agent.filter_by_capabilities(
            all_agents,
            ["nonexistent_capability"]
        )
        
        assert len(filtered) == 0
    
    def test_filter_with_empty_filter_returns_all(self, marketplace_agent, hol_registry):
        """Test that empty filter returns all agents."""
        all_agents = hol_registry.get_all_agents()
        
        filtered = marketplace_agent.filter_by_capabilities(
            all_agents,
            []
        )
        
        assert len(filtered) == len(all_agents)


class TestCaching:
    """Test discovery result caching."""
    
    def test_cache_stores_results(self, marketplace_agent):
        """Test that discovery results are cached."""
        payload = {"capability_filter": ["deepfake_detection"]}
        
        # First call should query registry
        result1 = marketplace_agent.handle_discover(payload)
        
        # Check cache
        assert len(marketplace_agent.cache) == 1
    
    def test_cache_returns_cached_results(self, marketplace_agent):
        """Test that cached results are returned on subsequent calls."""
        payload = {"capability_filter": ["deepfake_detection"]}
        
        # First call
        result1 = marketplace_agent.handle_discover(payload)
        
        # Second call should return cached result
        result2 = marketplace_agent.handle_discover(payload)
        
        assert result1 == result2
    
    def test_cache_expires_after_ttl(self, marketplace_agent):
        """Test that cache entries expire after TTL."""
        payload = {"capability_filter": ["deepfake_detection"]}
        
        # First call
        result1 = marketplace_agent.handle_discover(payload)
        
        # Wait for cache to expire (TTL is 2 seconds in fixture)
        time.sleep(2.5)
        
        # Cache should be expired
        cache_key = marketplace_agent._create_cache_key(
            ["deepfake_detection"],
            None
        )
        cached_result = marketplace_agent._get_cached_result(cache_key)
        
        assert cached_result is None
    
    def test_different_filters_create_different_cache_keys(self, marketplace_agent):
        """Test that different filters create different cache entries."""
        payload1 = {"capability_filter": ["deepfake_detection"]}
        payload2 = {"capability_filter": ["document_verification"]}
        
        marketplace_agent.handle_discover(payload1)
        marketplace_agent.handle_discover(payload2)
        
        # Should have 2 cache entries
        assert len(marketplace_agent.cache) == 2
    
    def test_clear_cache(self, marketplace_agent):
        """Test clearing the cache."""
        payload = {"capability_filter": ["deepfake_detection"]}
        
        marketplace_agent.handle_discover(payload)
        assert len(marketplace_agent.cache) == 1
        
        marketplace_agent.clear_cache()
        assert len(marketplace_agent.cache) == 0
    
    def test_get_cache_stats(self, marketplace_agent):
        """Test getting cache statistics."""
        payload = {"capability_filter": ["deepfake_detection"]}
        
        marketplace_agent.handle_discover(payload)
        
        stats = marketplace_agent.get_cache_stats()
        
        assert stats["cache_size"] == 1
        assert stats["cache_ttl"] == 2
        assert len(stats["cached_keys"]) == 1


class TestProcessRequest:
    """Test request processing."""
    
    def test_process_discover_request(self, marketplace_agent):
        """Test processing DISCOVER request."""
        request = {
            "message_type": "DISCOVER",
            "payload": {
                "capability_filter": ["deepfake_detection"]
            }
        }
        
        result = marketplace_agent.process_request(request)
        
        assert "agents" in result
        assert result["count"] == 1
    
    def test_process_discover_with_message_type_enum(self, marketplace_agent):
        """Test processing DISCOVER request with MessageType enum."""
        request = {
            "message_type": MessageType.DISCOVER,
            "payload": {
                "capability_filter": ["deepfake_detection"]
            }
        }
        
        result = marketplace_agent.process_request(request)
        
        assert "agents" in result
        assert result["count"] == 1
    
    def test_process_query_get_agent_status(self, marketplace_agent):
        """Test processing QUERY request for agent status."""
        request = {
            "message_type": "QUERY",
            "payload": {
                "action": "get_agent_status",
                "agent_id": "truthforge-image-001"
            }
        }
        
        result = marketplace_agent.process_request(request)
        
        assert result["agent_id"] == "truthforge-image-001"
        assert result["status"] == "ONLINE"
    
    def test_process_unsupported_message_type(self, marketplace_agent):
        """Test processing unsupported message type."""
        request = {
            "message_type": "UNSUPPORTED",
            "payload": {}
        }
        
        result = marketplace_agent.process_request(request)
        
        assert "error" in result
        assert "Unsupported message type" in result["error"]
    
    def test_process_unknown_action(self, marketplace_agent):
        """Test processing unknown action."""
        request = {
            "message_type": "QUERY",
            "payload": {
                "action": "unknown_action"
            }
        }
        
        result = marketplace_agent.process_request(request)
        
        assert "error" in result
        assert "Unknown action" in result["error"]
    
    def test_process_request_tracks_metrics(self, marketplace_agent):
        """Test that request processing tracks metrics."""
        initial_count = marketplace_agent.requests_processed
        
        request = {
            "message_type": "DISCOVER",
            "payload": {}
        }
        
        marketplace_agent.process_request(request)
        
        assert marketplace_agent.requests_processed == initial_count + 1


class TestPropertyBasedTests:
    """Property-based tests for Marketplace Agent."""
    
    def test_property_38_agent_discovery_response_completeness(self, marketplace_agent, hol_registry):
        """
        Property 38: Agent Discovery Response Completeness
        
        For any agent returned in a discovery response, the response shall include
        agent_id, capabilities list, endpoints, and current status.
        
        Validates: Requirements 15.4
        """
        from hypothesis import given, strategies as st
        
        # Define available capabilities in the test registry
        available_capabilities = [
            "deepfake_detection",
            "image_analysis",
            "document_verification",
            "bol_validation",
            "shipment_tracking",
            "fedex_integration"
        ]
        
        @given(
            # Generate random capability filters (0-4 capabilities, 0 means no filter)
            capability_filter=st.lists(
                st.sampled_from(available_capabilities),
                min_size=0,
                max_size=4,
                unique=True
            ),
            # Generate random status filter (or None for no filter)
            status_filter=st.one_of(
                st.none(),
                st.sampled_from(["ONLINE", "OFFLINE", "BUSY", "ERROR"])
            )
        )
        def property_test(capability_filter, status_filter):
            """
            Test that all returned agents have complete response fields.
            
            This property verifies that every agent in the discovery response
            contains all required fields: agent_id, capabilities, endpoints, and status.
            """
            # Build payload
            payload = {}
            if capability_filter:
                payload["capability_filter"] = capability_filter
            if status_filter:
                payload["status_filter"] = status_filter
            
            # Send DISCOVER message
            result = marketplace_agent.handle_discover(payload)
            
            # Property: Response must have required top-level fields
            assert "agents" in result, "Response missing 'agents' field"
            assert "count" in result, "Response missing 'count' field"
            assert "timestamp" in result, "Response missing 'timestamp' field"
            
            # Property: Count must match actual number of agents
            assert result["count"] == len(result["agents"]), (
                f"Count field {result['count']} does not match actual agents "
                f"returned {len(result['agents'])}"
            )
            
            # Property: Every agent must have all required fields
            required_fields = ["agent_id", "capabilities", "endpoints", "status"]
            
            for agent in result["agents"]:
                for field in required_fields:
                    assert field in agent, (
                        f"VIOLATION: Agent {agent.get('agent_id', 'UNKNOWN')} "
                        f"missing required field: {field}. "
                        f"Agent data: {agent}"
                    )
                
                # Additional validation: Check field types
                assert isinstance(agent["agent_id"], str), (
                    f"agent_id must be string, got {type(agent['agent_id'])}"
                )
                
                assert isinstance(agent["capabilities"], list), (
                    f"capabilities must be list, got {type(agent['capabilities'])}"
                )
                
                assert isinstance(agent["endpoints"], dict), (
                    f"endpoints must be dict, got {type(agent['endpoints'])}"
                )
                
                assert isinstance(agent["status"], str), (
                    f"status must be string, got {type(agent['status'])}"
                )
                
                # Validate status is a valid value
                valid_statuses = ["ONLINE", "OFFLINE", "BUSY", "ERROR"]
                assert agent["status"] in valid_statuses, (
                    f"status must be one of {valid_statuses}, got {agent['status']}"
                )
                
                # Validate agent_id is not empty
                assert len(agent["agent_id"]) > 0, (
                    "agent_id must not be empty string"
                )
                
                # Validate capabilities is not None (can be empty list)
                assert agent["capabilities"] is not None, (
                    "capabilities must not be None"
                )
        
        # Run the property test
        property_test()
    
    def test_property_21_discovery_response_matching(self, marketplace_agent, hol_registry):
        """
        Property 21: Discovery Response Matching
        
        For any DISCOVER message with capability filters, all agents returned
        in the response shall possess at least one of the requested capabilities.
        
        Validates: Requirements 5.6
        """
        from hypothesis import given, strategies as st
        
        # Define available capabilities in the test registry
        available_capabilities = [
            "deepfake_detection",
            "image_analysis",
            "document_verification",
            "bol_validation",
            "shipment_tracking",
            "fedex_integration"
        ]
        
        @given(
            # Generate random capability filters (1-3 capabilities)
            capability_filter=st.lists(
                st.sampled_from(available_capabilities),
                min_size=1,
                max_size=3,
                unique=True
            )
        )
        def property_test(capability_filter):
            """
            Test that all returned agents have at least one requested capability.
            """
            # Send DISCOVER message with capability filter
            payload = {
                "capability_filter": capability_filter
            }
            
            result = marketplace_agent.handle_discover(payload)
            
            # Property: All returned agents must have at least one requested capability
            for agent in result["agents"]:
                agent_capabilities = agent["capabilities"]
                
                # Check that agent has at least one matching capability
                has_matching_capability = any(
                    cap in agent_capabilities
                    for cap in capability_filter
                )
                
                assert has_matching_capability, (
                    f"Agent {agent['agent_id']} with capabilities {agent_capabilities} "
                    f"does not have any of the requested capabilities: {capability_filter}"
                )
            
            # Additional check: No agent should be returned if it has none of the requested capabilities
            all_agents = hol_registry.get_all_agents()
            for agent_metadata in all_agents:
                has_matching_capability = any(
                    cap in agent_metadata.capabilities
                    for cap in capability_filter
                )
                
                agent_in_results = any(
                    a["agent_id"] == agent_metadata.agent_id
                    for a in result["agents"]
                )
                
                # If agent has matching capability, it should be in results
                # If agent doesn't have matching capability, it should NOT be in results
                if has_matching_capability:
                    assert agent_in_results, (
                        f"Agent {agent_metadata.agent_id} has matching capability "
                        f"but was not returned in discovery results"
                    )
                else:
                    assert not agent_in_results, (
                        f"Agent {agent_metadata.agent_id} has no matching capability "
                        f"but was incorrectly returned in discovery results"
                    )
        
        # Run the property test
        property_test()
    
    def test_property_37_agent_discovery_filtering(self, marketplace_agent, hol_registry):
        """
        Property 37: Agent Discovery Filtering
        
        For any DISCOVER message with specific capability filters, the Marketplace_Agent
        shall return only agents that match at least one of the specified capabilities,
        and no agents lacking all specified capabilities.
        
        Validates: Requirements 15.2
        """
        from hypothesis import given, strategies as st
        
        # Define available capabilities in the test registry
        available_capabilities = [
            "deepfake_detection",
            "image_analysis",
            "document_verification",
            "bol_validation",
            "shipment_tracking",
            "fedex_integration"
        ]
        
        @given(
            # Generate random capability filters (1-4 capabilities)
            capability_filter=st.lists(
                st.sampled_from(available_capabilities),
                min_size=1,
                max_size=4,
                unique=True
            )
        )
        def property_test(capability_filter):
            """
            Test that discovery filtering returns only matching agents.
            
            This property verifies two critical aspects:
            1. All returned agents MUST have at least one requested capability
            2. No agents lacking ALL requested capabilities are returned
            """
            # Send DISCOVER message with capability filter
            payload = {
                "capability_filter": capability_filter
            }
            
            result = marketplace_agent.handle_discover(payload)
            
            # Get all agents from registry for comparison
            all_agents = hol_registry.get_all_agents()
            
            # Property Part 1: All returned agents must match at least one capability
            for agent in result["agents"]:
                agent_capabilities = agent["capabilities"]
                
                has_matching_capability = any(
                    cap in agent_capabilities
                    for cap in capability_filter
                )
                
                assert has_matching_capability, (
                    f"VIOLATION: Agent {agent['agent_id']} with capabilities "
                    f"{agent_capabilities} was returned but does not have any of "
                    f"the requested capabilities: {capability_filter}"
                )
            
            # Property Part 2: No agents lacking all capabilities should be returned
            for agent_metadata in all_agents:
                has_matching_capability = any(
                    cap in agent_metadata.capabilities
                    for cap in capability_filter
                )
                
                agent_in_results = any(
                    a["agent_id"] == agent_metadata.agent_id
                    for a in result["agents"]
                )
                
                # If agent lacks all requested capabilities, it must NOT be in results
                if not has_matching_capability:
                    assert not agent_in_results, (
                        f"VIOLATION: Agent {agent_metadata.agent_id} with capabilities "
                        f"{agent_metadata.capabilities} lacks all requested capabilities "
                        f"{capability_filter} but was incorrectly included in results"
                    )
                
                # Conversely, if agent has matching capability, it should be in results
                # (unless filtered by status or other criteria)
                if has_matching_capability and agent_metadata.status == "ONLINE":
                    assert agent_in_results, (
                        f"Agent {agent_metadata.agent_id} has matching capability "
                        f"and is ONLINE but was not returned in discovery results"
                    )
            
            # Property Part 3: Result count must match actual matching agents
            expected_count = sum(
                1 for agent in all_agents
                if any(cap in agent.capabilities for cap in capability_filter)
            )
            
            assert result["count"] == len(result["agents"]), (
                f"Result count {result['count']} does not match actual agents "
                f"returned {len(result['agents'])}"
            )
            
            assert result["count"] == expected_count, (
                f"Result count {result['count']} does not match expected count "
                f"{expected_count} based on registry state"
            )
        
        # Run the property test
        property_test()


    def test_property_39_offline_agent_status_indication(self, marketplace_agent, hol_registry):
        """
        Property 39: Offline Agent Status Indication
        
        For any agent that is currently offline or unreachable, the Marketplace_Agent
        shall include a status field indicating "OFFLINE" or "UNAVAILABLE" in the
        discovery response.
        
        Validates: Requirements 15.5
        """
        from hypothesis import given, strategies as st
        
        # Valid agent statuses
        valid_statuses = ["ONLINE", "OFFLINE", "BUSY", "ERROR"]
        
        @given(
            # Generate random agent statuses to set
            agent_statuses=st.lists(
                st.sampled_from(valid_statuses),
                min_size=3,
                max_size=3
            )
        )
        def property_test(agent_statuses):
            """
            Test that offline/unavailable agents are properly indicated in discovery responses.
            
            This property verifies that:
            1. All agents in discovery response have a status field
            2. Offline agents are marked with "OFFLINE" status
            3. The status field accurately reflects the agent's current state
            """
            # Clear cache to ensure fresh data
            marketplace_agent.clear_cache()
            
            # Set up test agents with different statuses
            test_agents = [
                "truthforge-image-001",
                "truthforge-verify-001",
                "truthforge-fedex-001"
            ]
            
            # Apply the generated statuses to the test agents
            for agent_id, status in zip(test_agents, agent_statuses):
                hol_registry.update_agent_status(agent_id, status)
            
            # Send DISCOVER message without filters (get all agents)
            payload = {}
            
            result = marketplace_agent.handle_discover(payload)
            
            # Property 1: All agents must have a status field
            for agent in result["agents"]:
                assert "status" in agent, (
                    f"VIOLATION: Agent {agent.get('agent_id', 'UNKNOWN')} "
                    f"missing status field in discovery response"
                )
            
            # Property 2: Status field must be a valid status value
            for agent in result["agents"]:
                assert agent["status"] in valid_statuses, (
                    f"VIOLATION: Agent {agent['agent_id']} has invalid status "
                    f"'{agent['status']}'. Must be one of {valid_statuses}"
                )
            
            # Property 3: Offline agents must be indicated as OFFLINE
            for agent_id, expected_status in zip(test_agents, agent_statuses):
                # Find this agent in the results
                agent_in_results = next(
                    (a for a in result["agents"] if a["agent_id"] == agent_id),
                    None
                )
                
                assert agent_in_results is not None, (
                    f"Agent {agent_id} not found in discovery results"
                )
                
                # Verify status matches what we set
                assert agent_in_results["status"] == expected_status, (
                    f"VIOLATION: Agent {agent_id} has status "
                    f"'{agent_in_results['status']}' in discovery response, "
                    f"but registry shows status '{expected_status}'. "
                    f"Status indication is inconsistent."
                )
            
            # Property 4: Specifically verify OFFLINE agents are properly indicated
            offline_agents = [
                agent_id for agent_id, status in zip(test_agents, agent_statuses)
                if status == "OFFLINE"
            ]
            
            for offline_agent_id in offline_agents:
                agent_in_results = next(
                    (a for a in result["agents"] if a["agent_id"] == offline_agent_id),
                    None
                )
                
                assert agent_in_results is not None, (
                    f"Offline agent {offline_agent_id} not found in discovery results"
                )
                
                assert agent_in_results["status"] == "OFFLINE", (
                    f"VIOLATION: Agent {offline_agent_id} is offline but discovery "
                    f"response shows status '{agent_in_results['status']}' instead of 'OFFLINE'"
                )
            
            # Property 5: Test with status filter for OFFLINE agents
            if offline_agents:
                # Clear cache again for filtered query
                marketplace_agent.clear_cache()
                
                offline_payload = {"status_filter": "OFFLINE"}
                offline_result = marketplace_agent.handle_discover(offline_payload)
                
                # All returned agents must have OFFLINE status
                for agent in offline_result["agents"]:
                    assert agent["status"] == "OFFLINE", (
                        f"VIOLATION: Agent {agent['agent_id']} returned in OFFLINE "
                        f"filter query but has status '{agent['status']}'"
                    )
                
                # Count must match number of offline agents
                assert offline_result["count"] == len(offline_agents), (
                    f"VIOLATION: OFFLINE filter returned {offline_result['count']} agents "
                    f"but expected {len(offline_agents)} offline agents"
                )
        
        # Run the property test
        property_test()


    def test_property_40_agent_discovery_caching(self, marketplace_agent, hol_registry):
        """
        Property 40: Agent Discovery Caching
        
        For any repeated DISCOVER request with identical filters within the TTL period,
        the Marketplace_Agent shall return cached results without querying the HOL
        registry again.
        
        Validates: Requirements 15.6
        """
        from hypothesis import given, strategies as st
        from unittest.mock import patch
        import time
        
        # Define available capabilities in the test registry
        available_capabilities = [
            "deepfake_detection",
            "image_analysis",
            "document_verification",
            "bol_validation",
            "shipment_tracking",
            "fedex_integration"
        ]
        
        @given(
            # Generate random capability filters (0-3 capabilities, 0 means no filter)
            capability_filter=st.lists(
                st.sampled_from(available_capabilities),
                min_size=0,
                max_size=3,
                unique=True
            ),
            # Generate random status filter (or None for no filter)
            status_filter=st.one_of(
                st.none(),
                st.sampled_from(["ONLINE", "OFFLINE", "BUSY", "ERROR"])
            ),
            # Number of repeated requests to test (2-5)
            num_requests=st.integers(min_value=2, max_value=5)
        )
        def property_test(capability_filter, status_filter, num_requests):
            """
            Test that repeated DISCOVER requests with identical filters return
            cached results without querying the HOL registry again.
            
            This property verifies:
            1. First request queries the HOL registry
            2. Subsequent identical requests within TTL return cached results
            3. HOL registry is not queried again for cached requests
            4. Cached results are identical to original results
            """
            # Clear cache before test
            marketplace_agent.clear_cache()
            
            # Build payload
            payload = {}
            if capability_filter:
                payload["capability_filter"] = capability_filter
            if status_filter:
                payload["status_filter"] = status_filter
            
            # Track HOL registry query calls
            original_query_method = marketplace_agent.query_hol_registry
            query_call_count = [0]  # Use list to allow modification in nested function
            
            def tracked_query(*args, **kwargs):
                query_call_count[0] += 1
                return original_query_method(*args, **kwargs)
            
            # Patch the query method to track calls
            with patch.object(marketplace_agent, 'query_hol_registry', side_effect=tracked_query):
                # Make first request
                result1 = marketplace_agent.handle_discover(payload)
                
                # Property 1: First request should query the HOL registry
                assert query_call_count[0] == 1, (
                    f"VIOLATION: First DISCOVER request should query HOL registry once, "
                    f"but query was called {query_call_count[0]} times"
                )
                
                # Store first result for comparison
                first_result = result1.copy()
                
                # Make subsequent identical requests within TTL
                for i in range(1, num_requests):
                    result = marketplace_agent.handle_discover(payload)
                    
                    # Property 2: Subsequent requests should NOT query HOL registry
                    assert query_call_count[0] == 1, (
                        f"VIOLATION: Request {i+1} should use cached results, "
                        f"but HOL registry was queried {query_call_count[0]} times total. "
                        f"Expected only 1 query (from first request)."
                    )
                    
                    # Property 3: Cached results must be identical to first result
                    # Compare agent lists (excluding timestamp which will differ)
                    assert result["count"] == first_result["count"], (
                        f"VIOLATION: Cached result count {result['count']} differs "
                        f"from original count {first_result['count']}"
                    )
                    
                    assert len(result["agents"]) == len(first_result["agents"]), (
                        f"VIOLATION: Cached result has {len(result['agents'])} agents, "
                        f"but original had {len(first_result['agents'])} agents"
                    )
                    
                    # Compare agent IDs (order-independent)
                    cached_agent_ids = sorted([a["agent_id"] for a in result["agents"]])
                    original_agent_ids = sorted([a["agent_id"] for a in first_result["agents"]])
                    
                    assert cached_agent_ids == original_agent_ids, (
                        f"VIOLATION: Cached result agent IDs {cached_agent_ids} differ "
                        f"from original agent IDs {original_agent_ids}"
                    )
                    
                    # Verify filters match
                    assert result["capability_filter"] == first_result["capability_filter"], (
                        f"VIOLATION: Cached result capability_filter differs from original"
                    )
                    
                    assert result["status_filter"] == first_result["status_filter"], (
                        f"VIOLATION: Cached result status_filter differs from original"
                    )
            
            # Property 4: Verify cache contains the entry
            cache_stats = marketplace_agent.get_cache_stats()
            assert cache_stats["cache_size"] >= 1, (
                f"VIOLATION: Cache should contain at least 1 entry after requests, "
                f"but cache size is {cache_stats['cache_size']}"
            )
            
            # Property 5: Test cache expiration after TTL
            # Wait for cache to expire (TTL is 2 seconds in fixture)
            time.sleep(2.5)
            
            # Clear the query counter
            query_call_count[0] = 0
            
            # Make another request after TTL expiration
            with patch.object(marketplace_agent, 'query_hol_registry', side_effect=tracked_query):
                result_after_ttl = marketplace_agent.handle_discover(payload)
                
                # Property 6: After TTL expiration, HOL registry should be queried again
                assert query_call_count[0] == 1, (
                    f"VIOLATION: After cache TTL expiration, HOL registry should be "
                    f"queried again, but query was called {query_call_count[0]} times"
                )
        
        # Run the property test
        property_test()


class TestIntegration:
    """Integration tests for Marketplace Agent."""
    
    def test_end_to_end_discovery_flow(self, marketplace_agent):
        """Test complete discovery flow."""
        # Register agent with HOL
        marketplace_agent.register_with_hol()
        assert marketplace_agent.registered
        
        # Process discovery request
        request = {
            "message_type": MessageType.DISCOVER,
            "payload": {
                "capability_filter": ["deepfake_detection", "document_verification"]
            }
        }
        
        result = marketplace_agent.process_request(request)
        
        # Verify results
        assert result["count"] == 2
        assert len(result["agents"]) == 2
        
        # Verify all agents have required fields
        for agent in result["agents"]:
            assert agent["agent_id"]
            assert agent["capabilities"]
            assert agent["status"]
    
    def test_health_check(self, marketplace_agent):
        """Test agent health check."""
        status = marketplace_agent.health_check()
        
        assert status.agent_id == "truthforge-market-001"
        assert status.status in ["ONLINE", "OFFLINE"]
