"""DocxTranslator - Main translation orchestrator with advanced features."""

import os
from pathlib import Path
from typing import Optional

from translatex.worker.extractor import Extractor
from translatex.worker.injector import Injector
from translatex.worker.translator import Translator
from translatex.utils.llm_client_factory import LLMClientFactory
from translatex.utils.cache import TranslationCache
from translatex.utils.checkpoint import CheckpointManager
from translatex.utils.context import ContextWindow
from translatex.utils.glossary import GlossaryLoader
from translatex.utils.review import ReviewGenerator
from translatex.utils.file_logger import get_logger


class DocxTranslator:
    """
    Translate a DOCX file while preserving formatting
    Supports OpenAI, OpenRouter, Groq, and Gemini providers
    
    Advanced Features:
    - Resume/Checkpoint: Resume interrupted translations
    - Translation Cache: Avoid re-translating identical text
    - Context Window: Include previous segments for coherent translation
    - Custom Glossary: Define custom terminology translations
    - Review Mode: Generate HTML comparison file
    
    Author: Hoang Hong Huy
    Email: huy.hoanghong.work@gmail.com
    GitHub: https://github.com/hoanghonghuy
    """

    def __init__(
        self,
        input_file: str,
        output_dir: str = "output",
        openai_api_key: str = "",
        openrouter_api_key: str = "",
        groq_api_key: str = "",
        gemini_api_key: str = "",
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        source_lang: str = "English",
        target_lang: str = "Vietnamese",
        max_chunk_size: int = 5000,
        max_concurrent: int = 100,
        # Advanced features
        cache_enabled: bool = True,
        context_window: int = 2,
        glossary_file: Optional[str] = None,
        review_mode: bool = False,
        auto_resume: bool = True,
    ):
        """
        Initialize DocxTranslator
        
        Args:
            input_file: Path to input DOCX file
            output_dir: Output directory
            openai_api_key: API key for OpenAI
            openrouter_api_key: API key for OpenRouter
            groq_api_key: API key for Groq
            gemini_api_key: API key for Gemini
            provider: Provider name ("openai", "openrouter", "groq", or "gemini")
            model: Model name
            source_lang: Source language
            target_lang: Target language
            max_chunk_size: Maximum chunk size
            max_concurrent: Maximum concurrent requests
            cache_enabled: Enable translation cache
            context_window: Number of previous segments as context (0 = disabled)
            glossary_file: Path to glossary YAML file
            review_mode: Generate review HTML file
            auto_resume: Auto-resume from checkpoint
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.provider = provider
        self.model = model
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.max_chunk_size = max_chunk_size
        self.max_concurrent = max_concurrent
        
        # Advanced feature settings
        self.cache_enabled = cache_enabled
        self.context_window_size = context_window
        self.glossary_file = glossary_file
        self.review_mode = review_mode
        self.auto_resume = auto_resume
        
        self.logger = get_logger()
        
        # Validate provider
        if not LLMClientFactory.validate_provider(provider):
            supported = ", ".join(LLMClientFactory.PROVIDERS.keys())
            raise ValueError(f"Invalid provider '{provider}'. Supported: {supported}")
        
        # Select correct API key based on provider
        self.api_key = self._get_api_key(
            provider, openai_api_key, openrouter_api_key, groq_api_key, gemini_api_key
        )

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Derive filenames
        file_name = os.path.splitext(os.path.basename(input_file))[0]
        self.checkpoint_file = os.path.join(output_dir, f"{file_name}_checkpoint.json")
        self.output_file = os.path.join(output_dir, f"{file_name}_translated.docx")
        self.cache_file = os.path.join(output_dir, ".translatex_cache.json")
        self.review_file = os.path.join(output_dir, f"{file_name}_review.html")
        
        # Initialize advanced feature components
        self._init_advanced_features()

        # Initialize pipeline components
        self.extractor = Extractor(self.input_file, self.checkpoint_file)
        self.translator = Translator(
            self.checkpoint_file,
            self.api_key,
            self.provider,
            self.model,
            self.source_lang,
            self.target_lang,
            self.max_chunk_size,
            self.max_concurrent,
            cache=self.cache,
            context_window=self.context,
            glossary=self.glossary.get_terms() if self.glossary else None,
        )
        self.injector = Injector(self.input_file, self.checkpoint_file, self.output_file)
    
    def _get_api_key(self, provider: str, openai_key: str, openrouter_key: str, 
                     groq_key: str, gemini_key: str) -> str:
        """Get API key for the specified provider."""
        key_map = {
            "openai": openai_key,
            "openrouter": openrouter_key,
            "groq": groq_key,
            "gemini": gemini_key,
        }
        api_key = key_map.get(provider, openai_key)
        if not api_key:
            raise ValueError(f"{provider.title()} API key not found. Please provide '{provider}_api_key'.")
        return api_key
    
    def _init_advanced_features(self):
        """Initialize advanced feature components."""
        # Translation cache
        self.cache = TranslationCache(
            cache_file=self.cache_file,
            enabled=self.cache_enabled
        )
        if self.cache_enabled:
            self.logger.info(f"Cache enabled: {self.cache.size()} entries loaded")
        
        # Context window
        self.context = ContextWindow(window_size=self.context_window_size)
        if self.context_window_size > 0:
            self.logger.info(f"Context window: {self.context_window_size} segments")
        
        # Glossary
        self.glossary = GlossaryLoader(glossary_file=self.glossary_file)
        self.logger.info(f"Glossary: {self.glossary.size()} terms loaded")
        
        # Checkpoint manager
        self.checkpoint_manager = CheckpointManager(self.checkpoint_file)
        
        # Review generator
        self.review_generator = ReviewGenerator(self.review_file) if self.review_mode else None

    def translate(self) -> str:
        """Run the entire translation pipeline.
        
        Returns:
            Path to output file
        """
        # Check for existing checkpoint
        if self.auto_resume and self.checkpoint_manager.exists():
            progress = self.checkpoint_manager.get_progress()
            if progress:
                print(f"Found checkpoint: {progress['completed']}/{progress['total']} segments completed")
                self.logger.info(f"Resuming from checkpoint: {progress['completed']}/{progress['total']}")
        
        # Extract segments
        self.extract()
        
        # Translate
        self.translator.translate()
        
        # Inject translations
        self.inject()
        
        # Generate review file if enabled
        if self.review_mode and self.review_generator:
            self._generate_review()
        
        # Clear checkpoint on success
        if self.checkpoint_manager.exists():
            self.checkpoint_manager.clear()
            self.logger.info("Checkpoint cleared after successful translation")
        
        return self.get_output_path()
    
    async def atranslate(self) -> str:
        """Run the entire translation pipeline asynchronously.
        
        Returns:
            Path to output file
        """
        self.extract()
        await self.translator._translate_all()
        self.inject()
        
        if self.review_mode and self.review_generator:
            self._generate_review()
        
        return self.get_output_path()

    def extract(self):
        """Extract segments and save checkpoint"""
        self.extractor.extract()

    def inject(self):
        """Inject translated segments into a new DOCX file"""
        self.injector.inject()
    
    def _generate_review(self):
        """Generate HTML review file for translation comparison."""
        import json
        
        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Add text segments to review
            for seg in data.get("text_segments", []):
                original = seg.get("full_text", "")
                translated = "".join(
                    run.get("translated_text", run.get("text", ""))
                    for run in seg.get("runs_list", [])
                )
                self.review_generator.add_segment(
                    index=seg.get("seg_idx", 0),
                    original=original,
                    translated=translated
                )
            
            # Generate HTML
            source_name = Path(self.input_file).name
            self.review_generator.generate(source_filename=source_name)
            self.logger.info(f"Review file generated: {self.review_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to generate review file: {e}")

    def get_output_path(self) -> str:
        """Return the absolute path of the translated file"""
        return os.path.abspath(self.output_file)
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "enabled": self.cache_enabled,
            "entries": self.cache.size() if self.cache else 0,
        }
