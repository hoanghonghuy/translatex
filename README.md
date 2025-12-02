# TranslateX 🌐

> **AI-powered DOCX Translation with Format Preservation**

TranslateX is a powerful tool for translating Microsoft Word documents (.docx) using AI (OpenAI, Gemini, Groq, OpenRouter) while preserving the original formatting, structure, and layout completely.

## 🚀 Features

- ✅ **Multi-Provider Support**: OpenAI, Google Gemini, Groq, OpenRouter
- ✅ **Format Preservation**: Keep all formatting, styles, tables, charts
- ✅ **Free Models**: Use Gemini or Groq for free translation
- ✅ **Smart Rate Limiting**: Auto-adjust for each provider's limits
- ✅ **Async Processing**: Fast parallel translation

## 📦 Installation

### From pip

```bash
pip install translatex
```

### From source

```bash
git clone https://github.com/hoanghonghuy/translatex.git
cd translatex
pip install -e .
```

## 🔑 Quick Start

### Using Gemini (FREE - Recommended!)

```python
from translatex import DocxTranslator

translator = DocxTranslator(
    input_file="document.docx",
    output_dir="./output",
    gemini_api_key="your-gemini-api-key",
    provider="gemini",
    model="gemini-2.0-flash",  # FREE!
    source_lang="English",
    target_lang="Vietnamese"
)

translator.translate()
print("Done!")
```

> 🚀 Get free Gemini API key at: https://aistudio.google.com/apikey

### Using Groq (FREE & Fast!)

```python
from translatex import DocxTranslator

translator = DocxTranslator(
    input_file="document.docx",
    output_dir="./output",
    groq_api_key="your-groq-api-key",
    provider="groq",
    model="llama-3.3-70b-versatile",  # FREE!
    source_lang="English",
    target_lang="Vietnamese"
)

translator.translate()
```

> 🚀 Get free Groq API key at: https://console.groq.com/keys

### Using OpenAI

```python
from translatex import DocxTranslator

translator = DocxTranslator(
    input_file="document.docx",
    output_dir="./output",
    openai_api_key="sk-your-openai-key",
    provider="openai",
    model="gpt-4o-mini",
    source_lang="English",
    target_lang="Vietnamese"
)

translator.translate()
```

## ⚙️ Configuration

Create `config.yaml`:

```yaml
# Provider: openai, gemini, groq, openrouter
provider: "gemini"

# API Keys
gemini_api_key: "your-key"
openai_api_key: ""
groq_api_key: ""
openrouter_api_key: ""

# Model
model: "gemini-2.0-flash"

# Translation
source_lang: "English"
target_lang: "Vietnamese"

# Performance
max_concurrent: 5
max_chunk_size: 5000
```

Run:

```bash
python main.py document.docx --output_dir output
```

## 🆓 Free Models

### Gemini (Recommended)

| Model | Rate Limit | Best For |
|-------|------------|----------|
| `gemini-2.0-flash` | 15 RPM | ⭐ Best balance |
| `gemini-2.5-flash` | 10 RPM | Higher quality |
| `gemini-2.0-flash-lite` | 30 RPM | Fastest |

### Groq

| Model | Description |
|-------|-------------|
| `llama-3.3-70b-versatile` | Best quality |
| `gemma2-9b-it` | Fast |
| `mixtral-8x7b-32768` | Good for long docs |

## 📄 License

MIT License

## 👨‍💻 Author

**Hoang Hong Huy**
- 📧 Email: huy.hoanghong.work@gmail.com
- 🐙 GitHub: [@hoanghonghuy](https://github.com/hoanghonghuy)

---

**TranslateX** - Smart document translation with AI! 🌐✨
