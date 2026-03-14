"""
Unit tests for Hedera client implementations.

Tests both HederaClient (production) and MockHederaClient (development)
to ensure proper blockchain integration and mock behavior.
"""

import pytest
import time
from datetime import datetime, timezone
from hypothesis import given, strategies as st
from agents.hedera_client import HederaClient, MockHederaClient, create_hedera_client
from agents.config import Config
from agents.hcs10_message import HCS10Message, MessageType


class TestMockHederaClient:
    """Tests for MockHederaClient."""
    
    @pytest.fixture
    def mock_config(self, tmp_path):
        """Fixture providing mock mode configuration."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "LOG_LEVEL=INFO\n"
        )
        return Config.load(str(env_file))
    
    @pytest.fixture
    def mock_client(self, mock_config):
        """Fixture providing MockHederaClient instance."""
        return MockHederaClient(mock_config)
    
    @pytest.fixture
    def sample_message(self):
        """Fixture providing a sample HCS10Message."""
        return HCS10Message(
            message_type=MessageType.REQUEST,
            sender_id="truthforge-orch-001",
            recipient_id="truthforge-image-001",
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            payload={"action": "analyze_image", "image_id": "img_123"}
        )
    
    def test_mock_client_initialization(self, mock_config):
        """Test MockHederaClient initializes correctly."""
        client = MockHederaClient(mock_config)
        
        assert client.config == mock_config
        assert client.authenticated is False
        assert client.total_cost_hbar == 0.0
        assert client.mock_balance == 1000.0
        assert client.transaction_counter == 0
    
    def test_mock_authenticate_always_succeeds(self, mock_client):
        """Test mock authentication always succeeds."""
        result = mock_client.authenticate()
        
        assert result is True
        assert mock_client.authenticated is True
    
    def test_mock_submit_message_returns_transaction_id(self, mock_client, sample_message):
        """Test mock message submission returns transaction ID."""
        transaction_id = mock_client.submit_message(sample_message)
        
        assert transaction_id
        assert isinstance(transaction_id, str)
        assert "@" in transaction_id  # Format: topic@timestamp.nanos
    
    def test_mock_submit_message_tracks_costs(self, mock_client, sample_message):
        """Test mock message submission tracks transaction costs."""
        initial_balance = mock_client.mock_balance
        initial_total_cost = mock_client.total_cost_hbar
        
        mock_client.submit_message(sample_message)
        
        # Cost should be tracked
        assert mock_client.total_cost_hbar > initial_total_cost
        assert mock_client.mock_balance < initial_balance
        
        # Verify cost amount (0.0001 HBAR per transaction)
        assert mock_client.total_cost_hbar == initial_total_cost + 0.0001
        assert mock_client.mock_balance == initial_balance - 0.0001
    
    def test_mock_submit_message_increments_counter(self, mock_client, sample_message):
        """Test mock message submission increments transaction counter."""
        assert mock_client.transaction_counter == 0
        
        mock_client.submit_message(sample_message)
        assert mock_client.transaction_counter == 1
        
        mock_client.submit_message(sample_message)
        assert mock_client.transaction_counter == 2
    
    def test_mock_submit_message_stores_receipt(self, mock_client, sample_message):
        """Test mock message submission stores transaction receipt."""
        transaction_id = mock_client.submit_message(sample_message)
        
        # Receipt should be stored
        assert transaction_id in mock_client.mock_transactions
        
        receipt = mock_client.mock_transactions[transaction_id]
        assert receipt["transaction_id"] == transaction_id
        assert receipt["status"] == "SUCCESS"
        assert "consensus_timestamp" in receipt
        assert "topic_sequence_number" in receipt
    
    def test_mock_submit_message_rejects_none(self, mock_client):
        """Test mock message submission rejects None message."""
        with pytest.raises(ValueError, match="Message cannot be None"):
            mock_client.submit_message(None)
    
    def test_mock_get_transaction_receipt_returns_stored_receipt(self, mock_client, sample_message):
        """Test getting receipt for stored transaction."""
        transaction_id = mock_client.submit_message(sample_message)
        
        receipt = mock_client.get_transaction_receipt(transaction_id)
        
        assert receipt["transaction_id"] == transaction_id
        assert receipt["status"] == "SUCCESS"
        assert "consensus_timestamp" in receipt
        assert "topic_sequence_number" in receipt
        # Message data should not be in receipt
        assert "message" not in receipt
    
    def test_mock_get_transaction_receipt_generates_for_unknown(self, mock_client):
        """Test getting receipt for unknown transaction generates mock receipt."""
        unknown_tx_id = "0.0.99999@1234567890.123456789"
        
        receipt = mock_client.get_transaction_receipt(unknown_tx_id)
        
        assert receipt["transaction_id"] == unknown_tx_id
        assert receipt["status"] == "SUCCESS"
        assert "consensus_timestamp" in receipt
    
    def test_mock_get_transaction_receipt_rejects_empty_id(self, mock_client):
        """Test getting receipt with empty transaction ID raises error."""
        with pytest.raises(ValueError, match="transaction_id cannot be empty"):
            mock_client.get_transaction_receipt("")
    
    def test_mock_check_balance_returns_balance(self, mock_client):
        """Test checking mock balance."""
        balance = mock_client.check_balance()
        
        assert balance == 1000.0
        assert isinstance(balance, float)
    
    def test_mock_check_balance_reflects_transactions(self, mock_client, sample_message):
        """Test balance decreases after transactions."""
        initial_balance = mock_client.check_balance()
        
        mock_client.submit_message(sample_message)
        
        new_balance = mock_client.check_balance()
        assert new_balance < initial_balance
        assert new_balance == initial_balance - 0.0001
    
    def test_mock_get_total_cost(self, mock_client, sample_message):
        """Test getting total transaction costs."""
        assert mock_client.get_total_cost() == 0.0
        
        mock_client.submit_message(sample_message)
        assert mock_client.get_total_cost() == 0.0001
        
        mock_client.submit_message(sample_message)
        assert mock_client.get_total_cost() == 0.0002
    
    def test_mock_reset_state(self, mock_client, sample_message):
        """Test resetting mock client state."""
        # Submit some transactions
        mock_client.submit_message(sample_message)
        mock_client.submit_message(sample_message)
        
        assert mock_client.transaction_counter == 2
        assert mock_client.total_cost_hbar > 0
        assert mock_client.mock_balance < 1000.0
        assert len(mock_client.mock_transactions) == 2
        
        # Reset state
        mock_client.reset_mock_state()
        
        assert mock_client.transaction_counter == 0
        assert mock_client.total_cost_hbar == 0.0
        assert mock_client.mock_balance == 1000.0
        assert len(mock_client.mock_transactions) == 0
    
    def test_mock_get_mock_transactions(self, mock_client, sample_message):
        """Test getting all mock transactions."""
        tx1 = mock_client.submit_message(sample_message)
        tx2 = mock_client.submit_message(sample_message)
        
        transactions = mock_client.get_mock_transactions()
        
        assert len(transactions) == 2
        assert tx1 in transactions
        assert tx2 in transactions
        
        # Should return a copy, not the original
        transactions.clear()
        assert len(mock_client.get_mock_transactions()) == 2
    
    def test_mock_multiple_messages_unique_transaction_ids(self, mock_client, sample_message):
        """Test multiple messages get unique transaction IDs."""
        tx_ids = set()
        
        for _ in range(5):
            tx_id = mock_client.submit_message(sample_message)
            tx_ids.add(tx_id)
            time.sleep(0.001)  # Small delay to ensure different timestamps
        
        # All transaction IDs should be unique
        assert len(tx_ids) == 5


class TestHederaClient:
    """Tests for HederaClient (production mode)."""
    
    @pytest.fixture
    def production_config(self, tmp_path):
        """Fixture providing production mode configuration."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=false\n"
            "HEDERA_ACCOUNT_ID=0.0.12345\n"
            "HEDERA_PRIVATE_KEY=302e020100300506032b65700422042012345678901234567890123456789012\n"
            "HEDERA_NETWORK=testnet\n"
            "HCS_TOPIC_ID=0.0.67890\n"
            "LOG_LEVEL=INFO\n"
        )
        return Config.load(str(env_file))
    
    def test_hedera_client_initialization_requires_credentials(self, tmp_path):
        """Test HederaClient requires credentials."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=false\n"
            "LOG_LEVEL=INFO\n"
        )
        
        # Config validation should fail first due to missing credentials
        with pytest.raises(ValueError, match="HEDERA_ACCOUNT_ID is required"):
            config = Config.load(str(env_file))
    
    def test_hedera_client_initialization_with_credentials(self, production_config):
        """Test HederaClient initializes with valid credentials."""
        client = HederaClient(production_config)
        
        assert client.config == production_config
        assert client.account_id == "0.0.12345"
        assert client.private_key == "302e020100300506032b65700422042012345678901234567890123456789012"
        assert client.network == "testnet"
        assert client.topic_id == "0.0.67890"
        assert client.authenticated is False
        assert client.client is None
    
    def test_hedera_client_submit_message_requires_authentication(self, production_config):
        """Test message submission requires authentication."""
        client = HederaClient(production_config)
        
        message = HCS10Message(
            message_type=MessageType.REQUEST,
            sender_id="test-sender",
            recipient_id="test-recipient",
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            payload={}
        )
        
        with pytest.raises(RuntimeError, match="Client not authenticated"):
            client.submit_message(message)
    
    def test_hedera_client_get_receipt_requires_authentication(self, production_config):
        """Test getting receipt requires authentication."""
        client = HederaClient(production_config)
        
        with pytest.raises(RuntimeError, match="Client not authenticated"):
            client.get_transaction_receipt("0.0.12345@1234567890.123456789")
    
    def test_hedera_client_check_balance_requires_authentication(self, production_config):
        """Test checking balance requires authentication."""
        client = HederaClient(production_config)
        
        with pytest.raises(RuntimeError, match="Client not authenticated"):
            client.check_balance()
    
    def test_hedera_client_submit_message_rejects_none(self, production_config):
        """Test message submission rejects None message."""
        client = HederaClient(production_config)
        client.authenticated = True  # Bypass authentication for this test
        
        with pytest.raises(ValueError, match="Message cannot be None"):
            client.submit_message(None)
    
    def test_hedera_client_get_receipt_rejects_empty_id(self, production_config):
        """Test getting receipt rejects empty transaction ID."""
        client = HederaClient(production_config)
        client.authenticated = True  # Bypass authentication for this test
        
        with pytest.raises(ValueError, match="transaction_id cannot be empty"):
            client.get_transaction_receipt("")


class TestCreateHederaClient:
    """Tests for create_hedera_client factory function."""
    
    def test_create_hedera_client_mock_mode(self, tmp_path):
        """Test factory creates MockHederaClient in mock mode."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "LOG_LEVEL=INFO\n"
        )
        config = Config.load(str(env_file))
        
        client = create_hedera_client(config)
        
        assert isinstance(client, MockHederaClient)
    
    def test_create_hedera_client_production_mode(self, tmp_path):
        """Test factory creates HederaClient in production mode."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=false\n"
            "HEDERA_ACCOUNT_ID=0.0.12345\n"
            "HEDERA_PRIVATE_KEY=302e020100300506032b65700422042012345678901234567890123456789012\n"
            "HEDERA_NETWORK=testnet\n"
            "HCS_TOPIC_ID=0.0.67890\n"
            "LOG_LEVEL=INFO\n"
        )
        config = Config.load(str(env_file))
        
        client = create_hedera_client(config)
        
        assert isinstance(client, HederaClient)


class TestHCSMessageSubmissionProperties:
    """Property-based tests for HCS message submission using Hypothesis."""
    
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
    def test_property_18_hcs_message_submission(self, msg_type, sender, recipient, payload, tmp_path_factory):
        """
        Feature: truthforge, Property 18: HCS Message Submission
        
        For any agent-to-agent message, the message shall be submitted to the 
        configured HCS topic and an HCS transaction ID shall be returned.
        
        Validates: Requirements 5.3
        """
        # Create a temporary config for this test
        tmp_path = tmp_path_factory.mktemp("test_hcs_submission")
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "HCS_TOPIC_ID=0.0.12345\n"
            "LOG_LEVEL=INFO\n"
        )
        config = Config.load(str(env_file))
        
        # Create and authenticate mock client
        mock_client = MockHederaClient(config)
        mock_client.authenticate()
        
        # Generate a valid ISO 8601 timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Create a valid HCS10Message
        message = HCS10Message(
            message_type=msg_type,
            sender_id=sender,
            recipient_id=recipient,
            timestamp=timestamp,
            payload=payload
        )
        
        # Property: Message submission must return a transaction ID
        transaction_id = mock_client.submit_message(message)
        
        assert transaction_id is not None, "Transaction ID must not be None"
        assert isinstance(transaction_id, str), "Transaction ID must be a string"
        assert len(transaction_id) > 0, "Transaction ID must not be empty"
        
        # Property: Transaction ID must follow expected format (topic@timestamp.nanos)
        assert "@" in transaction_id, "Transaction ID must contain '@' separator"
        
        parts = transaction_id.split("@")
        assert len(parts) == 2, "Transaction ID must have format: topic@timestamp.nanos"
        
        topic_part = parts[0]
        timestamp_part = parts[1]
        
        # Verify topic part is present
        assert len(topic_part) > 0, "Topic part must not be empty"
        
        # Verify timestamp part contains seconds and nanos
        assert "." in timestamp_part, "Timestamp part must contain seconds.nanos"
        
        # Property: Transaction ID must be retrievable via get_transaction_receipt
        receipt = mock_client.get_transaction_receipt(transaction_id)
        
        assert receipt is not None, "Receipt must not be None"
        assert isinstance(receipt, dict), "Receipt must be a dictionary"
        assert "transaction_id" in receipt, "Receipt must contain transaction_id"
        assert receipt["transaction_id"] == transaction_id, "Receipt transaction_id must match submitted transaction_id"
        
        # Property: Receipt must contain required fields
        assert "consensus_timestamp" in receipt, "Receipt must contain consensus_timestamp"
        assert "status" in receipt, "Receipt must contain status"
        assert receipt["status"] == "SUCCESS", "Receipt status must be SUCCESS for valid submission"
        
        # Property: Receipt must contain topic sequence number
        assert "topic_sequence_number" in receipt, "Receipt must contain topic_sequence_number"
        assert isinstance(receipt["topic_sequence_number"], int), "Topic sequence number must be an integer"
        assert receipt["topic_sequence_number"] > 0, "Topic sequence number must be positive"
        
        # Property: Consensus timestamp must be valid ISO 8601 format
        consensus_timestamp = receipt["consensus_timestamp"]
        assert isinstance(consensus_timestamp, str), "Consensus timestamp must be a string"
        # Verify it can be parsed as ISO 8601
        datetime.fromisoformat(consensus_timestamp.replace('Z', '+00:00'))
        
        # Property: Transaction must be tracked in client's transaction history
        mock_transactions = mock_client.get_mock_transactions()
        assert transaction_id in mock_transactions, "Transaction must be stored in client history"
        
        # Property: Multiple submissions must produce unique transaction IDs
        # Submit the same message again
        transaction_id_2 = mock_client.submit_message(message)
        assert transaction_id_2 != transaction_id, "Multiple submissions must produce unique transaction IDs"
        
        # Property: Transaction cost must be tracked
        total_cost = mock_client.get_total_cost()
        assert total_cost > 0, "Transaction costs must be tracked"
        assert isinstance(total_cost, float), "Total cost must be a float"


class TestProductionModeCostTrackingProperties:
    """Property-based tests for production mode cost tracking using Hypothesis."""
    
    @given(
        num_transactions=st.integers(min_value=1, max_value=20),
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
    def test_property_46_production_mode_cost_tracking(self, num_transactions, msg_type, sender, recipient, payload, tmp_path_factory):
        """
        Feature: truthforge, Property 46: Production Mode Cost Tracking
        
        For any HCS transaction in Production_Mode, the system shall record the HBAR cost 
        and maintain a running total of transaction costs.
        
        Validates: Requirements 12.4
        """
        # Create a temporary config for this test (using mock mode for testing)
        tmp_path = tmp_path_factory.mktemp("test_cost_tracking")
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "HCS_TOPIC_ID=0.0.12345\n"
            "LOG_LEVEL=INFO\n"
        )
        config = Config.load(str(env_file))
        
        # Create and authenticate mock client (simulates production behavior)
        mock_client = MockHederaClient(config)
        mock_client.authenticate()
        
        # Property: Initial cost should be zero
        initial_cost = mock_client.get_total_cost()
        assert initial_cost == 0.0, "Initial total cost must be zero"
        
        # Generate a valid ISO 8601 timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Create a valid HCS10Message
        message = HCS10Message(
            message_type=msg_type,
            sender_id=sender,
            recipient_id=recipient,
            timestamp=timestamp,
            payload=payload
        )
        
        # Property: Submit multiple transactions and track costs
        transaction_ids = []
        expected_cost_per_transaction = 0.0001  # Standard HCS message cost
        
        for i in range(num_transactions):
            # Submit message
            tx_id = mock_client.submit_message(message)
            transaction_ids.append(tx_id)
            
            # Property: Cost must increase after each transaction
            current_cost = mock_client.get_total_cost()
            expected_total_cost = expected_cost_per_transaction * (i + 1)
            
            # Use approximate comparison for floating point values
            assert abs(current_cost - expected_total_cost) < 1e-10, (
                f"After transaction {i+1}, total cost should be {expected_total_cost} HBAR, "
                f"but got {current_cost} HBAR"
            )
            
            # Property: Cost must be a positive float
            assert isinstance(current_cost, float), "Total cost must be a float"
            assert current_cost > 0, "Total cost must be positive after transactions"
        
        # Property: Final total cost must equal number of transactions * cost per transaction
        final_cost = mock_client.get_total_cost()
        expected_final_cost = expected_cost_per_transaction * num_transactions
        
        # Use approximate comparison for floating point values
        assert abs(final_cost - expected_final_cost) < 1e-10, (
            f"Final total cost should be {expected_final_cost} HBAR "
            f"({num_transactions} transactions * {expected_cost_per_transaction} HBAR), "
            f"but got {final_cost} HBAR"
        )
        
        # Property: Cost tracking must be monotonically increasing
        # (costs never decrease, only increase or stay the same)
        assert final_cost >= initial_cost, "Total cost must never decrease"
        
        # Property: Each transaction must have been recorded
        assert len(transaction_ids) == num_transactions, (
            f"Expected {num_transactions} transaction IDs, got {len(transaction_ids)}"
        )
        
        # Property: All transaction IDs must be unique
        assert len(set(transaction_ids)) == num_transactions, (
            "All transaction IDs must be unique"
        )
        
        # Property: Cost must persist across get_total_cost() calls
        cost_check_1 = mock_client.get_total_cost()
        cost_check_2 = mock_client.get_total_cost()
        assert cost_check_1 == cost_check_2, (
            "Total cost must remain consistent across multiple get_total_cost() calls"
        )
        
        # Property: Cost tracking must be accurate to the cent (0.0001 HBAR precision)
        # Verify no floating point precision errors
        assert abs(final_cost - expected_final_cost) < 1e-10, (
            "Cost tracking must maintain precision without floating point errors"
        )
        
        # Property: Cost must be retrievable via the base class method
        base_cost = mock_client.get_total_cost()
        assert base_cost == final_cost, (
            "Cost must be accessible through base class interface"
        )
        
        # Property: Resetting state must reset cost tracking
        mock_client.reset_mock_state()
        reset_cost = mock_client.get_total_cost()
        assert reset_cost == 0.0, (
            "After reset, total cost must return to zero"
        )
