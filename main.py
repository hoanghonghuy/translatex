from translatex import DocxTranslator
from translatex.utils.spinner import Spinner
import os
import sys
import argparse
import yaml
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def load_config(config_path: str) -> dict:
    """Đọc config từ file YAML"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded config from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"✗ Config file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"✗ Error parsing YAML config: {e}")
        raise

def main():
    config = load_config("config.yaml")
    parser = argparse.ArgumentParser(description="Translate a DOCX file")
    parser.add_argument("input_file", type=str, help="Input DOCX file")
    parser.add_argument("--output_dir", type=str, help="Output directory", default="output")
    args = parser.parse_args()

    input_file = args.input_file
    output_dir = args.output_dir
    
    # Provider configuration (default to "openai")
    provider = config.get("provider", "openai")
    
    # Get API keys
    openai_api_key = config.get("openai_api_key", "")
    openrouter_api_key = config.get("openrouter_api_key", "")
    groq_api_key = config.get("groq_api_key", "")
    gemini_api_key = config.get("gemini_api_key", "")
    
    # Validate API key based on provider
    if provider == "openrouter":
        if not openrouter_api_key:
            raise ValueError("OpenRouter API key not found in config. Please set 'openrouter_api_key' in config.yaml.")
    elif provider == "groq":
        if not groq_api_key:
            raise ValueError("Groq API key not found in config. Please set 'groq_api_key' in config.yaml.")
    elif provider == "gemini":
        if not gemini_api_key:
            raise ValueError("Gemini API key not found in config. Please set 'gemini_api_key' in config.yaml.")
    else:  # openai (default)
        if not openai_api_key:
            raise ValueError("OpenAI API key not found in config. Please set 'openai_api_key' in config.yaml.")
    
    model = config.get("model", "gpt-4o-mini")
    source_lang = config.get("source_lang", "English")
    target_lang = config.get("target_lang", "Vietnamese")
    max_chunk_size = config.get("max_chunk_size", 5000)
    max_concurrent = config.get("max_concurrent", 100)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Starting DOCX translation...\n")

    spinner = Spinner("Processing DOCX translation")
    spinner.start()
    try:
        docx_translator = DocxTranslator(
            input_file=input_file,
            output_dir=output_dir,
            openai_api_key=openai_api_key,
            openrouter_api_key=openrouter_api_key,
            groq_api_key=groq_api_key,
            gemini_api_key=gemini_api_key,
            provider=provider,
            model=model,
            source_lang=source_lang,
            target_lang=target_lang,
            max_chunk_size=max_chunk_size,
            max_concurrent=max_concurrent
        )
        docx_translator.translate()
        spinner.stop()
        print(f"Translation completed!\nOutput: {docx_translator.get_output_path()}")
    except Exception as e:
        spinner.stop()
        print(f"Translation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
