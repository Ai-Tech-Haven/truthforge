"""
Error Handling and Resilience Utilities for TruthForge

This module provides centralized error handling utilities including:
- Exponential backoff retry logic
- Network error retry decorators
- Blockchain transaction error handling
- Structured error logging

Requirements: 16.2, 16.3, 12.3, 16.4
"""

import time
import logging
import functools
from typing import Callable, Any, Optional, Type, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
) -> Callable:
    """
    Decorator that implements exponential backoff retry logic.
    
    Retries a function call with exponentially increasing delays between attempts.
    The delay follows the pattern: initial_delay * (backoff_factor ** attempt)
    
    Args:
        max_attempts: Maximum number of attempts (including initial call)
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay on each retry (default: 2.0 for exponential)
        max_delay: Maximum delay between retries in seconds
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called before each retry
                  Signature: on_retry(exception, attempt, delay)
    
    Returns:
        Decorated function that implements retry logic
    
    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def fetch_data():
            # This will retry up to 3 times with delays: 1s, 2s, 4s
            return api.get_data()
    
    Requirements: 16.2
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    # Don't retry on last attempt
                    if attempt >= max_attempts - 1:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (backoff_factor ** attempt),
                        max_delay
                    )
                    
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}/{max_attempts}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, attempt + 1, delay)
                        except Exception as callback_error:
                            logger.error(f"Retry callback failed: {callback_error}")
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def retry_network_operation(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    log_attempts: bool = True
) -> Callable:
    """
    Decorator specifically for network operations with retry logic.
    
    Wraps network operations with automatic retry on common network errors.
    Logs each retry attempt for monitoring and debugging.
    
    Args:
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry
        log_attempts: Whether to log each retry attempt
    
    Returns:
        Decorated function with network retry logic
    
    Example:
        @retry_network_operation(max_attempts=3)
        def call_external_api():
            return requests.get('https://api.example.com/data')
    
    Requirements: 16.3
    """
    # Common network-related exceptions
    network_exceptions = (
        ConnectionError,
        TimeoutError,
        OSError,  # Covers network-related OS errors
    )
    
    def on_retry_callback(exception: Exception, attempt: int, delay: float):
        """Log retry attempts for network operations"""
        if log_attempts:
            logger.info(
                f"Network operation retry attempt {attempt}: "
                f"Exception={type(exception).__name__}, "
                f"Message={str(exception)}, "
                f"Delay={delay:.2f}s"
            )
    
    return retry_with_backoff(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        backoff_factor=2.0,
        exceptions=network_exceptions,
        on_retry=on_retry_callback if log_attempts else None
    )


def log_transaction_failure(
    transaction_hash: Optional[str],
    error_message: str,
    account_id: Optional[str] = None,
    additional_details: Optional[dict] = None
) -> None:
    """
    Log blockchain transaction failures with structured details.
    
    Creates a structured log entry for failed blockchain transactions
    including transaction hash, error details, account ID, and timestamp.
    
    Args:
        transaction_hash: Transaction hash if available
        error_message: Error message describing the failure
        account_id: Hedera account ID involved in the transaction
        additional_details: Optional dictionary with additional context
    
    Requirements: 16.4
    """
    log_entry = {
        "event": "transaction_failure",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "transaction_hash": transaction_hash or "N/A",
        "error_message": error_message,
        "account_id": account_id or "N/A"
    }
    
    if additional_details:
        log_entry["details"] = additional_details
    
    logger.error(
        f"Blockchain transaction failed: "
        f"hash={transaction_hash}, "
        f"account={account_id}, "
        f"error={error_message}"
    )
    
    # Log structured data for monitoring systems
    logger.error(f"Transaction failure details: {log_entry}")


def retry_blockchain_transaction(
    max_attempts: int = 3,
    initial_delay: float = 2.0,
    production_mode: bool = True
) -> Callable:
    """
    Decorator for blockchain transaction operations with retry logic.
    
    Implements retry logic specifically for blockchain transactions in Production_Mode.
    Logs transaction failures with detailed information for debugging.
    
    Args:
        max_attempts: Maximum number of transaction attempts
        initial_delay: Initial delay in seconds before first retry
        production_mode: Whether running in production mode (enables retry)
    
    Returns:
        Decorated function with blockchain retry logic
    
    Example:
        @retry_blockchain_transaction(max_attempts=3, production_mode=True)
        def submit_hcs_message(message):
            return hedera_client.submit_message(message)
    
    Requirements: 12.3, 16.4
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # In mock mode, don't retry - just execute once
            if not production_mode:
                return func(*args, **kwargs)
            
            last_exception = None
            transaction_hash = None
            
            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    
                    # Log success if this was a retry
                    if attempt > 0:
                        logger.info(
                            f"Blockchain transaction succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Try to extract transaction hash from exception or result
                    if hasattr(e, 'transaction_id'):
                        transaction_hash = str(e.transaction_id)
                    
                    # Log the failure
                    log_transaction_failure(
                        transaction_hash=transaction_hash,
                        error_message=str(e),
                        additional_details={
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "function": func.__name__
                        }
                    )
                    
                    # Don't retry on last attempt
                    if attempt >= max_attempts - 1:
                        logger.error(
                            f"Blockchain transaction failed after {max_attempts} attempts"
                        )
                        raise
                    
                    # Calculate exponential backoff delay
                    delay = initial_delay * (2 ** attempt)
                    
                    logger.warning(
                        f"Retrying blockchain transaction in {delay:.2f}s "
                        f"(attempt {attempt + 2}/{max_attempts})"
                    )
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class RetryableError(Exception):
    """Base exception for errors that should trigger retry logic"""
    pass


class NetworkError(RetryableError):
    """Exception for network-related errors"""
    pass


class RateLimitError(RetryableError):
    """Exception for API rate limit errors"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class TransactionError(Exception):
    """Exception for blockchain transaction errors"""
    def __init__(self, message: str, transaction_id: Optional[str] = None):
        super().__init__(message)
        self.transaction_id = transaction_id
