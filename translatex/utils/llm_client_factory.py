"""
LLM Client Factory for WordFlux
Supports multiple providers: OpenAI, OpenRouter, Groq, and Gemini
"""
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)


class LLMClientFactory:
    """Factory class to create LLM clients for different providers"""
    
    PROVIDERS = {
        "openai": {
            "base_url": None,  # Use default OpenAI endpoint
            "key_field": "openai_api_key"
        },
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "key_field": "openrouter_api_key"
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "key_field": "groq_api_key"
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "key_field": "gemini_api_key"
        }
    }
    
    # OpenRouter free models
    FREE_MODELS = [
        "google/gemma-2-9b-it:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "qwen/qwen-2-7b-instruct:free",
    ]
    
    # Groq free models (free tier with rate limits)
    GROQ_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama-guard-3-8b",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "gemma2-9b-it",
        "mixtral-8x7b-32768",
    ]
    
    # Gemini free models (free tier with rate limits)
    # Rate limits: RPM = requests/min, TPM = tokens/min, RPD = requests/day
    GEMINI_MODELS = [
        "gemini-2.5-pro-preview-06-05",
        "gemini-2.5-flash-preview-05-20",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
    ]
    
    # Rate limits per model (RPM = requests per minute)
    # Used to calculate optimal delay between requests
    MODEL_RATE_LIMITS = {
        # Gemini models
        "gemini-2.5-pro-preview-06-05": {"rpm": 5, "recommended_concurrent": 1, "delay": 12},
        "gemini-2.5-flash-preview-05-20": {"rpm": 10, "recommended_concurrent": 1, "delay": 10, "sequential": True},
        "gemini-2.5-pro": {"rpm": 5, "recommended_concurrent": 1, "delay": 12},
        "gemini-2.5-flash": {"rpm": 10, "recommended_concurrent": 2, "delay": 6},
        "gemini-2.0-flash": {"rpm": 15, "recommended_concurrent": 3, "delay": 4},
        "gemini-2.0-flash-lite": {"rpm": 30, "recommended_concurrent": 5, "delay": 2},
        "gemini-1.5-flash": {"rpm": 15, "recommended_concurrent": 3, "delay": 4},
        "gemini-1.5-flash-8b": {"rpm": 15, "recommended_concurrent": 3, "delay": 4},
        "gemini-1.5-pro": {"rpm": 2, "recommended_concurrent": 1, "delay": 30},
        # Groq models (TPM limited, not RPM)
        "llama-3.3-70b-versatile": {"rpm": 30, "recommended_concurrent": 3, "delay": 2},
        "llama-3.1-8b-instant": {"rpm": 30, "recommended_concurrent": 5, "delay": 2},
        "gemma2-9b-it": {"rpm": 30, "recommended_concurrent": 5, "delay": 2},
        "mixtral-8x7b-32768": {"rpm": 30, "recommended_concurrent": 3, "delay": 2},
        # OpenAI models (high limits)
        "gpt-4o-mini": {"rpm": 500, "recommended_concurrent": 50, "delay": 0},
        "gpt-4o": {"rpm": 500, "recommended_concurrent": 50, "delay": 0},
        "gpt-4": {"rpm": 200, "recommended_concurrent": 20, "delay": 0},
    }
    
    @staticmethod
    def get_rate_limit_config(model: str) -> dict:
        """
        Get rate limit configuration for a model.
        
        Args:
            model: Model identifier
            
        Returns:
            Dict with rpm, recommended_concurrent, delay, and sequential flag
        """
        # Check exact match first
        if model in LLMClientFactory.MODEL_RATE_LIMITS:
            config = LLMClientFactory.MODEL_RATE_LIMITS[model].copy()
            if "sequential" not in config:
                config["sequential"] = False
            return config
        
        # Check partial match for preview models
        for known_model, known_config in LLMClientFactory.MODEL_RATE_LIMITS.items():
            if known_model in model or model in known_model:
                config = known_config.copy()
                if "sequential" not in config:
                    config["sequential"] = False
                return config
        
        # Default conservative config
        return {"rpm": 10, "recommended_concurrent": 2, "delay": 6, "sequential": False}
    
    @staticmethod
    def create_client(provider: str, api_key: str) -> AsyncOpenAI:
        """
        Create AsyncOpenAI client for the specified provider.
        
        Args:
            provider: Provider name ("openai" or "openrouter")
            api_key: API key for the provider
            
        Returns:
            AsyncOpenAI client configured for the provider
            
        Raises:
            ValueError: If provider is not supported or api_key is missing
        """
        if not LLMClientFactory.validate_provider(provider):
            supported = ", ".join(LLMClientFactory.PROVIDERS.keys())
            raise ValueError(f"Invalid provider '{provider}'. Supported: {supported}")
        
        if not api_key:
            key_field = LLMClientFactory.get_api_key_field(provider)
            raise ValueError(f"API key required for provider '{provider}'. Set '{key_field}' in config.")
        
        provider_config = LLMClientFactory.PROVIDERS[provider]
        base_url = provider_config["base_url"]
        
        if base_url:
            return AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            return AsyncOpenAI(api_key=api_key)
    
    @staticmethod
    def validate_provider(provider: str) -> bool:
        """
        Validate if provider is supported.
        
        Args:
            provider: Provider name to validate
            
        Returns:
            True if provider is supported, False otherwise
        """
        return provider in LLMClientFactory.PROVIDERS
    
    @staticmethod
    def is_free_model(model: str) -> bool:
        """
        Check if model is a free model.
        
        Args:
            model: Model identifier to check
            
        Returns:
            True if model ends with ":free" or is a Groq/Gemini model (free tier)
        """
        # OpenRouter free models end with :free
        if model.endswith(":free"):
            return True
        # Groq models are free (with rate limits)
        if model in LLMClientFactory.GROQ_MODELS:
            return True
        # Gemini models are free (with rate limits)
        if model in LLMClientFactory.GEMINI_MODELS:
            return True
        return False
    
    @staticmethod
    def get_api_key_field(provider: str) -> str:
        """
        Get the config field name for API key.
        
        Args:
            provider: Provider name
            
        Returns:
            Config field name for the API key
            
        Raises:
            ValueError: If provider is not supported
        """
        if not LLMClientFactory.validate_provider(provider):
            supported = ", ".join(LLMClientFactory.PROVIDERS.keys())
            raise ValueError(f"Invalid provider '{provider}'. Supported: {supported}")
        
        return LLMClientFactory.PROVIDERS[provider]["key_field"]
    
    @staticmethod
    def get_base_url(provider: str) -> str | None:
        """
        Get the base URL for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Base URL string or None for default
            
        Raises:
            ValueError: If provider is not supported
        """
        if not LLMClientFactory.validate_provider(provider):
            supported = ", ".join(LLMClientFactory.PROVIDERS.keys())
            raise ValueError(f"Invalid provider '{provider}'. Supported: {supported}")
        
        return LLMClientFactory.PROVIDERS[provider]["base_url"]
