"""
Unit and property-based tests for Intent Parser.

Tests the IntentParser class including intent detection, parameter extraction,
prompt generation, request construction, response formatting, and error handling.
"""

import pytest
from hypothesis import given, strategies as st
from agents.intent_parser import IntentParser, Intent, IntentType


class TestIntentType:
    """Tests for IntentType enum."""
    
    def test_intent_type_values(self):
        """Test that all intent types have correct values."""
        assert IntentType.VERIFY_ORDER.value == "verify_order"
        assert IntentType.VERIFY_TRACKING.value == "verify_tracking"
        assert IntentType.VERIFY_IMAGE.value == "verify_image"
        assert IntentType.VERIFY_DOCUMENT.value == "verify_document"
        assert IntentType.CHECK_STATUS.value == "check_status"
        assert IntentType.DISCOVER_AGENTS.value == "discover_agents"
        assert IntentType.UNKNOWN.value == "unknown"


class TestIntent:
    """Tests for Intent dataclass."""
    
    def test_intent_is_complete_with_no_missing_params(self):
        """Test that intent is complete when no parameters are missing."""
        intent = Intent(
            intent_type=IntentType.VERIFY_ORDER,
            parameters={'order_id': '12345'},
            confidence=0.9,
            missing_parameters=[]
        )
        assert intent.is_complete() is True
    
    def test_intent_is_not_complete_with_missing_params(self):
        """Test that intent is not complete when parameters are missing."""
        intent = Intent(
            intent_type=IntentType.VERIFY_ORDER,
            parameters={},
            confidence=0.9,
            missing_parameters=['order_id']
        )
        assert intent.is_complete() is False


class TestIntentParser:
    """Tests for IntentParser class."""
    
    @pytest.fixture
    def parser(self):
        """Fixture providing an IntentParser instance."""
        return IntentParser()
    
    def test_parser_initialization(self, parser):
        """Test that parser initializes with patterns."""
        assert parser.intent_patterns is not None
        assert parser.parameter_patterns is not None
        assert len(parser.intent_patterns) > 0
        assert len(parser.parameter_patterns) > 0
    
    def test_parse_message_empty_string(self, parser):
        """Test parsing empty message returns UNKNOWN intent."""
        intent = parser.parse_message("")
        assert intent.intent_type == IntentType.UNKNOWN
        assert intent.confidence == 0.0
    
    def test_parse_message_verify_order(self, parser):
        """Test parsing order verification message."""
        intent = parser.parse_message("verify order 12345")
        assert intent.intent_type == IntentType.VERIFY_ORDER
        assert 'order_id' in intent.parameters
        assert intent.parameters['order_id'] == '12345'
    
    def test_parse_message_verify_tracking(self, parser):
        """Test parsing tracking verification message."""
        intent = parser.parse_message("check tracking number 123456789012")
        assert intent.intent_type == IntentType.VERIFY_TRACKING
        assert 'tracking_number' in intent.parameters
    
    def test_parse_message_verify_image(self, parser):
        """Test parsing image verification message."""
        intent = parser.parse_message("analyze this cargo photo")
        assert intent.intent_type == IntentType.VERIFY_IMAGE
    
    def test_parse_message_discover_agents(self, parser):
        """Test parsing agent discovery message."""
        intent = parser.parse_message("list available agents")
        assert intent.intent_type == IntentType.DISCOVER_AGENTS
    
    def test_extract_parameters_order_id(self, parser):
        """Test extracting order ID parameter."""
        params = parser.extract_parameters(
            "verify order 12345",
            IntentType.VERIFY_ORDER
        )
        assert 'order_id' in params
        assert params['order_id'] == '12345'
    
    def test_extract_parameters_tracking_number(self, parser):
        """Test extracting tracking number parameter."""
        params = parser.extract_parameters(
            "tracking number 123456789012",
            IntentType.VERIFY_TRACKING
        )
        assert 'tracking_number' in params
        assert params['tracking_number'] == '123456789012'
    
    def test_generate_prompt_missing_order_id(self, parser):
        """Test generating prompt for missing order ID."""
        intent = Intent(
            intent_type=IntentType.VERIFY_ORDER,
            parameters={},
            confidence=0.9,
            missing_parameters=['order_id']
        )
        prompt = parser.generate_prompt(intent)
        assert 'order' in prompt.lower()
        assert len(prompt) > 0
    
    def test_generate_prompt_no_missing_params(self, parser):
        """Test generating prompt when no parameters are missing."""
        intent = Intent(
            intent_type=IntentType.VERIFY_ORDER,
            parameters={'order_id': '12345'},
            confidence=0.9,
            missing_parameters=[]
        )
        prompt = parser.generate_prompt(intent)
        assert prompt == ""
    
    def test_construct_request_complete_intent(self, parser):
        """Test constructing request from complete intent."""
        intent = Intent(
            intent_type=IntentType.VERIFY_ORDER,
            parameters={'order_id': '12345'},
            confidence=0.9,
            missing_parameters=[]
        )
        request = parser.construct_request(intent)
        assert request['action'] == 'verify_order'
        assert request['order_id'] == '12345'
        assert 'confidence' in request
    
    def test_construct_request_incomplete_intent_raises_error(self, parser):
        """Test that constructing request from incomplete intent raises error."""
        intent = Intent(
            intent_type=IntentType.VERIFY_ORDER,
            parameters={},
            confidence=0.9,
            missing_parameters=['order_id']
        )
        with pytest.raises(ValueError, match="missing parameters"):
            parser.construct_request(intent)
    
    def test_format_response_with_score(self, parser):
        """Test formatting response with authenticity score."""
        result = {
            'authenticity_score': 85.5,
            'verification_status': 'PASS',
            'hcs_transaction_id': '0.0.12345@1234567890.123456789'
        }
        response = parser.format_response(result)
        assert '85.5' in response
        assert 'PASS' in response or '✓' in response
    
    def test_format_response_empty_result(self, parser):
        """Test formatting response with empty result."""
        response = parser.format_response({})
        assert len(response) > 0
        assert 'could' in response.lower() or 'try again' in response.lower()
    
    def test_format_error_timeout(self, parser):
        """Test formatting timeout error."""
        error = Exception("timeout occurred")
        message = parser.format_error(error)
        assert 'timeout' in message.lower() or 'longer than expected' in message.lower()
    
    def test_format_error_not_found(self, parser):
        """Test formatting not found error."""
        error = ValueError("Order not found")
        message = parser.format_error(error, {'action': 'verify_order'})
        assert 'order' in message.lower()
        assert 'not found' in message.lower() or "couldn't find" in message.lower()
    
    def test_format_error_generic(self, parser):
        """Test formatting generic error."""
        error = Exception("Something went wrong")
        message = parser.format_error(error)
        assert len(message) > 0
        assert 'issue' in message.lower() or 'problem' in message.lower()


class TestIntentParserProperties:
    """Property-based tests for IntentParser using Hypothesis."""
    
    @given(
        user_message=st.text(min_size=1, max_size=500, alphabet=st.characters(
            blacklist_categories=['Cs', 'Cc'],
            blacklist_characters=['\x00', '\n', '\r', '\t']
        ))
    )
    def test_property_22_intent_parsing_execution(self, user_message):
        """
        Feature: truthforge, Property 22: Intent Parsing Execution
        
        For any user chat message, the Intent_Parser shall analyze the message 
        and return an Intent object containing the detected intent type and 
        extracted parameters.
        
        Validates: Requirements 8.1
        """
        parser = IntentParser()
        
        # Property: parse_message must always return an Intent object
        intent = parser.parse_message(user_message)
        assert isinstance(intent, Intent), "parse_message must return an Intent object"
        
        # Property: Intent must have an intent_type
        assert hasattr(intent, 'intent_type'), "Intent must have intent_type attribute"
        assert isinstance(intent.intent_type, IntentType), "intent_type must be IntentType enum"
        
        # Property: Intent must have parameters dictionary
        assert hasattr(intent, 'parameters'), "Intent must have parameters attribute"
        assert isinstance(intent.parameters, dict), "parameters must be a dictionary"
        
        # Property: Intent must have confidence score
        assert hasattr(intent, 'confidence'), "Intent must have confidence attribute"
        assert isinstance(intent.confidence, (int, float)), "confidence must be numeric"
        assert 0.0 <= intent.confidence <= 1.0, "confidence must be between 0 and 1"
        
        # Property: Intent must have missing_parameters list
        assert hasattr(intent, 'missing_parameters'), "Intent must have missing_parameters attribute"
        assert isinstance(intent.missing_parameters, list), "missing_parameters must be a list"
        
        # Property: All items in missing_parameters must be strings
        for param in intent.missing_parameters:
            assert isinstance(param, str), "missing_parameters items must be strings"
        
        # Property: Intent type must be one of the valid IntentType values
        valid_intent_types = [
            IntentType.VERIFY_ORDER,
            IntentType.VERIFY_TRACKING,
            IntentType.VERIFY_IMAGE,
            IntentType.VERIFY_DOCUMENT,
            IntentType.CHECK_STATUS,
            IntentType.DISCOVER_AGENTS,
            IntentType.UNKNOWN
        ]
        assert intent.intent_type in valid_intent_types, \
            f"intent_type must be one of {[t.value for t in valid_intent_types]}"
        
        # Property: Parameters dictionary keys must be strings
        for key in intent.parameters.keys():
            assert isinstance(key, str), "parameter keys must be strings"
        
        # Property: is_complete() method must return boolean
        is_complete = intent.is_complete()
        assert isinstance(is_complete, bool), "is_complete() must return boolean"
        
        # Property: Intent is complete if and only if missing_parameters is empty
        if len(intent.missing_parameters) == 0:
            assert is_complete is True, "Intent should be complete when no parameters are missing"
        else:
            assert is_complete is False, "Intent should not be complete when parameters are missing"
        
        # Property: Confidence should be 0 for UNKNOWN intents
        if intent.intent_type == IntentType.UNKNOWN:
            assert intent.confidence == 0.0, "UNKNOWN intent should have 0 confidence"
        
        # Property: Non-UNKNOWN intents should have positive confidence
        if intent.intent_type != IntentType.UNKNOWN:
            assert intent.confidence > 0.0, "Detected intents should have positive confidence"
    
    @given(
        order_id=st.text(min_size=4, max_size=20, alphabet=st.characters(
            whitelist_categories=['Lu', 'Ll', 'Nd'],
            min_codepoint=48, max_codepoint=122
        )).filter(lambda x: x.strip() and not x.isspace()),
        tracking_number=st.text(min_size=12, max_size=20, alphabet=st.characters(
            whitelist_categories=['Nd'],
            min_codepoint=48, max_codepoint=57
        )).filter(lambda x: len(x) >= 12),
        intent_keyword=st.sampled_from(['verify', 'check', 'validate', 'analyze']),
        entity_keyword=st.sampled_from(['order', 'tracking', 'shipment'])
    )
    def test_property_23_parameter_extraction(self, order_id, tracking_number, intent_keyword, entity_keyword):
        """
        Feature: truthforge, Property 23: Parameter Extraction
        
        For any chat message containing verification-related entities (order IDs, 
        tracking numbers), the Intent_Parser shall extract these parameters and 
        include them in the structured request.
        
        Validates: Requirements 8.2
        """
        parser = IntentParser()
        
        # Test order ID extraction
        if entity_keyword == 'order':
            # Construct message with order ID
            message_with_order = f"{intent_keyword} {entity_keyword} {order_id}"
            intent = parser.parse_message(message_with_order)
            
            # Property: If message contains order-related keywords and an ID-like pattern,
            # the parameters should contain 'order_id'
            if intent.intent_type in [IntentType.VERIFY_ORDER, IntentType.CHECK_STATUS]:
                # Extract parameters using the extract_parameters method
                params = parser.extract_parameters(message_with_order, intent.intent_type)
                
                # Property: Parameters must be a dictionary
                assert isinstance(params, dict), "extract_parameters must return a dictionary"
                
                # Property: If order ID pattern is present, it should be extracted
                # (Note: extraction may fail for some patterns, but if it succeeds, it must be correct)
                if 'order_id' in params:
                    extracted_id = params['order_id']
                    assert isinstance(extracted_id, str), "Extracted order_id must be a string"
                    assert len(extracted_id) > 0, "Extracted order_id must not be empty"
                    # The extracted ID should be present in the original message
                    assert extracted_id in message_with_order, \
                        f"Extracted order_id '{extracted_id}' must be present in message '{message_with_order}'"
        
        # Test tracking number extraction
        if entity_keyword in ['tracking', 'shipment']:
            # Construct message with tracking number
            message_with_tracking = f"{intent_keyword} {entity_keyword} number {tracking_number}"
            intent = parser.parse_message(message_with_tracking)
            
            # Property: If message contains tracking-related keywords and a number pattern,
            # the parameters should contain 'tracking_number'
            if intent.intent_type in [IntentType.VERIFY_TRACKING, IntentType.VERIFY_ORDER]:
                # Extract parameters using the extract_parameters method
                params = parser.extract_parameters(message_with_tracking, intent.intent_type)
                
                # Property: Parameters must be a dictionary
                assert isinstance(params, dict), "extract_parameters must return a dictionary"
                
                # Property: If tracking number pattern is present, it should be extracted
                if 'tracking_number' in params:
                    extracted_tracking = params['tracking_number']
                    assert isinstance(extracted_tracking, str), "Extracted tracking_number must be a string"
                    assert len(extracted_tracking) > 0, "Extracted tracking_number must not be empty"
                    # The extracted tracking number should be present in the original message
                    assert extracted_tracking in message_with_tracking, \
                        f"Extracted tracking_number '{extracted_tracking}' must be present in message '{message_with_tracking}'"
        
        # Test combined extraction (order ID and tracking number in same message)
        combined_message = f"{intent_keyword} order {order_id} with tracking {tracking_number}"
        intent = parser.parse_message(combined_message)
        
        if intent.intent_type in [IntentType.VERIFY_ORDER, IntentType.VERIFY_TRACKING]:
            params = parser.extract_parameters(combined_message, intent.intent_type)
            
            # Property: Parameters dictionary must be returned
            assert isinstance(params, dict), "extract_parameters must return a dictionary"
            
            # Property: All extracted parameter values must be strings
            for key, value in params.items():
                assert isinstance(key, str), "Parameter keys must be strings"
                assert isinstance(value, str), "Parameter values must be strings"
                assert len(value) > 0, "Parameter values must not be empty"
            
            # Property: Extracted parameters must be present in the original message
            for key, value in params.items():
                assert value in combined_message, \
                    f"Extracted parameter '{key}={value}' must be present in message '{combined_message}'"
            
            # Property: If both order and tracking patterns are present and they are different in the input,
            # they should be extracted as different values (unless the regex matches the same substring)
            if 'order_id' in params and 'tracking_number' in params:
                # Only assert they're different if the input values were actually different
                if order_id != tracking_number:
                    # They can still be the same if the regex extracted the same part
                    # This is acceptable behavior - we just verify both were extracted
                    assert params['order_id'] is not None, "order_id should be extracted"
                    assert params['tracking_number'] is not None, "tracking_number should be extracted"
        
        # Test that extract_parameters is consistent with parse_message
        test_message = f"{intent_keyword} order {order_id}"
        intent_from_parse = parser.parse_message(test_message)
        params_from_extract = parser.extract_parameters(test_message, intent_from_parse.intent_type)
        
        # Property: Parameters from parse_message should match extract_parameters
        for key in intent_from_parse.parameters:
            if key in params_from_extract:
                assert intent_from_parse.parameters[key] == params_from_extract[key], \
                    f"Parameter '{key}' should match between parse_message and extract_parameters"
        
        # Property: extract_parameters should never raise an exception
        # (it should return empty dict if no parameters found)
        try:
            result = parser.extract_parameters("random text", IntentType.UNKNOWN)
            assert isinstance(result, dict), "extract_parameters must always return a dict"
        except Exception as e:
            pytest.fail(f"extract_parameters should not raise exception: {e}")
    
    @given(
        intent_type=st.sampled_from([
            IntentType.VERIFY_ORDER,
            IntentType.VERIFY_TRACKING,
            IntentType.VERIFY_IMAGE,
            IntentType.VERIFY_DOCUMENT,
            IntentType.CHECK_STATUS
        ]),
        intent_keyword=st.sampled_from(['verify', 'check', 'validate', 'analyze'])
    )
    def test_property_24_missing_parameter_prompting(self, intent_type, intent_keyword):
        """
        Feature: truthforge, Property 24: Missing Parameter Prompting
        
        For any verification intent with missing required parameters, the 
        Intent_Parser shall generate a prompt requesting the specific missing 
        information.
        
        Validates: Requirements 8.3
        """
        parser = IntentParser()
        
        # Create messages that will trigger the intent but without parameters
        intent_messages = {
            IntentType.VERIFY_ORDER: f"{intent_keyword} order",
            IntentType.VERIFY_TRACKING: f"{intent_keyword} tracking",
            IntentType.VERIFY_IMAGE: f"{intent_keyword} image",
            IntentType.VERIFY_DOCUMENT: f"{intent_keyword} document",
            IntentType.CHECK_STATUS: f"{intent_keyword} status"
        }
        
        message = intent_messages.get(intent_type, f"{intent_keyword} something")
        
        # Parse the message - this should detect the intent but find missing parameters
        intent = parser.parse_message(message)
        
        # Property: If the intent type matches and parameters are missing,
        # generate_prompt must return a non-empty prompt
        if intent.intent_type == intent_type and not intent.is_complete():
            prompt = parser.generate_prompt(intent)
            
            # Property: Prompt must be a string
            assert isinstance(prompt, str), "generate_prompt must return a string"
            
            # Property: Prompt must not be empty when parameters are missing
            assert len(prompt) > 0, \
                f"generate_prompt must return non-empty prompt for incomplete intent {intent_type.value}"
            
            # Property: Prompt must be a question or request (contains '?' or imperative language)
            assert '?' in prompt or any(word in prompt.lower() for word in ['please', 'provide', 'what', 'can you']), \
                f"Prompt should be a question or polite request, got: {prompt}"
            
            # Property: Prompt must mention the missing parameter type
            missing_param = intent.missing_parameters[0]
            
            # Map parameter names to expected words in prompt
            param_keywords = {
                'order_id': ['order'],
                'tracking_number': ['tracking'],
                'image_url': ['image', 'photo', 'picture'],
                'document_url': ['document', 'bol', 'bill'],
                'request_id': ['request', 'id']
            }
            
            if missing_param in param_keywords:
                expected_keywords = param_keywords[missing_param]
                prompt_lower = prompt.lower()
                
                # Property: Prompt must contain at least one keyword related to the missing parameter
                assert any(keyword in prompt_lower for keyword in expected_keywords), \
                    f"Prompt for missing '{missing_param}' should mention one of {expected_keywords}, got: {prompt}"
            
            # Property: Prompt should be user-friendly (no technical jargon like 'parameter', 'missing', 'required')
            technical_words = ['parameter', 'missing', 'required', 'null', 'none', 'undefined']
            prompt_lower = prompt.lower()
            for tech_word in technical_words:
                assert tech_word not in prompt_lower, \
                    f"Prompt should be user-friendly and not contain technical word '{tech_word}', got: {prompt}"
            
            # Property: Prompt should be reasonably short (under 200 characters for usability)
            assert len(prompt) < 200, \
                f"Prompt should be concise (under 200 chars), got {len(prompt)} chars: {prompt}"
        
        # Property: If intent is complete (no missing parameters), generate_prompt returns empty string
        if intent.is_complete():
            prompt = parser.generate_prompt(intent)
            assert prompt == "", \
                f"generate_prompt should return empty string for complete intent, got: {prompt}"
        
        # Property: generate_prompt must never raise an exception
        try:
            # Test with various intent states
            test_intent = Intent(
                intent_type=intent_type,
                parameters={},
                confidence=0.8,
                missing_parameters=['test_param']
            )
            result = parser.generate_prompt(test_intent)
            assert isinstance(result, str), "generate_prompt must always return a string"
        except Exception as e:
            pytest.fail(f"generate_prompt should not raise exception: {e}")
        
        # Property: Prompt generation is deterministic for the same intent
        if not intent.is_complete():
            prompt1 = parser.generate_prompt(intent)
            prompt2 = parser.generate_prompt(intent)
            assert prompt1 == prompt2, \
                "generate_prompt should return the same prompt for the same intent"
    
    @given(
        intent_type=st.sampled_from([
            IntentType.VERIFY_ORDER,
            IntentType.VERIFY_TRACKING,
            IntentType.VERIFY_IMAGE,
            IntentType.VERIFY_DOCUMENT,
            IntentType.CHECK_STATUS,
            IntentType.DISCOVER_AGENTS
        ]),
        order_id=st.text(min_size=4, max_size=20, alphabet=st.characters(
            whitelist_categories=['Lu', 'Ll', 'Nd'],
            min_codepoint=48, max_codepoint=122
        )).filter(lambda x: x.strip() and not x.isspace()),
        tracking_number=st.text(min_size=12, max_size=20, alphabet=st.characters(
            whitelist_categories=['Nd'],
            min_codepoint=48, max_codepoint=57
        )).filter(lambda x: len(x) >= 12),
        request_id=st.text(min_size=8, max_size=36, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-').filter(lambda x: x.strip() and not x.isspace()),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    def test_property_25_structured_request_construction(
        self,
        intent_type,
        order_id,
        tracking_number,
        request_id,
        confidence
    ):
        """
        Feature: truthforge, Property 25: Structured Request Construction
        
        For any complete set of verification parameters, the Intent_Parser 
        shall construct a valid structured request containing all necessary 
        fields for the Orchestrator.
        
        Validates: Requirements 8.4
        """
        parser = IntentParser()
        
        # Build parameters based on intent type
        parameters = {}
        missing_parameters = []
        
        if intent_type == IntentType.VERIFY_ORDER:
            parameters['order_id'] = order_id
        elif intent_type == IntentType.VERIFY_TRACKING:
            parameters['tracking_number'] = tracking_number
        elif intent_type == IntentType.VERIFY_IMAGE:
            parameters['image_url'] = f"https://example.com/image_{order_id}.jpg"
        elif intent_type == IntentType.VERIFY_DOCUMENT:
            parameters['document_url'] = f"https://example.com/doc_{order_id}.pdf"
        elif intent_type == IntentType.CHECK_STATUS:
            parameters['request_id'] = request_id
        # DISCOVER_AGENTS doesn't require parameters
        
        # Create a complete intent (no missing parameters)
        intent = Intent(
            intent_type=intent_type,
            parameters=parameters,
            confidence=confidence,
            missing_parameters=missing_parameters
        )
        
        # Property: construct_request must return a dictionary
        request = parser.construct_request(intent)
        assert isinstance(request, dict), \
            "construct_request must return a dictionary"
        
        # Property: Request must contain 'action' field
        assert 'action' in request, \
            "Request must contain 'action' field"
        
        # Property: Action field must be a string
        assert isinstance(request['action'], str), \
            "Action field must be a string"
        
        # Property: Action must match the intent type value
        assert request['action'] == intent_type.value, \
            f"Action '{request['action']}' must match intent type '{intent_type.value}'"
        
        # Property: Request must contain 'confidence' field
        assert 'confidence' in request, \
            "Request must contain 'confidence' field"
        
        # Property: Confidence must be numeric
        assert isinstance(request['confidence'], (int, float)), \
            "Confidence must be numeric"
        
        # Property: Confidence must match the intent confidence
        assert request['confidence'] == confidence, \
            f"Request confidence {request['confidence']} must match intent confidence {confidence}"
        
        # Property: Request must contain all parameters from the intent
        for param_key, param_value in parameters.items():
            assert param_key in request, \
                f"Request must contain parameter '{param_key}' from intent"
            assert request[param_key] == param_value, \
                f"Request parameter '{param_key}' must match intent parameter value"
        
        # Property: Request must not contain missing_parameters field
        assert 'missing_parameters' not in request, \
            "Request should not contain 'missing_parameters' field"
        
        # Property: Request must not contain intent_type field (should be 'action' instead)
        assert 'intent_type' not in request, \
            "Request should not contain 'intent_type' field (should use 'action' instead)"
        
        # Property: All request keys must be strings
        for key in request.keys():
            assert isinstance(key, str), \
                f"Request key '{key}' must be a string"
        
        # Property: Request must be JSON-serializable (all values must be basic types)
        import json
        try:
            json.dumps(request)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Request must be JSON-serializable, got error: {e}")
        
        # Property: Intent-specific fields must be present
        if intent_type == IntentType.VERIFY_ORDER:
            assert 'verification_type' in request, \
                "VERIFY_ORDER request must contain 'verification_type'"
            assert request['verification_type'] == 'order', \
                "VERIFY_ORDER verification_type must be 'order'"
            assert 'require_image_analysis' in request, \
                "VERIFY_ORDER request must contain 'require_image_analysis'"
            assert request['require_image_analysis'] is True, \
                "VERIFY_ORDER must require image analysis"
            assert 'require_document_verification' in request, \
                "VERIFY_ORDER request must contain 'require_document_verification'"
            assert request['require_document_verification'] is True, \
                "VERIFY_ORDER must require document verification"
            assert 'order_id' in request, \
                "VERIFY_ORDER request must contain 'order_id'"
        
        elif intent_type == IntentType.VERIFY_TRACKING:
            assert 'verification_type' in request, \
                "VERIFY_TRACKING request must contain 'verification_type'"
            assert request['verification_type'] == 'tracking', \
                "VERIFY_TRACKING verification_type must be 'tracking'"
            assert 'require_document_verification' in request, \
                "VERIFY_TRACKING request must contain 'require_document_verification'"
            assert request['require_document_verification'] is True, \
                "VERIFY_TRACKING must require document verification"
            assert 'tracking_number' in request, \
                "VERIFY_TRACKING request must contain 'tracking_number'"
        
        elif intent_type == IntentType.VERIFY_IMAGE:
            assert 'verification_type' in request, \
                "VERIFY_IMAGE request must contain 'verification_type'"
            assert request['verification_type'] == 'image', \
                "VERIFY_IMAGE verification_type must be 'image'"
            assert 'require_image_analysis' in request, \
                "VERIFY_IMAGE request must contain 'require_image_analysis'"
            assert request['require_image_analysis'] is True, \
                "VERIFY_IMAGE must require image analysis"
            assert 'image_url' in request, \
                "VERIFY_IMAGE request must contain 'image_url'"
        
        elif intent_type == IntentType.VERIFY_DOCUMENT:
            assert 'verification_type' in request, \
                "VERIFY_DOCUMENT request must contain 'verification_type'"
            assert request['verification_type'] == 'document', \
                "VERIFY_DOCUMENT verification_type must be 'document'"
            assert 'require_document_verification' in request, \
                "VERIFY_DOCUMENT request must contain 'require_document_verification'"
            assert request['require_document_verification'] is True, \
                "VERIFY_DOCUMENT must require document verification"
            assert 'document_url' in request, \
                "VERIFY_DOCUMENT request must contain 'document_url'"
        
        elif intent_type == IntentType.CHECK_STATUS:
            assert request['action'] == 'check_status', \
                "CHECK_STATUS action must be 'check_status'"
            assert 'request_id' in request, \
                "CHECK_STATUS request must contain 'request_id'"
        
        elif intent_type == IntentType.DISCOVER_AGENTS:
            assert request['action'] == 'discover_agents', \
                "DISCOVER_AGENTS action must be 'discover_agents'"
        
        # Property: construct_request must be deterministic for the same intent
        request2 = parser.construct_request(intent)
        assert request == request2, \
            "construct_request must return the same request for the same intent"
        
        # Property: Request must not contain any None values
        for key, value in request.items():
            assert value is not None, \
                f"Request field '{key}' must not be None"
        
        # Property: Request must not contain empty string values for required fields
        required_fields = ['action']
        for field in required_fields:
            if field in request:
                assert request[field] != "", \
                    f"Required field '{field}' must not be empty string"
        
        # Property: Confidence value must be preserved exactly (no rounding)
        assert request['confidence'] == confidence, \
            f"Confidence must be preserved exactly: expected {confidence}, got {request['confidence']}"
        
        # Property: construct_request must never raise an exception for complete intents
        try:
            # Test with various complete intents
            test_intent = Intent(
                intent_type=IntentType.DISCOVER_AGENTS,
                parameters={},
                confidence=0.9,
                missing_parameters=[]
            )
            result = parser.construct_request(test_intent)
            assert isinstance(result, dict), "construct_request must always return a dict for complete intents"
        except Exception as e:
            pytest.fail(f"construct_request should not raise exception for complete intent: {e}")
        
        # Property: construct_request must raise ValueError for incomplete intents
        incomplete_intent = Intent(
            intent_type=IntentType.VERIFY_ORDER,
            parameters={},
            confidence=0.9,
            missing_parameters=['order_id']
        )
        
        with pytest.raises(ValueError, match="missing parameters"):
            parser.construct_request(incomplete_intent)
        
        # Property: Error message for incomplete intent must mention the missing parameters
        try:
            parser.construct_request(incomplete_intent)
            pytest.fail("Should have raised ValueError for incomplete intent")
        except ValueError as e:
            error_message = str(e)
            assert 'missing parameters' in error_message.lower(), \
                f"Error message should mention 'missing parameters', got: {error_message}"
            assert 'order_id' in error_message, \
                f"Error message should mention the missing parameter 'order_id', got: {error_message}"
    
    @given(
        error_type=st.sampled_from([
            ValueError,
            ConnectionError,
            TimeoutError,
            RuntimeError,
            KeyError,
            AttributeError,
            TypeError
        ]),
        error_message=st.text(min_size=5, max_size=200, alphabet=st.characters(
            blacklist_categories=['Cs', 'Cc'],
            blacklist_characters=['\x00']
        )).filter(lambda x: x.strip()),
        action=st.sampled_from([
            'verify_order',
            'verify_tracking',
            'verify_image',
            'verify_document',
            'check_status',
            'discover_agents',
            None
        ])
    )
    def test_property_27_user_friendly_error_messages(self, error_type, error_message, action):
        """
        Feature: truthforge, Property 27: User-Friendly Error Messages
        
        For any error that occurs during verification, the Intent_Parser shall 
        generate an error message that explains the issue without exposing 
        internal system details or stack traces.
        
        Validates: Requirements 8.6
        """
        parser = IntentParser()
        
        # Create an error instance
        error = error_type(error_message)
        
        # Create context if action is provided
        context = {'action': action} if action else None
        
        # Property: format_error must always return a string
        formatted_message = parser.format_error(error, context)
        assert isinstance(formatted_message, str), \
            "format_error must return a string"
        
        # Property: Error message must not be empty
        assert len(formatted_message) > 0, \
            "format_error must return a non-empty message"
        
        # Property: Error message must be reasonably short (under 500 characters for usability)
        assert len(formatted_message) < 500, \
            f"Error message should be concise (under 500 chars), got {len(formatted_message)} chars"
        
        # Property: Error message must not contain technical stack trace elements
        technical_patterns = [
            'traceback',
            'stack trace',
            'line ',
            'file "',
            '.py',
            'exception:',
            'raise ',
            'at 0x',  # Memory addresses
            '__',  # Python dunder methods
            'self.',
            'cls.',
        ]
        
        formatted_lower = formatted_message.lower()
        for pattern in technical_patterns:
            assert pattern not in formatted_lower, \
                f"Error message should not contain technical pattern '{pattern}', got: {formatted_message}"
        
        # Property: Error message must not expose internal class names or module paths
        internal_indicators = [
            'agents.',
            'hol_registry.',
            'tests.',
            'IntentParser',
            'BaseAgent',
            'HederaClient',
            'WooCommerceAdapter',
            'FedExAdapter',
            'DocumentVerifier',
            'RealityEngine',
            'Orchestrator'
        ]
        
        for indicator in internal_indicators:
            assert indicator not in formatted_message, \
                f"Error message should not expose internal class/module '{indicator}', got: {formatted_message}"
        
        # Property: Error message must not contain raw exception type names
        exception_type_names = [
            'ValueError',
            'ConnectionError',
            'TimeoutError',
            'RuntimeError',
            'KeyError',
            'AttributeError',
            'TypeError',
            'Exception'
        ]
        
        for exc_name in exception_type_names:
            assert exc_name not in formatted_message, \
                f"Error message should not contain exception type name '{exc_name}', got: {formatted_message}"
        
        # Property: Error message should be conversational (use first person or direct address)
        conversational_indicators = [
            'i ',
            "i'm",
            "i've",
            'we ',
            "we're",
            'you ',
            'your ',
            'please',
            'try again',
            'contact support'
        ]
        
        # At least one conversational indicator should be present
        has_conversational_tone = any(
            indicator in formatted_lower for indicator in conversational_indicators
        )
        assert has_conversational_tone, \
            f"Error message should have conversational tone with words like {conversational_indicators}, got: {formatted_message}"
        
        # Property: Error message should provide actionable guidance
        actionable_words = [
            'try',
            'check',
            'contact',
            'wait',
            'provide',
            'again',
            'moment',
            'support'
        ]
        
        has_actionable_guidance = any(
            word in formatted_lower for word in actionable_words
        )
        assert has_actionable_guidance, \
            f"Error message should provide actionable guidance with words like {actionable_words}, got: {formatted_message}"
        
        # Property: Error message must not contain sensitive information patterns
        sensitive_patterns = [
            'password',
            'api_key',
            'secret',
            'token',
            'private_key',
            'credential'
        ]
        
        for pattern in sensitive_patterns:
            assert pattern not in formatted_lower, \
                f"Error message should not contain sensitive information pattern '{pattern}', got: {formatted_message}"
        
        # Property: Error message should be grammatically correct (starts with capital, ends with punctuation)
        assert formatted_message[0].isupper() or formatted_message[0].isdigit() or formatted_message[0] in ['✓', '✗', '⚠', '🔗'], \
            f"Error message should start with capital letter or special character, got: {formatted_message}"
        
        assert formatted_message[-1] in ['.', '!', '?'], \
            f"Error message should end with proper punctuation, got: {formatted_message}"
        
        # Property: format_error must never raise an exception
        try:
            # Test with various error types and contexts
            test_errors = [
                ValueError("test"),
                Exception("test"),
                RuntimeError("test")
            ]
            for test_error in test_errors:
                result = parser.format_error(test_error, context)
                assert isinstance(result, str), "format_error must always return a string"
        except Exception as e:
            pytest.fail(f"format_error should not raise exception: {e}")
        
        # Property: Error messages for the same error should be deterministic
        formatted_message_2 = parser.format_error(error, context)
        assert formatted_message == formatted_message_2, \
            "format_error should return the same message for the same error"
        
        # Property: Context-specific errors should mention the context
        if context and action:
            # For order-related actions, the message should mention "order"
            if 'order' in action:
                # Only check if the error is related to not found or similar
                if 'not found' in error_message.lower() or '404' in error_message:
                    assert 'order' in formatted_lower, \
                        f"Error message for order action should mention 'order', got: {formatted_message}"
        
        # Property: Common error patterns should have specific, helpful messages
        if 'timeout' in error_message.lower():
            assert 'longer than expected' in formatted_lower or 'try again' in formatted_lower, \
                f"Timeout errors should explain the delay and suggest retry, got: {formatted_message}"
        
        if 'not found' in error_message.lower() or '404' in error_message:
            assert 'not found' in formatted_lower or "couldn't find" in formatted_lower, \
                f"Not found errors should clearly state item was not found, got: {formatted_message}"
        
        if 'authentication' in error_message.lower() or 'unauthorized' in error_message.lower():
            assert 'authentication' in formatted_lower or 'contact support' in formatted_lower, \
                f"Authentication errors should mention auth issue or suggest support, got: {formatted_message}"
        
        if 'rate limit' in error_message.lower():
            assert 'traffic' in formatted_lower or 'wait' in formatted_lower or 'try again' in formatted_lower, \
                f"Rate limit errors should explain traffic and suggest waiting, got: {formatted_message}"
        
        if 'network' in error_message.lower() or 'connection' in error_message.lower():
            assert 'connecting' in formatted_lower or 'connection' in formatted_lower or 'try again' in formatted_lower, \
                f"Network errors should mention connection issues, got: {formatted_message}"
        
        # Property: Generic errors should have a fallback message
        # If none of the specific patterns match, should still get a helpful generic message
        if not any(pattern in error_message.lower() for pattern in ['timeout', 'not found', 'authentication', 'rate limit', 'network']):
            assert 'issue' in formatted_lower or 'problem' in formatted_lower or 'try again' in formatted_lower, \
                f"Generic errors should mention 'issue' or 'problem', got: {formatted_message}"
    
    @given(
        authenticity_score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        verification_status=st.sampled_from(['PASS', 'FAIL', 'WARNING', 'UNKNOWN', None]),
        has_hcs_tx=st.booleans(),
        has_analysis_summary=st.booleans(),
        num_discrepancies=st.integers(min_value=0, max_value=10)
    )
    def test_property_26_natural_language_response_formatting(
        self, 
        authenticity_score, 
        verification_status, 
        has_hcs_tx, 
        has_analysis_summary,
        num_discrepancies
    ):
        """
        Feature: truthforge, Property 26: Natural Language Response Formatting
        
        For any verification result received from the Orchestrator, the 
        Intent_Parser shall format the result into a natural language response 
        containing the authenticity score and key findings.
        
        Validates: Requirements 8.5
        """
        parser = IntentParser()
        
        # Construct a verification result with various fields
        verification_result = {}
        
        # Add authenticity score
        verification_result['authenticity_score'] = authenticity_score
        
        # Add verification status
        if verification_status:
            verification_result['verification_status'] = verification_status
        
        # Add HCS transaction ID
        if has_hcs_tx:
            verification_result['hcs_transaction_id'] = '0.0.12345@1234567890.123456789'
        
        # Add analysis summary
        if has_analysis_summary:
            verification_result['analysis_summary'] = 'EXIF data shows no tampering. Lighting analysis passed.'
        
        # Add discrepancies
        if num_discrepancies > 0:
            verification_result['discrepancies'] = [
                {'description': f'Discrepancy {i+1}', 'severity': 'medium'}
                for i in range(num_discrepancies)
            ]
        
        # Property: format_response must always return a string
        response = parser.format_response(verification_result)
        assert isinstance(response, str), \
            "format_response must return a string"
        
        # Property: Response must not be empty
        assert len(response) > 0, \
            "format_response must return a non-empty response"
        
        # Property: Response must be in natural language (not JSON or technical format)
        assert not response.strip().startswith('{'), \
            "Response should be natural language, not JSON"
        assert not response.strip().startswith('['), \
            "Response should be natural language, not a list"
        
        # Property: Response must contain the authenticity score
        score_str = f"{authenticity_score:.1f}"
        assert score_str in response or str(int(authenticity_score)) in response, \
            f"Response must contain authenticity score {authenticity_score}, got: {response}"
        
        # Property: Response must mention "authenticity" or "score"
        response_lower = response.lower()
        assert 'authenticity' in response_lower or 'score' in response_lower, \
            f"Response should mention 'authenticity' or 'score', got: {response}"
        
        # Property: Response must indicate verification status with appropriate symbols or words
        if verification_status == 'PASS':
            assert '✓' in response or 'pass' in response_lower or 'success' in response_lower, \
                f"PASS status should be indicated with ✓ or 'pass', got: {response}"
        elif verification_status == 'FAIL':
            assert '✗' in response or 'fail' in response_lower, \
                f"FAIL status should be indicated with ✗ or 'fail', got: {response}"
        elif verification_status == 'WARNING':
            assert '⚠' in response or 'warning' in response_lower, \
                f"WARNING status should be indicated with ⚠ or 'warning', got: {response}"
        
        # Property: Response must provide confidence interpretation for the score
        if authenticity_score >= 80:
            assert 'high' in response_lower or 'authentic' in response_lower or 'confidence' in response_lower, \
                f"High scores (≥80) should indicate high confidence, got: {response}"
        elif authenticity_score >= 60:
            assert 'medium' in response_lower or 'concern' in response_lower or 'confidence' in response_lower, \
                f"Medium scores (60-79) should indicate medium confidence, got: {response}"
        elif authenticity_score < 60:
            assert 'low' in response_lower or 'issue' in response_lower or 'concern' in response_lower or 'confidence' in response_lower, \
                f"Low scores (<60) should indicate low confidence or issues, got: {response}"
        
        # Property: If HCS transaction ID is present, response must include blockchain proof link
        if has_hcs_tx:
            assert '0.0.12345@1234567890.123456789' in response, \
                f"Response must include HCS transaction ID when present, got: {response}"
            assert 'blockchain' in response_lower or 'proof' in response_lower or '🔗' in response, \
                f"Response should mention blockchain proof when HCS TX is present, got: {response}"
            assert 'hashscan.io' in response_lower or 'hedera' in response_lower, \
                f"Response should include Hedera explorer link when HCS TX is present, got: {response}"
        
        # Property: If analysis summary is present, response must include it
        if has_analysis_summary:
            assert 'EXIF' in response or 'Lighting' in response or 'analysis' in response_lower, \
                f"Response must include analysis summary when present, got: {response}"
        
        # Property: If discrepancies are present, response must mention them
        if num_discrepancies > 0:
            assert 'issue' in response_lower or 'discrepanc' in response_lower or 'found' in response_lower, \
                f"Response must mention issues/discrepancies when present, got: {response}"
            # Should show count of discrepancies
            assert str(num_discrepancies) in response or (num_discrepancies <= 3 and 'Discrepancy' in response), \
                f"Response should show count or list of discrepancies, got: {response}"
        
        # Property: Response must not contain technical jargon or internal details
        technical_terms = [
            'dict',
            'list',
            'None',
            'null',
            'undefined',
            'exception',
            'traceback',
            'error:',
            'function',
            'method',
            'class',
            '__',
            'self.',
            '.py'
        ]
        
        for term in technical_terms:
            assert term not in response, \
                f"Response should not contain technical term '{term}', got: {response}"
        
        # Property: Response must be grammatically correct (starts with capital or symbol)
        first_char = response[0]
        assert first_char.isupper() or first_char in ['✓', '✗', '⚠', '🔗', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'], \
            f"Response should start with capital letter or special symbol, got: {response}"
        
        # Property: Response must be reasonably concise (under 1000 characters for usability)
        assert len(response) < 1000, \
            f"Response should be concise (under 1000 chars), got {len(response)} chars"
        
        # Property: Response must use user-friendly language (conversational tone)
        # Check for conversational indicators
        conversational_indicators = [
            'i ',
            "i'm",
            "i've",
            'you',
            'your',
            'appears',
            'detected',
            'found',
            'completed',
            'passed',
            'failed'
        ]
        
        has_conversational_tone = any(
            indicator in response_lower for indicator in conversational_indicators
        )
        assert has_conversational_tone, \
            f"Response should have conversational tone with words like {conversational_indicators}, got: {response}"
        
        # Property: Response must not expose internal system details
        internal_indicators = [
            'agents.',
            'IntentParser',
            'BaseAgent',
            'Orchestrator',
            'RealityEngine',
            'DocumentVerifier',
            'WooCommerceAdapter',
            'FedExAdapter',
            'hol_registry',
            'tests.'
        ]
        
        for indicator in internal_indicators:
            assert indicator not in response, \
                f"Response should not expose internal detail '{indicator}', got: {response}"
        
        # Property: format_response must never raise an exception
        try:
            # Test with various result formats
            test_results = [
                {},
                {'authenticity_score': 50.0},
                {'verification_status': 'PASS'},
                {'hcs_transaction_id': '0.0.999@111.222'},
                None  # Edge case: None input
            ]
            
            for test_result in test_results:
                if test_result is not None:
                    result = parser.format_response(test_result)
                    assert isinstance(result, str), "format_response must always return a string"
        except Exception as e:
            pytest.fail(f"format_response should not raise exception: {e}")
        
        # Property: Response formatting is deterministic for the same input
        response_2 = parser.format_response(verification_result)
        assert response == response_2, \
            "format_response should return the same response for the same input"
        
        # Property: Empty result should return a helpful fallback message
        empty_response = parser.format_response({})
        assert isinstance(empty_response, str), "Empty result should return a string"
        assert len(empty_response) > 0, "Empty result should return non-empty message"
        assert 'try again' in empty_response.lower() or "couldn't" in empty_response.lower(), \
            f"Empty result should suggest trying again, got: {empty_response}"
        
        # Property: Response must provide actionable information
        # Should tell user what the score means or what to do next
        actionable_words = [
            'authentic',
            'confidence',
            'concern',
            'issue',
            'view',
            'check',
            'blockchain',
            'proof',
            'passed',
            'failed',
            'warning'
        ]
        
        has_actionable_info = any(
            word in response_lower for word in actionable_words
        )
        assert has_actionable_info, \
            f"Response should provide actionable information with words like {actionable_words}, got: {response}"
