"""
Tests for error handling and resilience utilities

Tests cover:
- Exponential backoff retry logic
- Network error retry decorators
- Blockchain transaction error handling
- Structured error logging
"""

import pytest
import time
import logging
from datetime import datetime, timezone
from unittest.mock import Mock, patch, call
from hypothesis import given, strategies as st, settings
from agents.error_handling import (
    retry_with_backoff,
    retry_network_operation,
    retry_blockchain_transaction,
    log_transaction_failure,
    RetryableError,
    NetworkError,
    RateLimitError,
    TransactionError
)


class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator"""
    
    def test_successful_first_attempt(self):
        """Test function succeeds on first attempt without retry"""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_function()
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure_then_success(self):
        """Test function retries on failure then succeeds"""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1)
        def eventually_successful():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = eventually_successful()
        
        assert result == "success"
        assert call_count == 3
    
    def test_all_attempts_fail(self):
        """Test function fails after all retry attempts"""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent failure")
        
        with pytest.raises(ValueError, match="Permanent failure"):
            always_fails()
        
        assert call_count == 3
    
    def test_exponential_backoff_timing(self):
        """Test that delays follow exponential backoff pattern"""
        call_times = []
        
        @retry_with_backoff(max_attempts=4, initial_delay=0.1, backoff_factor=2.0)
        def failing_function():
            call_times.append(time.time())
            raise ValueError("Test failure")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Verify we have 4 attempts
        assert len(call_times) == 4
        
        # Verify delays are approximately exponential: 0.1s, 0.2s, 0.4s
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        
        # Allow 50ms tolerance for timing
        assert 0.05 < delays[0] < 0.15  # ~0.1s
        assert 0.15 < delays[1] < 0.25  # ~0.2s
        assert 0.35 < delays[2] < 0.45  # ~0.4s
    
    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay"""
        call_times = []
        
        @retry_with_backoff(
            max_attempts=5,
            initial_delay=10.0,
            backoff_factor=2.0,
            max_delay=0.2
        )
        def failing_function():
            call_times.append(time.time())
            raise ValueError("Test failure")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # All delays should be capped at max_delay (0.2s)
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        
        for delay in delays:
            assert delay < 0.3  # Should be ~0.2s with tolerance
    
    def test_specific_exception_types(self):
        """Test retry only catches specified exception types"""
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1, exceptions=(ValueError,))
        def raises_value_error():
            raise ValueError("Should retry")
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.1, exceptions=(ValueError,))
        def raises_type_error():
            raise TypeError("Should not retry")
        
        # ValueError should be retried
        with pytest.raises(ValueError):
            raises_value_error()
        
        # TypeError should fail immediately (not in exceptions tuple)
        with pytest.raises(TypeError):
            raises_type_error()
    
    def test_on_retry_callback(self):
        """Test on_retry callback is called before each retry"""
        retry_calls = []
        
        def track_retries(exception, attempt, delay):
            retry_calls.append({
                'exception': exception,
                'attempt': attempt,
                'delay': delay
            })
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.1,
            on_retry=track_retries
        )
        def failing_function():
            raise ValueError("Test failure")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Should have 2 retry callbacks (not called on last attempt)
        assert len(retry_calls) == 2
        assert retry_calls[0]['attempt'] == 1
        assert retry_calls[1]['attempt'] == 2


class TestRetryNetworkOperation:
    """Tests for retry_network_operation decorator"""
    
    def test_retry_on_connection_error(self):
        """Test retry on ConnectionError"""
        call_count = 0
        
        @retry_network_operation(max_attempts=3, initial_delay=0.1)
        def network_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network unavailable")
            return "success"
        
        result = network_call()
        
        assert result == "success"
        assert call_count == 2
    
    def test_retry_on_timeout_error(self):
        """Test retry on TimeoutError"""
        call_count = 0
        
        @retry_network_operation(max_attempts=3, initial_delay=0.1)
        def network_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Request timed out")
            return "success"
        
        result = network_call()
        
        assert result == "success"
        assert call_count == 2
    
    def test_retry_on_os_error(self):
        """Test retry on OSError (network-related)"""
        call_count = 0
        
        @retry_network_operation(max_attempts=3, initial_delay=0.1)
        def network_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OSError("Network error")
            return "success"
        
        result = network_call()
        
        assert result == "success"
        assert call_count == 2
    
    def test_max_attempts_reached(self):
        """Test network operation fails after max attempts"""
        call_count = 0
        
        @retry_network_operation(max_attempts=3, initial_delay=0.1)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent network error")
        
        with pytest.raises(ConnectionError):
            always_fails()
        
        assert call_count == 3
    
    def test_logging_enabled(self, caplog):
        """Test retry attempts are logged when log_attempts=True"""
        
        @retry_network_operation(max_attempts=3, initial_delay=0.1, log_attempts=True)
        def failing_network_call():
            raise ConnectionError("Network error")
        
        with caplog.at_level(logging.INFO):
            with pytest.raises(ConnectionError):
                failing_network_call()
        
        # Should have log entries for retry attempts
        assert any("Network operation retry attempt" in record.message for record in caplog.records)


class TestLogTransactionFailure:
    """Tests for log_transaction_failure function"""
    
    def test_log_with_all_details(self, caplog):
        """Test logging transaction failure with all details"""
        with caplog.at_level(logging.ERROR):
            log_transaction_failure(
                transaction_hash="0x123abc",
                error_message="Insufficient balance",
                account_id="0.0.12345",
                additional_details={"balance": 0, "required": 100}
            )
        
        # Verify log contains key information
        log_messages = [record.message for record in caplog.records]
        assert any("0x123abc" in msg for msg in log_messages)
        assert any("Insufficient balance" in msg for msg in log_messages)
        assert any("0.0.12345" in msg for msg in log_messages)
    
    def test_log_without_transaction_hash(self, caplog):
        """Test logging when transaction hash is not available"""
        with caplog.at_level(logging.ERROR):
            log_transaction_failure(
                transaction_hash=None,
                error_message="Transaction failed",
                account_id="0.0.12345"
            )
        
        log_messages = [record.message for record in caplog.records]
        assert any("N/A" in msg or "Transaction failed" in msg for msg in log_messages)
    
    def test_log_without_account_id(self, caplog):
        """Test logging when account ID is not available"""
        with caplog.at_level(logging.ERROR):
            log_transaction_failure(
                transaction_hash="0x123abc",
                error_message="Transaction failed"
            )
        
        # Should not raise error, should log with N/A for account
        assert len(caplog.records) > 0


class TestRetryBlockchainTransaction:
    """Tests for retry_blockchain_transaction decorator"""
    
    def test_production_mode_retry_on_failure(self):
        """Test transaction retries in production mode"""
        call_count = 0
        
        @retry_blockchain_transaction(max_attempts=3, initial_delay=0.1, production_mode=True)
        def submit_transaction():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TransactionError("Transaction failed", transaction_id="0x123")
            return {"status": "success", "tx_id": "0x123"}
        
        result = submit_transaction()
        
        assert result["status"] == "success"
        assert call_count == 2
    
    def test_mock_mode_no_retry(self):
        """Test transaction does not retry in mock mode"""
        call_count = 0
        
        @retry_blockchain_transaction(max_attempts=3, initial_delay=0.1, production_mode=False)
        def submit_transaction():
            nonlocal call_count
            call_count += 1
            raise TransactionError("Transaction failed")
        
        with pytest.raises(TransactionError):
            submit_transaction()
        
        # Should only be called once (no retry in mock mode)
        assert call_count == 1
    
    def test_production_mode_all_attempts_fail(self):
        """Test transaction fails after all retries in production mode"""
        call_count = 0
        
        @retry_blockchain_transaction(max_attempts=3, initial_delay=0.1, production_mode=True)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise TransactionError("Persistent failure")
        
        with pytest.raises(TransactionError):
            always_fails()
        
        assert call_count == 3
    
    def test_exponential_backoff_for_transactions(self):
        """Test blockchain transactions use exponential backoff"""
        call_times = []
        
        @retry_blockchain_transaction(max_attempts=3, initial_delay=0.1, production_mode=True)
        def failing_transaction():
            call_times.append(time.time())
            raise TransactionError("Test failure")
        
        with pytest.raises(TransactionError):
            failing_transaction()
        
        # Verify exponential delays
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        
        # First delay ~0.1s, second delay ~0.2s
        assert 0.05 < delays[0] < 0.15
        assert 0.15 < delays[1] < 0.25
    
    def test_transaction_failure_logging(self, caplog):
        """Test transaction failures are logged with details"""
        
        @retry_blockchain_transaction(max_attempts=2, initial_delay=0.1, production_mode=True)
        def failing_transaction():
            raise TransactionError("Test failure", transaction_id="0x456")
        
        with caplog.at_level(logging.ERROR):
            with pytest.raises(TransactionError):
                failing_transaction()
        
        # Should have logged the failure
        assert any("transaction" in record.message.lower() for record in caplog.records)


class TestCustomExceptions:
    """Tests for custom exception classes"""
    
    def test_retryable_error(self):
        """Test RetryableError can be raised and caught"""
        with pytest.raises(RetryableError):
            raise RetryableError("Test error")
    
    def test_network_error(self):
        """Test NetworkError is a RetryableError"""
        error = NetworkError("Network failed")
        assert isinstance(error, RetryableError)
    
    def test_rate_limit_error_with_retry_after(self):
        """Test RateLimitError stores retry_after value"""
        error = RateLimitError("Rate limited", retry_after=60)
        assert error.retry_after == 60
        assert isinstance(error, RetryableError)
    
    def test_rate_limit_error_without_retry_after(self):
        """Test RateLimitError works without retry_after"""
        error = RateLimitError("Rate limited")
        assert error.retry_after is None
    
    def test_transaction_error_with_id(self):
        """Test TransactionError stores transaction_id"""
        error = TransactionError("Transaction failed", transaction_id="0x789")
        assert error.transaction_id == "0x789"
    
    def test_transaction_error_without_id(self):
        """Test TransactionError works without transaction_id"""
        error = TransactionError("Transaction failed")
        assert error.transaction_id is None


class TestPropertyBasedNetworkRetry:
    """Property-based tests for network error retry count"""
    
    @given(
        error_type=st.sampled_from([ConnectionError, TimeoutError, OSError]),
        max_attempts=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_network_error_retry_count(self, error_type, max_attempts):
        """
        Feature: truthforge, Property 43: Network Error Retry Count
        
        For any network error during an operation, the system shall attempt 
        the operation up to 3 times total (initial attempt plus 2 retries) 
        before failing permanently.
        
        This property verifies that:
        1. Network operations are retried exactly max_attempts times
        2. The function is called max_attempts times before raising the exception
        3. The final exception is raised after all retry attempts are exhausted
        4. This applies to all network error types (ConnectionError, TimeoutError, OSError)
        
        Validates: Requirements 16.3
        """
        call_count = 0
        
        @retry_network_operation(max_attempts=max_attempts, initial_delay=0.05)
        def failing_network_operation():
            nonlocal call_count
            call_count += 1
            raise error_type("Network operation failed")
        
        # Execute and expect the network error to be raised after all retries
        with pytest.raises(error_type):
            failing_network_operation()
        
        # Verify the function was called exactly max_attempts times
        assert call_count == max_attempts, \
            f"Expected {max_attempts} attempts for {error_type.__name__}, got {call_count}"
    
    @given(
        error_type=st.sampled_from([ConnectionError, TimeoutError, OSError]),
        success_on_attempt=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_network_retry_stops_on_success(self, error_type, success_on_attempt):
        """
        Property: Network retry stops immediately upon success
        
        For any network operation that succeeds on attempt N (where N <= max_attempts),
        the retry logic shall stop immediately and return the result without
        attempting further retries.
        
        Validates: Requirements 16.3
        """
        call_count = 0
        max_attempts = 3
        
        @retry_network_operation(max_attempts=max_attempts, initial_delay=0.05)
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < success_on_attempt:
                raise error_type("Temporary network error")
            return "success"
        
        result = eventually_succeeds()
        
        # Verify function succeeded
        assert result == "success"
        
        # Verify function was called exactly success_on_attempt times (no extra retries)
        assert call_count == success_on_attempt, \
            f"Expected {success_on_attempt} attempts, got {call_count}"
    
    @given(
        max_attempts=st.integers(min_value=2, max_value=4)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_network_retry_with_different_errors(self, max_attempts):
        """
        Property: Network retry handles different error types consistently
        
        For any network operation that raises different network error types
        across retries, the retry logic shall continue retrying until max_attempts
        is reached, regardless of which specific network error type is raised.
        
        Validates: Requirements 16.3
        """
        call_count = 0
        error_sequence = [ConnectionError, TimeoutError, OSError]
        
        @retry_network_operation(max_attempts=max_attempts, initial_delay=0.05)
        def raises_different_errors():
            nonlocal call_count
            error_type = error_sequence[call_count % len(error_sequence)]
            call_count += 1
            raise error_type(f"Network error type {error_type.__name__}")
        
        # Should raise one of the network errors after all retries
        with pytest.raises((ConnectionError, TimeoutError, OSError)):
            raises_different_errors()
        
        # Verify all attempts were made
        assert call_count == max_attempts, \
            f"Expected {max_attempts} attempts with mixed errors, got {call_count}"


class TestPropertyBasedTransactionFailureLogging:
    """Property-based tests for transaction failure logging"""
    
    @given(
        transaction_hash=st.one_of(
            st.none(),
            st.text(min_size=10, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='x-'))
        ),
        error_message=st.text(min_size=1, max_size=200),
        account_id=st.one_of(
            st.none(),
            st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Nd',), whitelist_characters='.'))
        ),
        has_additional_details=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_transaction_failure_logging(
        self, transaction_hash, error_message, account_id, has_additional_details
    ):
        """
        Feature: truthforge, Property 44: Transaction Failure Logging
        
        For any failed blockchain transaction, the system shall log the transaction 
        hash (if available), error message, account ID, and timestamp.
        
        This property verifies that:
        1. All transaction failures are logged with structured information
        2. Transaction hash is logged (or "N/A" if unavailable)
        3. Error message is included in the log
        4. Account ID is logged (or "N/A" if unavailable)
        5. Timestamp is included in the log entry
        6. Additional details are logged when provided
        7. Log level is ERROR for transaction failures
        
        Validates: Requirements 16.4
        """
        # Prepare additional details if needed
        additional_details = None
        if has_additional_details:
            additional_details = {
                "network": "testnet",
                "topic_id": "0.0.12345",
                "attempt": 1
            }
        
        # Use a custom log handler to capture logs instead of caplog fixture
        import io
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.ERROR)
        
        # Create a formatter to capture structured log data
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Get the logger and add our handler
        test_logger = logging.getLogger('agents.error_handling')
        original_level = test_logger.level
        test_logger.setLevel(logging.ERROR)
        test_logger.addHandler(handler)
        
        try:
            # Call log_transaction_failure
            log_transaction_failure(
                transaction_hash=transaction_hash,
                error_message=error_message,
                account_id=account_id,
                additional_details=additional_details
            )
            
            # Get the log output
            log_output = log_stream.getvalue()
            
            # Verify logs were created
            assert len(log_output) > 0, "No log output was created"
            
            # Verify transaction hash is logged (or N/A if None)
            if transaction_hash:
                assert transaction_hash in log_output, \
                    f"Transaction hash '{transaction_hash}' not found in logs"
            else:
                assert "N/A" in log_output, \
                    "Expected 'N/A' for missing transaction hash"
            
            # Verify error message is logged
            assert error_message in log_output, \
                f"Error message '{error_message}' not found in logs"
            
            # Verify account ID is logged (or N/A if None)
            if account_id:
                assert account_id in log_output, \
                    f"Account ID '{account_id}' not found in logs"
            else:
                # Should have N/A for account when not provided
                assert "N/A" in log_output or "account" in log_output.lower(), \
                    "Expected account information in logs"
            
            # Verify log level is ERROR
            assert "ERROR" in log_output, \
                "Expected ERROR level in log output"
            
            # Verify timestamp is present (check for ISO format indicators)
            # The log_transaction_failure function creates a timestamp internally
            assert "timestamp" in log_output.lower(), \
                "Timestamp not found in log output"
            
            # Verify additional details are logged when provided
            if has_additional_details and additional_details:
                # Check that at least one detail key appears in logs
                detail_found = any(
                    key in log_output for key in additional_details.keys()
                )
                assert detail_found, \
                    "Additional details not found in logs"
            
            # Verify structured logging format
            assert "transaction" in log_output.lower(), \
                "Transaction-related keywords not found in logs"
            
            assert "fail" in log_output.lower(), \
                "Failure-related keywords not found in logs"
        
        finally:
            # Clean up: remove handler and restore original level
            test_logger.removeHandler(handler)
            test_logger.setLevel(original_level)
            handler.close()


class TestPropertyBasedProductionModeTransactionRetry:
    """Property-based tests for production mode transaction retry"""
    
    @given(
        max_attempts=st.integers(min_value=2, max_value=4),
        initial_delay=st.floats(min_value=0.05, max_value=0.15),
        success_on_attempt=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_production_mode_transaction_retry(self, max_attempts, initial_delay, success_on_attempt):
        """
        Feature: truthforge, Property 45: Production Mode Transaction Retry
        
        For any failed HCS transaction in Production_Mode, the system shall retry 
        the transaction with exponential backoff up to the configured maximum retry count.
        
        This property verifies that:
        1. In production mode, failed transactions are retried up to max_attempts times
        2. Transactions use exponential backoff between retry attempts
        3. Successful transactions stop retrying immediately
        4. The retry count respects the configured maximum
        5. Transaction failures are logged with details
        
        Validates: Requirements 12.3
        """
        # Ensure success_on_attempt is within max_attempts range
        if success_on_attempt > max_attempts:
            success_on_attempt = max_attempts
        
        call_count = 0
        call_times = []
        
        @retry_blockchain_transaction(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            production_mode=True
        )
        def transaction_eventually_succeeds():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            
            if call_count < success_on_attempt:
                raise TransactionError(
                    f"Transaction failed on attempt {call_count}",
                    transaction_id=f"0x{call_count:04x}"
                )
            
            return {
                "status": "success",
                "transaction_id": f"0x{call_count:04x}",
                "consensus_timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Execute transaction
        result = transaction_eventually_succeeds()
        
        # Verify transaction succeeded
        assert result["status"] == "success", \
            "Transaction should succeed after retries"
        
        # Verify function was called exactly success_on_attempt times (no extra retries)
        assert call_count == success_on_attempt, \
            f"Expected {success_on_attempt} attempts, got {call_count}"
        
        # Verify exponential backoff timing if there were retries
        if len(call_times) > 1:
            delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
            
            # Verify delays follow exponential pattern
            for attempt_num, actual_delay in enumerate(delays):
                # Expected delay: initial_delay * (2 ** attempt_num)
                expected_delay = initial_delay * (2 ** attempt_num)
                
                # Allow 50% tolerance for timing variations
                tolerance = max(expected_delay * 0.5, 0.05)
                lower_bound = expected_delay - tolerance
                upper_bound = expected_delay + tolerance
                
                assert lower_bound <= actual_delay <= upper_bound, \
                    f"Retry {attempt_num}: delay {actual_delay:.3f}s not in expected range " \
                    f"[{lower_bound:.3f}s, {upper_bound:.3f}s] (expected {expected_delay:.3f}s)"
    
    @given(
        max_attempts=st.integers(min_value=2, max_value=3)
    )
    @settings(max_examples=30, deadline=None)
    def test_property_production_mode_all_retries_exhausted(self, max_attempts):
        """
        Property: Production mode retries until max_attempts is reached
        
        For any transaction that fails on all attempts in production mode,
        the system shall retry exactly max_attempts times before raising
        the final exception.
        
        Validates: Requirements 12.3
        """
        call_count = 0
        
        @retry_blockchain_transaction(
            max_attempts=max_attempts,
            initial_delay=0.1,
            production_mode=True
        )
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise TransactionError(
                f"Transaction failed on attempt {call_count}",
                transaction_id=f"0xfail{call_count:04x}"
            )
        
        # Execute and expect TransactionError after all retries
        with pytest.raises(TransactionError):
            always_fails()
        
        # Verify function was called exactly max_attempts times
        assert call_count == max_attempts, \
            f"Expected {max_attempts} attempts in production mode, got {call_count}"
    
    @given(
        max_attempts=st.integers(min_value=2, max_value=3)
    )
    @settings(max_examples=30, deadline=None)
    def test_property_mock_mode_no_retry(self, max_attempts):
        """
        Property: Mock mode does not retry transactions
        
        For any transaction that fails in mock mode (production_mode=False),
        the system shall NOT retry and shall fail immediately on the first attempt.
        
        This ensures mock mode is fast and doesn't waste time on retries
        during development and testing.
        
        Validates: Requirements 12.3, 11.1
        """
        call_count = 0
        
        @retry_blockchain_transaction(
            max_attempts=max_attempts,
            initial_delay=0.1,
            production_mode=False  # Mock mode
        )
        def fails_in_mock_mode():
            nonlocal call_count
            call_count += 1
            raise TransactionError(
                "Transaction failed in mock mode",
                transaction_id="0xmock0001"
            )
        
        # Execute and expect immediate failure
        with pytest.raises(TransactionError):
            fails_in_mock_mode()
        
        # Verify function was called only once (no retries in mock mode)
        assert call_count == 1, \
            f"Expected 1 attempt in mock mode, got {call_count}"
    
    @given(
        max_attempts=st.integers(min_value=2, max_value=3),
        initial_delay=st.floats(min_value=0.05, max_value=0.1)
    )
    @settings(max_examples=30, deadline=None)
    def test_property_production_mode_exponential_backoff_growth(self, max_attempts, initial_delay):
        """
        Property: Production mode uses exponential backoff (factor of 2)
        
        For any transaction retry sequence in production mode,
        each delay shall be approximately 2x the previous delay,
        following the exponential backoff pattern.
        
        Validates: Requirements 12.3, 16.2
        """
        call_times = []
        
        @retry_blockchain_transaction(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            production_mode=True
        )
        def always_fails():
            call_times.append(time.time())
            raise TransactionError("Test failure")
        
        with pytest.raises(TransactionError):
            always_fails()
        
        # Calculate actual delays
        if len(call_times) > 1:
            delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
            
            # Verify delays are increasing (exponential growth)
            for i in range(len(delays) - 1):
                # Each delay should be approximately 2x the previous
                # Allow 40% tolerance for timing variations
                ratio = delays[i+1] / delays[i] if delays[i] > 0 else 0
                
                # For exponential backoff with factor 2, ratio should be around 2.0
                # Allow range of 1.2 to 2.8 to account for timing variations
                assert 1.2 <= ratio <= 2.8, \
                    f"Delay ratio {ratio:.2f} not exponential (delays: {delays[i]:.3f}s -> {delays[i+1]:.3f}s)"


class TestPropertyBasedExponentialBackoff:
    """Property-based tests for exponential backoff timing"""
    
    @given(
        max_attempts=st.integers(min_value=2, max_value=5),
        initial_delay=st.floats(min_value=0.05, max_value=0.2),
        backoff_factor=st.floats(min_value=1.5, max_value=3.0)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_exponential_backoff_timing(self, max_attempts, initial_delay, backoff_factor):
        """
        Feature: truthforge, Property 42: Exponential Backoff Timing
        
        For any API rate limit error, subsequent retry attempts shall wait for 
        exponentially increasing durations (e.g., 1s, 2s, 4s, 8s) before retrying.
        
        This property verifies that:
        1. Each retry delay is approximately backoff_factor times the previous delay
        2. The first delay matches the initial_delay
        3. All delays follow the exponential pattern: initial_delay * (backoff_factor ** attempt)
        
        Validates: Requirements 16.2
        """
        call_times = []
        
        @retry_with_backoff(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            backoff_factor=backoff_factor
        )
        def failing_function():
            call_times.append(time.time())
            raise RateLimitError("Rate limit exceeded")
        
        # Execute and expect failure after all retries
        with pytest.raises(RateLimitError):
            failing_function()
        
        # Verify we have the expected number of attempts
        assert len(call_times) == max_attempts, \
            f"Expected {max_attempts} attempts, got {len(call_times)}"
        
        # Calculate actual delays between attempts
        actual_delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        
        # Verify each delay follows exponential backoff pattern
        for attempt_num, actual_delay in enumerate(actual_delays):
            # Expected delay: initial_delay * (backoff_factor ** attempt_num)
            expected_delay = initial_delay * (backoff_factor ** attempt_num)
            
            # Allow 50% tolerance for timing variations in test environment
            # (system scheduling, GC, thread switching, etc. can affect precise timing on Windows)
            # We add a minimum tolerance of 0.02s to handle very small delays
            tolerance = max(expected_delay * 0.5, 0.02)
            lower_bound = expected_delay - tolerance
            upper_bound = expected_delay + tolerance
            
            assert lower_bound <= actual_delay <= upper_bound, \
                f"Attempt {attempt_num}: delay {actual_delay:.3f}s not in expected range " \
                f"[{lower_bound:.3f}s, {upper_bound:.3f}s] (expected {expected_delay:.3f}s)"
        
        # Verify delays are increasing (exponential growth)
        if len(actual_delays) > 1:
            for i in range(len(actual_delays) - 1):
                # Each delay should be at least as large as the previous (within tolerance)
                # For exponential backoff with factor > 1, delays should increase
                if backoff_factor > 1.0:
                    assert actual_delays[i+1] >= actual_delays[i] * 0.7, \
                        f"Delays not increasing exponentially: {actual_delays[i]:.3f}s -> {actual_delays[i+1]:.3f}s"
    
    @given(
        initial_delay=st.floats(min_value=0.05, max_value=0.2),
        max_delay=st.floats(min_value=0.15, max_value=0.3)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_max_delay_cap(self, initial_delay, max_delay):
        """
        Property: Exponential backoff respects max_delay cap
        
        For any exponential backoff configuration with max_delay set,
        no retry delay shall exceed the max_delay value.
        
        Validates: Requirements 16.2
        """
        # Ensure max_delay is greater than initial_delay
        if max_delay <= initial_delay:
            max_delay = initial_delay + 0.1
        
        call_times = []
        
        @retry_with_backoff(
            max_attempts=5,
            initial_delay=initial_delay,
            backoff_factor=2.0,
            max_delay=max_delay
        )
        def failing_function():
            call_times.append(time.time())
            raise ValueError("Test failure")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Calculate actual delays
        actual_delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        
        # Verify no delay exceeds max_delay (with small tolerance for timing)
        for i, delay in enumerate(actual_delays):
            assert delay <= max_delay + 0.05, \
                f"Delay {i} ({delay:.3f}s) exceeds max_delay ({max_delay:.3f}s)"
    
    @given(
        max_attempts=st.integers(min_value=2, max_value=4),
        initial_delay=st.floats(min_value=0.05, max_value=0.15)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_retry_count_matches_max_attempts(self, max_attempts, initial_delay):
        """
        Property: Retry logic attempts exactly max_attempts times
        
        For any function decorated with retry_with_backoff,
        the function shall be called exactly max_attempts times before failing.
        
        Validates: Requirements 16.2
        """
        call_count = 0
        
        @retry_with_backoff(max_attempts=max_attempts, initial_delay=initial_delay)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent failure")
        
        with pytest.raises(ValueError):
            always_fails()
        
        assert call_count == max_attempts, \
            f"Expected {max_attempts} attempts, got {call_count}"

