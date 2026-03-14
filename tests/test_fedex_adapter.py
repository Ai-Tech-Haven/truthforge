"""
Tests for FedEx Adapter agent.

This module contains unit tests for the FedExAdapter and MockFedExAdapter classes,
including authentication, shipment querying, data extraction, and error handling.
"""

import pytest
from datetime import datetime, timezone
from agents.fedex_adapter import FedExAdapter, MockFedExAdapter
from agents.document_verifier import ShipmentData, Address
from agents.config import Config
from agents.hedera_client import MockHederaClient


@pytest.fixture
def config():
    """Create test configuration"""
    return Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="test-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.67890",
        mock_mode=True,
        fedex_api_key="test-api-key",
        fedex_secret_key="test-secret-key",
        fedex_account_number="123456789"
    )


@pytest.fixture
def hedera_client(config):
    """Create mock Hedera client"""
    return MockHederaClient(config)


@pytest.fixture
def fedex_adapter(config, hedera_client):
    """Create FedExAdapter instance"""
    return FedExAdapter(config, hedera_client)


@pytest.fixture
def mock_fedex_adapter(config, hedera_client):
    """Create MockFedExAdapter instance"""
    return MockFedExAdapter(config, hedera_client)


class TestFedExAdapterInitialization:
    """Test FedEx Adapter initialization"""
    
    def test_initialization_with_valid_config(self, config, hedera_client):
        """Test that FedExAdapter initializes correctly with valid config"""
        adapter = FedExAdapter(config, hedera_client)
        
        assert adapter.agent_id == "truthforge-fedex-001"
        assert "shipment-tracking" in adapter.capabilities
        assert "fedex-integration" in adapter.capabilities
        assert "logistics-data" in adapter.capabilities
        assert adapter.fedex_api_key == "test-api-key"
        assert adapter.fedex_secret_key == "test-secret-key"
        assert adapter.fedex_account_number == "123456789"
        assert adapter.authenticated is False
    
    def test_initialization_with_custom_agent_id(self, config, hedera_client):
        """Test initialization with custom agent ID"""
        adapter = FedExAdapter(config, hedera_client, agent_id="custom-fedex-001")
        
        assert adapter.agent_id == "custom-fedex-001"


class TestFedExAuthentication:
    """Test FedEx authentication"""
    
    def test_authenticate_in_mock_mode(self, fedex_adapter):
        """Test authentication succeeds in mock mode"""
        result = fedex_adapter.authenticate()
        
        assert result is True
        assert fedex_adapter.authenticated is True
        assert fedex_adapter.access_token is not None
        assert "mock-fedex-token" in fedex_adapter.access_token
        assert fedex_adapter.token_expiry is not None
    
    def test_authenticate_without_credentials_in_production_mode(self, hedera_client):
        """Test authentication fails without credentials in production mode"""
        config = Config(
            hedera_account_id="0.0.12345",
            hedera_private_key="test-key",
            hedera_network="testnet",
            hcs_topic_id="0.0.67890",
            mock_mode=False,  # Production mode
            fedex_api_key="",  # Missing credentials
            fedex_secret_key=""
        )
        adapter = FedExAdapter(config, hedera_client)
        
        with pytest.raises(RuntimeError, match="FedEx authentication failed"):
            adapter.authenticate()
    
    def test_token_expiry_check(self, fedex_adapter):
        """Test token expiry checking"""
        # Initially no token
        assert fedex_adapter._is_token_expired() is True
        
        # After authentication, token should not be expired
        fedex_adapter.authenticate()
        assert fedex_adapter._is_token_expired() is False
        
        # Set token to expired
        fedex_adapter.token_expiry = datetime.now(timezone.utc).timestamp() - 100
        assert fedex_adapter._is_token_expired() is True


class TestShipmentQuerying:
    """Test shipment querying functionality"""
    
    def test_query_shipment_success(self, fedex_adapter):
        """Test successful shipment query"""
        tracking_number = "123456789012"
        
        shipment_data = fedex_adapter.query_shipment(tracking_number)
        
        assert isinstance(shipment_data, ShipmentData)
        assert shipment_data.tracking_number == tracking_number
        assert isinstance(shipment_data.origin_address, Address)
        assert isinstance(shipment_data.destination_address, Address)
        assert shipment_data.weight > 0
    
    def test_query_shipment_without_tracking_number(self, fedex_adapter):
        """Test query fails without tracking number"""
        with pytest.raises(ValueError, match="tracking_number is required"):
            fedex_adapter.query_shipment("")
    
    def test_query_shipment_authenticates_if_needed(self, fedex_adapter):
        """Test query authenticates automatically if not authenticated"""
        assert fedex_adapter.authenticated is False
        
        shipment_data = fedex_adapter.query_shipment("123456789012")
        
        assert fedex_adapter.authenticated is True
        assert isinstance(shipment_data, ShipmentData)
    
    def test_query_shipment_reauthenticates_on_expired_token(self, fedex_adapter):
        """Test query re-authenticates when token is expired"""
        # Authenticate first
        fedex_adapter.authenticate()
        old_token = fedex_adapter.access_token
        
        # Expire the token
        fedex_adapter.token_expiry = datetime.now(timezone.utc).timestamp() - 100
        
        # Query should re-authenticate
        shipment_data = fedex_adapter.query_shipment("123456789012")
        
        assert fedex_adapter.authenticated is True
        assert fedex_adapter.access_token != old_token
        assert isinstance(shipment_data, ShipmentData)


class TestDataExtraction:
    """Test shipment data extraction"""
    
    def test_extract_shipment_data_complete(self, fedex_adapter):
        """Test extraction of complete shipment data"""
        api_response = {
            "trackingNumber": "123456789012",
            "origin": {
                "street": "123 Main St",
                "city": "Memphis",
                "state": "TN",
                "postalCode": "38125",
                "country": "USA"
            },
            "destination": {
                "street": "456 Oak Ave",
                "city": "New York",
                "state": "NY",
                "postalCode": "10001",
                "country": "USA"
            },
            "status": "IN_TRANSIT",
            "weight": 25.5,
            "shipmentDate": "2026-02-20T10:00:00Z",
            "estimatedDelivery": "2026-02-23T17:00:00Z",
            "cargoDescription": "Electronics"
        }
        
        shipment_data = fedex_adapter.extract_shipment_data(api_response)
        
        assert shipment_data.tracking_number == "123456789012"
        assert shipment_data.origin_address.city == "Memphis"
        assert shipment_data.origin_address.state == "TN"
        assert shipment_data.destination_address.city == "New York"
        assert shipment_data.destination_address.state == "NY"
        assert shipment_data.current_status == "IN_TRANSIT"
        assert shipment_data.weight == 25.5
        assert shipment_data.cargo_description == "Electronics"
    
    def test_extract_shipment_data_minimal(self, fedex_adapter):
        """Test extraction with minimal data"""
        api_response = {
            "trackingNumber": "999999999999",
            "origin": {"city": "Chicago", "state": "IL", "country": "USA"},
            "destination": {"city": "Boston", "state": "MA", "country": "USA"},
            "status": "DELIVERED",
            "weight": 10.0
        }
        
        shipment_data = fedex_adapter.extract_shipment_data(api_response)
        
        assert shipment_data.tracking_number == "999999999999"
        assert shipment_data.origin_address.city == "Chicago"
        assert shipment_data.destination_address.city == "Boston"
        assert shipment_data.current_status == "DELIVERED"
        assert shipment_data.weight == 10.0
    
    def test_extract_shipment_data_with_missing_fields(self, fedex_adapter):
        """Test extraction handles missing optional fields"""
        api_response = {
            "trackingNumber": "111111111111",
            "origin": {},
            "destination": {},
            "status": "UNKNOWN"
        }
        
        shipment_data = fedex_adapter.extract_shipment_data(api_response)
        
        assert shipment_data.tracking_number == "111111111111"
        assert shipment_data.current_status == "UNKNOWN"
        assert shipment_data.weight == 0.0


class TestProcessRequest:
    """Test request processing"""
    
    def test_process_request_success(self, fedex_adapter):
        """Test successful request processing"""
        request = {
            "tracking_number": "123456789012"
        }
        
        response = fedex_adapter.process_request(request)
        
        assert response["status"] == "success"
        assert "result" in response
        assert response["result"]["tracking_number"] == "123456789012"
    
    def test_process_request_missing_tracking_number(self, fedex_adapter):
        """Test request fails without tracking number"""
        request = {}
        
        response = fedex_adapter.process_request(request)
        
        assert response["status"] == "error"
        assert "tracking_number is required" in response["error"]
    
    def test_process_request_tracks_metrics(self, fedex_adapter):
        """Test request processing tracks metrics"""
        initial_count = fedex_adapter.requests_processed
        
        request = {"tracking_number": "123456789012"}
        fedex_adapter.process_request(request)
        
        assert fedex_adapter.requests_processed == initial_count + 1


class TestMockFedExAdapter:
    """Test Mock FedEx Adapter"""
    
    def test_mock_adapter_initialization(self, mock_fedex_adapter):
        """Test mock adapter initializes with test data"""
        assert mock_fedex_adapter.agent_id == "truthforge-fedex-mock-001"
        assert len(mock_fedex_adapter.test_shipments) == 3
        assert "123456789012" in mock_fedex_adapter.test_shipments
        assert "999999999999" in mock_fedex_adapter.test_shipments
        assert "111111111111" in mock_fedex_adapter.test_shipments
    
    def test_mock_authentication_always_succeeds(self, mock_fedex_adapter):
        """Test mock authentication always succeeds"""
        result = mock_fedex_adapter.authenticate()
        
        assert result is True
        assert mock_fedex_adapter.authenticated is True
        assert mock_fedex_adapter.access_token == "mock-fedex-token"
    
    def test_mock_query_predefined_shipment(self, mock_fedex_adapter):
        """Test querying predefined test shipment"""
        shipment_data = mock_fedex_adapter.query_shipment("123456789012")
        
        assert shipment_data.tracking_number == "123456789012"
        assert shipment_data.current_status == "IN_TRANSIT"
        assert shipment_data.origin_address.city == "Memphis"
        assert shipment_data.destination_address.city == "San Francisco"
        assert shipment_data.cargo_description == "Electronics - Smartphone"
    
    def test_mock_query_delivered_shipment(self, mock_fedex_adapter):
        """Test querying delivered shipment"""
        shipment_data = mock_fedex_adapter.query_shipment("999999999999")
        
        assert shipment_data.tracking_number == "999999999999"
        assert shipment_data.current_status == "DELIVERED"
        assert shipment_data.cargo_description == "Books - Educational Materials"
    
    def test_mock_query_delayed_shipment(self, mock_fedex_adapter):
        """Test querying delayed shipment"""
        shipment_data = mock_fedex_adapter.query_shipment("111111111111")
        
        assert shipment_data.tracking_number == "111111111111"
        assert shipment_data.current_status == "DELAYED"
        assert shipment_data.weight == 42.0
    
    def test_mock_query_not_found_error(self, mock_fedex_adapter):
        """Test error case for shipment not found"""
        with pytest.raises(RuntimeError, match="Shipment not found"):
            mock_fedex_adapter.query_shipment("000000000000")
    
    def test_mock_query_unknown_tracking_number(self, mock_fedex_adapter):
        """Test querying unknown tracking number generates mock data"""
        tracking_number = "555555555555"
        
        shipment_data = mock_fedex_adapter.query_shipment(tracking_number)
        
        assert shipment_data.tracking_number == tracking_number
        assert isinstance(shipment_data.origin_address, Address)
        assert isinstance(shipment_data.destination_address, Address)
        assert shipment_data.weight > 0
        assert shipment_data.current_status in ["IN_TRANSIT", "OUT_FOR_DELIVERY", "AT_FACILITY"]
    
    def test_mock_query_deterministic_generation(self, mock_fedex_adapter):
        """Test mock data generation is deterministic"""
        tracking_number = "777777777777"
        
        # Query same tracking number twice
        shipment1 = mock_fedex_adapter.query_shipment(tracking_number)
        shipment2 = mock_fedex_adapter.query_shipment(tracking_number)
        
        # Should generate identical data
        assert shipment1.origin_address.city == shipment2.origin_address.city
        assert shipment1.destination_address.city == shipment2.destination_address.city
        assert shipment1.weight == shipment2.weight
        assert shipment1.current_status == shipment2.current_status


class TestErrorHandling:
    """Test error handling"""
    
    def test_get_error_code_rate_limit(self, fedex_adapter):
        """Test error code for rate limit"""
        error = RuntimeError("FedEx API rate limit exceeded")
        code = fedex_adapter._get_error_code(error)
        
        assert code == "RATE_LIMIT_EXCEEDED"
    
    def test_get_error_code_authentication(self, fedex_adapter):
        """Test error code for authentication failure"""
        error = RuntimeError("Authentication failed")
        code = fedex_adapter._get_error_code(error)
        
        assert code == "AUTHENTICATION_FAILED"
    
    def test_get_error_code_not_found(self, fedex_adapter):
        """Test error code for shipment not found"""
        error = RuntimeError("Shipment not found")
        code = fedex_adapter._get_error_code(error)
        
        assert code == "SHIPMENT_NOT_FOUND"
    
    def test_get_error_code_invalid_tracking(self, fedex_adapter):
        """Test error code for invalid tracking number"""
        error = ValueError("Invalid tracking number format")
        code = fedex_adapter._get_error_code(error)
        
        assert code == "INVALID_TRACKING_NUMBER"
    
    def test_get_error_code_unknown(self, fedex_adapter):
        """Test error code for unknown error"""
        error = Exception("Something went wrong")
        code = fedex_adapter._get_error_code(error)
        
        assert code == "UNKNOWN_ERROR"


class TestHelperMethods:
    """Test helper methods"""
    
    def test_parse_date_iso_format(self, fedex_adapter):
        """Test parsing ISO format date"""
        date_str = "2026-02-20T10:00:00Z"
        parsed = fedex_adapter._parse_date(date_str)
        
        assert parsed.year == 2026
        assert parsed.month == 2
        assert parsed.day == 20
        assert parsed.hour == 10
    
    def test_parse_date_simple_format(self, fedex_adapter):
        """Test parsing simple date format"""
        date_str = "2026-02-20"
        parsed = fedex_adapter._parse_date(date_str)
        
        assert parsed.year == 2026
        assert parsed.month == 2
        assert parsed.day == 20
    
    def test_parse_date_invalid_format(self, fedex_adapter):
        """Test parsing invalid date format raises error"""
        with pytest.raises(ValueError, match="Unable to parse date"):
            fedex_adapter._parse_date("invalid-date")
    
    def test_shipment_data_to_dict(self, fedex_adapter):
        """Test converting ShipmentData to dictionary"""
        shipment_data = ShipmentData(
            tracking_number="123456789012",
            origin_address=Address("123 St", "Memphis", "TN", "38125", "USA"),
            destination_address=Address("456 Ave", "New York", "NY", "10001", "USA"),
            current_status="IN_TRANSIT",
            weight=25.5,
            shipment_date=datetime(2026, 2, 20, 10, 0, 0, tzinfo=timezone.utc),
            estimated_delivery=datetime(2026, 2, 23, 17, 0, 0, tzinfo=timezone.utc),
            cargo_description="Electronics"
        )
        
        result = fedex_adapter._shipment_data_to_dict(shipment_data)
        
        assert result["tracking_number"] == "123456789012"
        assert result["origin_address"]["city"] == "Memphis"
        assert result["destination_address"]["city"] == "New York"
        assert result["current_status"] == "IN_TRANSIT"
        assert result["weight"] == 25.5
        assert result["cargo_description"] == "Electronics"
        assert "2026-02-20" in result["shipment_date"]
        assert "2026-02-23" in result["estimated_delivery"]


class TestFedExErrorHandling:
    """Test FedEx error handling - Requirements 7.4, 7.5"""
    
    def test_rate_limit_handling_raises_error(self, hedera_client):
        """Test rate limit handling raises appropriate error"""
        # Create production mode config to test actual error handling
        config = Config(
            hedera_account_id="0.0.12345",
            hedera_private_key="test-key",
            hedera_network="testnet",
            hcs_topic_id="0.0.67890",
            mock_mode=False,  # Production mode
            fedex_api_key="test-api-key",
            fedex_secret_key="test-secret-key"
        )
        adapter = FedExAdapter(config, hedera_client)
        
        # Track retry attempts
        retry_attempts = []
        
        def mock_api_call_with_rate_limit(tracking_number):
            """Mock API call that always fails with rate limit"""
            retry_attempts.append(datetime.now(timezone.utc))
            raise RuntimeError("FedEx API rate limit exceeded")
        
        # Patch the simulate method
        import unittest.mock
        with unittest.mock.patch.object(adapter, "_simulate_fedex_api_call", mock_api_call_with_rate_limit):
            # Authenticate first
            adapter.authenticate()
            
            # Query should raise rate limit error
            with pytest.raises(RuntimeError, match="rate limit"):
                adapter.query_shipment("123456789012")
            
            # Verify attempt was made
            assert len(retry_attempts) >= 1
    
    def test_authentication_failure_recovery(self, fedex_adapter):
        """Test authentication failure recovery"""
        # Track authentication attempts
        auth_attempts = []
        
        def mock_authenticate_with_failure():
            """Mock authentication that fails first time, succeeds second time"""
            auth_attempts.append(datetime.now(timezone.utc))
            
            if len(auth_attempts) == 1:
                # First attempt fails
                fedex_adapter.authenticated = False
                raise RuntimeError("FedEx authentication failed: Invalid credentials")
            else:
                # Second attempt succeeds
                fedex_adapter.authenticated = True
                fedex_adapter.access_token = "recovered-token"
                fedex_adapter.token_expiry = datetime.now(timezone.utc).timestamp() + 3600
                return True
        
        # Replace authenticate method
        import unittest.mock
        with unittest.mock.patch.object(fedex_adapter, "authenticate", mock_authenticate_with_failure):
            # First authentication attempt should fail
            with pytest.raises(RuntimeError, match="authentication failed"):
                fedex_adapter.authenticate()
            
            assert len(auth_attempts) == 1
            assert fedex_adapter.authenticated is False
            
            # Second authentication attempt should succeed
            result = fedex_adapter.authenticate()
            
            assert result is True
            assert len(auth_attempts) == 2
            assert fedex_adapter.authenticated is True
            assert fedex_adapter.access_token == "recovered-token"
    
    def test_authentication_error_triggers_reauthentication(self, hedera_client):
        """Test that authentication errors during query trigger re-authentication"""
        # Create production mode config
        config = Config(
            hedera_account_id="0.0.12345",
            hedera_private_key="test-key",
            hedera_network="testnet",
            hcs_topic_id="0.0.67890",
            mock_mode=False,
            fedex_api_key="test-api-key",
            fedex_secret_key="test-secret-key"
        )
        adapter = FedExAdapter(config, hedera_client)
        
        # Track calls
        api_calls = []
        auth_calls = []
        
        def mock_api_call_with_auth_error(tracking_number):
            """Mock API call that fails with auth error on first attempt"""
            api_calls.append(tracking_number)
            
            if len(api_calls) == 1:
                raise RuntimeError("Authentication failed: Token expired")
            
            # Second attempt succeeds
            return {
                "trackingNumber": tracking_number,
                "origin": {"city": "Memphis", "state": "TN", "country": "USA"},
                "destination": {"city": "New York", "state": "NY", "country": "USA"},
                "status": "IN_TRANSIT",
                "weight": 25.5,
                "shipmentDate": "2026-02-20T10:00:00Z",
                "estimatedDelivery": "2026-02-23T17:00:00Z"
            }
        
        def mock_authenticate():
            """Track authentication calls"""
            auth_calls.append(datetime.now(timezone.utc))
            adapter.authenticated = True
            adapter.access_token = f"token-{len(auth_calls)}"
            adapter.token_expiry = datetime.now(timezone.utc).timestamp() + 3600
            return True
        
        # Patch methods
        import unittest.mock
        with unittest.mock.patch.object(adapter, "_simulate_fedex_api_call", mock_api_call_with_auth_error):
            with unittest.mock.patch.object(adapter, "authenticate", mock_authenticate):
                # Query should handle auth error by re-authenticating
                shipment_data = adapter.query_shipment("123456789012")
                
                # Verify re-authentication occurred
                assert len(auth_calls) >= 1
                assert len(api_calls) == 2  # First attempt failed, second succeeded
                assert isinstance(shipment_data, ShipmentData)
                assert shipment_data.tracking_number == "123456789012"
    
    def test_unavailable_shipment_error_response(self, hedera_client):
        """Test unavailable shipment error responses"""
        # Create production mode config
        config = Config(
            hedera_account_id="0.0.12345",
            hedera_private_key="test-key",
            hedera_network="testnet",
            hcs_topic_id="0.0.67890",
            mock_mode=False,
            fedex_api_key="test-api-key",
            fedex_secret_key="test-secret-key"
        )
        adapter = FedExAdapter(config, hedera_client)
        
        def mock_api_call_not_found(tracking_number):
            """Mock API call that returns shipment not found"""
            raise RuntimeError("Shipment not found or unavailable")
        
        # Patch the simulate method
        import unittest.mock
        with unittest.mock.patch.object(adapter, "_simulate_fedex_api_call", mock_api_call_not_found):
            # Authenticate first
            adapter.authenticate()
            
            # Query should raise error for unavailable shipment
            with pytest.raises(RuntimeError, match="Shipment not found|unavailable"):
                adapter.query_shipment("999999999999")
    
    def test_unavailable_shipment_returns_structured_error(self, fedex_adapter, monkeypatch):
        """Test unavailable shipment returns structured error through process_request"""
        def mock_query_not_found(tracking_number):
            """Mock query that raises not found error"""
            raise RuntimeError("Shipment not found or unavailable")
        
        # Patch query_shipment
        monkeypatch.setattr(fedex_adapter, "query_shipment", mock_query_not_found)
        
        # Process request should return structured error
        request = {"tracking_number": "999999999999"}
        response = fedex_adapter.process_request(request)
        
        assert response["status"] == "error"
        assert "not found" in response["error"].lower() or "unavailable" in response["error"].lower()
        assert response["error_code"] == "SHIPMENT_NOT_FOUND"
    
    def test_rate_limit_error_returns_correct_error_code(self, fedex_adapter, monkeypatch):
        """Test rate limit error returns correct error code"""
        def mock_query_rate_limit(tracking_number):
            """Mock query that raises rate limit error"""
            raise RuntimeError("FedEx API rate limit exceeded")
        
        # Patch query_shipment
        monkeypatch.setattr(fedex_adapter, "query_shipment", mock_query_rate_limit)
        
        # Process request should return structured error with rate limit code
        request = {"tracking_number": "123456789012"}
        response = fedex_adapter.process_request(request)
        
        assert response["status"] == "error"
        assert "rate limit" in response["error"].lower()
        assert response["error_code"] == "RATE_LIMIT_EXCEEDED"
    
    def test_authentication_error_returns_correct_error_code(self, fedex_adapter, monkeypatch):
        """Test authentication error returns correct error code"""
        def mock_query_auth_error(tracking_number):
            """Mock query that raises authentication error"""
            raise RuntimeError("Authentication failed: Invalid token")
        
        # Patch query_shipment
        monkeypatch.setattr(fedex_adapter, "query_shipment", mock_query_auth_error)
        
        # Process request should return structured error with auth code
        request = {"tracking_number": "123456789012"}
        response = fedex_adapter.process_request(request)
        
        assert response["status"] == "error"
        assert "auth" in response["error"].lower()
        assert response["error_code"] == "AUTHENTICATION_FAILED"
    
    def test_multiple_error_types_handled_correctly(self, fedex_adapter):
        """Test that different error types are handled with appropriate error codes"""
        # Test various error scenarios
        error_scenarios = [
            (RuntimeError("FedEx API rate limit exceeded"), "RATE_LIMIT_EXCEEDED"),
            (RuntimeError("Authentication failed"), "AUTHENTICATION_FAILED"),
            (RuntimeError("Shipment not found"), "SHIPMENT_NOT_FOUND"),
            (ValueError("Invalid tracking number format"), "INVALID_TRACKING_NUMBER"),
            (Exception("Unknown error occurred"), "UNKNOWN_ERROR")
        ]
        
        for error, expected_code in error_scenarios:
            code = fedex_adapter._get_error_code(error)
            assert code == expected_code, f"Expected {expected_code} for error: {error}"
    
    def test_error_tracking_increments_error_count(self, fedex_adapter, monkeypatch):
        """Test that errors increment the error count metric"""
        def mock_query_error(tracking_number):
            """Mock query that always fails"""
            raise RuntimeError("Simulated error")
        
        # Patch query_shipment
        monkeypatch.setattr(fedex_adapter, "query_shipment", mock_query_error)
        
        initial_error_count = fedex_adapter.error_count
        
        # Process failing request
        request = {"tracking_number": "123456789012"}
        response = fedex_adapter.process_request(request)
        
        assert response["status"] == "error"
        assert fedex_adapter.error_count == initial_error_count + 1


class TestIntegration:
    """Integration tests"""
    
    def test_end_to_end_shipment_query(self, mock_fedex_adapter):
        """Test complete shipment query workflow"""
        # Process request through the agent
        request = {"tracking_number": "123456789012"}
        response = mock_fedex_adapter.process_request(request)
        
        # Verify response structure
        assert response["status"] == "success"
        assert "result" in response
        
        result = response["result"]
        assert result["tracking_number"] == "123456789012"
        assert result["current_status"] == "IN_TRANSIT"
        assert "origin_address" in result
        assert "destination_address" in result
        assert result["weight"] == 15.5
    
    def test_health_check_after_requests(self, mock_fedex_adapter):
        """Test health check reflects request processing"""
        # Register the agent first
        mock_fedex_adapter.register_with_hol()
        
        # Process some requests
        mock_fedex_adapter.process_request({"tracking_number": "123456789012"})
        mock_fedex_adapter.process_request({"tracking_number": "999999999999"})
        
        # Check health
        status = mock_fedex_adapter.health_check()
        
        assert status.agent_id == "truthforge-fedex-mock-001"
        assert status.status == "ONLINE"
        assert status.requests_processed == 2
        assert status.error_count == 0
