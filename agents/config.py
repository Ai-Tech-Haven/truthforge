"""
TruthForge Configuration Management

This module provides configuration loading and validation for the TruthForge system.
It supports both mock mode (development) and production mode with appropriate
validation for each mode.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List
from dotenv import load_dotenv


@dataclass
class Config:
    """
    Configuration class for TruthForge system.
    
    Loads configuration from environment variables and validates required fields
    based on the operating mode (mock vs production).
    
    Attributes:
        # Hedera Configuration
        hedera_account_id: Hedera account ID (format: 0.0.xxxxx)
        hedera_private_key: Hedera private key (DER encoded)
        hedera_network: Hedera network (testnet or mainnet)
        hcs_topic_id: HCS Topic ID for agent messaging
        hol_registry_endpoint: HOL Registry endpoint URL
        
        # WooCommerce Configuration
        woocommerce_url: WooCommerce store URL
        woocommerce_consumer_key: WooCommerce REST API consumer key
        woocommerce_consumer_secret: WooCommerce REST API consumer secret
        woocommerce_enabled: Enable WooCommerce integration
        woocommerce_webhook_secret: WooCommerce webhook secret for validation
        
        # FedEx Configuration
        fedex_api_key: FedEx API key
        fedex_secret_key: FedEx secret key
        fedex_account_number: FedEx account number
        
        # System Configuration
        mock_mode: Enable mock mode for development (no real API calls)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        api_port: API server port
        max_retries: Maximum retry attempts for failed operations
        timeout_seconds: Request timeout in seconds
        api_auth_token: Optional API authentication token
        debug: Enable debug mode
        
        # Agent Configuration
        agent_stake_amount: HBAR amount for agent staking
        hcs_topic_memo_prefix: Prefix for HCS topic memos
        
        # TruthForge Settings
        max_image_size_mb: Maximum image size in MB
        supported_image_types: List of supported image file types
        deepfake_detection_threshold: Threshold for deepfake detection (0-1)
    """
    
    # Hedera Configuration
    hedera_account_id: str = ""
    hedera_private_key: str = ""
    hedera_network: str = "testnet"
    hcs_topic_id: str = ""
    hol_registry_endpoint: str = "https://hol-registry.testnet.hashgraph.io"
    
    # WooCommerce Configuration
    woocommerce_url: str = ""
    woocommerce_consumer_key: str = ""
    woocommerce_consumer_secret: str = ""
    woocommerce_enabled: bool = False
    woocommerce_webhook_secret: str = ""
    
    # FedEx Configuration
    fedex_api_key: str = ""
    fedex_secret_key: str = ""
    fedex_account_number: str = ""
    
    # System Configuration
    mock_mode: bool = True
    log_level: str = "INFO"
    api_port: int = 5000
    max_retries: int = 3
    timeout_seconds: int = 30
    api_auth_token: Optional[str] = None
    debug: bool = False
    
    # Agent Configuration
    agent_stake_amount: int = 100
    hcs_topic_memo_prefix: str = "HCS-10:TRUTHFORGE:"
    
    # TruthForge Settings
    max_image_size_mb: int = 10
    supported_image_types: List[str] = field(default_factory=lambda: ["jpg", "png", "pdf"])
    deepfake_detection_threshold: float = 0.75
    
    @classmethod
    def load(cls, env_file: str = ".env") -> "Config":
        """
        Load configuration from environment variables.
        
        Reads configuration from the specified .env file and environment variables.
        Validates required fields based on the operating mode.
        
        Args:
            env_file: Path to the .env file (default: ".env")
            
        Returns:
            Config: Configured Config instance
            
        Raises:
            ValueError: If required configuration fields are missing
            FileNotFoundError: If .env file doesn't exist and required vars are missing
        """
        # Load environment variables from .env file (override existing env vars)
        load_dotenv(env_file, override=True)
        
        # Parse supported image types
        image_types_str = os.getenv("SUPPORTED_IMAGE_TYPES", "jpg,png,pdf")
        supported_image_types = [t.strip() for t in image_types_str.split(",")]
        
        # Create config instance with values from environment
        config = cls(
            # Hedera Configuration
            hedera_account_id=os.getenv("HEDERA_ACCOUNT_ID", ""),
            hedera_private_key=os.getenv("HEDERA_PRIVATE_KEY", ""),
            hedera_network=os.getenv("HEDERA_NETWORK", "testnet"),
            hcs_topic_id=os.getenv("HCS_TOPIC_ID", ""),
            hol_registry_endpoint=os.getenv("HOL_REGISTRY_ENDPOINT", 
                                           "https://hol-registry.testnet.hashgraph.io"),
            
            # WooCommerce Configuration
            woocommerce_url=os.getenv("WOOCOMMERCE_STORE_URL", 
                                     os.getenv("WOOCOMMERCE_URL", "")),
            woocommerce_consumer_key=os.getenv("WOOCOMMERCE_CONSUMER_KEY", ""),
            woocommerce_consumer_secret=os.getenv("WOOCOMMERCE_CONSUMER_SECRET", ""),
            woocommerce_enabled=os.getenv("WOOCOMMERCE_ENABLED", "false").lower() == "true",
            woocommerce_webhook_secret=os.getenv("WOOCOMMERCE_WEBHOOK_SECRET", ""),
            
            # FedEx Configuration
            fedex_api_key=os.getenv("FEDEX_API_KEY", ""),
            fedex_secret_key=os.getenv("FEDEX_SECRET_KEY", ""),
            fedex_account_number=os.getenv("FEDEX_ACCOUNT_NUMBER", ""),
            
            # System Configuration
            mock_mode=os.getenv("MOCK_MODE", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            api_port=int(os.getenv("PORT", os.getenv("API_PORT", "5000"))),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "30")),
            api_auth_token=os.getenv("API_AUTH_TOKEN"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            
            # Agent Configuration
            agent_stake_amount=int(os.getenv("AGENT_STAKE_AMOUNT", "100")),
            hcs_topic_memo_prefix=os.getenv("HCS_TOPIC_MEMO_PREFIX", "HCS-10:TRUTHFORGE:"),
            
            # TruthForge Settings
            max_image_size_mb=int(os.getenv("MAX_IMAGE_SIZE_MB", "10")),
            supported_image_types=supported_image_types,
            deepfake_detection_threshold=float(os.getenv("DEEPFAKE_DETECTION_THRESHOLD", "0.75")),
        )
        
        # Validate configuration
        config.validate()
        
        return config
    
    def validate(self) -> None:
        """
        Validate configuration based on operating mode.
        
        In production mode, validates that all required API credentials are present.
        In mock mode, allows operation without real API credentials.
        
        Raises:
            ValueError: If required configuration fields are missing for the current mode
        """
        errors = []
        
        # Validate system configuration (always required)
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(
                f"Invalid LOG_LEVEL: {self.log_level}. "
                "Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
            )
        
        if self.api_port < 1 or self.api_port > 65535:
            errors.append(f"Invalid API_PORT: {self.api_port}. Must be between 1 and 65535")
        
        if self.max_retries < 0:
            errors.append(f"Invalid MAX_RETRIES: {self.max_retries}. Must be >= 0")
        
        if self.timeout_seconds < 1:
            errors.append(f"Invalid TIMEOUT_SECONDS: {self.timeout_seconds}. Must be >= 1")
        
        if self.hedera_network not in ["testnet", "mainnet"]:
            errors.append(
                f"Invalid HEDERA_NETWORK: {self.hedera_network}. "
                "Must be 'testnet' or 'mainnet'"
            )
        
        # Validate TruthForge settings
        if self.max_image_size_mb < 1:
            errors.append(f"Invalid MAX_IMAGE_SIZE_MB: {self.max_image_size_mb}. Must be >= 1")
        
        if not (0 <= self.deepfake_detection_threshold <= 1):
            errors.append(
                f"Invalid DEEPFAKE_DETECTION_THRESHOLD: {self.deepfake_detection_threshold}. "
                "Must be between 0 and 1"
            )
        
        if not self.supported_image_types:
            errors.append("SUPPORTED_IMAGE_TYPES cannot be empty")
        
        # In production mode, validate required credentials
        if not self.mock_mode:
            # Hedera credentials are required in production
            if not self.hedera_account_id:
                errors.append(
                    "HEDERA_ACCOUNT_ID is required in production mode. "
                    "Set MOCK_MODE=true for development without credentials."
                )
            
            if not self.hedera_private_key:
                errors.append(
                    "HEDERA_PRIVATE_KEY is required in production mode. "
                    "Set MOCK_MODE=true for development without credentials."
                )
            
            if not self.hcs_topic_id:
                errors.append(
                    "HCS_TOPIC_ID is required in production mode. "
                    "Set MOCK_MODE=true for development without credentials."
                )
            
            # Validate Hedera account ID format
            if self.hedera_account_id and not self._is_valid_hedera_account_id(self.hedera_account_id):
                errors.append(
                    f"Invalid HEDERA_ACCOUNT_ID format: {self.hedera_account_id}. "
                    "Expected format: 0.0.xxxxx"
                )
            
            # Validate HCS topic ID format
            if self.hcs_topic_id and not self._is_valid_hedera_account_id(self.hcs_topic_id):
                errors.append(
                    f"Invalid HCS_TOPIC_ID format: {self.hcs_topic_id}. "
                    "Expected format: 0.0.xxxxx"
                )
        
        # Raise all validation errors together
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
            raise ValueError(error_message)
    
    def _is_valid_hedera_account_id(self, account_id: str) -> bool:
        """
        Validate Hedera account ID format.
        
        Args:
            account_id: Account ID to validate
            
        Returns:
            bool: True if valid format (0.0.xxxxx), False otherwise
        """
        parts = account_id.split(".")
        if len(parts) != 3:
            return False
        
        try:
            # All parts should be numeric
            for part in parts:
                int(part)
            return True
        except ValueError:
            return False
    
    def __repr__(self) -> str:
        """
        String representation of Config with sensitive data masked.
        
        Returns:
            str: Safe string representation
        """
        return (
            f"Config("
            f"hedera_account_id='{self.hedera_account_id}', "
            f"hedera_network='{self.hedera_network}', "
            f"mock_mode={self.mock_mode}, "
            f"log_level='{self.log_level}', "
            f"api_port={self.api_port})"
        )
