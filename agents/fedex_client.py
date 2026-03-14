"""
FedEx API Client for TruthForge

This module provides integration with FedEx APIs for shipment creation,
tracking, and document management.
"""
import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FedExClient:
    """
    FedEx API Client
    
    Handles authentication and API calls to FedEx services including
    shipment creation, tracking, and document retrieval.
    """
    
    def __init__(self, environment: str = 'sandbox'):
        """
        Initialize FedEx API client
        
        Args:
            environment: 'sandbox' or 'production'
        """
        self.api_key = os.getenv('FEDEX_API_KEY')
        self.secret_key = os.getenv('FEDEX_SECRET_KEY')
        self.account_number = os.getenv('FEDEX_ACCOUNT_NUMBER')
        self.environment = environment
        
        # Set base URL based on environment
        if environment == 'sandbox':
            self.base_url = "https://apis-sandbox.fedex.com"
        else:
            self.base_url = "https://apis.fedex.com"
        
        self.access_token = None
        self.token_expiry = None
        
        logger.info(f"FedEx client initialized ({environment} mode)")
    
    def _get_access_token(self) -> str:
        """
        Get or refresh OAuth access token
        
        Returns:
            str: Access token
            
        Raises:
            Exception: If authentication fails
        """
        # Return cached token if still valid
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.access_token
        
        # Request new token
        auth_url = f"{self.base_url}/oauth/token"
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.secret_key
        }
        
        try:
            response = requests.post(auth_url, data=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            
            # Set expiry with 60 second buffer
            expires_in = data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info("FedEx access token obtained successfully")
            return self.access_token
        
        except requests.exceptions.RequestException as e:
            logger.error(f"FedEx authentication failed: {e}")
            raise Exception(f"FedEx auth failed: {str(e)}")
    
    def create_shipment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a FedEx shipment
        
        Args:
            order_data: Order data including shipping and billing addresses
            
        Returns:
            dict: Shipment creation response
            
        Raises:
            Exception: If shipment creation fails
        """
        token = self._get_access_token()
        headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json'
        }
        
        # Extract addresses from order data
        shipping_address = order_data.get('shipping', {})
        billing_address = order_data.get('billing', {})
        
        # Build shipment payload
        payload = {
            "accountNumber": {"value": self.account_number},
            "requestedShipment": {
                "shipper": {
                    "address": {
                        "streetLines": [billing_address.get('address_1', '')],
                        "city": billing_address.get('city', ''),
                        "stateOrProvinceCode": billing_address.get('state', ''),
                        "postalCode": billing_address.get('postcode', ''),
                        "countryCode": billing_address.get('country', 'US')
                    },
                    "contact": {
                        "personName": f"{billing_address.get('first_name', '')} {billing_address.get('last_name', '')}",
                        "phoneNumber": billing_address.get('phone', '')
                    }
                },
                "recipient": {
                    "address": {
                        "streetLines": [shipping_address.get('address_1', '')],
                        "city": shipping_address.get('city', ''),
                        "stateOrProvinceCode": shipping_address.get('state', ''),
                        "postalCode": shipping_address.get('postcode', ''),
                        "countryCode": shipping_address.get('country', 'US')
                    },
                    "contact": {
                        "personName": f"{shipping_address.get('first_name', '')} {shipping_address.get('last_name', '')}",
                        "phoneNumber": shipping_address.get('phone', '')
                    }
                },
                "pickupType": "USE_SCHEDULED_PICKUP",
                "serviceType": "FEDEX_PRIORITY_OVERNIGHT",
                "packagingType": "YOUR_PACKAGING",
                "requestedPackageLineItems": [
                    {
                        "weight": {
                            "units": "KG",
                            "value": order_data.get('weight', 10)
                        },
                        "dimensions": {
                            "length": 30,
                            "width": 20,
                            "height": 15,
                            "units": "CM"
                        }
                    }
                ],
                "shippingChargesPayment": {
                    "paymentType": "SENDER"
                },
                "labelSpecification": {
                    "labelFormatType": "COMMON2D",
                    "imageType": "PDF"
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/ship/v1/shipments",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"FedEx shipment created successfully")
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Shipment creation failed: {e}")
            raise Exception(f"Shipment creation failed: {str(e)}")
    
    def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """
        Track a FedEx shipment
        
        Args:
            tracking_number: FedEx tracking number
            
        Returns:
            dict: Tracking information
            
        Raises:
            Exception: If tracking request fails
        """
        token = self._get_access_token()
        headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            "trackingInfo": [
                {
                    "trackingNumberInfo": {
                        "trackingNumber": tracking_number
                    }
                }
            ],
            "includeDetailedScans": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/track/v1/trackingnumbers",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Tracking info retrieved for {tracking_number}")
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Tracking request failed: {e}")
            raise Exception(f"Tracking request failed: {str(e)}")
    
    def get_shipment_documents(self, tracking_number: str) -> Dict[str, Any]:
        """
        Retrieve shipment documents (BOL, commercial invoice, etc.)
        
        Args:
            tracking_number: FedEx tracking number
            
        Returns:
            dict: Document information
        """
        # This would use FedEx's document retrieval API
        # Implementation depends on specific FedEx API endpoints available
        logger.info(f"Document retrieval for {tracking_number} (not yet implemented)")
        return {
            "tracking_number": tracking_number,
            "documents": [],
            "message": "Document retrieval not yet implemented"
        }
    
    def validate_address(self, address: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate an address using FedEx Address Validation API
        
        Args:
            address: Address dictionary
            
        Returns:
            dict: Validation result
        """
        token = self._get_access_token()
        headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            "addressesToValidate": [
                {
                    "address": {
                        "streetLines": [address.get('address_1', '')],
                        "city": address.get('city', ''),
                        "stateOrProvinceCode": address.get('state', ''),
                        "postalCode": address.get('postcode', ''),
                        "countryCode": address.get('country', 'US')
                    }
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/address/v1/addresses/resolve",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info("Address validation completed")
            return result
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Address validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
