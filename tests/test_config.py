"""
Unit tests for Config class
"""

import os
import pytest
import tempfile
from agents.config import Config


class TestConfig:
    """Test suite for Config class"""
    
    @pytest.fixture(autouse=True)
    def clear_env_vars(self):
        """Clear environment variables before each test"""
        # Store original env vars
        original_env = os.environ.copy()
        
        # Clear TruthForge-related env vars
        env_vars_to_clear = [
            "HEDERA_ACCOUNT_ID", "HEDERA_PRIVATE_KEY", "HEDERA_NETWORK", 
            "HCS_TOPIC_ID", "HOL_REGISTRY_ENDPOINT",
            "WOOCOMMERCE_STORE_URL", "WOOCOMMERCE_URL", "WOOCOMMERCE_CONSUMER_KEY", 
            "WOOCOMMERCE_CONSUMER_SECRET", "WOOCOMMERCE_ENABLED", "WOOCOMMERCE_WEBHOOK_SECRET",
            "FEDEX_API_KEY", "FEDEX_SECRET_KEY", "FEDEX_ACCOUNT_NUMBER",
            "MOCK_MODE", "LOG_LEVEL", "PORT", "API_PORT", "MAX_RETRIES", 
            "TIMEOUT_SECONDS", "API_AUTH_TOKEN", "DEBUG",
            "AGENT_STAKE_AMOUNT", "HCS_TOPIC_MEMO_PREFIX",
            "MAX_IMAGE_SIZE_MB", "SUPPORTED_IMAGE_TYPES", "DEEPFAKE_DETECTION_THRESHOLD"
        ]
        
        for var in env_vars_to_clear:
            os.environ.pop(var, None)
        
        yield
        
        # Restore original env vars
        os.environ.clear()
        os.environ.update(original_env)
    
    def test_config_load_with_mock_mode(self, tmp_path):
        """Test that Config loads successfully in mock mode without credentials"""
        # Create a temporary .env file with minimal config
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "LOG_LEVEL=INFO\n"
            "PORT=5000\n"
        )
        
        # Load config
        config = Config.load(str(env_file))
        
        # Verify mock mode is enabled
        assert config.mock_mode is True
        assert config.log_level == "INFO"
        assert config.api_port == 5000
        assert config.max_image_size_mb == 10
        assert config.deepfake_detection_threshold == 0.75
        assert "jpg" in config.supported_image_types
    
    def test_config_load_production_mode_requires_hedera_credentials(self, tmp_path):
        """Test that production mode requires Hedera credentials"""
        # Create a temporary .env file with production mode but no credentials
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=false\n"
            "LOG_LEVEL=INFO\n"
        )
        
        # Should raise ValueError due to missing credentials
        with pytest.raises(ValueError) as exc_info:
            Config.load(str(env_file))
        
        assert "HEDERA_ACCOUNT_ID is required in production mode" in str(exc_info.value)
    
    def test_config_load_with_all_fields(self, tmp_path):
        """Test that Config loads all fields correctly"""
        # Create a temporary .env file with all fields
        env_file = tmp_path / ".env"
        env_file.write_text(
            "HEDERA_ACCOUNT_ID=0.0.12345\n"
            "HEDERA_PRIVATE_KEY=test_key\n"
            "HEDERA_NETWORK=testnet\n"
            "HCS_TOPIC_ID=0.0.67890\n"
            "HOL_REGISTRY_ENDPOINT=https://test-hol.com\n"
            "WOOCOMMERCE_STORE_URL=https://test.com\n"
            "WOOCOMMERCE_CONSUMER_KEY=ck_test\n"
            "WOOCOMMERCE_CONSUMER_SECRET=cs_test\n"
            "WOOCOMMERCE_ENABLED=true\n"
            "WOOCOMMERCE_WEBHOOK_SECRET=webhook_secret\n"
            "FEDEX_API_KEY=fedex_key\n"
            "FEDEX_SECRET_KEY=fedex_secret\n"
            "FEDEX_ACCOUNT_NUMBER=123456\n"
            "MOCK_MODE=false\n"
            "LOG_LEVEL=DEBUG\n"
            "PORT=8080\n"
            "MAX_RETRIES=5\n"
            "TIMEOUT_SECONDS=60\n"
            "API_AUTH_TOKEN=test_token\n"
            "DEBUG=true\n"
            "AGENT_STAKE_AMOUNT=200\n"
            "HCS_TOPIC_MEMO_PREFIX=TEST:\n"
            "MAX_IMAGE_SIZE_MB=20\n"
            "SUPPORTED_IMAGE_TYPES=jpg,png,gif\n"
            "DEEPFAKE_DETECTION_THRESHOLD=0.85\n"
        )
        
        # Load config
        config = Config.load(str(env_file))
        
        # Verify all fields
        assert config.hedera_account_id == "0.0.12345"
        assert config.hedera_private_key == "test_key"
        assert config.hedera_network == "testnet"
        assert config.hcs_topic_id == "0.0.67890"
        assert config.hol_registry_endpoint == "https://test-hol.com"
        assert config.woocommerce_url == "https://test.com"
        assert config.woocommerce_consumer_key == "ck_test"
        assert config.woocommerce_consumer_secret == "cs_test"
        assert config.woocommerce_enabled is True
        assert config.woocommerce_webhook_secret == "webhook_secret"
        assert config.fedex_api_key == "fedex_key"
        assert config.fedex_secret_key == "fedex_secret"
        assert config.fedex_account_number == "123456"
        assert config.mock_mode is False
        assert config.log_level == "DEBUG"
        assert config.api_port == 8080
        assert config.max_retries == 5
        assert config.timeout_seconds == 60
        assert config.api_auth_token == "test_token"
        assert config.debug is True
        assert config.agent_stake_amount == 200
        assert config.hcs_topic_memo_prefix == "TEST:"
        assert config.max_image_size_mb == 20
        assert config.supported_image_types == ["jpg", "png", "gif"]
        assert config.deepfake_detection_threshold == 0.85
    
    def test_config_validation_invalid_log_level(self, tmp_path):
        """Test that invalid log level raises ValueError"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "LOG_LEVEL=INVALID\n"
        )
        
        with pytest.raises(ValueError) as exc_info:
            Config.load(str(env_file))
        
        assert "Invalid LOG_LEVEL" in str(exc_info.value)
    
    def test_config_validation_invalid_port(self, tmp_path):
        """Test that invalid port raises ValueError"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "PORT=99999\n"
        )
        
        with pytest.raises(ValueError) as exc_info:
            Config.load(str(env_file))
        
        assert "Invalid API_PORT" in str(exc_info.value)
    
    def test_config_validation_invalid_hedera_network(self, tmp_path):
        """Test that invalid Hedera network raises ValueError"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "HEDERA_NETWORK=invalid\n"
        )
        
        with pytest.raises(ValueError) as exc_info:
            Config.load(str(env_file))
        
        assert "Invalid HEDERA_NETWORK" in str(exc_info.value)
    
    def test_config_validation_invalid_hedera_account_id_format(self, tmp_path):
        """Test that invalid Hedera account ID format raises ValueError"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=false\n"
            "HEDERA_ACCOUNT_ID=invalid_format\n"
            "HEDERA_PRIVATE_KEY=test_key\n"
            "HCS_TOPIC_ID=0.0.67890\n"
        )
        
        with pytest.raises(ValueError) as exc_info:
            Config.load(str(env_file))
        
        assert "Invalid HEDERA_ACCOUNT_ID format" in str(exc_info.value)
    
    def test_config_validation_invalid_image_size(self, tmp_path):
        """Test that invalid image size raises ValueError"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "MAX_IMAGE_SIZE_MB=0\n"
        )
        
        with pytest.raises(ValueError) as exc_info:
            Config.load(str(env_file))
        
        assert "Invalid MAX_IMAGE_SIZE_MB" in str(exc_info.value)
    
    def test_config_validation_invalid_threshold(self, tmp_path):
        """Test that invalid deepfake threshold raises ValueError"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "DEEPFAKE_DETECTION_THRESHOLD=1.5\n"
        )
        
        with pytest.raises(ValueError) as exc_info:
            Config.load(str(env_file))
        
        assert "Invalid DEEPFAKE_DETECTION_THRESHOLD" in str(exc_info.value)
    
    def test_config_repr_masks_sensitive_data(self, tmp_path):
        """Test that __repr__ doesn't expose sensitive data"""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "HEDERA_PRIVATE_KEY=super_secret_key\n"
        )
        
        config = Config.load(str(env_file))
        repr_str = repr(config)
        
        # Sensitive data should not be in repr
        assert "super_secret_key" not in repr_str
        # But basic info should be present
        assert "mock_mode=True" in repr_str
    
    def test_config_supports_both_port_and_api_port(self, tmp_path):
        """Test that Config supports both PORT and API_PORT env vars"""
        # Test with PORT
        env_file = tmp_path / ".env"
        env_file.write_text(
            "MOCK_MODE=true\n"
            "PORT=8000\n"
        )
        config = Config.load(str(env_file))
        assert config.api_port == 8000
        
        # Test with API_PORT (should be overridden by PORT if both exist)
        env_file.write_text(
            "MOCK_MODE=true\n"
            "PORT=9000\n"
            "API_PORT=8000\n"
        )
        config = Config.load(str(env_file))
        assert config.api_port == 9000
