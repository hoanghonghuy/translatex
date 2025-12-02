# TranslateX

AI-powered DOCX translation with format preservation. Supports OpenAI, Google Gemini, Groq, and OpenRouter.

## Features

- Multi-provider support: OpenAI, Gemini, Groq, OpenRouter
- Preserves all formatting, styles, tables, and charts
- Free translation with Gemini or Groq
- Smart rate limiting per provider
- Async parallel processing

### Advanced Features

- **Resume/Checkpoint**: Auto-resume interrupted translations
- **Batch Processing**: Translate multiple files at once
- **Translation Cache**: Avoid re-translating identical text
- **Context Window**: Include previous segments for coherent translation
- **Custom Glossary**: Define custom terminology translations
- **Review Mode**: Generate HTML comparison file
- **Smart Retry**: Exponential backoff for API errors
- **File Logging**: Save logs for debugging

## Installation

```bash
git clone https://github.com/hoanghonghuy/translatex.git
cd translatex
pip install -r requirements.txt
```

## Configuration

1. Copy config template:
```bash
cp config.example.yaml config.yaml
```

2. Edit `config.yaml` and add your API key:
```yaml
provider: "gemini"
gemini_api_key: "your-api-key-here"
model: "gemini-2.0-flash"
source_lang: "English"
target_lang: "Vietnamese"
```

Get free API keys:
- Gemini: https://aistudio.google.com/apikey
- Groq: https://console.groq.com/keys

## Usage

### Single File

```bash
python main.py document.docx
```

### Batch Processing

```bash
python main.py ./documents/
```

### Custom Output Directory

```bash
python main.py document.docx --output_dir ./translated
```

### Python API

```python
from translatex import DocxTranslator

translator = DocxTranslator(
    input_file="document.docx",
    output_dir="./output",
    gemini_api_key="your-api-key",
    provider="gemini",
    model="gemini-2.0-flash",
    source_lang="English",
    target_lang="Vietnamese",
    # Advanced features
    cache_enabled=True,
    context_window=2,
    review_mode=False,
)

translator.translate()
```

## Advanced Configuration

```yaml
# config.yaml

# Provider and API keys
provider: "gemini"
gemini_api_key: "your-key"

# Model settings
model: "gemini-2.0-flash"
source_lang: "English"
target_lang: "Vietnamese"

# Performance
max_concurrent: 5
max_chunk_size: 5000

# Advanced features
auto_resume: true        # Resume from checkpoint
batch_enabled: true      # Allow batch processing
cache_enabled: true      # Cache translations
context_window: 2        # Previous segments as context
review_mode: false       # Generate review HTML
max_retries: 3           # Retry failed requests
log_level: "INFO"        # DEBUG, INFO, WARNING, ERROR
log_to_file: true        # Save logs to file
glossary_file: "glossary.yaml"  # Custom terminology
```

## Custom Glossary

Create `glossary.yaml` to define custom translations:

```yaml
terms:
  "API": "API"
  "frontend": "giao diện người dùng"
  "backend": "máy chủ"
  "database": "cơ sở dữ liệu"
```

## Supported Models

### Gemini (Free)

| Model | Rate Limit | Notes |
|-------|------------|-------|
| gemini-2.0-flash | 15 RPM | Recommended |
| gemini-2.5-flash | 10 RPM | Higher quality |
| gemini-2.0-flash-lite | 30 RPM | Fastest |

### Groq (Free)

| Model | Notes |
|-------|-------|
| llama-3.3-70b-versatile | Best quality |
| gemma2-9b-it | Fast |
| mixtral-8x7b-32768 | Long context |

### OpenAI (Paid)

| Model | Notes |
|-------|-------|
| gpt-4o-mini | Cost effective |
| gpt-4o | Best quality |

## License

MIT License
