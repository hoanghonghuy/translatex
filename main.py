"""TranslateX - DOCX Translation Tool with Advanced Features"""

import os
import sys
import argparse
import yaml

from translatex import DocxTranslator
from translatex.batch import BatchProcessor
from translatex.docs.translator import DocsTranslator
from translatex.utils.file_logger import setup_logger, get_logger
from translatex.utils.console import (
    console, print_banner, print_config, print_success, print_error,
    print_warning, print_info, print_summary, print_file_result,
    create_progress, print_docs_header, print_docx_header
)


def load_config(config_path: str) -> dict:
    """Load config from YAML file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print_error(f"Config file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        print_error(f"Error parsing YAML config: {e}")
        raise


def create_translator(config: dict, input_file: str, output_dir: str) -> DocxTranslator:
    """Create a DocxTranslator instance from config"""
    return DocxTranslator(
        input_file=input_file,
        output_dir=output_dir,
        openai_api_key=config.get("openai_api_key", ""),
        openrouter_api_key=config.get("openrouter_api_key", ""),
        groq_api_key=config.get("groq_api_key", ""),
        gemini_api_key=config.get("gemini_api_key", ""),
        ollama_api_key=config.get("ollama_api_key", ""),
        deepseek_api_key=config.get("deepseek_api_key", ""),
        provider=config.get("provider", "openai"),
        model=config.get("model", "gpt-4o-mini"),
        source_lang=config.get("source_lang", "English"),
        target_lang=config.get("target_lang", "Vietnamese"),
        max_chunk_size=config.get("max_chunk_size", 5000),
        max_concurrent=config.get("max_concurrent", 100),
        cache_enabled=config.get("cache_enabled", True),
        context_window=config.get("context_window", 2),
        glossary_file=config.get("glossary_file"),
        review_mode=config.get("review_mode", False),
        auto_resume=config.get("auto_resume", True),
    )


def translate_single_file(config: dict, input_file: str, output_dir: str):
    """Translate a single DOCX file"""
    logger = get_logger()
    
    print_docx_header(input_file, output_dir)
    print_config(
        provider=config.get("provider", "openai"),
        model=config.get("model", "gpt-4o-mini"),
        source_lang=config.get("source_lang", "English"),
        target_lang=config.get("target_lang", "Vietnamese"),
        cache=config.get("cache_enabled", True),
        context_window=config.get("context_window", 2)
    )
    
    try:
        translator = create_translator(config, input_file, output_dir)
        translator.translate()
        
        output_path = translator.get_output_path()
        console.print()
        print_success(f"Done! → [cyan]{output_path}[/cyan]")
            
        logger.log_summary({
            "Input file": input_file,
            "Output file": output_path,
            "Provider": config.get("provider", "openai"),
            "Model": config.get("model", "gpt-4o-mini"),
        })
        
    except Exception as e:
        console.print()
        print_error(f"Translation failed: {e}")
        logger.error(f"Translation failed: {e}")
        sys.exit(1)


def translate_batch(config: dict, input_dir: str, output_dir: str):
    """Translate multiple DOCX files in a directory"""
    logger = get_logger()
    
    processor = BatchProcessor(translator_factory=lambda: None)
    
    try:
        files = processor.find_docx_files(input_dir)
    except Exception as e:
        print_error(f"Error finding files: {e}")
        logger.error(f"Batch error: {e}")
        sys.exit(1)
    
    if not files:
        print_warning("No .docx files found in directory")
        return
    
    print_info(f"Found [cyan]{len(files)}[/cyan] DOCX files to translate")
    print_config(
        provider=config.get("provider", "openai"),
        model=config.get("model", "gpt-4o-mini"),
        source_lang=config.get("source_lang", "English"),
        target_lang=config.get("target_lang", "Vietnamese")
    )
    
    results = {}
    
    with create_progress() as progress:
        task = progress.add_task("Translating files...", total=len(files))
        
        for file_path in files:
            filename = os.path.basename(file_path)
            progress.update(task, description=f"[cyan]{filename[:40]}[/cyan]")
            
            try:
                translator = create_translator(config, file_path, output_dir)
                translator.translate()
                results[file_path] = {"status": "success", "output": translator.get_output_path()}
            except Exception as e:
                results[file_path] = {"status": "failed", "error": str(e)}
                logger.error(f"Failed to translate {filename}: {e}")
            
            progress.advance(task)
    
    # Print results
    console.print()
    for path, result in results.items():
        filename = os.path.basename(path)
        print_file_result(filename, result["status"], result.get("output"), result.get("error"))
    
    # Print summary
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    failed_count = sum(1 for r in results.values() if r["status"] == "failed")
    
    console.print()
    print_summary("Batch Translation Complete", {
        "Total files": len(files),
        "Translated": success_count,
        "Failed": failed_count,
    })


def translate_docs(config: dict, source_dir: str, output_dir: str, force: bool = False):
    """Translate documentation directory (Markdown/MDX files)"""
    logger = get_logger()
    
    provider = config.get("provider", "openai")
    key_map = {
        "openai": "openai_api_key",
        "openrouter": "openrouter_api_key",
        "groq": "groq_api_key",
        "gemini": "gemini_api_key",
        "ollama": None,
        "ollama-cloud": "ollama_api_key",
        "deepseek": "deepseek_api_key",
    }
    # Ollama local doesn't need API key
    if provider == "ollama":
        api_key = ""
    else:
        key_field = key_map.get(provider, "openai_api_key")
        api_key = config.get(key_field, "") if key_field else ""
    
    print_config(
        provider=provider,
        model=config.get("model", "gpt-4o-mini"),
        source_lang=config.get("source_lang", "English"),
        target_lang=config.get("target_lang", "Vietnamese"),
        cache=config.get("cache_enabled", True),
        force_retranslate=force
    )
    
    try:
        translator = DocsTranslator(
            api_key=api_key,
            provider=provider,
            model=config.get("model", "gpt-4o-mini"),
            source_lang=config.get("source_lang", "English"),
            target_lang=config.get("target_lang", "Vietnamese"),
            cache_enabled=config.get("cache_enabled", True),
            glossary_file=config.get("glossary_file"),
        )
        
        # Custom progress callback
        from translatex.docs.scanner import DocsScanner
        scanner = DocsScanner(source_dir, output_dir)
        files = scanner.scan()
        
        if not files:
            print_warning("No documentation files found")
            return
        
        scanner.ensure_output_structure()
        asset_count = scanner.copy_assets()
        
        print_docs_header(source_dir, output_dir, len(files), asset_count)
        
        # Translate with rich progress
        stats = {"files_translated": 0, "files_cached": 0, "files_failed": 0}
        
        with create_progress() as progress:
            task = progress.add_task("Translating docs...", total=len(files))
            
            from translatex.docs.manifest import ManifestManager
            from pathlib import Path
            
            manifest_path = Path(output_dir) / ".translatex_manifest.json"
            manifest = ManifestManager(str(manifest_path))
            if not force:
                manifest.load()
            manifest.set_directories(source_dir, output_dir)
            
            for doc_file in files:
                filename = Path(doc_file.source_path).name
                progress.update(task, description=f"[cyan]{filename[:40]}[/cyan]")
                
                # Check if file needs translation
                if not force and not manifest.is_changed(doc_file.relative_path, doc_file.source_path):
                    stats["files_cached"] += 1
                    progress.advance(task)
                    continue
                
                try:
                    result = translator.translate_file(doc_file.source_path, doc_file.output_path)
                    if result:
                        manifest.update(doc_file.relative_path, doc_file.source_hash, doc_file.output_path)
                        stats["files_translated"] += 1
                    else:
                        stats["files_failed"] += 1
                except Exception as e:
                    stats["files_failed"] += 1
                    logger.error(f"Failed: {doc_file.relative_path}: {e}")
                
                progress.advance(task)
            
            manifest.save()
        
        console.print()
        print_success("Documentation translation completed!")
        print_summary("Translation Summary", {
            "Files translated": stats["files_translated"],
            "Files cached (unchanged)": stats["files_cached"],
            "Files failed": stats["files_failed"],
            "API calls": translator.stats.get("api_calls", 0),
            "Cache hits": translator.stats.get("cache_hits", 0),
        })
        
    except Exception as e:
        print_error(f"Docs translation failed: {e}")
        logger.error(f"Docs translation failed: {e}")
        sys.exit(1)


def main():
    print_banner()
    
    config = load_config("config.yaml")
    
    parser = argparse.ArgumentParser(
        description="TranslateX - Translate DOCX and Documentation files with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py document.docx                    # Translate single DOCX file
  python main.py ./docs/                          # Translate all DOCX in directory
  python main.py --docs ./nextjs-docs/ -o ./vi/  # Translate Markdown/MDX docs
  python main.py --docs ./docs/ --force          # Force retranslate all docs
        """
    )
    parser.add_argument("input", type=str, nargs="?", help="Input DOCX file or directory")
    parser.add_argument("--output_dir", "-o", type=str, help="Output directory", default="output")
    parser.add_argument("--docs", type=str, help="Translate documentation directory (Markdown/MDX)")
    parser.add_argument("--force", action="store_true", help="Force retranslation (ignore cache)")
    args = parser.parse_args()
    
    output_dir = args.output_dir
    
    # Validate provider API key (Ollama local doesn't need API key)
    provider = config.get("provider", "openai")
    key_map = {
        "openai": "openai_api_key",
        "openrouter": "openrouter_api_key",
        "groq": "groq_api_key",
        "gemini": "gemini_api_key",
        "ollama": None,  # Ollama local doesn't need API key
        "ollama-cloud": "ollama_api_key",
        "deepseek": "deepseek_api_key",
    }
    
    if provider != "ollama":
        key_field = key_map.get(provider)
        if key_field:
            api_key = config.get(key_field, "")
            if not api_key:
                print_error(f"API key not found for provider '{provider}'. Please set '{key_field}' in config.yaml.")
                sys.exit(1)
    
    os.makedirs(output_dir, exist_ok=True)
    
    setup_logger(
        level=config.get("log_level", "INFO"),
        log_to_file=config.get("log_to_file", True),
        output_dir=output_dir
    )
    
    # Handle docs translation mode
    if args.docs:
        if not os.path.isdir(args.docs):
            print_error(f"Docs directory not found: {args.docs}")
            sys.exit(1)
        translate_docs(config, args.docs, output_dir, force=args.force)
        return
    
    # Handle DOCX translation
    input_path = args.input
    if not input_path:
        parser.print_help()
        sys.exit(1)
    
    if os.path.isdir(input_path):
        if not config.get("batch_enabled", True):
            print_error("Batch processing is disabled. Set 'batch_enabled: true' in config.")
            sys.exit(1)
        translate_batch(config, input_path, output_dir)
    elif os.path.isfile(input_path):
        if not input_path.lower().endswith('.docx'):
            print_error("Input file must be a .docx file")
            sys.exit(1)
        translate_single_file(config, input_path, output_dir)
    else:
        print_error(f"Input not found: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
