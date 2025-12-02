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

### Command Line

```bash
python main.py document.docx --output_dir output
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
    target_lang="Vietnamese"
)

translator.translate()
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
