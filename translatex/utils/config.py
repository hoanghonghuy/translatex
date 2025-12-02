"""Configuration management for TranslateX."""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .exceptions import ConfigError


@dataclass
class TranslateXConfig:
    """Configuration dataclass with all settings."""
    
    # Provider settings
    provider: str = "gemini"
    openai_api_key: str = ""
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    gemini_api_key: str = ""
    
    # Model settings
    model: str = "gemini-2.0-flash"
    
    # Translation settings
    source_lang: str = "English"
    target_lang: str = "Vietnamese"
    
    # Performance settings
    max_concurrent: int = 5
    max_chunk_size: int = 5000
    
    # Advanced features - Resume/Checkpoint
    auto_resume: bool = True
    
    # Advanced features - Batch Processing
    batch_enabled: bool = True
    
    # Advanced features - Cache
    cache_enabled: bool = True
    
    # Advanced features - Context Window
    context_window: int = 2
    
    # Advanced features - Review Mode
    review_mode: bool = False
    
    # Advanced features - Error Handling
    max_retries: int = 3
    
    # Advanced features - Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    
    # Advanced features - Glossary
    glossary_file: Optional[str] = "glossary.yaml"
    
    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "TranslateXConfig":
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {config_path}")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
    
    def get_api_key(self) -> str:
        """Get API key for current provider."""
        key_map = {
            "openai": self.openai_api_key,
            "gemini": self.gemini_api_key,
            "groq": self.groq_api_key,
            "openrouter": self.openrouter_api_key,
        }
        return key_map.get(self.provider, "")
