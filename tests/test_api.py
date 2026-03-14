"""
Unit tests for TruthForge Flask API endpoints.

Tests the REST API endpoints including verification requests, status checks,
history retrieval, agent discovery, and webhook handling.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from api.app import create_app
from agents.config import Config
from agents.orchestrator import Orchestrator
from hol_registry.registry import HOLRegistry, AgentMetadata


@pytest.fixture
def mock_config():
    """Create mock configuration for testing."""
    config = Mock(spec=Config)
    config.mock_mode = True
    config.api_auth_token = "test-token-12345"
    config.woocommerce_webhook_secret = "webhook-secret"
    config.hcs_topic_id = "0.0.12345"
    return config


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator for testing."""
    from agents.orchestrator_agent import OrchestratorAgent
    orchestrator = Mock(spec=OrchestratorAgent)
    
    # Default successful response matching new format
    orchestrator.process_request.return_value = {
        "success": True,
        "natural_language_response": "Verification completed successfully",
        "unified_report": {
            "authenticity_score": 85.5,
            "hcs_transaction_id": "0.0.12345@1234567890.123456789",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    
    return orchestrator


@pytest.fixture
def mock_hol_registry():
    """Create mock HOL registry for testing."""
    registry = Mock(spec=HOLRegistry)
    
    # Create sample agent metadata
    agent1 = AgentMetadata(
        agent_id="truthforge-image-001",
        capabilities=["image_analysis", "deepfake_detection"],
        endpoints={"api": "http://localhost:5001"},
        hcs_topic_id="0.0.12345",
        status="ONLINE"
    )
    
    agent2 = AgentMetadata(
        agent_id="truthforge-verify-001",
        capabilities=["document_verification", "bol_validation"],
        endpoints={"api": "http://localhost:5002"},
        hcs_topic_id="0.0.12345",
        status="ONLINE"
    )
    
    registry.query_agents.return_value = [agent1, agent2]
    
    return registry


@pytest.fixture
def mock_database():
    """Create mock database for testing."""
    database = Mock()
    database.is_connected.return_value = True
    database.query_records.return_value = []
    database.count_records.return_value = 0
    return database


@pytest.fixture
def client(mock_config, mock_orchestrator, mock_hol_registry, mock_database):
    """Create Flask test client."""
    app = create_app(mock_config, mock_orchestrator, mock_hol_registry, mock_database)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client


class TestVerifyEndpoint:
    """Tests for POST /api/verify endpoint."""
    
    def test_verify_with_valid_request(self, client, mock_orchestrator):
        """Test POST /api/verify with valid request returns 200."""
        response = client.post(
            '/api/verify',
            json={
                "action": "verify_image",
                "image_data": "base64encodeddata"
            },
            headers={"Authorization": "Bearer test-token-12345"}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "request_id" in data
        assert data["status"] == "completed"
        assert data["success"] is True
        assert "unified_report" in data
        
        # Verify orchestrator was called
        mock_orchestrator.process_request.assert_called_once()
    
    def test_verify_without_auth_token(self, client):
        """Test POST /api/verify without auth token returns 401."""
        response = client.post(
            '/api/verify',
            json={"action": "verify_image"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        
        assert "error" in data
        assert data["error"]["code"] == "MISSING_AUTH_TOKEN"
    
    def test_verify_with_invalid_auth_token(self, client):
        """Test POST /api/verify with invalid token returns 401."""
        response = client.post(
            '/api/verify',
            json={"action": "verify_image"},
            headers={"Authorization": "Bearer wrong-token"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        
        assert "error" in data
        assert data["error"]["code"] == "INVALID_AUTH_TOKEN"
    
    def test_verify_without_request_body(self, client):
        """Test POST /api/verify without body returns 400."""
        response = client.post(
            '/api/verify',
            headers={
                "Authorization": "Bearer test-token-12345",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data
        assert data["error"]["code"] == "INVALID_REQUEST"
    
    def test_verify_without_action_field(self, client):
        """Test POST /api/verify without action field returns 400."""
        response = client.post(
            '/api/verify',
            json={"image_data": "base64data"},
            headers={"Authorization": "Bearer test-token-12345"}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data
        assert data["error"]["code"] == "MISSING_ACTION"
    
    def test_verify_with_orchestrator_error(self, client, mock_orchestrator):
        """Test POST /api/verify handles orchestrator errors."""
        mock_orchestrator.process_request.return_value = {
            "success": False,
            "error": "Agent timeout"
        }
        
        response = client.post(
            '/api/verify',
            json={"action": "verify_image"},
            headers={"Authorization": "Bearer test-token-12345"}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["status"] == "error"
        assert "error" in data


class TestStatusEndpoint:
    """Tests for GET /api/status/<request_id> endpoint."""
    
    def test_get_status_for_existing_request(self, client, mock_orchestrator):
        """Test GET /api/status returns correct status for existing request."""
        # First create a verification request
        verify_response = client.post(
            '/api/verify',
            json={"action": "verify_image"},
            headers={"Authorization": "Bearer test-token-12345"}
        )
        
        verify_data = json.loads(verify_response.data)
        request_id = verify_data["request_id"]
        
        # Now check status
        response = client.get(f'/api/status/{request_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["request_id"] == request_id
        assert data["status"] in ["completed", "error"]
        assert "result" in data
    
    def test_get_status_for_nonexistent_request(self, client):
        """Test GET /api/status returns 404 for nonexistent request."""
        response = client.get('/api/status/nonexistent-request-id')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert "error" in data
        assert data["error"]["code"] == "REQUEST_NOT_FOUND"


class TestHistoryEndpoint:
    """Tests for GET /api/history endpoint."""
    
    def test_get_history_returns_verification_list(self, client, mock_orchestrator):
        """Test GET /api/history returns list of verifications."""
        # Create some verification requests
        for i in range(3):
            client.post(
                '/api/verify',
                json={"action": "verify_image", "test_id": i},
                headers={"Authorization": "Bearer test-token-12345"}
            )
        
        # Get history
        response = client.get(
            '/api/history',
            headers={"Authorization": "Bearer test-token-12345"}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "verifications" in data
        assert len(data["verifications"]) == 3
        assert data["total"] == 3
        assert data["limit"] == 50
        assert data["offset"] == 0
    
    def test_get_history_with_pagination(self, client, mock_orchestrator):
        """Test GET /api/history with pagination parameters."""
        # Create some verification requests
        for i in range(5):
            client.post(
                '/api/verify',
                json={"action": "verify_image"},
                headers={"Authorization": "Bearer test-token-12345"}
            )
        
        # Get history with limit and offset
        response = client.get(
            '/api/history?limit=2&offset=1',
            headers={"Authorization": "Bearer test-token-12345"}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert len(data["verifications"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 1
    
    def test_get_history_with_invalid_limit(self, client):
        """Test GET /api/history with invalid limit returns 400."""
        response = client.get(
            '/api/history?limit=200',
            headers={"Authorization": "Bearer test-token-12345"}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data
        assert data["error"]["code"] == "INVALID_LIMIT"
    
    def test_get_history_without_auth(self, client):
        """Test GET /api/history without auth returns 401."""
        response = client.get('/api/history')
        
        assert response.status_code == 401


class TestAgentsEndpoint:
    """Tests for GET /api/agents endpoint."""
    
    def test_get_agents_returns_agent_status(self, client, mock_hol_registry):
        """Test GET /api/agents returns list of registered agents."""
        response = client.get('/api/agents')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "agents" in data
        assert "count" in data
        assert data["count"] == 2
        assert len(data["agents"]) == 2
        
        # Verify agent structure
        agent = data["agents"][0]
        assert "agentId" in agent
        assert "capabilities" in agent
        assert "status" in agent
        assert "endpoints" in agent
    
    def test_get_agents_with_capability_filter(self, client, mock_hol_registry):
        """Test GET /api/agents with capability filter."""
        response = client.get('/api/agents?capability=image_analysis')
        
        assert response.status_code == 200
        
        # Verify registry was called with filter
        mock_hol_registry.query_agents.assert_called_with(
            capability_filter=['image_analysis'],
            status_filter=None
        )
    
    def test_get_agents_with_status_filter(self, client, mock_hol_registry):
        """Test GET /api/agents with status filter."""
        response = client.get('/api/agents?status=ONLINE')
        
        assert response.status_code == 200
        
        # Verify registry was called with filter
        mock_hol_registry.query_agents.assert_called_with(
            capability_filter=None,
            status_filter='ONLINE'
        )


class TestWooCommerceWebhook:
    """Tests for POST /api/woocommerce/webhook endpoint."""
    
    def test_webhook_with_valid_payload(self, client, mock_orchestrator):
        """Test POST /api/woocommerce/webhook with valid payload."""
        response = client.post(
            '/api/woocommerce/webhook',
            json={
                "id": 12345,
                "status": "processing",
                "total": "99.99"
            },
            headers={"X-WC-Webhook-Signature": "valid-signature"}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["status"] == "received"
        assert "request_id" in data
        # Order ID is converted to string in the API
        assert data["order_id"] == "12345"
        
        # Verify orchestrator was called
        mock_orchestrator.process_request.assert_called_once()
    
    def test_webhook_without_order_id(self, client):
        """Test POST /api/woocommerce/webhook without order ID returns 400."""
        response = client.post(
            '/api/woocommerce/webhook',
            json={"status": "processing"},
            headers={"X-WC-Webhook-Signature": "valid-signature"}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data
        assert data["error"]["code"] == "MISSING_ORDER_ID"
    
    def test_webhook_without_payload(self, client):
        """Test POST /api/woocommerce/webhook without payload returns 400."""
        response = client.post(
            '/api/woocommerce/webhook',
            headers={
                "X-WC-Webhook-Signature": "valid-signature",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data
        assert data["error"]["code"] == "INVALID_PAYLOAD"
    
    def test_webhook_processing_error_returns_200(self, client, mock_orchestrator):
        """Test webhook returns 200 even on processing error to prevent retries."""
        mock_orchestrator.process_request.side_effect = Exception("Processing failed")
        
        response = client.post(
            '/api/woocommerce/webhook',
            json={"id": 12345},
            headers={"X-WC-Webhook-Signature": "valid-signature"}
        )
        
        # Should still return 200 to acknowledge receipt
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["status"] == "error"


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""
    
    def test_health_check_returns_healthy(self, client):
        """Test GET /health returns healthy status."""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "mock_mode" in data


class TestErrorHandlers:
    """Tests for error handler middleware."""
    
    def test_404_error_returns_structured_response(self, client):
        """Test 404 errors return structured JSON response."""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
        assert "timestamp" in data["error"]
    
    def test_405_error_returns_structured_response(self, client):
        """Test 405 Method Not Allowed returns structured response."""
        response = client.put('/api/verify')
        
        assert response.status_code == 405
        data = json.loads(response.data)
        
        assert "error" in data
        assert data["error"]["code"] == "METHOD_NOT_ALLOWED"


class TestAuthenticationMiddleware:
    """Tests for authentication middleware."""
    
    def test_auth_with_bearer_token(self, client):
        """Test authentication with valid Bearer token."""
        response = client.post(
            '/api/verify',
            json={"action": "verify_image"},
            headers={"Authorization": "Bearer test-token-12345"}
        )
        
        assert response.status_code == 200
    
    def test_auth_with_invalid_format(self, client):
        """Test authentication with invalid header format."""
        response = client.post(
            '/api/verify',
            json={"action": "verify_image"},
            headers={"Authorization": "test-token-12345"}
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        
        assert data["error"]["code"] == "INVALID_AUTH_FORMAT"
    
    def test_unprotected_endpoints_work_without_auth(self, client):
        """Test unprotected endpoints work without authentication."""
        # Health check should work without auth
        response = client.get('/health')
        assert response.status_code == 200
        
        # Status check should work without auth
        response = client.get('/api/status/some-id')
        assert response.status_code == 404  # Not found, but not auth error
        
        # Agents endpoint should work without auth
        response = client.get('/api/agents')
        assert response.status_code == 200


# Property-Based Tests
from hypothesis import given, strategies as st, settings, HealthCheck


class TestAPIErrorResponseProperties:
    """Property-based tests for API error response structure."""
    
    @given(
        error_scenario=st.sampled_from([
            # Validation errors (400)
            {"endpoint": "/api/verify", "method": "POST", "data": None, "headers": {"Authorization": "Bearer test-token-12345"}, "expected_status": 400},
            {"endpoint": "/api/verify", "method": "POST", "data": {}, "headers": {"Authorization": "Bearer test-token-12345"}, "expected_status": 400},
            {"endpoint": "/api/verify", "method": "POST", "data": {"no_action": "test"}, "headers": {"Authorization": "Bearer test-token-12345"}, "expected_status": 400},
            {"endpoint": "/api/history", "method": "GET", "params": {"limit": 200}, "headers": {"Authorization": "Bearer test-token-12345"}, "expected_status": 400},
            {"endpoint": "/api/woocommerce/webhook", "method": "POST", "data": None, "headers": {"X-WC-Webhook-Signature": "sig"}, "expected_status": 400},
            {"endpoint": "/api/woocommerce/webhook", "method": "POST", "data": {"no_id": "test"}, "headers": {"X-WC-Webhook-Signature": "sig"}, "expected_status": 400},
            # Authentication errors (401)
            {"endpoint": "/api/verify", "method": "POST", "data": {"action": "test"}, "headers": {}, "expected_status": 401},
            {"endpoint": "/api/verify", "method": "POST", "data": {"action": "test"}, "headers": {"Authorization": "Bearer wrong-token"}, "expected_status": 401},
            {"endpoint": "/api/history", "method": "GET", "headers": {}, "expected_status": 401},
            # Not found errors (404)
            {"endpoint": "/api/status/nonexistent-id", "method": "GET", "expected_status": 404},
            {"endpoint": "/api/nonexistent", "method": "GET", "expected_status": 404},
            # Method not allowed (405)
            {"endpoint": "/api/verify", "method": "PUT", "expected_status": 405},
            {"endpoint": "/api/agents", "method": "POST", "expected_status": 405},
        ])
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_33_api_error_response_structure(self, client, error_scenario):
        """
        Feature: truthforge, Property 33: API Error Response Structure
        
        For any API error (validation failure, internal error, not found), the response 
        shall be a structured JSON object containing an error code, message, and 
        appropriate HTTP status code.
        
        Validates: Requirements 13.7
        
        This property test verifies that:
        1. All error responses return the expected HTTP status code
        2. All error responses are valid JSON
        3. All error responses contain required fields: error.code, error.message, error.timestamp
        4. Error codes are meaningful and consistent
        5. Error messages are human-readable
        """
        endpoint = error_scenario["endpoint"]
        method = error_scenario["method"]
        expected_status = error_scenario["expected_status"]
        headers = error_scenario.get("headers", {})
        data = error_scenario.get("data")
        params = error_scenario.get("params", {})
        
        # Make request based on method
        if method == "POST":
            if data is None:
                response = client.post(endpoint, headers=headers)
            else:
                response = client.post(endpoint, json=data, headers=headers)
        elif method == "GET":
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{endpoint}?{query_string}" if query_string else endpoint
            response = client.get(url, headers=headers)
        elif method == "PUT":
            response = client.put(endpoint, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Property 1: Response must have expected HTTP status code
        assert response.status_code == expected_status, \
            f"Expected status {expected_status} for {method} {endpoint}, got {response.status_code}"
        
        # Property 2: Response must be valid JSON
        try:
            data = json.loads(response.data)
        except json.JSONDecodeError as e:
            pytest.fail(f"Response is not valid JSON: {e}")
        
        # Property 3: Response must contain 'error' field
        assert "error" in data, \
            f"Error response must contain 'error' field. Got: {list(data.keys())}"
        
        error = data["error"]
        
        # Property 4: Error must contain 'code' field
        assert "code" in error, \
            f"Error must contain 'code' field. Got: {list(error.keys())}"
        
        # Property 5: Error code must be a non-empty string
        assert isinstance(error["code"], str), \
            f"Error code must be a string, got {type(error['code'])}"
        assert len(error["code"]) > 0, \
            "Error code must not be empty"
        
        # Property 6: Error must contain 'message' field
        assert "message" in error, \
            f"Error must contain 'message' field. Got: {list(error.keys())}"
        
        # Property 7: Error message must be a non-empty string
        assert isinstance(error["message"], str), \
            f"Error message must be a string, got {type(error['message'])}"
        assert len(error["message"]) > 0, \
            "Error message must not be empty"
        
        # Property 8: Error must contain 'timestamp' field
        assert "timestamp" in error, \
            f"Error must contain 'timestamp' field. Got: {list(error.keys())}"
        
        # Property 9: Timestamp must be a valid ISO 8601 string
        assert isinstance(error["timestamp"], str), \
            f"Timestamp must be a string, got {type(error['timestamp'])}"
        try:
            datetime.fromisoformat(error["timestamp"].replace('Z', '+00:00'))
        except ValueError as e:
            pytest.fail(f"Timestamp is not valid ISO 8601 format: {e}")
        
        # Property 10: Error code should match error category
        status_to_code_prefix = {
            400: ["INVALID", "MISSING", "BAD"],
            401: ["MISSING_AUTH", "INVALID_AUTH", "UNAUTHORIZED"],
            403: ["FORBIDDEN"],
            404: ["NOT_FOUND", "REQUEST_NOT_FOUND"],
            405: ["METHOD_NOT_ALLOWED"],
            500: ["INTERNAL"]
        }
        
        expected_prefixes = status_to_code_prefix.get(expected_status, [])
        if expected_prefixes:
            code_matches = any(
                error["code"].startswith(prefix) or error["code"] == prefix 
                for prefix in expected_prefixes
            )
            assert code_matches, \
                f"Error code '{error['code']}' should start with one of {expected_prefixes} for status {expected_status}"
    
    @given(
        http_status=st.sampled_from([400, 401, 404, 405])
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_33_error_structure_consistency(self, client, http_status):
        """
        Feature: truthforge, Property 33: API Error Response Structure
        
        For any HTTP error status code, all error responses with that status must
        have consistent structure regardless of the endpoint or error type.
        
        This property test verifies structural consistency across all error types.
        """
        # Map status codes to endpoints that produce them
        status_to_endpoint = {
            400: ("/api/verify", "POST", {}, {"Authorization": "Bearer test-token-12345"}),
            401: ("/api/verify", "POST", {"action": "test"}, {}),
            404: ("/api/status/nonexistent", "GET", None, {}),
            405: ("/api/verify", "PUT", None, {})
        }
        
        endpoint, method, data, headers = status_to_endpoint[http_status]
        
        # Make request
        if method == "POST":
            response = client.post(endpoint, json=data, headers=headers)
        elif method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "PUT":
            response = client.put(endpoint, headers=headers)
        
        # Verify status code
        assert response.status_code == http_status
        
        # Parse response
        data = json.loads(response.data)
        
        # Property: All error responses must have identical structure
        required_fields = ["error"]
        required_error_fields = ["code", "message", "timestamp"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        for field in required_error_fields:
            assert field in data["error"], f"Missing required error field: {field}"
        
        # Property: Optional 'details' field can be present but must be a dict
        if "details" in data["error"]:
            assert isinstance(data["error"]["details"], dict), \
                "Error details must be a dictionary"


class TestAPIAuthenticationProperties:
    """Property-based tests for API authentication validation."""
    
    @given(
        token=st.one_of(
            st.none(),
            st.text(min_size=0, max_size=100).filter(
                lambda x: x != "test-token-12345" and '\n' not in x and '\r' not in x
            ),
            st.just("")
        )
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_32_api_authentication_validation(self, client, token):
        """
        Feature: truthforge, Property 32: API Authentication Validation
        
        For any API request to protected endpoints, requests without valid 
        authentication tokens shall be rejected with a 401 Unauthorized response.
        
        Validates: Requirements 13.6
        
        This property test verifies that:
        1. Requests without authentication tokens are rejected with 401
        2. Requests with invalid tokens are rejected with 401
        3. Requests with empty tokens are rejected with 401
        4. The error response contains proper structure
        """
        # Test protected endpoint: POST /api/verify
        if token is None:
            # No Authorization header
            response = client.post(
                '/api/verify',
                json={"action": "verify_image"}
            )
        elif token == "":
            # Empty token
            response = client.post(
                '/api/verify',
                json={"action": "verify_image"},
                headers={"Authorization": f"Bearer {token}"}
            )
        else:
            # Invalid token
            response = client.post(
                '/api/verify',
                json={"action": "verify_image"},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        # Property: All invalid auth attempts must return 401
        assert response.status_code == 401, \
            f"Expected 401 for invalid token, got {response.status_code}"
        
        # Property: Response must be valid JSON
        data = json.loads(response.data)
        
        # Property: Response must contain error structure
        assert "error" in data, "Response must contain 'error' field"
        assert "code" in data["error"], "Error must contain 'code' field"
        assert "message" in data["error"], "Error must contain 'message' field"
        assert "timestamp" in data["error"], "Error must contain 'timestamp' field"
        
        # Property: Error code must be authentication-related
        assert data["error"]["code"] in [
            "MISSING_AUTH_TOKEN",
            "INVALID_AUTH_TOKEN",
            "INVALID_AUTH_FORMAT"
        ], f"Error code must be auth-related, got {data['error']['code']}"
    
    @given(
        endpoint=st.sampled_from([
            '/api/verify',
            '/api/history'
        ]),
        method=st.sampled_from(['POST', 'GET'])
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_32_protected_endpoints_require_auth(self, client, endpoint, method):
        """
        Feature: truthforge, Property 32: API Authentication Validation
        
        For any protected endpoint, requests without authentication must be rejected.
        
        This property test verifies that all protected endpoints consistently
        enforce authentication requirements.
        """
        # Skip invalid combinations
        if endpoint == '/api/verify' and method == 'GET':
            return
        if endpoint == '/api/history' and method == 'POST':
            return
        
        # Make request without authentication
        if method == 'POST':
            response = client.post(endpoint, json={"action": "test"})
        else:
            response = client.get(endpoint)
        
        # Property: All protected endpoints must return 401 without auth
        assert response.status_code == 401, \
            f"Protected endpoint {method} {endpoint} must return 401 without auth"
        
        # Property: Response must contain error structure
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"]["code"] == "MISSING_AUTH_TOKEN"
    
    @given(
        auth_format=st.one_of(
            st.just("Basic token123"),
            st.just("token123"),
            st.just("bearer token123"),  # lowercase
            st.just("BEARER token123"),  # uppercase
            st.just("Token token123"),
            st.text(min_size=1, max_size=50).filter(
                lambda x: not x.startswith("Bearer ") and len(x.split()) != 2 
                and '\n' not in x and '\r' not in x
            )
        )
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_property_32_invalid_auth_format_rejected(self, client, auth_format):
        """
        Feature: truthforge, Property 32: API Authentication Validation
        
        For any authentication header with invalid format, the request must be
        rejected with 401 and INVALID_AUTH_FORMAT error code.
        
        This property test verifies that only "Bearer <token>" format is accepted.
        """
        response = client.post(
            '/api/verify',
            json={"action": "verify_image"},
            headers={"Authorization": auth_format}
        )
        
        # Property: Invalid format must return 401
        assert response.status_code == 401, \
            f"Invalid auth format '{auth_format}' must return 401"
        
        # Property: Error code must indicate format issue
        data = json.loads(response.data)
        assert "error" in data
        # Could be INVALID_AUTH_FORMAT or INVALID_AUTH_TOKEN depending on parsing
        assert data["error"]["code"] in ["INVALID_AUTH_FORMAT", "INVALID_AUTH_TOKEN"]



class TestSystemStatusEndpoint:
    """Tests for GET /api/status/system endpoint."""
    
    def test_system_status_returns_mock_mode(self, client):
        """Test GET /api/status/system returns system information."""
        response = client.get('/api/status/system')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "mock_mode" in data
        assert data["mock_mode"] is True
        assert "agent_count" in data
    
    def test_system_status_includes_agent_count(self, client, mock_hol_registry):
        """Test GET /api/status/system includes agent count."""
        response = client.get('/api/status/system')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["agent_count"] == 2  # From mock_hol_registry fixture


class TestFrontendIntegration:
    """Tests for frontend integration endpoints."""
    
    def test_verify_with_natural_language_message(self, client, mock_orchestrator):
        """Test POST /api/verify accepts natural language messages."""
        response = client.post(
            '/api/verify',
            json={
                "message": "Verify order #12345",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            headers={"Authorization": "Bearer test-token-12345"}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "request_id" in data
        assert data["status"] == "completed"
        
        # Verify orchestrator was called
        mock_orchestrator.process_request.assert_called_once()
        call_args = mock_orchestrator.process_request.call_args[0][0]
        assert call_args["type"] == "natural_language"
        assert call_args["message"] == "Verify order #12345"
    
    def test_verify_response_includes_natural_language(self, client, mock_orchestrator):
        """Test POST /api/verify returns natural language response."""
        mock_orchestrator.process_request.return_value = {
            "success": True,
            "natural_language_response": "The cargo photo has been verified with an authenticity score of 85.5%",
            "unified_report": {
                "authenticity_score": 85.5,
                "hcs_transaction_id": "0.0.12345@1234567890.123456789"
            }
        }
        
        response = client.post(
            '/api/verify',
            json={"message": "Verify this photo"},
            headers={"Authorization": "Bearer test-token-12345"}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "response" in data
        assert "unified_report" in data
        assert data["unified_report"]["authenticity_score"] == 85.5
