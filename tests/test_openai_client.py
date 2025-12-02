"""
Property-based tests for OpenAIClientManager
Uses Hypothesis for property-based testing
"""
import pytest
from hypothesis import given, strategies as st, settings
from translatex.utils.openai_client import OpenAIClientManager
from translatex.utils.llm_client_factory import LLMClientFactory


class TestAPIKeyFieldSelection:
    """
    **Feature: openrouter-support, Property 3: API key field selection**
    *For any* provider, the system SHALL use the correct API key field 
    (openai_api_key for openai, openrouter_api_key for openrouter).
    **Validates: Requirements 2.1, 2.3**
    """
    
    @given(provider=st.sampled_from(["openai", "openrouter", "groq"]))
    @settings(max_examples=100, deadline=None)
    def test_client_manager_uses_correct_provider(self, provider: str):
        """Property: ClientManager stores and returns correct provider"""
        dummy_key = "test-api-key-12345"
        manager = OpenAIClientManager(api_key=dummy_key, provider=provider)
        
        assert manager.get_provider() == provider
    
    @given(provider=st.sampled_from(["openai", "openrouter", "groq"]))
    @settings(max_examples=100, deadline=None)
    def test_client_manager_creates_valid_client(self, provider: str):
        """Property: ClientManager creates a valid client for any supported provider"""
        dummy_key = "test-api-key-12345"
        manager = OpenAIClientManager(api_key=dummy_key, provider=provider)
        
        client = manager.get_client()
        assert client is not None
    
    def test_openai_api_key_field(self):
        """OpenAI provider should use openai_api_key field"""
        assert LLMClientFactory.get_api_key_field("openai") == "openai_api_key"
    
    def test_openrouter_api_key_field(self):
        """OpenRouter provider should use openrouter_api_key field"""
        assert LLMClientFactory.get_api_key_field("openrouter") == "openrouter_api_key"
    
    def test_missing_api_key_raises_error(self):
        """Missing API key should raise ValueError"""
        with pytest.raises(ValueError) as exc_info:
            OpenAIClientManager(api_key="", provider="openai")
        
        assert "openai_api_key" in str(exc_info.value)
    
    def test_invalid_provider_raises_error(self):
        """Invalid provider should raise ValueError"""
        with pytest.raises(ValueError) as exc_info:
            OpenAIClientManager(api_key="test-key", provider="invalid")
        
        assert "Invalid provider" in str(exc_info.value)
    
    def test_default_provider_is_openai(self):
        """Default provider should be openai"""
        manager = OpenAIClientManager(api_key="test-key")
        assert manager.get_provider() == "openai"
