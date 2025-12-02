"""TranslateX - DOCX Translation Tool with Advanced Features"""

import os
import sys
import argparse
import yaml

from translatex import DocxTranslator
from translatex.batch import BatchProcessor
from translatex.utils.spinner import Spinner
from translatex.utils.file_logger import setup_logger, get_logger
from translatex.utils.config import TranslateXConfig


def load_config(config_path: str) -> dict:
    """Load config from YAML file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        print(f"Error parsing YAML config: {e}")
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
        provider=config.get("provider", "openai"),
        model=config.get("model", "gpt-4o-mini"),
        source_lang=config.get("source_lang", "English"),
        target_lang=config.get("target_lang", "Vietnamese"),
        max_chunk_size=config.get("max_chunk_size", 5000),
        max_concurrent=config.get("max_concurrent", 100),
        # Advanced features
        cache_enabled=config.get("cache_enabled", True),
        context_window=config.get("context_window", 2),
        glossary_file=config.get("glossary_file"),
        review_mode=config.get("review_mode", False),
        auto_resume=config.get("auto_resume", True),
    )


def translate_single_file(config: dict, input_file: str, output_dir: str):
    """Translate a single DOCX file"""
    logger = get_logger()
    
    print("Starting DOCX translation...\n")
    
    spinner = Spinner("Processing DOCX translation")
    spinner.start()
    
    try:
        translator = create_translator(config, input_file, output_dir)
        translator.translate()
        spinner.stop()
        
        output_path = translator.get_output_path()
        print(f"Translation completed!\nOutput: {output_path}")
        logger.info(f"Translation completed: {output_path}")
        
        # Log summary
        logger.log_summary({
            "Input file": input_file,
            "Output file": output_path,
            "Provider": config.get("provider", "openai"),
            "Model": config.get("model", "gpt-4o-mini"),
        })
        
    except Exception as e:
        spinner.stop()
        print(f"Translation failed: {e}")
        logger.error(f"Translation failed: {e}")
        sys.exit(1)


def translate_batch(config: dict, input_dir: str, output_dir: str):
    """Translate multiple DOCX files in a directory"""
    logger = get_logger()
    
    print(f"Starting batch translation from: {input_dir}\n")
    
    def translator_factory():
        # Factory will be called with specific file later
        return None
    
    processor = BatchProcessor(translator_factory=translator_factory)
    
    # Find all DOCX files
    try:
        files = processor.find_docx_files(input_dir)
    except Exception as e:
        print(f"Error finding files: {e}")
        logger.error(f"Batch error: {e}")
        sys.exit(1)
    
    if not files:
        print("No .docx files found in directory")
        logger.warning("No .docx files found")
        return
    
    print(f"Found {len(files)} DOCX files to translate\n")
    logger.info(f"Batch processing {len(files)} files")
    
    # Process each file
    results = {}
    for idx, file_path in enumerate(files):
        filename = os.path.basename(file_path)
        print(f"\n[{idx + 1}/{len(files)}] Translating: {filename}")
        
        try:
            translator = create_translator(config, file_path, output_dir)
            translator.translate()
            results[file_path] = {"status": "success", "output": translator.get_output_path()}
            print(f"  Completed: {translator.get_output_path()}")
        except Exception as e:
            results[file_path] = {"status": "failed", "error": str(e)}
            print(f"  Failed: {e}")
            logger.error(f"Failed to translate {filename}: {e}")
    
    # Print summary
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    failed_count = sum(1 for r in results.values() if r["status"] == "failed")
    
    print(f"\n{'='*50}")
    print(f"BATCH COMPLETE: {success_count} succeeded, {failed_count} failed")
    print(f"{'='*50}")
    
    logger.log_summary({
        "Total files": len(files),
        "Succeeded": success_count,
        "Failed": failed_count,
    })
    
    if failed_count > 0:
        print("\nFailed files:")
        for path, result in results.items():
            if result["status"] == "failed":
                print(f"  - {os.path.basename(path)}: {result['error']}")


def main():
    config = load_config("config.yaml")
    
    parser = argparse.ArgumentParser(
        description="TranslateX - Translate DOCX files with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py document.docx                    # Translate single file
  python main.py ./docs/                          # Translate all DOCX in directory
  python main.py document.docx --output_dir out  # Custom output directory
        """
    )
    parser.add_argument("input", type=str, help="Input DOCX file or directory")
    parser.add_argument("--output_dir", type=str, help="Output directory", default="output")
    args = parser.parse_args()
    
    input_path = args.input
    output_dir = args.output_dir
    
    # Validate provider API key
    provider = config.get("provider", "openai")
    key_map = {
        "openai": "openai_api_key",
        "openrouter": "openrouter_api_key",
        "groq": "groq_api_key",
        "gemini": "gemini_api_key",
    }
    
    api_key = config.get(key_map.get(provider, "openai_api_key"), "")
    if not api_key:
        print(f"API key not found for provider '{provider}'. Please set '{key_map[provider]}' in config.yaml.")
        sys.exit(1)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Setup logging
    setup_logger(
        level=config.get("log_level", "INFO"),
        log_to_file=config.get("log_to_file", True),
        output_dir=output_dir
    )
    
    # Check if input is file or directory
    if os.path.isdir(input_path):
        # Batch processing
        if not config.get("batch_enabled", True):
            print("Batch processing is disabled in config. Set 'batch_enabled: true' to enable.")
            sys.exit(1)
        translate_batch(config, input_path, output_dir)
    elif os.path.isfile(input_path):
        # Single file
        if not input_path.lower().endswith('.docx'):
            print("Input file must be a .docx file")
            sys.exit(1)
        translate_single_file(config, input_path, output_dir)
    else:
        print(f"Input not found: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
