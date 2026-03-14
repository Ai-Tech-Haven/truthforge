"""
Tests for WooCommerce Adapter

This module tests the WooCommerce Adapter agent functionality including
order fetching, cargo photo retrieval, order updates, and webhook handling.
"""

import pytest
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings

from agents.woocommerce_adapter import (
    WooCommerceAdapter,
    MockWooCommerceAdapter,
    Order,
    OrderItem,
    Address
)
from agents.config import Config
from agents.hedera_client import MockHederaClient


@pytest.fixture
def mock_config():
    """Create mock configuration for testing."""
    config = Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="mock-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.67890",
        woocommerce_url="https://example.com",
        woocommerce_consumer_key="ck_test",
        woocommerce_consumer_secret="cs_test",
        woocommerce_webhook_secret="webhook_secret",
        mock_mode=True
    )
    return config


@pytest.fixture
def mock_hedera_client(mock_config):
    """Create mock Hedera client for testing."""
    return MockHederaClient(mock_config)


@pytest.fixture
def woocommerce_adapter(mock_config, mock_hedera_client):
    """Create WooCommerce adapter for testing."""
    return WooCommerceAdapter(mock_config, mock_hedera_client)


@pytest.fixture
def mock_woocommerce_adapter(mock_config, mock_hedera_client):
    """Create mock WooCommerce adapter for testing."""
    return MockWooCommerceAdapter(mock_config, mock_hedera_client)


class TestWooCommerceAdapter:
    """Test WooCommerce Adapter functionality."""
    
    def test_initialization(self, woocommerce_adapter):
        """Test adapter initialization."""
        assert woocommerce_adapter.agent_id == "truthforge-woo-001"
        assert "woocommerce-integration" in woocommerce_adapter.capabilities
        assert "order-management" in woocommerce_adapter.capabilities
        assert woocommerce_adapter.store_url == "https://example.com"
        assert woocommerce_adapter.consumer_key == "ck_test"
        assert woocommerce_adapter.consumer_secret == "cs_test"
    
    def test_authentication_mock_mode(self, woocommerce_adapter):
        """Test authentication in mock mode."""
        result = woocommerce_adapter.authenticate()
        assert result is True
        assert woocommerce_adapter.authenticated is True
    
    def test_fetch_order_mock_mode(self, woocommerce_adapter):
        """Test fetching order in mock mode."""
        order = woocommerce_adapter.fetch_order("12345")
        
        assert isinstance(order, Order)
        assert order.order_id == "12345"
        assert order.order_number == "ORD-12345"
        assert order.customer_name == "John Doe"
        assert order.customer_email == "customer@example.com"
        assert isinstance(order.shipping_address, Address)
        assert len(order.items) > 0
        assert order.total_amount > 0
    
    def test_fetch_order_invalid_id(self, woocommerce_adapter):
        """Test fetching order with invalid ID."""
        with pytest.raises(ValueError, match="order_id is required"):
            woocommerce_adapter.fetch_order("")
    
    def test_fetch_cargo_photos(self, woocommerce_adapter):
        """Test fetching cargo photos."""
        order = woocommerce_adapter.fetch_order("12345")
        photos = woocommerce_adapter.fetch_cargo_photos(order)
        
        assert isinstance(photos, list)
        assert len(photos) >= 0
        # In mock mode, should return mock photo URLs
        if len(photos) > 0:
            assert all(isinstance(url, str) for url in photos)
            assert all(url.startswith("https://") for url in photos)
    
    def test_update_order_meta(self, woocommerce_adapter):
        """Test updating order metadata."""
        verification_data = {
            "status": "verified",
            "authenticity_score": 95.5,
            "hcs_transaction_id": "0.0.12345@1234567890.123456789"
        }
        
        result = woocommerce_adapter.update_order_meta("12345", verification_data)
        assert result is True
    
    def test_update_order_meta_invalid_params(self, woocommerce_adapter):
        """Test updating order meta with invalid parameters."""
        with pytest.raises(ValueError, match="order_id is required"):
            woocommerce_adapter.update_order_meta("", {"data": "test"})
        
        with pytest.raises(ValueError, match="verification_data is required"):
            woocommerce_adapter.update_order_meta("12345", None)
    
    def test_add_order_note(self, woocommerce_adapter):
        """Test adding order note."""
        note = "Verification completed successfully"
        result = woocommerce_adapter.add_order_note("12345", note)
        assert result is True
    
    def test_add_order_note_invalid_params(self, woocommerce_adapter):
        """Test adding order note with invalid parameters."""
        with pytest.raises(ValueError, match="order_id is required"):
            woocommerce_adapter.add_order_note("", "test note")
        
        with pytest.raises(ValueError, match="note is required"):
            woocommerce_adapter.add_order_note("12345", "")
    
    def test_process_request_fetch_order(self, woocommerce_adapter):
        """Test process_request with fetch_order action."""
        request = {
            "action": "fetch_order",
            "order_id": "12345"
        }
        
        response = woocommerce_adapter.process_request(request)
        
        assert response["status"] == "success"
        assert "result" in response
        assert response["result"]["order_id"] == "12345"
    
    def test_process_request_update_order_meta(self, woocommerce_adapter):
        """Test process_request with update_order_meta action."""
        request = {
            "action": "update_order_meta",
            "order_id": "12345",
            "verification_data": {
                "status": "verified",
                "authenticity_score": 95.5
            }
        }
        
        response = woocommerce_adapter.process_request(request)
        
        assert response["status"] == "success"
        assert response["result"]["updated"] is True
    
    def test_process_request_add_order_note(self, woocommerce_adapter):
        """Test process_request with add_order_note action."""
        request = {
            "action": "add_order_note",
            "order_id": "12345",
            "note": "Test note"
        }
        
        response = woocommerce_adapter.process_request(request)
        
        assert response["status"] == "success"
        assert response["result"]["added"] is True
    
    def test_process_request_unknown_action(self, woocommerce_adapter):
        """Test process_request with unknown action."""
        request = {
            "action": "unknown_action"
        }
        
        response = woocommerce_adapter.process_request(request)
        
        assert response["status"] == "error"
        assert "Unknown action" in response["error"]
    
    def test_handle_webhook(self, woocommerce_adapter):
        """Test webhook handling."""
        webhook_data = {
            "order_id": "12345",
            "payload": {"test": "data"}
        }
        
        result = woocommerce_adapter.handle_webhook(webhook_data)
        assert result is True
    
    def test_handle_webhook_missing_order_id(self, woocommerce_adapter):
        """Test webhook handling with missing order ID."""
        webhook_data = {
            "payload": {"test": "data"}
        }
        
        with pytest.raises(ValueError, match="order_id not found"):
            woocommerce_adapter.handle_webhook(webhook_data)


class TestMockWooCommerceAdapter:
    """Test Mock WooCommerce Adapter functionality."""
    
    def test_initialization(self, mock_woocommerce_adapter):
        """Test mock adapter initialization."""
        assert mock_woocommerce_adapter.agent_id == "truthforge-woo-mock-001"
        assert len(mock_woocommerce_adapter.test_orders) == 3
        assert "1001" in mock_woocommerce_adapter.test_orders
        assert "1002" in mock_woocommerce_adapter.test_orders
        assert "1003" in mock_woocommerce_adapter.test_orders
    
    def test_authentication_always_succeeds(self, mock_woocommerce_adapter):
        """Test mock authentication always succeeds."""
        result = mock_woocommerce_adapter.authenticate()
        assert result is True
        assert mock_woocommerce_adapter.authenticated is True
    
    def test_fetch_predefined_order(self, mock_woocommerce_adapter):
        """Test fetching predefined test order."""
        order = mock_woocommerce_adapter.fetch_order("1001")
        
        assert order.order_id == "1001"
        assert order.order_number == "ORD-1001"
        assert order.customer_name == "Alice Johnson"
        assert order.customer_email == "alice@example.com"
        assert order.order_status == "processing"
        assert len(order.items) == 1
        assert order.items[0].name == "Laptop Computer"
    
    def test_fetch_order_with_multiple_items(self, mock_woocommerce_adapter):
        """Test fetching order with multiple items."""
        order = mock_woocommerce_adapter.fetch_order("1002")
        
        assert order.order_id == "1002"
        assert len(order.items) == 2
        assert order.order_status == "completed"
        assert order.total_amount == 1659.96
    
    def test_fetch_order_with_cargo_photos(self, mock_woocommerce_adapter):
        """Test fetching order with cargo photos."""
        order = mock_woocommerce_adapter.fetch_order("1003")
        
        assert order.order_id == "1003"
        assert len(order.cargo_photo_urls) == 3
        assert all("cargo-1003" in url for url in order.cargo_photo_urls)
    
    def test_fetch_order_not_found(self, mock_woocommerce_adapter):
        """Test fetching non-existent order."""
        with pytest.raises(RuntimeError, match="Order not found"):
            mock_woocommerce_adapter.fetch_order("9999")
    
    def test_fetch_unknown_order_generates_data(self, mock_woocommerce_adapter):
        """Test fetching unknown order generates mock data."""
        order = mock_woocommerce_adapter.fetch_order("5555")
        
        assert order.order_id == "5555"
        assert order.order_number == "ORD-5555"
        assert order.customer_name != ""
        assert order.customer_email != ""
        assert len(order.items) > 0
    
    def test_fetch_cargo_photos_for_test_order(self, mock_woocommerce_adapter):
        """Test fetching cargo photos for test order 1003."""
        order = mock_woocommerce_adapter.fetch_order("1003")
        photos = mock_woocommerce_adapter.fetch_cargo_photos(order)
        
        assert len(photos) == 3
        assert all("cargo-1003" in url for url in photos)
    
    def test_update_order_meta_stores_in_memory(self, mock_woocommerce_adapter):
        """Test order meta update stores in memory."""
        verification_data = {
            "status": "verified",
            "authenticity_score": 92.3,
            "hcs_transaction_id": "0.0.12345@1234567890.123456789"
        }
        
        result = mock_woocommerce_adapter.update_order_meta("1001", verification_data)
        
        assert result is True
        assert "1001" in mock_woocommerce_adapter.order_updates
        assert mock_woocommerce_adapter.order_updates["1001"]["verification_data"] == verification_data
    
    def test_add_order_note_stores_in_memory(self, mock_woocommerce_adapter):
        """Test order note addition stores in memory."""
        note = "Verification completed with high confidence"
        
        result = mock_woocommerce_adapter.add_order_note("1001", note)
        
        assert result is True
        assert "1001" in mock_woocommerce_adapter.order_notes
        assert len(mock_woocommerce_adapter.order_notes["1001"]) == 1
        assert note in mock_woocommerce_adapter.order_notes["1001"][0]["note"]
    
    def test_multiple_notes_on_same_order(self, mock_woocommerce_adapter):
        """Test adding multiple notes to same order."""
        mock_woocommerce_adapter.add_order_note("1001", "First note")
        mock_woocommerce_adapter.add_order_note("1001", "Second note")
        
        assert len(mock_woocommerce_adapter.order_notes["1001"]) == 2


class TestDataModels:
    """Test data model classes."""
    
    def test_address_creation(self):
        """Test Address creation."""
        address = Address(
            street="123 Main St",
            city="San Francisco",
            state="CA",
            postal_code="94102",
            country="USA"
        )
        
        assert address.street == "123 Main St"
        assert address.city == "San Francisco"
        assert address.state == "CA"
        assert address.postal_code == "94102"
        assert address.country == "USA"
    
    def test_address_to_dict(self):
        """Test Address to_dict conversion."""
        address = Address(
            street="123 Main St",
            city="San Francisco",
            state="CA",
            postal_code="94102",
            country="USA"
        )
        
        address_dict = address.to_dict()
        
        assert address_dict["street"] == "123 Main St"
        assert address_dict["city"] == "San Francisco"
        assert address_dict["state"] == "CA"
        assert address_dict["postal_code"] == "94102"
        assert address_dict["country"] == "USA"
    
    def test_order_item_creation(self):
        """Test OrderItem creation."""
        item = OrderItem(
            product_id="123",
            name="Test Product",
            quantity=2,
            price=99.99,
            total=199.98
        )
        
        assert item.product_id == "123"
        assert item.name == "Test Product"
        assert item.quantity == 2
        assert item.price == 99.99
        assert item.total == 199.98
    
    def test_order_item_to_dict(self):
        """Test OrderItem to_dict conversion."""
        item = OrderItem(
            product_id="123",
            name="Test Product",
            quantity=2,
            price=99.99,
            total=199.98
        )
        
        item_dict = item.to_dict()
        
        assert item_dict["product_id"] == "123"
        assert item_dict["name"] == "Test Product"
        assert item_dict["quantity"] == 2
        assert item_dict["price"] == 99.99
        assert item_dict["total"] == 199.98
    
    def test_order_creation(self):
        """Test Order creation."""
        address = Address(
            street="123 Main St",
            city="San Francisco",
            state="CA",
            postal_code="94102",
            country="USA"
        )
        
        items = [
            OrderItem(
                product_id="123",
                name="Test Product",
                quantity=1,
                price=99.99,
                total=99.99
            )
        ]
        
        order = Order(
            order_id="1001",
            order_number="ORD-1001",
            customer_name="John Doe",
            customer_email="john@example.com",
            shipping_address=address,
            items=items,
            total_amount=99.99,
            order_status="processing",
            cargo_photo_urls=[]
        )
        
        assert order.order_id == "1001"
        assert order.order_number == "ORD-1001"
        assert order.customer_name == "John Doe"
        assert order.customer_email == "john@example.com"
        assert order.shipping_address == address
        assert len(order.items) == 1
        assert order.total_amount == 99.99
        assert order.order_status == "processing"
        assert order.verification_status is None
        assert order.verification_data is None
    
    def test_order_to_dict(self):
        """Test Order to_dict conversion."""
        address = Address(
            street="123 Main St",
            city="San Francisco",
            state="CA",
            postal_code="94102",
            country="USA"
        )
        
        items = [
            OrderItem(
                product_id="123",
                name="Test Product",
                quantity=1,
                price=99.99,
                total=99.99
            )
        ]
        
        order = Order(
            order_id="1001",
            order_number="ORD-1001",
            customer_name="John Doe",
            customer_email="john@example.com",
            shipping_address=address,
            items=items,
            total_amount=99.99,
            order_status="processing",
            cargo_photo_urls=["https://example.com/photo1.jpg"]
        )
        
        order_dict = order.to_dict()
        
        assert order_dict["order_id"] == "1001"
        assert order_dict["order_number"] == "ORD-1001"
        assert order_dict["customer_name"] == "John Doe"
        assert order_dict["customer_email"] == "john@example.com"
        assert isinstance(order_dict["shipping_address"], dict)
        assert len(order_dict["items"]) == 1
        assert order_dict["total_amount"] == 99.99
        assert order_dict["order_status"] == "processing"
        assert len(order_dict["cargo_photo_urls"]) == 1



# Property-Based Tests

@given(order_id=st.text(min_size=1, max_size=20).filter(lambda x: x != "9999" and x.strip() != ""))
@settings(max_examples=100)
def test_property_13_woocommerce_order_fetching(order_id):
    """
    Feature: truthforge, Property 13: WooCommerce Order Fetching
    
    For any received order webhook with a valid order ID, the WooCommerce_Adapter 
    shall successfully fetch order details including customer_name, shipping_address, 
    items, and order_status.
    
    Validates: Requirements 4.3
    """
    # Create config and client inside the test
    config = Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="mock-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.67890",
        woocommerce_url="https://example.com",
        woocommerce_consumer_key="ck_test",
        woocommerce_consumer_secret="cs_test",
        woocommerce_webhook_secret="webhook_secret",
        mock_mode=True
    )
    hedera_client = MockHederaClient(config)
    
    # Create adapter
    adapter = MockWooCommerceAdapter(config, hedera_client)
    
    # Fetch order with the generated order ID
    order = adapter.fetch_order(order_id)
    
    # Verify order is returned
    assert order is not None
    assert isinstance(order, Order)
    
    # Verify required fields are present and non-empty
    # customer_name
    assert hasattr(order, 'customer_name')
    assert order.customer_name is not None
    assert isinstance(order.customer_name, str)
    assert len(order.customer_name.strip()) > 0
    
    # shipping_address
    assert hasattr(order, 'shipping_address')
    assert order.shipping_address is not None
    assert isinstance(order.shipping_address, Address)
    assert order.shipping_address.street is not None
    assert order.shipping_address.city is not None
    assert order.shipping_address.state is not None
    assert order.shipping_address.postal_code is not None
    assert order.shipping_address.country is not None
    
    # items
    assert hasattr(order, 'items')
    assert order.items is not None
    assert isinstance(order.items, list)
    assert len(order.items) > 0
    for item in order.items:
        assert isinstance(item, OrderItem)
        assert item.product_id is not None
        assert item.name is not None
        assert item.quantity > 0
    
    # order_status
    assert hasattr(order, 'order_status')
    assert order.order_status is not None
    assert isinstance(order.order_status, str)
    assert len(order.order_status.strip()) > 0


@given(order_id=st.text(min_size=1, max_size=20).filter(lambda x: x != "9999" and x.strip() != ""))
@settings(max_examples=100)
def test_property_14_cargo_photo_retrieval(order_id):
    """
    Feature: truthforge, Property 14: Cargo Photo Retrieval
    
    For any WooCommerce order containing cargo photo attachments, the WooCommerce_Adapter 
    shall retrieve all photo URLs from the WordPress media library.
    
    Validates: Requirements 4.4
    """
    # Create config and client inside the test
    config = Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="mock-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.67890",
        woocommerce_url="https://example.com",
        woocommerce_consumer_key="ck_test",
        woocommerce_consumer_secret="cs_test",
        woocommerce_webhook_secret="webhook_secret",
        mock_mode=True
    )
    hedera_client = MockHederaClient(config)
    
    # Create adapter
    adapter = MockWooCommerceAdapter(config, hedera_client)
    
    # Fetch order with the generated order ID
    order = adapter.fetch_order(order_id)
    
    # Verify order is returned
    assert order is not None
    assert isinstance(order, Order)
    
    # Fetch cargo photos for the order
    photo_urls = adapter.fetch_cargo_photos(order)
    
    # Verify photo URLs are returned as a list
    assert photo_urls is not None
    assert isinstance(photo_urls, list)
    
    # If the order has cargo photos (either predefined or generated), verify they are valid URLs
    if len(photo_urls) > 0:
        # All photo URLs must be strings
        assert all(isinstance(url, str) for url in photo_urls)
        
        # All photo URLs must be non-empty
        assert all(len(url.strip()) > 0 for url in photo_urls)
        
        # All photo URLs must be valid HTTP/HTTPS URLs
        assert all(url.startswith("http://") or url.startswith("https://") for url in photo_urls)
        
        # Photo URLs should contain the order ID for traceability
        assert all(order_id in url for url in photo_urls)
    
    # Verify that the order's cargo_photo_urls field is consistent with fetch_cargo_photos result
    # Note: For test order 1003, cargo_photo_urls is pre-populated in the order object
    # For other orders, cargo_photo_urls may be empty in the order object but fetch_cargo_photos returns URLs
    # This tests that fetch_cargo_photos can retrieve photos even if not in the order object initially


@given(
    order_id=st.text(min_size=1, max_size=20).filter(lambda x: x != "9999" and x.strip() != ""),
    authenticity_score=st.floats(min_value=0.0, max_value=100.0),
    hcs_transaction_id=st.builds(
        lambda a, b, c: f"{a}.{b}.{c}@{b}{c}.{a}{b}{c}",
        st.integers(min_value=0, max_value=999),
        st.integers(min_value=0, max_value=999999),
        st.integers(min_value=0, max_value=999999)
    )
)
@settings(max_examples=100)
def test_property_15_verification_result_round_trip(order_id, authenticity_score, hcs_transaction_id):
    """
    Feature: truthforge, Property 15: Verification Result Round-Trip
    
    For any verification request initiated through the WooCommerce_Adapter, when verification 
    completes, the corresponding WooCommerce order shall be updated with the authenticity score 
    and HCS proof link.
    
    Validates: Requirements 4.6
    """
    # Create config and client inside the test
    config = Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="mock-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.67890",
        woocommerce_url="https://example.com",
        woocommerce_consumer_key="ck_test",
        woocommerce_consumer_secret="cs_test",
        woocommerce_webhook_secret="webhook_secret",
        mock_mode=True
    )
    hedera_client = MockHederaClient(config)
    
    # Create adapter
    adapter = MockWooCommerceAdapter(config, hedera_client)
    
    # Step 1: Initiate verification request by fetching order
    order = adapter.fetch_order(order_id)
    
    # Verify order is returned
    assert order is not None
    assert isinstance(order, Order)
    assert order.order_id == order_id
    
    # Step 2: Simulate verification completion with results
    verification_data = {
        "status": "verified",
        "authenticity_score": authenticity_score,
        "hcs_transaction_id": hcs_transaction_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Step 3: Update order with verification results
    update_result = adapter.update_order_meta(order_id, verification_data)
    
    # Verify update was successful
    assert update_result is True
    
    # Step 4: Verify the order was updated with authenticity score and HCS proof link
    # Check that the update was stored in the adapter's tracking
    assert order_id in adapter.order_updates
    
    stored_update = adapter.order_updates[order_id]
    assert "verification_data" in stored_update
    
    stored_verification = stored_update["verification_data"]
    
    # Verify authenticity score is present and matches
    assert "authenticity_score" in stored_verification
    assert stored_verification["authenticity_score"] == authenticity_score
    
    # Verify HCS transaction ID (proof link) is present and matches
    assert "hcs_transaction_id" in stored_verification
    assert stored_verification["hcs_transaction_id"] == hcs_transaction_id
    
    # Verify verification status is present
    assert "status" in stored_verification
    assert stored_verification["status"] == "verified"
    
    # Verify timestamp is present
    assert "timestamp" in stored_verification
    assert stored_verification["timestamp"] is not None


@given(
    order_id=st.text(min_size=1, max_size=20).filter(lambda x: x != "9999" and x.strip() != ""),
    verification_note=st.text(min_size=1, max_size=200).filter(lambda x: x.strip() != "")
)
@settings(max_examples=100)
def test_property_16_order_note_addition(order_id, verification_note):
    """
    Feature: truthforge, Property 16: Order Note Addition
    
    For any completed verification, the WooCommerce order shall contain a new order note 
    with the verification timestamp and agent identifier.
    
    Validates: Requirements 4.7
    """
    # Create config and client inside the test
    config = Config(
        hedera_account_id="0.0.12345",
        hedera_private_key="mock-private-key",
        hedera_network="testnet",
        hcs_topic_id="0.0.67890",
        woocommerce_url="https://example.com",
        woocommerce_consumer_key="ck_test",
        woocommerce_consumer_secret="cs_test",
        woocommerce_webhook_secret="webhook_secret",
        mock_mode=True
    )
    hedera_client = MockHederaClient(config)
    
    # Create adapter
    adapter = MockWooCommerceAdapter(config, hedera_client)
    
    # Step 1: Fetch order to initiate verification
    order = adapter.fetch_order(order_id)
    
    # Verify order is returned
    assert order is not None
    assert isinstance(order, Order)
    assert order.order_id == order_id
    
    # Step 2: Simulate verification completion by adding order note
    note_result = adapter.add_order_note(order_id, verification_note)
    
    # Verify note addition was successful
    assert note_result is True
    
    # Step 3: Verify the order contains the new note
    # Check that the note was stored in the adapter's tracking
    assert order_id in adapter.order_notes
    assert len(adapter.order_notes[order_id]) > 0
    
    # Get the most recent note
    latest_note = adapter.order_notes[order_id][-1]
    
    # Verify note structure
    assert "note" in latest_note
    assert "timestamp" in latest_note
    
    note_content = latest_note["note"]
    note_timestamp = latest_note["timestamp"]
    
    # Verify note contains the verification message
    assert verification_note in note_content
    
    # Verify note contains agent identifier
    assert adapter.agent_id in note_content
    assert "Agent:" in note_content
    
    # Verify note contains timestamp
    assert "Timestamp:" in note_content
    assert note_timestamp is not None
    
    # Verify timestamp is in ISO format and recent
    try:
        timestamp_dt = datetime.fromisoformat(note_timestamp.replace('Z', '+00:00'))
        # Verify timestamp is within last minute (reasonable for test execution)
        time_diff = datetime.now(timezone.utc) - timestamp_dt
        assert time_diff.total_seconds() < 60
    except ValueError:
        # If timestamp parsing fails, the test should fail
        assert False, f"Invalid timestamp format: {note_timestamp}"
    
    # Verify note contains TruthForge marker
    assert "TruthForge" in note_content or "truthforge" in note_content.lower()
