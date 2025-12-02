from openai import AsyncOpenAI
from translatex.utils.llm_client_factory import LLMClientFactory
import logging

logger = logging.getLogger(__name__)


class OpenAIClientManager:
    """Quản lý LLM API client (OpenAI hoặc OpenRouter)"""
    
    def __init__(self, api_key: str, provider: str = "openai"):
        """
        Khởi tạo LLM client
        
        Args:
            api_key: API key cho provider
            provider: Provider name ("openai" hoặc "openrouter")
        """
        self.provider = provider
        self.api_key = api_key
        
        # Validate và tạo client qua factory
        self.client = LLMClientFactory.create_client(provider, api_key)
        
        logger.info(f"Initialized {provider} client")
    
    def get_client(self) -> AsyncOpenAI:
        """Trả về LLM client"""
        return self.client
    
    def get_provider(self) -> str:
        """Trả về provider name"""
        return self.provider
