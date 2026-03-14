"""
TruthForge Hedera Client

This module provides blockchain integration with Hedera Consensus Service (HCS)
for immutable message timestamping and transaction management.
"""

import logging
import time
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from agents.config import Config
from agents.hcs10_message import HCS10Message
from agents.error_handling import (
    retry_blockchain_transaction,
    log_transaction_failure
)


logger = logging.getLogger(__name__)


class HederaClientBase(ABC):
    """
    Abstract base class for Hedera client implementations.
    
    Provides interface for blockchain operations including authentication,
    message submission, and transaction receipt retrieval.
    """
    
    def __init__(self, config: Config):
        """
        Initialize Hedera client with configuration.
        
        Args:
            config: TruthForge configuration object
        """
        self.config = config
        self.authenticated = False
        self.total_cost_hbar = 0.0
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with Hedera network.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    def submit_message(self, message: HCS10Message) -> str:
        """
        Submit a message to HCS topic.
        
        Args:
            message: HCS10Message to submit
            
        Returns:
            str: Transaction ID
            
        Raises:
            ValueError: If message is invalid
            RuntimeError: If submission fails
        """
        pass
    
    @abstractmethod
    def get_transaction_receipt(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get transaction receipt from Hedera network.
        
        Args:
            transaction_id: Transaction ID to query
            
        Returns:
            Dict containing receipt data with keys:
                - transaction_id: str
                - consensus_timestamp: str (ISO 8601)
                - status: str
                - topic_sequence_number: int (optional)
                
        Raises:
            ValueError: If transaction_id is invalid
            RuntimeError: If receipt retrieval fails
        """
        pass
    
    @abstractmethod
    def check_balance(self) -> float:
        """
        Check account balance in HBAR.
        
        Returns:
            float: Account balance in HBAR
            
        Raises:
            RuntimeError: If balance check fails
        """
        pass
    
    def get_total_cost(self) -> float:
        """
        Get total transaction costs incurred.
        
        Returns:
            float: Total cost in HBAR
        """
        return self.total_cost_hbar


class HederaClient(HederaClientBase):
    """
    Production Hedera client for real blockchain operations.
    
    Integrates with Hedera SDK to submit messages to HCS topics,
    retrieve transaction receipts, and manage account operations.
    """
    
    def __init__(self, config: Config):
        """
        Initialize production Hedera client.
        
        Args:
            config: TruthForge configuration object
            
        Raises:
            ValueError: If required credentials are missing
        """
        super().__init__(config)
        
        if not config.hedera_account_id:
            raise ValueError("HEDERA_ACCOUNT_ID is required for production mode")
        
        if not config.hedera_private_key:
            raise ValueError("HEDERA_PRIVATE_KEY is required for production mode")
        
        if not config.hcs_topic_id:
            raise ValueError("HCS_TOPIC_ID is required for production mode")
        
        self.account_id = config.hedera_account_id
        self.private_key = config.hedera_private_key
        self.network = config.hedera_network
        self.topic_id = config.hcs_topic_id
        
        # Hedera SDK client (will be initialized in authenticate)
        self.client = None
        
        logger.info(
            f"Initialized HederaClient for {self.network} "
            f"(account: {self.account_id}, topic: {self.topic_id})"
        )
    
    def authenticate(self) -> bool:
        """
        Authenticate with Hedera network using account credentials.
        
        Initializes the Hedera SDK client and validates credentials.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            RuntimeError: If authentication fails
        """
        try:
            # Import Hedera SDK (only when needed for production)
            try:
                from hedera import Client, AccountId, PrivateKey
            except ImportError:
                raise RuntimeError(
                    "hedera-sdk-python is required for production mode. "
                    "Install with: pip install hedera-sdk-python"
                )
            
            # Create client for specified network
            if self.network == "testnet":
                self.client = Client.forTestnet()
            elif self.network == "mainnet":
                self.client = Client.forMainnet()
            else:
                raise ValueError(f"Invalid network: {self.network}")
            
            # Set operator (account that pays for transactions)
            account_id = AccountId.fromString(self.account_id)
            private_key = PrivateKey.fromString(self.private_key)
            self.client.setOperator(account_id, private_key)
            
            self.authenticated = True
            logger.info(f"Successfully authenticated with Hedera {self.network}")
            
            return True
            
        except Exception as e:
            logger.error(f"Hedera authentication failed: {e}")
            raise RuntimeError(f"Failed to authenticate with Hedera: {e}")
    
    def submit_message(self, message: HCS10Message) -> str:
        """
        Submit a message to HCS topic.
        
        Validates balance before submission and tracks transaction costs.
        Uses retry logic with exponential backoff for production mode.
        
        Args:
            message: HCS10Message to submit
            
        Returns:
            str: Transaction ID (format: 0.0.xxxxx@timestamp.nanos)
            
        Raises:
            ValueError: If message is invalid
            RuntimeError: If submission fails or insufficient balance
        
        Requirements: 12.3, 16.4 - Transaction retry and failure logging
        """
        if not self.authenticated:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")
        
        if not message:
            raise ValueError("Message cannot be None")
        
        # Use retry decorator for production mode
        production_mode = not self.config.mock_mode
        
        @retry_blockchain_transaction(
            max_attempts=self.config.max_retries,
            initial_delay=2.0,
            production_mode=production_mode
        )
        def _submit_transaction():
            """Inner function that performs the actual transaction submission."""
            try:
                # Import Hedera SDK components
                from hedera import TopicMessageSubmitTransaction, TopicId, Hbar
                
                # Check balance before transaction
                balance = self.check_balance()
                estimated_cost = 0.0001  # Estimated cost in HBAR for HCS message
                
                if balance < estimated_cost:
                    raise RuntimeError(
                        f"Insufficient balance: {balance} HBAR. "
                        f"Need at least {estimated_cost} HBAR for transaction."
                    )
                
                # Serialize message to HCS format
                message_bytes = message.to_hcs_format()
                
                # Create and execute transaction
                topic_id = TopicId.fromString(self.topic_id)
                transaction = (
                    TopicMessageSubmitTransaction()
                    .setTopicId(topic_id)
                    .setMessage(message_bytes)
                )
                
                # Execute transaction
                response = transaction.execute(self.client)
                
                # Get receipt to confirm success
                receipt = response.getReceipt(self.client)
                
                # Get transaction ID
                transaction_id = str(response.transactionId)
                
                # Track cost (approximate)
                cost = 0.0001  # Typical HCS message cost
                self.total_cost_hbar += cost
                
                logger.info(
                    f"Successfully submitted message to HCS topic {self.topic_id}. "
                    f"Transaction ID: {transaction_id}, Cost: {cost} HBAR"
                )
                
                return transaction_id
                
            except Exception as e:
                # Log transaction failure with details
                transaction_hash = getattr(e, 'transaction_id', None)
                log_transaction_failure(
                    transaction_hash=transaction_hash,
                    error_message=str(e),
                    account_id=self.account_id,
                    additional_details={
                        "topic_id": self.topic_id,
                        "network": self.network,
                        "message_type": message.message_type.value if hasattr(message, 'message_type') else "unknown"
                    }
                )
                raise RuntimeError(f"Failed to submit message to HCS: {e}")
        
        # Execute with retry logic
        return _submit_transaction()
    
    def get_transaction_receipt(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get transaction receipt from Hedera network.
        
        Args:
            transaction_id: Transaction ID to query
            
        Returns:
            Dict containing receipt data
            
        Raises:
            ValueError: If transaction_id is invalid
            RuntimeError: If receipt retrieval fails
        """
        if not self.authenticated:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")
        
        if not transaction_id:
            raise ValueError("transaction_id cannot be empty")
        
        try:
            from hedera import TransactionId, TransactionReceiptQuery
            
            # Parse transaction ID
            tx_id = TransactionId.fromString(transaction_id)
            
            # Query receipt
            query = TransactionReceiptQuery().setTransactionId(tx_id)
            receipt = query.execute(self.client)
            
            # Extract consensus timestamp
            consensus_timestamp = receipt.consensusTimestamp
            timestamp_iso = datetime.fromtimestamp(
                consensus_timestamp.seconds,
                tz=timezone.utc
            ).isoformat().replace('+00:00', 'Z')
            
            receipt_data = {
                "transaction_id": transaction_id,
                "consensus_timestamp": timestamp_iso,
                "status": str(receipt.status),
                "topic_sequence_number": getattr(receipt, 'topicSequenceNumber', None)
            }
            
            logger.info(f"Retrieved receipt for transaction {transaction_id}")
            
            return receipt_data
            
        except Exception as e:
            logger.error(f"Failed to get transaction receipt: {e}")
            raise RuntimeError(f"Failed to retrieve transaction receipt: {e}")
    
    def check_balance(self) -> float:
        """
        Check account balance in HBAR.
        
        Returns:
            float: Account balance in HBAR
            
        Raises:
            RuntimeError: If balance check fails
        """
        if not self.authenticated:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")
        
        try:
            from hedera import AccountBalanceQuery, AccountId
            
            account_id = AccountId.fromString(self.account_id)
            query = AccountBalanceQuery().setAccountId(account_id)
            balance = query.execute(self.client)
            
            # Convert to HBAR (balance is in tinybars)
            balance_hbar = balance.hbars.toTinybars() / 100_000_000
            
            logger.debug(f"Account balance: {balance_hbar} HBAR")
            
            return balance_hbar
            
        except Exception as e:
            logger.error(f"Failed to check balance: {e}")
            raise RuntimeError(f"Failed to check account balance: {e}")



class MockHederaClient(HederaClientBase):
    """
    Mock Hedera client for development and testing.
    
    Simulates blockchain operations without real transactions or costs.
    Useful for development, testing, and demonstrations.
    """
    
    def __init__(self, config: Config):
        """
        Initialize mock Hedera client.
        
        Args:
            config: TruthForge configuration object
        """
        super().__init__(config)
        
        self.mock_balance = 1000.0  # Mock balance in HBAR
        self.mock_transactions = {}  # Store mock transaction receipts
        self.transaction_counter = 0
        
        logger.info("Initialized MockHederaClient (development mode)")
    
    def authenticate(self) -> bool:
        """
        Mock authentication (always succeeds).
        
        Returns:
            bool: Always True
        """
        self.authenticated = True
        logger.info("Mock authentication successful")
        return True
    
    def submit_message(self, message: HCS10Message) -> str:
        """
        Mock message submission to HCS topic.
        
        Generates fake transaction IDs and simulates costs without
        actual blockchain transactions.
        
        Args:
            message: HCS10Message to submit
            
        Returns:
            str: Mock transaction ID (format: 0.0.12345@timestamp.nanos)
            
        Raises:
            ValueError: If message is invalid
        """
        if not message:
            raise ValueError("Message cannot be None")
        
        # Generate mock transaction ID
        self.transaction_counter += 1
        timestamp_seconds = int(time.time())
        timestamp_nanos = int((time.time() % 1) * 1_000_000_000)
        
        # Use config topic ID if available, otherwise use mock
        topic_id = self.config.hcs_topic_id or "0.0.12345"
        transaction_id = f"{topic_id}@{timestamp_seconds}.{timestamp_nanos}"
        
        # Simulate transaction cost
        mock_cost = 0.0001  # Mock cost in HBAR
        self.total_cost_hbar += mock_cost
        self.mock_balance -= mock_cost
        
        # Store mock receipt
        consensus_timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        self.mock_transactions[transaction_id] = {
            "transaction_id": transaction_id,
            "consensus_timestamp": consensus_timestamp,
            "status": "SUCCESS",
            "topic_sequence_number": self.transaction_counter,
            "message": message.to_hcs_format()
        }
        
        logger.info(
            f"Mock message submitted. Transaction ID: {transaction_id}, "
            f"Mock cost: {mock_cost} HBAR"
        )
        
        return transaction_id
    
    def get_transaction_receipt(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get mock transaction receipt.
        
        Returns simulated receipt data with consensus timestamps.
        
        Args:
            transaction_id: Transaction ID to query
            
        Returns:
            Dict containing mock receipt data
            
        Raises:
            ValueError: If transaction_id is invalid or not found
        """
        if not transaction_id:
            raise ValueError("transaction_id cannot be empty")
        
        # Check if transaction exists in mock storage
        if transaction_id in self.mock_transactions:
            receipt = self.mock_transactions[transaction_id].copy()
            # Remove message data from receipt
            receipt.pop("message", None)
            
            logger.info(f"Retrieved mock receipt for transaction {transaction_id}")
            return receipt
        
        # If not found, generate a mock receipt on the fly
        logger.warning(
            f"Transaction {transaction_id} not found in mock storage. "
            "Generating mock receipt."
        )
        
        return {
            "transaction_id": transaction_id,
            "consensus_timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "status": "SUCCESS",
            "topic_sequence_number": self.transaction_counter
        }
    
    def check_balance(self) -> float:
        """
        Check mock account balance.
        
        Returns:
            float: Mock account balance in HBAR
        """
        logger.debug(f"Mock account balance: {self.mock_balance} HBAR")
        return self.mock_balance
    
    def reset_mock_state(self) -> None:
        """
        Reset mock client state.
        
        Useful for testing to clear transaction history and reset balance.
        """
        self.mock_balance = 1000.0
        self.mock_transactions = {}
        self.transaction_counter = 0
        self.total_cost_hbar = 0.0
        logger.info("Mock client state reset")
    
    def get_mock_transactions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all mock transactions for testing/debugging.
        
        Returns:
            Dict mapping transaction IDs to receipt data
        """
        return self.mock_transactions.copy()


def create_hedera_client(config: Config) -> HederaClientBase:
    """
    Factory function to create appropriate Hedera client based on configuration.
    
    Args:
        config: TruthForge configuration object
        
    Returns:
        HederaClientBase: HederaClient for production, MockHederaClient for mock mode
    """
    if config.mock_mode:
        logger.info("Creating MockHederaClient (mock mode enabled)")
        return MockHederaClient(config)
    else:
        logger.info("Creating HederaClient (production mode)")
        return HederaClient(config)
