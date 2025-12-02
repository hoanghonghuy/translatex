"""Documentation translator for Markdown and MDX files."""

import os
from pathlib import Path
from typing import Optional, Callable
from tqdm import tqdm

from .markdown_parser import MarkdownParser, ContentBlock
from .mdx_parser import MDXParser
from .scanner import DocsScanner, DocFile
from .manifest import ManifestManager
from translatex.utils.cache import TranslationCache
from translatex.utils.glossary import GlossaryLoader
from translatex.utils.file_logger import get_logger
from translatex.utils.llm_client_factory import LLMClientFactory
from translatex.utils.openai_client import OpenAIClientManager
from translatex.utils.prompt_builder import PromptBuilder


class DocsTranslator:
    """Main translator for documentation files."""
    
    def __init__(
        self,
        api_key: str,
        provider: str = "gemini",
        model: str = "gemini-2.0-flash",
        source_lang: str = "English",
        target_lang: str = "Vietnamese",
        cache_enabled: bool = True,
        glossary_file: Optional[str] = None,
        translatable_fields: list = None,
    ):
        """Initialize docs translator.
        
        Args:
            api_key: API key for LLM provider
            provider: LLM provider name
            model: Model name
            source_lang: Source language
            target_lang: Target language
            cache_enabled: Enable translation cache
            glossary_file: Path to glossary file
            translatable_fields: Frontmatter fields to translate
        """
        self.provider = provider
        self.model = model
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        # Initialize LLM client
        self.client_manager = OpenAIClientManager(api_key=api_key, provider=provider)
        self.client = self.client_manager.get_client()
        
        # Initialize parsers
        self.md_parser = MarkdownParser(translatable_fields=translatable_fields)
        self.mdx_parser = MDXParser(translatable_fields=translatable_fields)
        
        # Initialize cache
        self.cache = TranslationCache(enabled=cache_enabled) if cache_enabled else None
        
        # Initialize glossary
        self.glossary = GlossaryLoader(glossary_file=glossary_file)
        
        # Initialize prompt builder
        self.prompt_builder = PromptBuilder(
            source_lang=source_lang,
            target_lang=target_lang,
            glossary=self.glossary.get_terms()
        )
        
        self.logger = get_logger()
        
        # Stats
        self.stats = {
            "files_translated": 0,
            "files_cached": 0,
            "files_failed": 0,
            "api_calls": 0,
            "cache_hits": 0
        }
    
    def translate_file(self, file_path: str, output_path: str = None) -> Optional[str]:
        """Translate a single markdown/mdx file.
        
        Args:
            file_path: Path to source file
            output_path: Path for output file (optional)
            
        Returns:
            Translated content or None on error
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return None
        
        # Read source content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return None
        
        # Select parser based on extension
        ext = file_path.suffix.lower()
        parser = self.mdx_parser if ext == ".mdx" else self.md_parser
        
        # Parse content
        blocks = parser.parse(content)
        
        # Get translatable segments
        segments = parser.get_translatable_text(blocks)
        
        if not segments:
            self.logger.debug(f"No translatable content in {file_path}")
            return content
        
        # Translate each segment
        translations = {}
        for idx, text in segments:
            translated = self._translate_text(text)
            if translated:
                translations[idx] = translated
        
        # Update blocks with translations
        blocks = parser.update_translated_text(blocks, translations)
        
        # Reconstruct content
        translated_content = parser.reconstruct(blocks)
        
        # Write output if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(translated_content)
                self.logger.debug(f"Wrote translated file: {output_path}")
            except IOError as e:
                self.logger.error(f"Failed to write {output_path}: {e}")
        
        return translated_content
    
    def _translate_text(self, text: str) -> Optional[str]:
        """Translate a text segment using LLM.
        
        Args:
            text: Text to translate
            
        Returns:
            Translated text or None on error
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get(text)
            if cached:
                self.stats["cache_hits"] += 1
                return cached
        
        # Build prompt for markdown translation
        system_prompt = self._build_docs_system_prompt()
        user_prompt = f"Translate the following documentation text:\n\n{text}"
        
        try:
            import asyncio
            
            async def do_translate():
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return response.choices[0].message.content.strip()
            
            translated = asyncio.run(do_translate())
            self.stats["api_calls"] += 1
            
            # Store in cache
            if self.cache and translated:
                self.cache.set(text, translated)
            
            return translated
            
        except Exception as e:
            self.logger.error(f"Translation error: {e}")
            return None
    
    def _build_docs_system_prompt(self) -> str:
        """Build system prompt for documentation translation."""
        glossary_section = ""
        if self.glossary:
            terms = self.glossary.get_terms()
            if terms:
                glossary_section = "\n\nGLOSSARY (use these exact translations):\n"
                glossary_section += "\n".join(f"- {k} → {v}" for k, v in list(terms.items())[:50])
        
        return f"""You are a professional technical documentation translator from {self.source_lang} to {self.target_lang}.

TRANSLATION GUIDELINES:
- Translate naturally while maintaining technical accuracy
- Preserve all markdown formatting (headers, lists, bold, italic, etc.)
- Keep all placeholders like __CODE_BLOCK_0__, __INLINE_CODE_0__, __URL_0__, etc. unchanged
- Do not translate code, URLs, file paths, or technical identifiers
- Maintain the same paragraph structure
{glossary_section}

IMPORTANT:
- Return ONLY the translated text
- Do not add explanations or notes
- Preserve all special placeholders exactly as they appear"""
    
    def translate_directory(
        self,
        source_dir: str,
        output_dir: str,
        force: bool = False,
        on_progress: Callable[[int, int, str], None] = None
    ) -> dict:
        """Translate entire documentation directory.
        
        Args:
            source_dir: Source documentation directory
            output_dir: Output directory
            force: Force retranslation of all files
            on_progress: Progress callback(current, total, filename)
            
        Returns:
            Translation statistics
        """
        self.logger.info(f"Starting docs translation: {source_dir} -> {output_dir}")
        
        # Initialize scanner
        scanner = DocsScanner(source_dir, output_dir)
        
        # Initialize manifest
        manifest_path = Path(output_dir) / ".translatex_manifest.json"
        manifest = ManifestManager(str(manifest_path))
        if not force:
            manifest.load()
        manifest.set_directories(source_dir, output_dir)
        
        # Scan for files
        files = scanner.scan()
        
        if not files:
            self.logger.warning("No documentation files found")
            return self.stats
        
        # Ensure output structure
        scanner.ensure_output_structure()
        
        # Copy assets
        scanner.copy_assets()
        
        # Translate files
        total = len(files)
        
        with tqdm(total=total, desc="Translating docs", unit="file") as pbar:
            for doc_file in files:
                filename = Path(doc_file.source_path).name
                pbar.set_postfix_str(filename[:30])
                
                if on_progress:
                    on_progress(pbar.n + 1, total, filename)
                
                # Check if file needs translation
                if not force and not manifest.is_changed(doc_file.relative_path, doc_file.source_path):
                    self.logger.debug(f"Skipping unchanged: {doc_file.relative_path}")
                    self.stats["files_cached"] += 1
                    pbar.update(1)
                    continue
                
                # Translate file
                try:
                    result = self.translate_file(doc_file.source_path, doc_file.output_path)
                    
                    if result:
                        # Update manifest
                        manifest.update(
                            doc_file.relative_path,
                            doc_file.source_hash,
                            doc_file.output_path
                        )
                        self.stats["files_translated"] += 1
                    else:
                        self.stats["files_failed"] += 1
                        
                except Exception as e:
                    self.logger.error(f"Failed to translate {doc_file.relative_path}: {e}")
                    self.stats["files_failed"] += 1
                
                pbar.update(1)
        
        # Save manifest
        manifest.save()
        
        # Log summary
        self._log_summary()
        
        return self.stats
    
    def _log_summary(self):
        """Log translation summary."""
        self.logger.info("=" * 50)
        self.logger.info("DOCS TRANSLATION SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Files translated: {self.stats['files_translated']}")
        self.logger.info(f"Files cached (unchanged): {self.stats['files_cached']}")
        self.logger.info(f"Files failed: {self.stats['files_failed']}")
        self.logger.info(f"API calls: {self.stats['api_calls']}")
        self.logger.info(f"Cache hits: {self.stats['cache_hits']}")
        self.logger.info("=" * 50)
    
    def should_translate(self, file_path: str, manifest: ManifestManager) -> bool:
        """Check if file needs translation based on hash.
        
        Args:
            file_path: Source file path
            manifest: ManifestManager instance
            
        Returns:
            True if file should be translated
        """
        scanner = DocsScanner("", "")  # Dummy for relative path
        relative = Path(file_path).name  # Simplified
        return manifest.is_changed(relative, file_path)
