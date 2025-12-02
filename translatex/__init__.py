"""
TranslateX
AI-powered DOCX translation with format preservation.
Supports OpenAI, Gemini, Groq, and OpenRouter.

Author: Hoang Hong Huy
Email: huy.hoanghong.work@gmail.com
GitHub: https://github.com/hoanghonghuy
"""
from .docxtranslator import DocxTranslator
from .batch import BatchProcessor
from .utils.cache import TranslationCache
from .utils.checkpoint import CheckpointManager
from .utils.context import ContextWindow
from .utils.glossary import GlossaryLoader
from .utils.review import ReviewGenerator
from .utils.config import TranslateXConfig

__version__ = "1.1.0"

__all__ = [
    "DocxTranslator",
    "BatchProcessor",
    "TranslationCache",
    "CheckpointManager",
    "ContextWindow",
    "GlossaryLoader",
    "ReviewGenerator",
    "TranslateXConfig",
]
