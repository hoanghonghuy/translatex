"""
Property-based tests for LLMClientFactory
Uses Hypothesis for property-based testing
"""
import pytest
from hypothesis import given, strategies as st, settings
from translatex.utils.llm_client_factory import LLMClientFactory


class TestProviderEndpointMapping:
    """
    **Feature: openrouter-support, Property 1: Provider endpoint mapping**
    *For any* valid provider name ("openai" or "openrouter"), the LLMClientFactory 
    SHALL return a client configured with the correct base_url for that provider.
    **Validates: Requirements 1.1, 1.2**
    """
    
    @given(provider=st.sampled_from(["openai", "openrouter", "groq"]))
    @settings(max_examples=100)
    def test_valid_provider_returns_correct_base_url(self, provider: str):
        """Property: Valid providers map to correct base URLs"""
        expected_base_url = LLMClientFactory.PROVIDERS[provider]["base_url"]
        actual_base_url = LLMClientFactory.get_base_url(provider)
        assert actual_base_url == expected_base_url
    
    @given(provider=st.sampled_from(["openai", "openrouter", "groq"]))
    @settings(max_examples=100, deadline=None)
    def test_valid_provider_creates_client_successfully(self, provider: str):
        """Property: Valid providers with valid API key create client without error"""
        # Use a dummy API key for testing client creation
        dummy_key = "test-api-key-12345"
        client = LLMClientFactory.create_client(provider, dummy_key)
        assert client is not None
        
        # Verify base_url is set correctly
        expected_base_url = LLMClientFactory.PROVIDERS[provider]["base_url"]
        if expected_base_url:
            assert str(client.base_url).rstrip('/') == expected_base_url.rstrip('/')
    
    def test_openai_uses_default_endpoint(self):
        """OpenAI provider should use default endpoint (None base_url)"""
        assert LLMClientFactory.get_base_url("openai") is None
    
    def test_openrouter_uses_correct_endpoint(self):
        """OpenRouter provider should use OpenRouter API endpoint"""
        assert LLMClientFactory.get_base_url("openrouter") == "https://openrouter.ai/api/v1"
    
    def test_groq_uses_correct_endpoint(self):
        """Groq provider should use Groq API endpoint"""
        assert LLMClientFactory.get_base_url("groq") == "https://api.groq.com/openai/v1"


class TestInvalidProviderRejection:
    """
    **Feature: openrouter-support, Property 2: Invalid provider rejection**
    *For any* string that is not "openai" or "openrouter", the LLMClientFactory 
    SHALL raise a ValueError with a descriptive message.
    **Validates: Requirements 1.3**
    """
    
    @given(provider=st.text().filter(lambda x: x not in ["openai", "openrouter", "groq"]))
    @settings(max_examples=100)
    def test_invalid_provider_raises_value_error(self, provider: str):
        """Property: Invalid providers raise ValueError"""
        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create_client(provider, "dummy-key")
        
        assert "Invalid provider" in str(exc_info.value)
        assert "openai" in str(exc_info.value)
        assert "openrouter" in str(exc_info.value)
    
    @given(provider=st.text().filter(lambda x: x not in ["openai", "openrouter", "groq"]))
    @settings(max_examples=100)
    def test_invalid_provider_validation_returns_false(self, provider: str):
        """Property: Invalid providers fail validation"""
        assert LLMClientFactory.validate_provider(provider) is False
    
    def test_empty_string_provider_rejected(self):
        """Empty string should be rejected as invalid provider"""
        assert LLMClientFactory.validate_provider("") is False
        with pytest.raises(ValueError):
            LLMClientFactory.create_client("", "dummy-key")
    
    def test_case_sensitive_provider(self):
        """Provider names should be case-sensitive"""
        assert LLMClientFactory.validate_provider("OpenAI") is False
        assert LLMClientFactory.validate_provider("OPENAI") is False
        assert LLMClientFactory.validate_provider("OpenRouter") is False


class TestFreeModelDetection:
    """
    **Feature: openrouter-support, Property 5: Free model detection**
    *For any* model string, the is_free_model function SHALL return True 
    if and only if the model ends with ":free".
    **Validates: Requirements 6.2**
    """
    
    @given(model_base=st.text(min_size=1))
    @settings(max_examples=100)
    def test_model_with_free_suffix_detected(self, model_base: str):
        """Property: Any model ending with :free is detected as free"""
        free_model = f"{model_base}:free"
        assert LLMClientFactory.is_free_model(free_model) is True
    
    @given(model=st.text().filter(
        lambda x: not x.endswith(":free") 
        and x not in LLMClientFactory.GROQ_MODELS 
        and x not in LLMClientFactory.GEMINI_MODELS
    ))
    @settings(max_examples=100)
    def test_model_without_free_suffix_not_detected(self, model: str):
        """Property: Models not ending with :free and not in free lists are not free"""
        assert LLMClientFactory.is_free_model(model) is False
    
    def test_known_free_models(self):
        """All known free models should be detected"""
        for model in LLMClientFactory.FREE_MODELS:
            assert LLMClientFactory.is_free_model(model) is True
    
    def test_paid_models_not_free(self):
        """Paid models should not be detected as free"""
        paid_models = [
            "gpt-4o-mini",
            "gpt-4",
            "claude-3-sonnet",
            "google/gemma-2-9b-it",  # Without :free suffix
        ]
        for model in paid_models:
            assert LLMClientFactory.is_free_model(model) is False
    
    def test_groq_models_are_free(self):
        """Groq models should be detected as free"""
        for model in LLMClientFactory.GROQ_MODELS:
            assert LLMClientFactory.is_free_model(model) is True
    
    def test_gemini_models_are_free(self):
        """Gemini models should be detected as free"""
        for model in LLMClientFactory.GEMINI_MODELS:
            assert LLMClientFactory.is_free_model(model) is True


class TestAPIKeyValidation:
    """Test API key validation in create_client"""
    
    @given(provider=st.sampled_from(["openai", "openrouter", "groq"]))
    @settings(max_examples=100)
    def test_missing_api_key_raises_error(self, provider: str):
        """Property: Missing API key raises ValueError with helpful message"""
        with pytest.raises(ValueError) as exc_info:
            LLMClientFactory.create_client(provider, "")
        
        expected_key_field = LLMClientFactory.get_api_key_field(provider)
        assert expected_key_field in str(exc_info.value)
    
    @given(provider=st.sampled_from(["openai", "openrouter", "groq"]))
    @settings(max_examples=100)
    def test_get_api_key_field_returns_correct_field(self, provider: str):
        """Property: get_api_key_field returns correct field name for provider"""
        expected = LLMClientFactory.PROVIDERS[provider]["key_field"]
        actual = LLMClientFactory.get_api_key_field(provider)
        assert actual == expected
    
    def test_groq_api_key_field(self):
        """Groq provider should use groq_api_key field"""
        assert LLMClientFactory.get_api_key_field("groq") == "groq_api_key"
