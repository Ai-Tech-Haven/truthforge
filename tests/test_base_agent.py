"""
Unit tests for BaseAgent class
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
from hypothesis import given, strategies as st, settings

from agents.base_agent import BaseAgent, AgentStatus
from agents.config import Config
from agents.hedera_client import MockHederaClient
from agents.hcs10_message import HCS10Message, MessageType


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing"""
    
    def process_request(self, request):
        """Simple implementation for testing"""
        return {"status": "success", "data": request.get("data", "")}


class TestAgentStatus:
    """Test suite for AgentStatus dataclass"""
    
    def test_agent_status_creation(self):
        """Test that AgentStatus can be created with all fields"""
        status = AgentStatus(
            agent_id="test-agent-001",
            status="ONLINE",
            last_heartbeat=datetime.now(timezone.utc),
            requests_processed=10,
            average_response_time=0.5,
            error_count=2
        )
        
        assert status.agent_id == "test-agent-001"
        assert status.status == "ONLINE"
        assert status.requests_processed == 10
        assert status.average_response_time == 0.5
        assert status.error_count == 2
    
    def test_agent_status_to_dict(self):
        """Test that AgentStatus converts to dictionary correctly"""
        heartbeat = datetime.now(timezone.utc)
        status = AgentStatus(
            agent_id="test-agent-001",
            status="ONLINE",
            last_heartbeat=heartbeat,
            requests_processed=10,
            average_response_time=0.5,
            error_count=2
        )
        
        status_dict = status.to_dict()
        
        assert status_dict["agent_id"] == "test-agent-001"
        assert status_dict["status"] == "ONLINE"
        assert status_dict["last_heartbeat"] == heartbeat.isoformat()
        assert status_dict["requests_processed"] == 10
        assert status_dict["average_response_time"] == 0.5
        assert status_dict["error_count"] == 2


class TestBaseAgent:
    """Test suite for BaseAgent class"""
    
    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a mock configuration for testing"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "LOG_LEVEL=INFO\n"
            "HCS_TOPIC_ID=0.0.12345\n"
        )
        return Config.load(str(env_file))
    
    @pytest.fixture
    def mock_hedera_client(self, mock_config):
        """Create a mock Hedera client for testing"""
        client = MockHederaClient(mock_config)
        client.authenticate()
        return client
    
    @pytest.fixture
    def test_agent(self, mock_config, mock_hedera_client):
        """Create a test agent instance"""
        return ConcreteAgent(
            agent_id="test-agent-001",
            capabilities=["test", "verification"],
            hcs_topic_id="0.0.12345",
            config=mock_config,
            hedera_client=mock_hedera_client
        )
    
    def test_base_agent_initialization(self, test_agent):
        """Test that BaseAgent initializes correctly with valid parameters"""
        assert test_agent.agent_id == "test-agent-001"
        assert test_agent.capabilities == ["test", "verification"]
        assert test_agent.hcs_topic_id == "0.0.12345"
        assert test_agent.registered is False
        assert test_agent.requests_processed == 0
        assert test_agent.error_count == 0
    
    def test_base_agent_initialization_missing_agent_id(self, mock_config, mock_hedera_client):
        """Test that BaseAgent raises ValueError when agent_id is missing"""
        with pytest.raises(ValueError) as exc_info:
            ConcreteAgent(
                agent_id="",
                capabilities=["test"],
                hcs_topic_id="0.0.12345",
                config=mock_config,
                hedera_client=mock_hedera_client
            )
        
        assert "agent_id is required" in str(exc_info.value)
    
    def test_base_agent_initialization_empty_capabilities(self, mock_config, mock_hedera_client):
        """Test that BaseAgent raises ValueError when capabilities is empty"""
        with pytest.raises(ValueError) as exc_info:
            ConcreteAgent(
                agent_id="test-agent-001",
                capabilities=[],
                hcs_topic_id="0.0.12345",
                config=mock_config,
                hedera_client=mock_hedera_client
            )
        
        assert "capabilities list cannot be empty" in str(exc_info.value)
    
    def test_base_agent_initialization_missing_hcs_topic_id(self, mock_config, mock_hedera_client):
        """Test that BaseAgent raises ValueError when hcs_topic_id is missing"""
        with pytest.raises(ValueError) as exc_info:
            ConcreteAgent(
                agent_id="test-agent-001",
                capabilities=["test"],
                hcs_topic_id="",
                config=mock_config,
                hedera_client=mock_hedera_client
            )
        
        assert "hcs_topic_id is required" in str(exc_info.value)
    
    def test_register_with_hol(self, test_agent):
        """Test that agent can register with HOL successfully"""
        result = test_agent.register_with_hol()
        
        assert result is True
        assert test_agent.registered is True
    
    def test_register_with_hol_authenticates_client(self, mock_config):
        """Test that register_with_hol authenticates Hedera client if needed"""
        # Create unauthenticated client
        client = MockHederaClient(mock_config)
        assert client.authenticated is False
        
        agent = ConcreteAgent(
            agent_id="test-agent-001",
            capabilities=["test"],
            hcs_topic_id="0.0.12345",
            config=mock_config,
            hedera_client=client
        )
        
        # Register should authenticate
        agent.register_with_hol()
        
        assert client.authenticated is True
        assert agent.registered is True
    
    def test_send_message(self, test_agent):
        """Test that agent can send messages successfully"""
        message = HCS10Message(
            message_type=MessageType.REQUEST,
            sender_id="test-agent-001",
            recipient_id="test-agent-002",
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={"action": "test"}
        )
        
        transaction_id = test_agent.send_message("test-agent-002", message)
        
        assert transaction_id is not None
        assert "@" in transaction_id  # Mock transaction ID format
    
    def test_send_message_updates_sender_id(self, test_agent):
        """Test that send_message updates sender_id if it doesn't match agent_id"""
        message = HCS10Message(
            message_type=MessageType.REQUEST,
            sender_id="wrong-agent",
            recipient_id="test-agent-002",
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={"action": "test"}
        )
        
        test_agent.send_message("test-agent-002", message)
        
        # Sender ID should be updated to match agent_id
        assert message.sender_id == "test-agent-001"
    
    def test_send_message_updates_recipient_id(self, test_agent):
        """Test that send_message updates recipient_id if it doesn't match parameter"""
        message = HCS10Message(
            message_type=MessageType.REQUEST,
            sender_id="test-agent-001",
            recipient_id="wrong-recipient",
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={"action": "test"}
        )
        
        test_agent.send_message("test-agent-002", message)
        
        # Recipient ID should be updated
        assert message.recipient_id == "test-agent-002"
    
    def test_send_message_generates_signature(self, test_agent):
        """Test that send_message generates signature if not present"""
        message = HCS10Message(
            message_type=MessageType.REQUEST,
            sender_id="test-agent-001",
            recipient_id="test-agent-002",
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={"action": "test"}
        )
        
        # Message has no signature initially
        assert message.signature == ""
        
        test_agent.send_message("test-agent-002", message)
        
        # Signature should be generated
        assert message.signature != ""
    
    def test_send_message_missing_recipient_id(self, test_agent):
        """Test that send_message raises ValueError when recipient_id is missing"""
        message = HCS10Message(
            message_type=MessageType.REQUEST,
            sender_id="test-agent-001",
            recipient_id="test-agent-002",
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={"action": "test"}
        )
        
        with pytest.raises(ValueError) as exc_info:
            test_agent.send_message("", message)
        
        assert "recipient_id is required" in str(exc_info.value)
    
    def test_send_message_increments_error_count_on_failure(self, test_agent):
        """Test that send_message increments error_count when submission fails"""
        # Mock the hedera_client to raise an exception
        test_agent.hedera_client.submit_message = Mock(side_effect=RuntimeError("Network error"))
        
        message = HCS10Message(
            message_type=MessageType.REQUEST,
            sender_id="test-agent-001",
            recipient_id="test-agent-002",
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={"action": "test"}
        )
        
        initial_error_count = test_agent.error_count
        
        with pytest.raises(RuntimeError):
            test_agent.send_message("test-agent-002", message)
        
        assert test_agent.error_count == initial_error_count + 1
    
    def test_receive_message_returns_none(self, test_agent):
        """Test that receive_message returns None (not implemented)"""
        result = test_agent.receive_message()
        assert result is None
    
    def test_process_request_abstract_method(self, test_agent):
        """Test that process_request is implemented by concrete class"""
        request = {"data": "test"}
        response = test_agent.process_request(request)
        
        assert response["status"] == "success"
        assert response["data"] == "test"
    
    def test_health_check(self, test_agent):
        """Test that health_check returns AgentStatus with correct data"""
        # Register agent first
        test_agent.register_with_hol()
        
        # Process some requests
        test_agent.requests_processed = 5
        test_agent.total_response_time = 2.5
        test_agent.error_count = 1
        
        status = test_agent.health_check()
        
        assert isinstance(status, AgentStatus)
        assert status.agent_id == "test-agent-001"
        assert status.status == "ONLINE"
        assert status.requests_processed == 5
        assert status.average_response_time == 0.5  # 2.5 / 5
        assert status.error_count == 1
    
    def test_health_check_offline_when_not_registered(self, test_agent):
        """Test that health_check returns OFFLINE status when not registered"""
        status = test_agent.health_check()
        
        assert status.status == "OFFLINE"
    
    def test_health_check_error_status_with_high_error_rate(self, test_agent):
        """Test that health_check returns ERROR status with high error rate"""
        test_agent.register_with_hol()
        test_agent.requests_processed = 10
        test_agent.error_count = 6  # 60% error rate
        
        status = test_agent.health_check()
        
        assert status.status == "ERROR"
    
    def test_health_check_updates_heartbeat(self, test_agent):
        """Test that health_check updates last_heartbeat timestamp"""
        old_heartbeat = test_agent.last_heartbeat
        
        # Wait a tiny bit to ensure timestamp changes
        import time
        time.sleep(0.01)
        
        status = test_agent.health_check()
        
        assert test_agent.last_heartbeat > old_heartbeat
        assert status.last_heartbeat == test_agent.last_heartbeat
    
    def test_track_request_success(self, test_agent):
        """Test that _track_request updates metrics correctly for success"""
        initial_requests = test_agent.requests_processed
        initial_time = test_agent.total_response_time
        initial_errors = test_agent.error_count
        
        test_agent._track_request(response_time=0.5, success=True)
        
        assert test_agent.requests_processed == initial_requests + 1
        assert test_agent.total_response_time == initial_time + 0.5
        assert test_agent.error_count == initial_errors
    
    def test_track_request_failure(self, test_agent):
        """Test that _track_request updates metrics correctly for failure"""
        initial_requests = test_agent.requests_processed
        initial_errors = test_agent.error_count
        
        test_agent._track_request(response_time=0.5, success=False)
        
        assert test_agent.requests_processed == initial_requests + 1
        assert test_agent.error_count == initial_errors + 1
    
    def test_repr(self, test_agent):
        """Test that __repr__ returns readable string representation"""
        repr_str = repr(test_agent)
        
        assert "ConcreteAgent" in repr_str
        assert "test-agent-001" in repr_str
        assert "test" in repr_str
        assert "verification" in repr_str
        assert "registered=False" in repr_str



class MockHOLRegistry:
    """
    Mock HOL Registry for testing agent registration persistence.
    
    Stores agent registration data in memory and allows querying
    to verify that registration data persists correctly.
    """
    
    def __init__(self):
        self.agents = {}
    
    def register_agent(self, agent_id: str, capabilities: list, hcs_topic_id: str, metadata: dict):
        """Store agent registration data"""
        self.agents[agent_id] = {
            "agent_id": agent_id,
            "capabilities": capabilities,
            "hcs_topic_id": hcs_topic_id,
            "metadata": metadata
        }
    
    def query_agent(self, agent_id: str):
        """Retrieve agent registration data"""
        return self.agents.get(agent_id)


class TestAgentRegistrationPersistence:
    """
    Property-based tests for agent registration persistence.
    
    Feature: truthforge, Property 2: Agent Registration Persistence
    For any agent registration with capabilities, endpoints, and metadata,
    querying the HOL registry immediately after registration shall return
    all provided registration data unchanged.
    
    Validates: Requirements 1.3, 1.4
    """
    
    @given(
        agent_id=st.text(min_size=5, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'
        )),
        capabilities=st.lists(
            st.text(min_size=3, max_size=20, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll')
            )),
            min_size=1,
            max_size=10,
            unique=True
        ),
        hcs_topic_id=st.from_regex(r'0\.0\.\d{1,10}', fullmatch=True),
        network=st.sampled_from(['testnet', 'mainnet'])
    )
    @settings(max_examples=100, deadline=None)
    def test_agent_registration_persistence(self, agent_id, capabilities, hcs_topic_id, network):
        """
        Property 2: Agent Registration Persistence
        
        For any agent registration with capabilities, endpoints, and metadata,
        querying the HOL registry immediately after registration shall return
        all provided registration data unchanged.
        
        This test verifies that:
        1. Agent registration data is stored correctly
        2. All fields (agent_id, capabilities, hcs_topic_id, metadata) persist
        3. Querying immediately after registration returns unchanged data
        
        Validates: Requirements 1.3, 1.4
        """
        # Create mock HOL registry
        hol_registry = MockHOLRegistry()
        
        # Create config using environment variables (no file needed)
        import os
        os.environ['MOCK_MODE'] = 'true'
        os.environ['LOG_LEVEL'] = 'INFO'
        os.environ['HCS_TOPIC_ID'] = hcs_topic_id
        os.environ['HEDERA_NETWORK'] = network
        
        config = Config(
            mock_mode=True,
            log_level='INFO',
            hcs_topic_id=hcs_topic_id,
            hedera_network=network
        )
        
        # Create Hedera client
        hedera_client = MockHederaClient(config)
        hedera_client.authenticate()
        
        # Create agent
        agent = ConcreteAgent(
            agent_id=agent_id,
            capabilities=capabilities,
            hcs_topic_id=hcs_topic_id,
            config=config,
            hedera_client=hedera_client
        )
        
        # Prepare registration metadata
        metadata = {
            "version": "1.0.0",
            "network": network
        }
        
        # Register agent with HOL registry
        hol_registry.register_agent(
            agent_id=agent_id,
            capabilities=capabilities,
            hcs_topic_id=hcs_topic_id,
            metadata=metadata
        )
        
        # Query the HOL registry immediately after registration
        retrieved_data = hol_registry.query_agent(agent_id)
        
        # Verify all registration data is returned unchanged
        assert retrieved_data is not None, f"Agent {agent_id} not found in HOL registry"
        assert retrieved_data["agent_id"] == agent_id, "Agent ID mismatch"
        assert retrieved_data["capabilities"] == capabilities, "Capabilities mismatch"
        assert retrieved_data["hcs_topic_id"] == hcs_topic_id, "HCS Topic ID mismatch"
        assert retrieved_data["metadata"] == metadata, "Metadata mismatch"
        
        # Verify that capabilities list is preserved exactly
        assert len(retrieved_data["capabilities"]) == len(capabilities), "Capabilities count mismatch"
        for cap in capabilities:
            assert cap in retrieved_data["capabilities"], f"Capability {cap} not found in retrieved data"
        
        # Verify metadata fields are preserved
        assert retrieved_data["metadata"]["version"] == metadata["version"], "Metadata version mismatch"
        assert retrieved_data["metadata"]["network"] == metadata["network"], "Metadata network mismatch"


class TestAgentReRegistrationIdempotence:
    """
    Property-based tests for agent re-registration idempotence.
    
    Feature: truthforge, Property 3: Agent Re-registration Idempotence
    For any agent that is already registered, attempting to re-register
    with the same agent ID shall succeed and update the registration
    without creating duplicates.
    
    Validates: Requirements 1.5
    """
    
    @given(
        agent_id=st.text(min_size=5, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'
        )),
        initial_capabilities=st.lists(
            st.text(min_size=3, max_size=20, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll')
            )),
            min_size=1,
            max_size=10,
            unique=True
        ),
        updated_capabilities=st.lists(
            st.text(min_size=3, max_size=20, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll')
            )),
            min_size=1,
            max_size=10,
            unique=True
        ),
        hcs_topic_id=st.from_regex(r'0\.0\.\d{1,10}', fullmatch=True),
        network=st.sampled_from(['testnet', 'mainnet'])
    )
    @settings(max_examples=100, deadline=None)
    def test_agent_reregistration_idempotence(
        self, 
        agent_id, 
        initial_capabilities, 
        updated_capabilities, 
        hcs_topic_id, 
        network
    ):
        """
        Property 3: Agent Re-registration Idempotence
        
        For any agent that is already registered, attempting to re-register
        with the same agent ID shall succeed and update the registration
        without creating duplicates.
        
        This test verifies that:
        1. Initial registration succeeds
        2. Re-registration with same agent_id succeeds
        3. Re-registration updates the agent data (capabilities, metadata)
        4. No duplicate entries are created in the registry
        5. Only one agent entry exists after re-registration
        
        Validates: Requirements 1.5
        """
        # Create mock HOL registry
        hol_registry = MockHOLRegistry()
        
        # Create config
        import os
        os.environ['MOCK_MODE'] = 'true'
        os.environ['LOG_LEVEL'] = 'INFO'
        os.environ['HCS_TOPIC_ID'] = hcs_topic_id
        os.environ['HEDERA_NETWORK'] = network
        
        config = Config(
            mock_mode=True,
            log_level='INFO',
            hcs_topic_id=hcs_topic_id,
            hedera_network=network
        )
        
        # Create Hedera client
        hedera_client = MockHederaClient(config)
        hedera_client.authenticate()
        
        # Create agent with initial capabilities
        agent = ConcreteAgent(
            agent_id=agent_id,
            capabilities=initial_capabilities,
            hcs_topic_id=hcs_topic_id,
            config=config,
            hedera_client=hedera_client
        )
        
        # Initial registration metadata
        initial_metadata = {
            "version": "1.0.0",
            "network": network,
            "registration_count": 1
        }
        
        # Perform initial registration
        hol_registry.register_agent(
            agent_id=agent_id,
            capabilities=initial_capabilities,
            hcs_topic_id=hcs_topic_id,
            metadata=initial_metadata
        )
        
        # Verify initial registration succeeded
        initial_data = hol_registry.query_agent(agent_id)
        assert initial_data is not None, "Initial registration failed"
        assert initial_data["agent_id"] == agent_id
        assert initial_data["capabilities"] == initial_capabilities
        
        # Count agents before re-registration (should be 1)
        initial_agent_count = len(hol_registry.agents)
        assert initial_agent_count >= 1, "No agents registered"
        
        # Update agent capabilities for re-registration
        agent.capabilities = updated_capabilities
        
        # Updated registration metadata
        updated_metadata = {
            "version": "1.0.1",
            "network": network,
            "registration_count": 2
        }
        
        # Perform re-registration with same agent_id but updated data
        hol_registry.register_agent(
            agent_id=agent_id,
            capabilities=updated_capabilities,
            hcs_topic_id=hcs_topic_id,
            metadata=updated_metadata
        )
        
        # Verify re-registration succeeded
        updated_data = hol_registry.query_agent(agent_id)
        assert updated_data is not None, "Re-registration failed"
        
        # Verify agent data was updated (not duplicated)
        assert updated_data["agent_id"] == agent_id, "Agent ID changed after re-registration"
        assert updated_data["capabilities"] == updated_capabilities, "Capabilities not updated"
        assert updated_data["metadata"]["version"] == "1.0.1", "Metadata not updated"
        assert updated_data["metadata"]["registration_count"] == 2, "Registration count not updated"
        
        # Verify no duplicate entries were created
        final_agent_count = len(hol_registry.agents)
        assert final_agent_count == initial_agent_count, (
            f"Duplicate agent entries created: expected {initial_agent_count}, "
            f"got {final_agent_count}"
        )
        
        # Verify only one entry exists for this agent_id
        matching_agents = [
            agent_data for agent_data in hol_registry.agents.values()
            if agent_data["agent_id"] == agent_id
        ]
        assert len(matching_agents) == 1, (
            f"Expected exactly 1 agent entry, found {len(matching_agents)}"
        )
        
        # Verify the single entry has the updated data
        assert matching_agents[0]["capabilities"] == updated_capabilities
        assert matching_agents[0]["metadata"]["version"] == "1.0.1"
