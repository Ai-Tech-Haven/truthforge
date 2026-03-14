"""
Unit tests for VerificationComplianceAgent

Replaces the old reality_engine tests. This agent handles all document
validation and compliance checks in the TruthForge platform.
"""

import pytest
import math
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from dataclasses import dataclass, field
from typing import List, Optional

from agents.verification_compliance_agent import (
    VerificationComplianceAgent,
    AnalysisResult,
    ExifReport,
    LightingReport,
    ArtifactReport,
    MetadataReport,
    BOLData,
    VerificationReport,
)
from agents.config import Config
from agents.hedera_client import MockHederaClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_config(mock_mode: bool = True) -> Config:
    """Build a minimal Config suitable for tests."""
    return Config(
        mock_mode=mock_mode,
        log_level="INFO",
        hcs_topic_id="0.0.12345",
        hedera_account_id="0.0.99999",
        hedera_private_key="mock-private-key",
        hedera_network="testnet",
    )


def make_agent() -> VerificationComplianceAgent:
    """Build a VerificationComplianceAgent wired to mock dependencies."""
    config = make_config(mock_mode=True)
    hedera_client = MockHederaClient(config)
    hedera_client.authenticate()
    return VerificationComplianceAgent(
        agent_id="truthforge-verify-001",
        capabilities=["document_verification", "image_analysis", "compliance_check"],
        hcs_topic_id="0.0.12345",
        config=config,
        hedera_client=hedera_client,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def agent():
    return make_agent()


@pytest.fixture
def sample_image_data():
    """Minimal valid JPEG bytes for testing."""
    return (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
        b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x7f\xff\xd9'
    )


@pytest.fixture
def sample_bol_data():
    """Sample Bill of Lading bytes for testing."""
    return b"BILL OF LADING\nShipper: Test Corp\nConsignee: Port Authority\nWeight: 1000kg"


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestAgentInitialization:

    def test_agent_id_is_correct(self, agent):
        assert agent.agent_id == "truthforge-verify-001"

    def test_agent_has_required_capabilities(self, agent):
        caps = agent.capabilities
        assert any("verif" in c.lower() for c in caps)

    def test_requests_processed_starts_at_zero(self, agent):
        assert agent.requests_processed == 0


# ---------------------------------------------------------------------------
# Image Analysis
# ---------------------------------------------------------------------------

class TestImageAnalysis:

    def test_analyze_image_returns_analysis_result(self, agent, sample_image_data):
        result = agent.analyze_image(sample_image_data, image_id="img-001")
        assert isinstance(result, AnalysisResult)

    def test_authenticity_score_in_valid_range(self, agent, sample_image_data):
        result = agent.analyze_image(sample_image_data, image_id="img-001")
        assert 0 <= result.authenticity_score <= 100

    def test_all_four_layer_reports_present(self, agent, sample_image_data):
        result = agent.analyze_image(sample_image_data, image_id="img-001")
        assert isinstance(result.exif_report, ExifReport)
        assert isinstance(result.lighting_report, LightingReport)
        assert isinstance(result.artifact_report, ArtifactReport)
        assert isinstance(result.metadata_report, MetadataReport)

    def test_all_confidence_scores_in_range(self, agent, sample_image_data):
        result = agent.analyze_image(sample_image_data, image_id="img-001")
        for score in [
            result.exif_report.confidence_score,
            result.lighting_report.confidence_score,
            result.artifact_report.confidence_score,
            result.metadata_report.confidence_score,
        ]:
            assert 0 <= score <= 100

    def test_overall_assessment_is_non_empty_string(self, agent, sample_image_data):
        result = agent.analyze_image(sample_image_data, image_id="img-001")
        assert isinstance(result.overall_assessment, str)
        assert len(result.overall_assessment) > 0

    def test_confidence_level_in_valid_range(self, agent, sample_image_data):
        result = agent.analyze_image(sample_image_data, image_id="img-001")
        assert 0 <= result.confidence_level <= 100

    def test_timestamp_is_datetime(self, agent, sample_image_data):
        result = agent.analyze_image(sample_image_data, image_id="img-001")
        assert isinstance(result.timestamp, datetime)

    def test_image_id_preserved_in_result(self, agent, sample_image_data):
        result = agent.analyze_image(sample_image_data, image_id="img-test-999")
        assert result.image_id == "img-test-999"

    def test_hcs_transaction_id_present(self, agent, sample_image_data):
        result = agent.analyze_image(sample_image_data, image_id="img-001")
        assert isinstance(result.hcs_transaction_id, str)
        assert len(result.hcs_transaction_id) > 0


# ---------------------------------------------------------------------------
# Individual Analysis Layers
# ---------------------------------------------------------------------------

class TestAnalysisLayers:

    def test_exif_analysis_returns_exif_report(self, agent, sample_image_data):
        report = agent.exif_analysis(sample_image_data)
        assert isinstance(report, ExifReport)
        assert isinstance(report.has_exif_data, bool)
        assert 0 <= report.confidence_score <= 100

    def test_lighting_analysis_returns_lighting_report(self, agent, sample_image_data):
        report = agent.lighting_analysis(sample_image_data)
        assert isinstance(report, LightingReport)
        assert 0 <= report.lighting_consistency <= 100
        assert 0 <= report.confidence_score <= 100

    def test_ai_artifact_detection_returns_artifact_report(self, agent, sample_image_data):
        report = agent.ai_artifact_detection(sample_image_data)
        assert isinstance(report, ArtifactReport)
        assert isinstance(report.ai_artifacts_detected, bool)
        assert 0 <= report.generation_probability <= 100
        assert 0 <= report.confidence_score <= 100

    def test_metadata_verification_returns_metadata_report(self, agent, sample_image_data):
        report = agent.metadata_verification(sample_image_data)
        assert isinstance(report, MetadataReport)
        assert isinstance(report.metadata_consistent, bool)
        assert report.file_size > 0
        assert 0 <= report.confidence_score <= 100


# ---------------------------------------------------------------------------
# Authenticity Score Computation
# ---------------------------------------------------------------------------

class TestAuthenticityScore:

    def test_compute_score_returns_float_in_range(self, agent):
        reports = [
            ExifReport(
                has_exif_data=True, camera_make=None, camera_model=None,
                capture_timestamp=None, gps_coordinates=None, software_used=None,
                tampering_indicators=[], confidence_score=80.0,
            ),
            LightingReport(
                lighting_consistency=85.0, shadow_analysis={}, reflection_analysis={},
                color_temperature=5500.0, anomalies_detected=[], confidence_score=85.0,
            ),
            ArtifactReport(
                ai_artifacts_detected=False, artifact_locations=[], artifact_types=[],
                generation_probability=5.0, confidence_score=90.0,
            ),
            MetadataReport(
                metadata_consistent=True, file_format="JPEG", file_size=1000,
                dimensions=(100, 100), compression_artifacts=False,
                edit_history=[], confidence_score=95.0,
            ),
        ]
        score = agent.compute_authenticity_score(reports)
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_compute_score_empty_reports_returns_zero(self, agent):
        score = agent.compute_authenticity_score([])
        assert score == 0.0

    def test_score_is_not_nan_or_inf(self, agent, sample_image_data):
        result = agent.analyze_image(sample_image_data, image_id="img-001")
        assert not math.isnan(result.authenticity_score)
        assert not math.isinf(result.authenticity_score)


# ---------------------------------------------------------------------------
# Document Verification (Bill of Lading)
# ---------------------------------------------------------------------------

class TestDocumentVerification:

    def test_extract_bol_fields_returns_bol_data(self, agent, sample_bol_data):
        bol = agent.extract_bol_fields(sample_bol_data)
        assert isinstance(bol, BOLData)

    def test_generate_verification_report_returns_report(self, agent, sample_bol_data):
        bol = agent.extract_bol_fields(sample_bol_data)
        report = agent.generate_verification_report(bol)
        assert isinstance(report, VerificationReport)

    def test_verification_report_has_status(self, agent, sample_bol_data):
        bol = agent.extract_bol_fields(sample_bol_data)
        report = agent.generate_verification_report(bol)
        assert hasattr(report, "verification_status")
        assert report.verification_status in ("PASS", "FAIL", "verified", "pending", "failed")


# ---------------------------------------------------------------------------
# process_request dispatch
# ---------------------------------------------------------------------------

class TestProcessRequest:

    def test_process_image_request_returns_success(self, agent, sample_image_data):
        response = agent.process_request({
            "type": "image_analysis",
            "image_data": sample_image_data,
            "image_id": "img-dispatch-001",
        })
        assert response.get("success") is True

    def test_process_document_request_returns_success(self, agent, sample_bol_data):
        response = agent.process_request({
            "type": "document_verification",
            "document_data": sample_bol_data,
        })
        assert response.get("success") is True

    def test_process_request_unknown_type_returns_error(self, agent):
        response = agent.process_request({"type": "unknown_type"})
        assert response.get("success") is False

    def test_process_request_increments_counter(self, agent, sample_image_data):
        before = agent.requests_processed
        agent.process_request({
            "type": "image_analysis",
            "image_data": sample_image_data,
            "image_id": "img-counter-001",
        })
        assert agent.requests_processed == before + 1


# ---------------------------------------------------------------------------
# Property-Based Tests
# ---------------------------------------------------------------------------

from hypothesis import given, strategies as st, settings


class TestVerificationProperties:
    """Property-based tests — universal invariants for all valid inputs."""

    @given(image_data=st.binary(min_size=50, max_size=5000))
    @settings(max_examples=50, deadline=None)
    def test_property_all_four_layers_always_execute(self, image_data):
        """All four analysis layers must produce reports for any binary input."""
        agent = make_agent()
        result = agent.analyze_image(image_data, image_id="prop-test")
        assert result.exif_report is not None
        assert result.lighting_report is not None
        assert result.artifact_report is not None
        assert result.metadata_report is not None

    @given(image_data=st.binary(min_size=50, max_size=5000))
    @settings(max_examples=50, deadline=None)
    def test_property_authenticity_score_always_in_bounds(self, image_data):
        """Authenticity score must always be in [0, 100]."""
        agent = make_agent()
        result = agent.analyze_image(image_data, image_id="prop-test")
        assert 0 <= result.authenticity_score <= 100
        assert not math.isnan(result.authenticity_score)
        assert not math.isinf(result.authenticity_score)

    @given(image_data=st.binary(min_size=50, max_size=5000))
    @settings(max_examples=50, deadline=None)
    def test_property_hcs_transaction_id_always_present(self, image_data):
        """Every analysis must produce a non-empty HCS transaction ID."""
        agent = make_agent()
        result = agent.analyze_image(image_data, image_id="prop-test")
        assert isinstance(result.hcs_transaction_id, str)
        assert len(result.hcs_transaction_id) > 0

    @given(image_data=st.binary(min_size=50, max_size=5000))
    @settings(max_examples=50, deadline=None)
    def test_property_confidence_level_always_in_bounds(self, image_data):
        """Confidence level must always be in [0, 100]."""
        agent = make_agent()
        result = agent.analyze_image(image_data, image_id="prop-test")
        assert 0 <= result.confidence_level <= 100
