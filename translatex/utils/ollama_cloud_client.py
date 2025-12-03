"""
Ollama Cloud Client - Custom async client for Ollama Cloud API
Ollama Cloud uses a different API format than OpenAI
"""
import aiohttp
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Choice:
    message: Message
    index: int = 0
    finish_reason: str = "stop"


@dataclass
class ChatCompletion:
    """OpenAI-compatible response format"""
    choices: list[Choice]
    model: str
    id: str = "ollama-cloud"
    

class OllamaCloudClient:
    """Async client for Ollama Cloud API"""
    
    BASE_URL = "https://ollama.com/api"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat = self.Chat(self)
    
    class Chat:
        def __init__(self, client: "OllamaCloudClient"):
            self.client = client
            self.completions = self.Completions(client)
        
        class Completions:
            def __init__(self, client: "OllamaCloudClient"):
                self.client = client
            
            async def create(
                self,
                model: str,
                messages: list[dict],
                temperature: float = 0.7,
                max_tokens: Optional[int] = None,
                **kwargs
            ) -> ChatCompletion:
                """Create chat completion using Ollama Cloud API"""
                # Remove -cloud suffix if present (Ollama Cloud doesn't use it)
                if model.endswith("-cloud"):
                    model = model[:-6]
                
                url = f"{OllamaCloudClient.BASE_URL}/chat"
                headers = {
                    "Authorization": f"Bearer {self.client.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature
                    }
                }
                
                if max_tokens:
                    payload["options"]["num_predict"] = max_tokens
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"Ollama Cloud API error: {response.status} - {error_text}")
                        
                        data = await response.json()
                        
                        # Convert Ollama response to OpenAI-compatible format
                        content = data.get("message", {}).get("content", "")
                        
                        return ChatCompletion(
                            choices=[
                                Choice(
                                    message=Message(role="assistant", content=content),
                                    finish_reason=data.get("done_reason", "stop")
                                )
                            ],
                            model=data.get("model", model)
                        )
