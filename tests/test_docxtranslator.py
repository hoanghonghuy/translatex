"""
Property-based tests for DocxTranslator
Uses Hypothesis for property-based testing
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock
import tempfile
import os


class TestDefaultProviderFallback:
    """
    **Feature: openrouter-support, Property 4: Default provider fallback**
    *For any* configuration where provider is not specified, the system 
    SHALL default to "openai" provider.
    **Validates: Requirements 5.1, 5.2**
    """
    
    def test_default_provider_is_openai(self):
        """Default provider should be openai when not specified"""
        # Import here to avoid import errors during collection
        from translatex.docxtranslator import DocxTranslator
        
        # Create a temporary docx file for testing
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        
        try:
            # Mock Document to avoid needing a real docx file
            with patch('translatex.worker.extractor.Document'), \
                 patch('translatex.worker.injector.Document'):
                
                translator = DocxTranslator(
                    input_file=temp_file,
                    openai_api_key="test-key-12345"
                    # provider not specified - should default to "openai"
                )
                
                assert translator.provider == "openai"
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_explicit_openai_provider(self):
        """Explicit openai provider should work"""
        from translatex.docxtranslator import DocxTranslator
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        
        try:
            with patch('translatex.worker.extractor.Document'), \
                 patch('translatex.worker.injector.Document'):
                
                translator = DocxTranslator(
                    input_file=temp_file,
                    openai_api_key="test-key-12345",
                    provider="openai"
                )
                
                assert translator.provider == "openai"
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_explicit_openrouter_provider(self):
        """Explicit openrouter provider should work"""
        from translatex.docxtranslator import DocxTranslator
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        
        try:
            with patch('translatex.worker.extractor.Document'), \
                 patch('translatex.worker.injector.Document'):
                
                translator = DocxTranslator(
                    input_file=temp_file,
                    openrouter_api_key="test-key-12345",
                    provider="openrouter"
                )
                
                assert translator.provider == "openrouter"
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_missing_openai_key_raises_error(self):
        """Missing OpenAI key should raise error when provider is openai"""
        from translatex.docxtranslator import DocxTranslator
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        
        try:
            with patch('translatex.worker.extractor.Document'), \
                 patch('translatex.worker.injector.Document'):
                
                with pytest.raises(ValueError) as exc_info:
                    DocxTranslator(
                        input_file=temp_file,
                        provider="openai"
                        # No API key provided
                    )
                
                assert "openai" in str(exc_info.value).lower() and "api key" in str(exc_info.value).lower()
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_missing_openrouter_key_raises_error(self):
        """Missing OpenRouter key should raise error when provider is openrouter"""
        from translatex.docxtranslator import DocxTranslator
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        
        try:
            with patch('translatex.worker.extractor.Document'), \
                 patch('translatex.worker.injector.Document'):
                
                with pytest.raises(ValueError) as exc_info:
                    DocxTranslator(
                        input_file=temp_file,
                        provider="openrouter"
                        # No API key provided
                    )
                
                assert "openrouter" in str(exc_info.value).lower() and "api key" in str(exc_info.value).lower()
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_invalid_provider_raises_error(self):
        """Invalid provider should raise error"""
        from translatex.docxtranslator import DocxTranslator
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        
        try:
            with patch('translatex.worker.extractor.Document'), \
                 patch('translatex.worker.injector.Document'):
                
                with pytest.raises(ValueError) as exc_info:
                    DocxTranslator(
                        input_file=temp_file,
                        openai_api_key="test-key",
                        provider="invalid_provider"
                    )
                
                assert "Invalid provider" in str(exc_info.value)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    @given(provider=st.sampled_from(["openai", "openrouter", "groq", "gemini"]))
    @settings(max_examples=100, deadline=None)
    def test_valid_providers_accepted(self, provider: str):
        """
        Property: All valid providers should be accepted
        **Feature: openrouter-support, Property 4: Default provider fallback**
        **Validates: Requirements 5.1, 5.2**
        """
        from translatex.docxtranslator import DocxTranslator
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        
        try:
            with patch('translatex.worker.extractor.Document'), \
                 patch('translatex.worker.injector.Document'):
                
                api_key_kwargs = {}
                if provider == "openai":
                    api_key_kwargs["openai_api_key"] = "test-key-12345"
                elif provider == "openrouter":
                    api_key_kwargs["openrouter_api_key"] = "test-key-12345"
                elif provider == "groq":
                    api_key_kwargs["groq_api_key"] = "test-key-12345"
                else:  # gemini
                    api_key_kwargs["gemini_api_key"] = "test-key-12345"
                
                translator = DocxTranslator(
                    input_file=temp_file,
                    provider=provider,
                    **api_key_kwargs
                )
                
                assert translator.provider == provider
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_explicit_groq_provider(self):
        """Explicit groq provider should work"""
        from translatex.docxtranslator import DocxTranslator
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        
        try:
            with patch('translatex.worker.extractor.Document'), \
                 patch('translatex.worker.injector.Document'):
                
                translator = DocxTranslator(
                    input_file=temp_file,
                    groq_api_key="test-key-12345",
                    provider="groq"
                )
                
                assert translator.provider == "groq"
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_missing_groq_key_raises_error(self):
        """Missing Groq key should raise error when provider is groq"""
        from translatex.docxtranslator import DocxTranslator
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        
        try:
            with patch('translatex.worker.extractor.Document'), \
                 patch('translatex.worker.injector.Document'):
                
                with pytest.raises(ValueError) as exc_info:
                    DocxTranslator(
                        input_file=temp_file,
                        provider="groq"
                        # No API key provided
                    )
                
                assert "Groq API key" in str(exc_info.value)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_explicit_gemini_provider(self):
        """Explicit gemini provider should work"""
        from translatex.docxtranslator import DocxTranslator
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        
        try:
            with patch('translatex.worker.extractor.Document'), \
                 patch('translatex.worker.injector.Document'):
                
                translator = DocxTranslator(
                    input_file=temp_file,
                    gemini_api_key="test-key-12345",
                    provider="gemini"
                )
                
                assert translator.provider == "gemini"
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_missing_gemini_key_raises_error(self):
        """Missing Gemini key should raise error when provider is gemini"""
        from translatex.docxtranslator import DocxTranslator
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_file = f.name
        
        try:
            with patch('translatex.worker.extractor.Document'), \
                 patch('translatex.worker.injector.Document'):
                
                with pytest.raises(ValueError) as exc_info:
                    DocxTranslator(
                        input_file=temp_file,
                        provider="gemini"
                        # No API key provided
                    )
                
                assert "Gemini API key" in str(exc_info.value)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
