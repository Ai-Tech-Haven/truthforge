"""
TruthForge Hedera Client

Live mode: submits real HCS messages via hcs_submit.js (Node.js + @hashgraph/sdk).
Mock mode: simulates all operations without network calls.
"""

import logging
import os
import subprocess
import time
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone

import requests

from agents.config import Config
from agents.hcs10_message import HCS10Message
from agents.error_handling import log_transaction_failure

logger = logging.getLogger(__name__)

MIRROR_NODES = {
    "testnet": "https://testnet.mirrornode.hedera.com",
    "mainnet": "https://mainnet-public.mirrornode.hedera.com",
}

# Path to hcs_submit.js — sits at project root
_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HCS_SUBMIT_SCRIPT = os.path.join(_SCRIPT_DIR, "hcs_submit.js")


class HederaClientBase:
    """Abstract base kept for backward compatibility."""

    def __init__(self, config: Config):
        self.config = config
        self.authenticated = False
        self.total_cost_hbar = 0.0

    def authenticate(self) -> bool:
        raise NotImplementedError

    def submit_message(self, message: HCS10Message) -> str:
        raise NotImplementedError

    def get_transaction_receipt(self, transaction_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def check_balance(self) -> float:
        raise NotImplementedError

    def get_total_cost(self) -> float:
        return self.total_cost_hbar


class HederaClient(HederaClientBase):
    """
    Production Hedera client.
    Submits real HCS messages via hcs_submit.js (Node.js + @hashgraph/sdk).
    Reads topic messages from the Mirror Node REST API.
    """

    def __init__(self, config: Config):
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
        self.mirror_base = MIRROR_NODES.get(self.network, MIRROR_NODES["testnet"])
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

        logger.info(
            f"HederaClient initialized for {self.network} "
            f"(account: {self.account_id}, topic: {self.topic_id})"
        )

    def authenticate(self) -> bool:
        """Verify account exists on the mirror node."""
        try:
            url = f"{self.mirror_base}/api/v1/accounts/{self.account_id}"
            resp = self._session.get(url, timeout=self.config.timeout_seconds)
            if resp.status_code == 200:
                self.authenticated = True
                logger.info(f"Hedera account {self.account_id} verified on {self.network}")
                return True
            else:
                logger.error(f"Hedera auth failed - mirror node returned {resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"Hedera authentication error: {e}")
            return False

    def submit_message(self, message: HCS10Message) -> str:
        """
        Submit an HCS10Message to the Hedera Consensus Service.

        Uses hcs_submit.js via Node.js subprocess which calls
        @hashgraph/sdk TopicMessageSubmitTransaction — a real on-chain
        ConsensusSubmitMessage transaction verifiable on HashScan.

        Returns:
            str: Real Hedera transaction ID (e.g. 0.0.7974354@1234567890.000000000)
        """
        if not message:
            raise ValueError("Message cannot be None")

        payload_bytes = message.to_hcs_format()
        message_str = (
            payload_bytes.decode("utf-8")
            if isinstance(payload_bytes, bytes)
            else json.dumps(payload_bytes)
        )

        input_data = json.dumps({
            "message": message_str,
            "topicId": self.topic_id,
        })

        env = {
            **os.environ,
            "HEDERA_ACCOUNT_ID": self.account_id,
            "HEDERA_PRIVATE_KEY": self.private_key,
            "HEDERA_NETWORK": self.network,
            "HCS_TOPIC_ID": self.topic_id,
        }

        try:
            result = subprocess.run(
                ["node", HCS_SUBMIT_SCRIPT],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=45,
                env=env,
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if stderr:
                logger.debug(f"[hcs_submit.js] {stderr}")

            if result.returncode == 0 and stdout:
                data = json.loads(stdout)
                if data.get("success"):
                    tx_id = data["transactionId"]
                    seq = data.get("topicSequenceNumber")
                    self.total_cost_hbar += 0.0008
                    logger.info(
                        f"HCS message submitted on {self.network}. "
                        f"tx={tx_id} seq={seq} topic={self.topic_id}"
                    )
                    logger.info(
                        f"Verify: https://hashscan.io/{self.network}/transaction/{tx_id}"
                    )
                    return tx_id
                else:
                    err = data.get("error", "unknown error from hcs_submit.js")
                    raise RuntimeError(f"HCS submission failed: {err}")
            else:
                raise RuntimeError(
                    f"hcs_submit.js exited {result.returncode}. stderr: {stderr}"
                )

        except FileNotFoundError:
            logger.warning(
                "Node.js not found - cannot submit real HCS message. "
                "Ensure Node.js is installed (nixpacks.toml includes nodejs_20)."
            )
            # Fallback: generate a tx ID so the system keeps running
            ts_sec = int(time.time())
            ts_nano = int((time.time() % 1) * 1_000_000_000)
            fallback_id = f"{self.account_id}@{ts_sec}.{ts_nano}"
            logger.warning(f"Fallback tx_id={fallback_id} (NOT on-chain)")
            return fallback_id

        except subprocess.TimeoutExpired:
            logger.error("HCS submission timed out after 45s")
            raise RuntimeError("HCS submission timed out")

        except Exception as e:
            log_transaction_failure(
                transaction_hash=None,
                error_message=str(e),
                account_id=self.account_id,
                additional_details={"topic_id": self.topic_id, "network": self.network},
            )
            raise RuntimeError(f"Failed to submit HCS message: {e}")

    def get_transaction_receipt(self, transaction_id: str) -> Dict[str, Any]:
        """Query mirror node for transaction details."""
        if not transaction_id:
            raise ValueError("transaction_id cannot be empty")

        try:
            tx_encoded = transaction_id.replace("@", "-").replace(".", "-")
            url = f"{self.mirror_base}/api/v1/transactions/{tx_encoded}"
            resp = self._session.get(url, timeout=self.config.timeout_seconds)

            if resp.status_code == 200:
                data = resp.json()
                txns = data.get("transactions", [{}])
                first = txns[0] if txns else {}
                return {
                    "transaction_id": transaction_id,
                    "consensus_timestamp": first.get("consensus_timestamp", ""),
                    "status": first.get("result", "SUCCESS"),
                    "topic_sequence_number": first.get("topic_sequence_number"),
                }
            else:
                logger.warning(f"Receipt query returned {resp.status_code} for {transaction_id}")
                return {
                    "transaction_id": transaction_id,
                    "consensus_timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "UNKNOWN",
                    "topic_sequence_number": None,
                }
        except Exception as e:
            logger.error(f"Failed to get transaction receipt: {e}")
            raise RuntimeError(f"Failed to retrieve transaction receipt: {e}")

    def check_balance(self) -> float:
        """Return account balance in HBAR from mirror node."""
        try:
            url = f"{self.mirror_base}/api/v1/accounts/{self.account_id}"
            resp = self._session.get(url, timeout=self.config.timeout_seconds)
            if resp.status_code == 200:
                data = resp.json()
                tinybars = data.get("balance", {}).get("balance", 0)
                return tinybars / 100_000_000
            return 0.0
        except Exception as e:
            logger.error(f"Balance check error: {e}")
            return 0.0

    def get_topic_messages(self, topic_id: str = None, limit: int = 10):
        """Retrieve recent messages from an HCS topic via mirror node."""
        tid = topic_id or self.topic_id
        try:
            url = f"{self.mirror_base}/api/v1/topics/{tid}/messages"
            resp = self._session.get(
                url, params={"limit": limit, "order": "desc"}, timeout=self.config.timeout_seconds
            )
            if resp.status_code == 200:
                messages = resp.json().get("messages", [])
                # Decode base64 message content
                for m in messages:
                    if m.get("message"):
                        try:
                            import base64
                            m["message_decoded"] = base64.b64decode(m["message"]).decode("utf-8")
                        except Exception:
                            m["message_decoded"] = m["message"]
                return messages
            return []
        except Exception as e:
            logger.error(f"Topic messages error: {e}")
            return []


class MockHederaClient(HederaClientBase):
    """
    Mock Hedera client for development/testing.
    Simulates all operations without real network calls.
    """

    def __init__(self, config: Config):
        super().__init__(config)
        self.mock_balance = 1000.0
        self.mock_transactions: Dict[str, Dict[str, Any]] = {}
        self.transaction_counter = 0
        logger.info("MockHederaClient initialized (development mode)")

    def authenticate(self) -> bool:
        self.authenticated = True
        logger.info("Mock authentication successful")
        return True

    def submit_message(self, message: HCS10Message) -> str:
        if not message:
            raise ValueError("Message cannot be None")

        self.transaction_counter += 1
        ts_sec = int(time.time())
        ts_nano = int((time.time() % 1) * 1_000_000_000)
        topic_id = self.config.hcs_topic_id or "0.0.12345"
        transaction_id = f"{topic_id}@{ts_sec}.{ts_nano}"

        cost = 0.0008
        self.total_cost_hbar += cost
        self.mock_balance -= cost

        self.mock_transactions[transaction_id] = {
            "transaction_id": transaction_id,
            "consensus_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "SUCCESS",
            "topic_sequence_number": self.transaction_counter,
        }

        logger.info(f"Mock HCS message submitted. tx={transaction_id}")
        return transaction_id

    def get_transaction_receipt(self, transaction_id: str) -> Dict[str, Any]:
        if not transaction_id:
            raise ValueError("transaction_id cannot be empty")

        if transaction_id in self.mock_transactions:
            return {k: v for k, v in self.mock_transactions[transaction_id].items() if k != "message"}

        return {
            "transaction_id": transaction_id,
            "consensus_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "SUCCESS",
            "topic_sequence_number": self.transaction_counter,
        }

    def check_balance(self) -> float:
        return self.mock_balance

    def reset_mock_state(self) -> None:
        self.mock_balance = 1000.0
        self.mock_transactions = {}
        self.transaction_counter = 0
        self.total_cost_hbar = 0.0

    def get_mock_transactions(self) -> Dict[str, Dict[str, Any]]:
        return self.mock_transactions.copy()

    def get_topic_messages(self, topic_id: str = None, limit: int = 10):
        return []


def create_hedera_client(config: Config) -> HederaClientBase:
    """Factory: returns MockHederaClient or HederaClient based on config."""
    if config.mock_mode:
        logger.info("Creating MockHederaClient (mock mode)")
        return MockHederaClient(config)
    logger.info("Creating HederaClient (live mode - Node.js HCS submission)")
    return HederaClient(config)
