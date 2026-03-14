"""
Marketplace Agent for TruthForge

This agent handles WooCommerce integration, order management,
and marketplace-related operations.
"""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class MarketplaceAgent(BaseAgent):
    """
    Marketplace Agent for WooCommerce integration
    
    Handles order fetching, status updates, and verification notes
    for WooCommerce stores.
    """
    
    def __init__(
        self,
        agent_id: str = "truthforge-market-001",
        agent_name: str = "Marketplace Agent",
        capabilities: List[str] = None,
        hcs_topic_id: str = "",
        hedera_client=None,
        hol_registry=None,
        mock_mode: bool = True
    ):
        """
        Initialize Marketplace Agent
        
        Args:
            agent_id: Unique agent identifier
            agent_name: Human-readable agent name
            capabilities: List of agent capabilities
            hcs_topic_id: Hedera Consensus Service topic ID
            hedera_client: Hedera client instance
            hol_registry: HOL registry instance
            mock_mode: Whether to use mock data
        """
        if capabilities is None:
            capabilities = [
                "woocommerce_integration",
                "order_management",
                "marketplace_operations",
                "discover_agents",
                "get_reputation"
            ]
        
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            capabilities=capabilities,
            hcs_topic_id=hcs_topic_id,
            hedera_client=hedera_client,
            hol_registry=hol_registry
        )
        
        self.mock_mode = mock_mode
        self.wc_client = self._init_woocommerce_client()
        
        logger.info(f"Marketplace Agent initialized (mock_mode={mock_mode})")
    
    def _init_woocommerce_client(self):
        """
        Initialize WooCommerce API client (only if live mode)
        
        Returns:
            WooCommerce API client or None if mock mode
        """
        if self.mock_mode:
            logger.info("Mock mode enabled, WooCommerce client not initialized")
            return None
        
        try:
            from woocommerce import API
            
            store_url = os.getenv('WOOCOMMERCE_STORE_URL')
            consumer_key = os.getenv('WOOCOMMERCE_CONSUMER_KEY')
            consumer_secret = os.getenv('WOOCOMMERCE_CONSUMER_SECRET')
            
            if not all([store_url, consumer_key, consumer_secret]):
                logger.warning("WooCommerce credentials not configured")
                return None
            
            client = API(
                url=store_url,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                version='wc/v3',
                timeout=30
            )
            
            logger.info(f"WooCommerce client initialized for {store_url}")
            return client
        
        except ImportError:
            logger.error("WooCommerce package not installed. Run: pip install woocommerce")
            return None
        except Exception as e:
            logger.error(f"Failed to init WooCommerce client: {e}")
            return None
    
    def get_order_details(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch order details from WooCommerce
        
        Args:
            order_id: WooCommerce order ID
            
        Returns:
            Order details dictionary or None if error
        """
        if self.mock_mode or not self.wc_client:
            return self._mock_order(order_id)
        
        try:
            response = self.wc_client.get(f"orders/{order_id}")
            order_data = response.json()
            logger.info(f"Fetched order {order_id} from WooCommerce")
            return order_data
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            return None
    
    def update_order_status(
        self,
        order_id: str,
        status: str,
        note: Optional[str] = None
    ) -> bool:
        """
        Update order status and optionally add a note
        
        Args:
            order_id: WooCommerce order ID
            status: New order status (processing, completed, etc.)
            note: Optional customer note
            
        Returns:
            bool: True if successful
        """
        if self.mock_mode or not self.wc_client:
            logger.info(f"Mock: Updated order {order_id} to {status}")
            return True
        
        data = {"status": status}
        if note:
            data["customer_note"] = note
        
        try:
            self.wc_client.put(f"orders/{order_id}", data)
            logger.info(f"Updated order {order_id} to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {e}")
            return False
    
    def add_verification_note(
        self,
        order_id: str,
        verification: Dict[str, Any],
        hcs_tx: str
    ) -> bool:
        """
        Add a customer note with verification proof
        
        Args:
            order_id: WooCommerce order ID
            verification: Verification result dictionary
            hcs_tx: Hedera transaction reference
            
        Returns:
            bool: True if successful
        """
        note = f"""🛡️ TruthForge Verification Complete

• Score: {verification.get('score', 'N/A')}%
• Compliance: {verification.get('compliance', 'Verified')}
• Hedera Proof: {hcs_tx}
• Timestamp: {datetime.now(timezone.utc).isoformat()}

Your shipment has been verified and recorded on the Hedera blockchain.
"""
        
        return self.update_order_status(order_id, 'processing', note)
    
    def _mock_order(self, order_id: str) -> Dict[str, Any]:
        """
        Mock order data for development
        
        Args:
            order_id: Order ID
            
        Returns:
            Mock order data
        """
        return {
            'id': order_id,
            'status': 'processing',
            'billing': {
                'first_name': 'John',
                'last_name': 'Doe',
                'address_1': '123 Test St',
                'city': 'Testville',
                'state': 'CA',
                'postcode': '90210',
                'country': 'US'
            },
            'shipping': {
                'first_name': 'John',
                'last_name': 'Doe',
                'address_1': '456 Port Rd',
                'city': 'Port City',
                'state': 'CA',
                'postcode': '90211',
                'country': 'US'
            },
            'line_items': [
                {
                    'name': 'Luxury Watch',
                    'quantity': 1,
                    'total': '2450.00'
                }
            ],
            'total': '2450.00',
            'currency': 'USD',
            'date_created': datetime.now(timezone.utc).isoformat()
        }
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process marketplace-related requests
        
        Args:
            request: Request dictionary
            
        Returns:
            Response dictionary
        """
        action = request.get('action')
        
        if action == 'get_order':
            order_id = request.get('order_id')
            order = self.get_order_details(order_id)
            return {
                'success': order is not None,
                'order': order,
                'agent_id': self.agent_id
            }
        
        elif action == 'update_order':
            order_id = request.get('order_id')
            status = request.get('status')
            note = request.get('note')
            success = self.update_order_status(order_id, status, note)
            return {
                'success': success,
                'order_id': order_id,
                'agent_id': self.agent_id
            }
        
        elif action == 'add_verification':
            order_id = request.get('order_id')
            verification = request.get('verification', {})
            hcs_tx = request.get('hcs_tx', 'N/A')
            success = self.add_verification_note(order_id, verification, hcs_tx)
            return {
                'success': success,
                'order_id': order_id,
                'agent_id': self.agent_id
            }
        
        else:
            return {
                'success': False,
                'error': f'Unknown action: {action}',
                'agent_id': self.agent_id
            }
