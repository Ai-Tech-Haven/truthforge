"""
Integration tests for FedEx Adapter with Document Verifier.

This module tests the integration between FedExAdapter and DocumentVerifier
to ensure shipment data can be queried and used for document verification.
"""

import pytest
from datetime import datetime, timezone
from agents.fedex_adapter import MockFedExAdapter
from agents.document_verifier import DocumentVerifier, BOLData, Address
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
        mock_mode=True
    )


@pytest.fixture
def hedera_client(config):
    """Create mock Hedera client"""
    return MockHederaClient(config)


@pytest.fixture
def fedex_adapter(config, hedera_client):
    """Create MockFedExAdapter instance"""
    return MockFedExAdapter(config, hedera_client)


@pytest.fixture
def document_verifier(config, hedera_client):
    """Create DocumentVerifier instance"""
    return DocumentVerifier(config, hedera_client)


class TestFedExDocumentIntegration:
    """Test integration between FedEx Adapter and Document Verifier"""
    
    def test_query_shipment_and_verify_document(self, fedex_adapter, document_verifier):
        """Test complete workflow: query FedEx -> verify BOL"""
        # Step 1: Query shipment data from FedEx
        tracking_number = "123456789012"
        shipment_data = fedex_adapter.query_shipment(tracking_number)
        
        assert shipment_data.tracking_number == tracking_number
        assert shipment_data.origin_address.city == "Memphis"
        
        # Step 2: Create matching BOL document
        bol_document = {
            "tracking_number": tracking_number,
            "origin_address": {
                "street": "100 FedEx Pkwy",
                "city": "Memphis",
                "state": "TN",
                "postal_code": "38125",
                "country": "USA"
            },
            "destination_address": {
                "street": "789 Main St",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94102",
                "country": "USA"
            },
            "shipper_name": "Test Shipper",
            "consignee_name": "Test Consignee",
            "cargo_description": "Electronics - Smartphone",
            "weight": 15.5,
            "declared_value": 500.0,
            "shipment_date": "2026-02-20T08:30:00Z",
            "expected_delivery": "2026-02-24T17:00:00Z"
        }
        
        # Step 3: Extract BOL fields
        bol_data = document_verifier.extract_bol_fields(bol_document)
        
        assert bol_data.tracking_number == tracking_number
        
        # Step 4: Cross-reference BOL with shipment data
        comparison = document_verifier.cross_reference_shipment(bol_data, shipment_data)
        
        assert comparison["tracking_number_match"] is True
        assert comparison["origin_match"] is True
        assert comparison["destination_match"] is True
        assert comparison["weight_match"] is True
        
        # Step 5: Generate verification report
        discrepancies = document_verifier.flag_discrepancies(comparison)
        report = document_verifier.generate_verification_report(
            bol_data=bol_data,
            shipment_data=shipment_data,
            discrepancies=discrepancies
        )
        
        assert report.verification_status == "PASS"
        assert report.confidence_level == 100.0
        assert len(report.discrepancies) == 0
    
    def test_query_shipment_and_detect_discrepancies(self, fedex_adapter, document_verifier):
        """Test workflow with mismatched BOL and shipment data"""
        # Step 1: Query shipment data from FedEx
        tracking_number = "123456789012"
        shipment_data = fedex_adapter.query_shipment(tracking_number)
        
        # Step 2: Create BOL with mismatched data
        bol_document = {
            "tracking_number": tracking_number,
            "origin_address": {
                "street": "Wrong Address",
                "city": "Chicago",  # Wrong city
                "state": "IL",
                "postal_code": "60601",
                "country": "USA"
            },
            "destination_address": {
                "street": "789 Main St",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94102",
                "country": "USA"
            },
            "shipper_name": "Test Shipper",
            "consignee_name": "Test Consignee",
            "cargo_description": "Electronics - Smartphone",
            "weight": 50.0,  # Wrong weight
            "declared_value": 500.0,
            "shipment_date": "2026-02-20T08:30:00Z",
            "expected_delivery": "2026-02-24T17:00:00Z"
        }
        
        # Step 3: Extract and verify
        bol_data = document_verifier.extract_bol_fields(bol_document)
        comparison = document_verifier.cross_reference_shipment(bol_data, shipment_data)
        discrepancies = document_verifier.flag_discrepancies(comparison)
        
        # Should detect origin mismatch and weight mismatch
        assert len(discrepancies) > 0
        
        # Check for specific discrepancies
        discrepancy_fields = [d.field_name for d in discrepancies]
        assert "origin_address" in discrepancy_fields
        assert "weight" in discrepancy_fields
        
        # Generate report
        report = document_verifier.generate_verification_report(
            bol_data=bol_data,
            shipment_data=shipment_data,
            discrepancies=discrepancies
        )
        
        assert report.verification_status in ["FAIL", "WARNING"]
        assert report.confidence_level < 100.0
    
    def test_process_request_workflow(self, fedex_adapter, document_verifier):
        """Test using process_request methods for both agents"""
        # Query FedEx through process_request
        fedex_request = {"tracking_number": "999999999999"}
        fedex_response = fedex_adapter.process_request(fedex_request)
        
        assert fedex_response["status"] == "success"
        shipment_data_dict = fedex_response["result"]
        
        # Create BOL document matching the delivered shipment
        bol_document = {
            "tracking_number": "999999999999",
            "origin_address": {
                "street": "200 Warehouse Dr",
                "city": "Chicago",
                "state": "IL",
                "postal_code": "60601",
                "country": "USA"
            },
            "destination_address": {
                "street": "321 Oak Ave",
                "city": "Boston",
                "state": "MA",
                "postal_code": "02101",
                "country": "USA"
            },
            "shipper_name": "Test Shipper",
            "consignee_name": "Test Consignee",
            "cargo_description": "Books - Educational Materials",
            "weight": 8.2,
            "declared_value": 100.0,
            "shipment_date": "2026-02-18T10:00:00Z",
            "expected_delivery": "2026-02-21T14:30:00Z"
        }
        
        # Verify document through process_request
        verifier_request = {
            "bol_document": bol_document,
            "shipment_data": shipment_data_dict
        }
        verifier_response = document_verifier.process_request(verifier_request)
        
        assert verifier_response["status"] == "success"
        result = verifier_response["result"]
        assert result["verification_status"] == "PASS"
        assert result["confidence_level"] == 100.0
    
    def test_error_handling_shipment_not_found(self, fedex_adapter, document_verifier):
        """Test error handling when shipment is not found"""
        # Try to query non-existent shipment
        fedex_request = {"tracking_number": "000000000000"}
        fedex_response = fedex_adapter.process_request(fedex_request)
        
        assert fedex_response["status"] == "error"
        assert "Shipment not found" in fedex_response["error"]
        assert fedex_response["error_code"] == "SHIPMENT_NOT_FOUND"
    
    def test_multiple_shipment_queries(self, fedex_adapter):
        """Test querying multiple shipments"""
        tracking_numbers = ["123456789012", "999999999999", "111111111111"]
        
        for tracking_number in tracking_numbers:
            shipment_data = fedex_adapter.query_shipment(tracking_number)
            
            assert shipment_data.tracking_number == tracking_number
            assert isinstance(shipment_data.origin_address, Address)
            assert isinstance(shipment_data.destination_address, Address)
            assert shipment_data.weight > 0
        
        # All queries should succeed
        assert len(tracking_numbers) == 3
