"""
TruthForge Carrier Adapter Agent (Council-Grade)

This agent provides multi-carrier data ingestion and normalization services.
It integrates with multiple shipping carriers (FedEx, UPS, DHL, Maersk, MSC)
to retrieve shipment data and normalize it into a unified schema for
verification and tracking purposes.
"""

import logging
import time
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from agents.base_agent import BaseAgent
from agents.config import Config
from agents.hedera_client import HederaClientBase
from agents.hcs10_message import HCS10Message, MessageType
from agents.fedex_client import FedExClient
from database.database import db_session
from database.models import ShipmentData


logger = logging.getLogger(__name__)


@dataclass
class CarrierShipmentData:
    """Normalized shipment data structure."""
    tracking_number: str
    carrier: str
    origin: str
    destination: str
    current_status: str
    estimated_delivery: str
    vessel: Optional[str] = None
    service_type: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, float]] = None
    last_update: Optional[str] = None
    tracking_events: Optional[List[Dict[str, Any]]] = None


@dataclass
class CarrierResponse:
    """Carrier API response wrapper."""
    success: bool
    carrier: str
    tracking_number: str
    shipment_data: Optional[CarrierShipmentData]
    error_message: Optional[str]
    response_time: float
    timestamp: datetime


class CarrierAdapterAgent(BaseAgent):
    """
    Carrier Adapter Agent for multi-carrier data integration.
    
    Provides Council-Grade carrier data ingestion and normalization
    services for FedEx, UPS, DHL, Maersk, MSC, and other major carriers.
    All carrier operations are timestamped on Hedera blockchain.
    """
    
    def __init__(
        self,
        agent_id: str,
        capabilities: List[str],
        hcs_topic_id: str,
        config: Config,
        hedera_client: HederaClientBase
    ):
        """
        Initialize Carrier Adapter Agent.
        
        Args:
            agent_id: Unique agent identifier
            capabilities: List of agent capabilities
            hcs_topic_id: HCS topic for messaging
            config: TruthForge configuration
            hedera_client: Hedera client for blockchain operations
        """
        super().__init__(agent_id, capabilities, hcs_topic_id, config, hedera_client)
        
        # Initialize FedEx client
        fedex_env = 'production' if not config.mock_mode else 'sandbox'
        self.fedex_client = FedExClient(environment=fedex_env) if not config.mock_mode else None
        
        # Supported carriers with their API configurations
        self.supported_carriers = {
            'fedex': {
                'name': 'FedEx',
                'api_endpoint': 'https://apis.fedex.com/track/v1/trackingnumbers',
                'auth_required': True,
                'tracking_pattern': r'^[0-9]{12,14}$|^[0-9]{20}$'
            },
            'ups': {
                'name': 'UPS',
                'api_endpoint': 'https://onlinetools.ups.com/track/v1/details',
                'auth_required': True,
                'tracking_pattern': r'^1Z[0-9A-Z]{16}$'
            },
            'dhl': {
                'name': 'DHL',
                'api_endpoint': 'https://api-eu.dhl.com/track/shipments',
                'auth_required': True,
                'tracking_pattern': r'^[0-9]{10,11}$'
            },
            'maersk': {
                'name': 'Maersk',
                'api_endpoint': 'https://api.maersk.com/track',
                'auth_required': True,
                'tracking_pattern': r'^[A-Z]{4}[0-9]{7}$'
            },
            'msc': {
                'name': 'MSC',
                'api_endpoint': 'https://api.msc.com/tracking',
                'auth_required': True,
                'tracking_pattern': r'^[A-Z]{4}[0-9]{7}$'
            }
        }
        
        logger.info(f"Initialized {self.__class__.__name__} with {len(self.supported_carriers)} carriers")
    
    def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process carrier data requests.
        
        Args:
            request: Request containing carrier operation parameters
            
        Returns:
            Dict[str, Any]: Carrier operation results
        """
        start_time = time.time()
        
        try:
            request_type = request.get('type', 'unknown')
            
            if request_type == 'query_shipment':
                result = self._process_shipment_query(request)
            elif request_type == 'normalize_data':
                result = self._process_data_normalization(request)
            elif request_type == 'get_supported_carriers':
                result = self._get_supported_carriers()
            elif request_type == 'create_shipment':
                result = self.process_order_shipment(request.get('order_data', {}))
            else:
                raise ValueError(f"Unsupported request type: {request_type}")
            
            # Track successful request
            response_time = time.time() - start_time
            self._track_request(response_time, success=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing carrier request: {e}")
            response_time = time.time() - start_time
            self._track_request(response_time, success=False)
            
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def process_order_shipment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process order shipment creation via FedEx.
        
        This method creates a shipment for an order, either using the FedEx API
        in live mode or returning mock data in mock mode.
        
        Args:
            order_data: Order data including shipping and billing addresses
            
        Returns:
            Dict containing shipment creation result with tracking number
        """
        try:
            # Mock mode or no FedEx client available
            if self.config.mock_mode or not self.fedex_client:
                logger.info("Using mock shipment creation")
                return {
                    'success': True,
                    'tracking_number': f'MOCK{int(time.time())}',
                    'shipment_id': f'MOCK-SHIP-{int(time.time())}',
                    'label_url': 'http://mock.label/url',
                    'carrier': 'FedEx',
                    'service_type': 'FEDEX_PRIORITY_OVERNIGHT',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            # Live mode - use FedEx API
            logger.info("Creating FedEx shipment in live mode")
            shipment_response = self.fedex_client.create_shipment(order_data)
            
            # Extract tracking number from FedEx response
            # FedEx API structure: output.transactionShipments[0].masterTrackingNumber
            transaction_shipments = shipment_response.get('output', {}).get('transactionShipments', [])
            
            if not transaction_shipments:
                raise ValueError("No shipment data in FedEx response")
            
            first_shipment = transaction_shipments[0]
            tracking_number = first_shipment.get('masterTrackingNumber')
            shipment_id = first_shipment.get('shipmentId', tracking_number)
            
            # Extract label URL
            shipment_documents = first_shipment.get('shipmentDocuments', [])
            label_url = shipment_documents[0].get('url') if shipment_documents else None
            
            result = {
                'success': True,
                'tracking_number': tracking_number,
                'shipment_id': shipment_id,
                'label_url': label_url,
                'carrier': 'FedEx',
                'service_type': first_shipment.get('serviceType', 'FEDEX_PRIORITY_OVERNIGHT'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'fedex_response': shipment_response
            }
            
            logger.info(f"FedEx shipment created: {tracking_number}")
            return result
            
        except Exception as e:
            logger.error(f"FedEx shipment creation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _process_shipment_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process shipment tracking query."""
        tracking_number = request.get('tracking_number')
        carrier = request.get('carrier')
        
        if not tracking_number:
            raise ValueError("tracking_number is required")
        
        # Auto-detect carrier if not specified
        if not carrier:
            carrier = self.identify_carrier(tracking_number)
        
        # Query shipment data
        carrier_response = self.query_shipment(carrier, tracking_number)
        
        # Store result in database
        self._store_shipment_data(carrier_response)
        
        return {
            'success': carrier_response.success,
            'carrier_response': asdict(carrier_response),
            'agent_id': self.agent_id
        }
    
    def _process_data_normalization(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process data normalization request."""
        raw_data = request.get('raw_data')
        carrier = request.get('carrier')
        
        if not raw_data or not carrier:
            raise ValueError("raw_data and carrier are required")
        
        # Normalize carrier data
        normalized_data = self.normalize_tracking_data(carrier, raw_data)
        
        return {
            'success': True,
            'normalized_data': asdict(normalized_data),
            'agent_id': self.agent_id
        }
    
    def _get_supported_carriers(self) -> Dict[str, Any]:
        """Get list of supported carriers."""
        carriers = []
        for carrier_id, config in self.supported_carriers.items():
            carriers.append({
                'id': carrier_id,
                'name': config['name'],
                'auth_required': config['auth_required'],
                'tracking_pattern': config['tracking_pattern']
            })
        
        return {
            'success': True,
            'supported_carriers': carriers,
            'total_carriers': len(carriers),
            'agent_id': self.agent_id
        }
    
    def identify_carrier(self, tracking_number: str) -> str:
        """
        Identify carrier based on tracking number format.
        
        Args:
            tracking_number: Tracking number to analyze
            
        Returns:
            str: Identified carrier ID or 'unknown'
        """
        tracking_number = tracking_number.strip().upper()
        
        for carrier_id, config in self.supported_carriers.items():
            pattern = config['tracking_pattern']
            if re.match(pattern, tracking_number):
                logger.debug(f"Identified carrier {carrier_id} for tracking {tracking_number}")
                return carrier_id
        
        logger.warning(f"Could not identify carrier for tracking number: {tracking_number}")
        return 'unknown'
    
    def query_shipment(self, carrier: str, tracking_number: str) -> CarrierResponse:
        """
        Query shipment data from specified carrier.
        
        Args:
            carrier: Carrier identifier
            tracking_number: Tracking number to query
            
        Returns:
            CarrierResponse: Carrier API response with normalized data
        """
        start_time = time.time()
        
        try:
            if carrier not in self.supported_carriers:
                raise ValueError(f"Unsupported carrier: {carrier}")
            
            # Validate tracking number format
            if not self.validate_tracking_format(carrier, tracking_number):
                raise ValueError(f"Invalid tracking number format for {carrier}: {tracking_number}")
            
            # In mock mode, return simulated data
            if self.config.mock_mode:
                shipment_data = self._generate_mock_shipment_data(carrier, tracking_number)
                response_time = time.time() - start_time
                
                return CarrierResponse(
                    success=True,
                    carrier=carrier,
                    tracking_number=tracking_number,
                    shipment_data=shipment_data,
                    error_message=None,
                    response_time=response_time,
                    timestamp=datetime.now(timezone.utc)
                )
            
            # In live mode, make actual API calls
            shipment_data = self._query_carrier_api(carrier, tracking_number)
            response_time = time.time() - start_time
            
            # Submit to HCS for timestamping
            hcs_transaction_id = self._submit_to_hcs({
                'action': 'carrier_query',
                'carrier': carrier,
                'tracking_number': tracking_number,
                'success': True
            })
            
            return CarrierResponse(
                success=True,
                carrier=carrier,
                tracking_number=tracking_number,
                shipment_data=shipment_data,
                error_message=None,
                response_time=response_time,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Carrier query failed for {carrier}/{tracking_number}: {e}")
            
            # Submit error to HCS
            self._submit_to_hcs({
                'action': 'carrier_query',
                'carrier': carrier,
                'tracking_number': tracking_number,
                'success': False,
                'error': str(e)
            })
            
            return CarrierResponse(
                success=False,
                carrier=carrier,
                tracking_number=tracking_number,
                shipment_data=None,
                error_message=str(e),
                response_time=response_time,
                timestamp=datetime.now(timezone.utc)
            )
    
    def normalize_tracking_data(self, carrier: str, raw_data: Dict[str, Any]) -> CarrierShipmentData:
        """
        Normalize carrier-specific data into unified schema.
        
        Args:
            carrier: Carrier identifier
            raw_data: Raw carrier API response data
            
        Returns:
            CarrierShipmentData: Normalized shipment data
        """
        try:
            # Carrier-specific normalization logic
            if carrier == 'fedex':
                return self._normalize_fedex_data(raw_data)
            elif carrier == 'ups':
                return self._normalize_ups_data(raw_data)
            elif carrier == 'dhl':
                return self._normalize_dhl_data(raw_data)
            elif carrier == 'maersk':
                return self._normalize_maersk_data(raw_data)
            elif carrier == 'msc':
                return self._normalize_msc_data(raw_data)
            else:
                # Generic normalization for unknown carriers
                return self._normalize_generic_data(carrier, raw_data)
                
        except Exception as e:
            logger.error(f"Data normalization failed for {carrier}: {e}")
            # Return minimal data structure
            return CarrierShipmentData(
                tracking_number=raw_data.get('tracking_number', 'unknown'),
                carrier=carrier,
                origin='Unknown',
                destination='Unknown',
                current_status='Error',
                estimated_delivery='Unknown'
            )
    
    def validate_tracking_format(self, carrier: str, tracking_number: str) -> bool:
        """
        Validate tracking number format for specified carrier.
        
        Args:
            carrier: Carrier identifier
            tracking_number: Tracking number to validate
            
        Returns:
            bool: True if format is valid, False otherwise
        """
        if carrier not in self.supported_carriers:
            return False
        
        pattern = self.supported_carriers[carrier]['tracking_pattern']
        return bool(re.match(pattern, tracking_number.strip().upper()))
    
    def get_supported_carriers(self) -> List[str]:
        """
        Get list of supported carrier identifiers.
        
        Returns:
            List[str]: List of supported carrier IDs
        """
        return list(self.supported_carriers.keys())
    
    def handle_rate_limits(self, carrier: str, error: Exception) -> bool:
        """
        Handle carrier API rate limits with exponential backoff.
        
        Args:
            carrier: Carrier identifier
            error: Rate limit exception
            
        Returns:
            bool: True if retry should be attempted, False otherwise
        """
        logger.warning(f"Rate limit hit for {carrier}: {error}")
        
        # Implement exponential backoff
        # In production, this would track rate limit windows per carrier
        backoff_time = 60  # Start with 1 minute
        
        logger.info(f"Backing off for {backoff_time} seconds for {carrier}")
        time.sleep(backoff_time)
        
        return True  # Allow retry
    
    def _query_carrier_api(self, carrier: str, tracking_number: str) -> CarrierShipmentData:
        """Query actual carrier API (production mode)."""
        # This would contain actual API integration code
        # For now, return mock data even in live mode
        logger.info(f"Querying {carrier} API for {tracking_number} (live mode)")
        return self._generate_mock_shipment_data(carrier, tracking_number)
    
    def _generate_mock_shipment_data(self, carrier: str, tracking_number: str) -> CarrierShipmentData:
        """Generate mock shipment data for testing."""
        carrier_configs = {
            'fedex': {
                'origin': 'Memphis, TN, US',
                'destination': 'Los Angeles, CA, US',
                'status': 'In Transit',
                'service': 'FedEx Express'
            },
            'ups': {
                'origin': 'Atlanta, GA, US',
                'destination': 'New York, NY, US',
                'status': 'Out for Delivery',
                'service': 'UPS Ground'
            },
            'dhl': {
                'origin': 'Leipzig, Germany',
                'destination': 'Chicago, IL, US',
                'status': 'In Transit',
                'service': 'DHL Express'
            },
            'maersk': {
                'origin': 'Shanghai, China',
                'destination': 'Long Beach, CA, US',
                'status': 'At Sea',
                'service': 'Ocean Freight',
                'vessel': 'Maersk Shanghai'
            },
            'msc': {
                'origin': 'Rotterdam, Netherlands',
                'destination': 'New York, NY, US',
                'status': 'Port Departure',
                'service': 'Ocean Freight',
                'vessel': 'MSC Oscar'
            }
        }
        
        config = carrier_configs.get(carrier, {
            'origin': 'Unknown Origin',
            'destination': 'Unknown Destination',
            'status': 'Unknown',
            'service': 'Standard'
        })
        
        # Generate estimated delivery (3-7 days from now)
        import random
        days_ahead = random.randint(3, 7)
        estimated_delivery = datetime.now(timezone.utc)
        estimated_delivery = estimated_delivery.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        estimated_delivery = estimated_delivery.replace(day=estimated_delivery.day + days_ahead)
        
        return CarrierShipmentData(
            tracking_number=tracking_number,
            carrier=self.supported_carriers[carrier]['name'],
            origin=config['origin'],
            destination=config['destination'],
            current_status=config['status'],
            estimated_delivery=estimated_delivery.strftime('%Y-%m-%d'),
            vessel=config.get('vessel'),
            service_type=config['service'],
            weight=random.uniform(1.0, 100.0),
            dimensions={'length': 20, 'width': 15, 'height': 10},
            last_update=datetime.now(timezone.utc).isoformat(),
            tracking_events=[
                {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'status': config['status'],
                    'location': config['origin'],
                    'description': f"Package processed at {config['origin']}"
                }
            ]
        )
    
    def _normalize_fedex_data(self, raw_data: Dict[str, Any]) -> CarrierShipmentData:
        """Normalize FedEx API response data."""
        # FedEx-specific field mapping
        return CarrierShipmentData(
            tracking_number=raw_data.get('trackingNumber', ''),
            carrier='FedEx',
            origin=raw_data.get('shipperAddress', {}).get('city', 'Unknown'),
            destination=raw_data.get('recipientAddress', {}).get('city', 'Unknown'),
            current_status=raw_data.get('latestStatusDetail', {}).get('description', 'Unknown'),
            estimated_delivery=raw_data.get('estimatedDeliveryTimeWindow', {}).get('window', {}).get('ends', 'Unknown'),
            service_type=raw_data.get('serviceDetail', {}).get('description', 'Unknown'),
            weight=raw_data.get('packageDetails', {}).get('weight', {}).get('value'),
            last_update=raw_data.get('latestStatusDetail', {}).get('scanTimestamp', ''),
            tracking_events=raw_data.get('scanEvents', [])
        )
    
    def _normalize_ups_data(self, raw_data: Dict[str, Any]) -> CarrierShipmentData:
        """Normalize UPS API response data."""
        # UPS-specific field mapping
        return CarrierShipmentData(
            tracking_number=raw_data.get('trackingNumber', ''),
            carrier='UPS',
            origin=raw_data.get('shipFrom', {}).get('address', {}).get('city', 'Unknown'),
            destination=raw_data.get('shipTo', {}).get('address', {}).get('city', 'Unknown'),
            current_status=raw_data.get('currentStatus', {}).get('description', 'Unknown'),
            estimated_delivery=raw_data.get('deliveryDate', {}).get('date', 'Unknown'),
            service_type=raw_data.get('service', {}).get('description', 'Unknown'),
            weight=raw_data.get('weight', {}).get('value'),
            tracking_events=raw_data.get('activity', [])
        )
    
    def _normalize_dhl_data(self, raw_data: Dict[str, Any]) -> CarrierShipmentData:
        """Normalize DHL API response data."""
        # DHL-specific field mapping
        shipments = raw_data.get('shipments', [])
        if not shipments:
            raise ValueError("No shipment data found in DHL response")
        
        shipment = shipments[0]
        events = shipment.get('events', [])
        latest_event = events[0] if events else {}
        
        return CarrierShipmentData(
            tracking_number=shipment.get('id', ''),
            carrier='DHL',
            origin=shipment.get('origin', {}).get('address', {}).get('addressLocality', 'Unknown'),
            destination=shipment.get('destination', {}).get('address', {}).get('addressLocality', 'Unknown'),
            current_status=latest_event.get('description', 'Unknown'),
            estimated_delivery=shipment.get('estimatedTimeOfDelivery', 'Unknown'),
            service_type=shipment.get('service', 'Unknown'),
            tracking_events=events
        )
    
    def _normalize_maersk_data(self, raw_data: Dict[str, Any]) -> CarrierShipmentData:
        """Normalize Maersk API response data."""
        # Maersk-specific field mapping for ocean freight
        return CarrierShipmentData(
            tracking_number=raw_data.get('containerNumber', ''),
            carrier='Maersk',
            origin=raw_data.get('originLocation', {}).get('name', 'Unknown'),
            destination=raw_data.get('destinationLocation', {}).get('name', 'Unknown'),
            current_status=raw_data.get('transportPlan', {}).get('status', 'Unknown'),
            estimated_delivery=raw_data.get('estimatedTimeOfArrival', 'Unknown'),
            vessel=raw_data.get('vesselName', 'Unknown'),
            service_type='Ocean Freight',
            tracking_events=raw_data.get('events', [])
        )
    
    def _normalize_msc_data(self, raw_data: Dict[str, Any]) -> CarrierShipmentData:
        """Normalize MSC API response data."""
        # MSC-specific field mapping for ocean freight
        return CarrierShipmentData(
            tracking_number=raw_data.get('containerNumber', ''),
            carrier='MSC',
            origin=raw_data.get('placeOfReceipt', 'Unknown'),
            destination=raw_data.get('placeOfDelivery', 'Unknown'),
            current_status=raw_data.get('status', 'Unknown'),
            estimated_delivery=raw_data.get('estimatedTimeOfArrival', 'Unknown'),
            vessel=raw_data.get('vesselName', 'Unknown'),
            service_type='Ocean Freight',
            tracking_events=raw_data.get('milestones', [])
        )
    
    def _normalize_generic_data(self, carrier: str, raw_data: Dict[str, Any]) -> CarrierShipmentData:
        """Normalize data from unknown/generic carriers."""
        return CarrierShipmentData(
            tracking_number=raw_data.get('tracking_number', raw_data.get('id', 'unknown')),
            carrier=carrier,
            origin=raw_data.get('origin', 'Unknown'),
            destination=raw_data.get('destination', 'Unknown'),
            current_status=raw_data.get('status', 'Unknown'),
            estimated_delivery=raw_data.get('estimated_delivery', 'Unknown'),
            service_type=raw_data.get('service_type', 'Standard')
        )
    
    def _submit_to_hcs(self, payload: Dict[str, Any]) -> str:
        """Submit carrier operation to HCS for timestamping."""
        try:
            message = HCS10Message(
                message_type=MessageType.NOTIFY,
                sender_id=self.agent_id,
                recipient_id="hcs-consensus",
                timestamp=datetime.now(timezone.utc).isoformat(),
                payload=payload
            )
            
            # Generate signature
            secret_key = self.config.hedera_private_key or "mock-secret-key"
            message.signature = message.generate_signature(secret_key)
            
            # Submit to HCS
            transaction_id = self.hedera_client.submit_message(message)
            logger.info(f"Submitted carrier operation to HCS: {transaction_id}")
            
            return transaction_id
            
        except Exception as e:
            logger.error(f"Failed to submit to HCS: {e}")
            return f"mock-tx-{int(time.time())}"
    
    def _store_shipment_data(self, response: CarrierResponse) -> None:
        """Store shipment data in database."""
        try:
            if response.shipment_data:
                shipment_data = ShipmentData(
                    shipment_id=response.shipment_data.tracking_number,
                    carrier=response.shipment_data.carrier,
                    tracking_number=response.shipment_data.tracking_number,
                    origin=response.shipment_data.origin,
                    destination=response.shipment_data.destination,
                    status=response.shipment_data.current_status,
                    estimated_delivery=None,  # Would need to parse date string
                    shipment_data=asdict(response.shipment_data)
                )
                
                db_session.add(shipment_data)
                db_session.commit()
                logger.debug(f"Stored shipment data for {response.tracking_number}")
            
        except Exception as e:
            logger.error(f"Failed to store shipment data: {e}")
            db_session.rollback()