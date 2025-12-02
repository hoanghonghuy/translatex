# TranslateX

AI-powered DOCX translation with format preservation. Supports OpenAI, Google Gemini, Groq, and OpenRouter.

## Features

- Multi-provider support: OpenAI, Gemini, Groq, OpenRouter
- Preserves all formatting, styles, tables, and charts
- Free translation with Gemini or Groq
- Smart rate limiting per provider
- Async parallel processing

## Installation

```bash
pip install translatex
```

Or from source:

```bash
git clone https://github.com/hoanghonghuy/translatex.git
cd translatex
pip install -e .
```

## Quick Start

### Using Gemini (Free)

```python
from translatex import DocxTranslator

translator = DocxTranslator(
    input_file="document.docx",
    output_dir="./output",
    gemini_api_key="your-api-key",
    provider="gemini",
    model="gemini-2.0-flash",
    source_lang="English",
    target_lang="Vietnamese"
)

translator.translate()
```

Get free Gemini API key: https://aistudio.google.com/apikey

### Using Groq (Free)

```python
from translatex import DocxTranslator

translator = DocxTranslator(
    input_file="document.docx",
    output_dir="./output",
    groq_api_key="your-api-key",
    provider="groq",
    model="llama-3.3-70b-versatile",
    source_lang="English",
    target_lang="Vietnamese"
)

translator.translate()
```

Get free Groq API key: https://console.groq.com/keys

### Using OpenAI

```python
from translatex import DocxTranslator

translator = DocxTranslator(
    input_file="document.docx",
    output_dir="./output",
    openai_api_key="sk-your-key",
    provider="openai",
    model="gpt-4o-mini",
    source_lang="English",
    target_lang="Vietnamese"
)

translator.translate()
```

## Configuration

Create `config.yaml`:

```yaml
provider: "gemini"
gemini_api_key: "your-key"
model: "gemini-2.0-flash"
source_lang: "English"
target_lang: "Vietnamese"
max_concurrent: 5
max_chunk_size: 5000
```

Run via CLI:

```bash
python main.py document.docx --output_dir output
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

## Author

Hoang Hong Huy  
Email: huy.hoanghong.work@gmail.com  
GitHub: https://github.com/hoanghonghuy
