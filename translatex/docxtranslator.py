import os
from translatex.worker.extractor import Extractor
from translatex.worker.injector import Injector
from translatex.worker.translator import Translator
from translatex.utils.llm_client_factory import LLMClientFactory


class DocxTranslator:
    """
    Translate a DOCX file while preserving formatting
    Supports OpenAI, OpenRouter, Groq, and Gemini providers
    
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
        max_concurrent: int = 100
    ):
        """
        Khởi tạo DocxTranslator
        
        Args:
            input_file: Đường dẫn file DOCX đầu vào
            output_dir: Thư mục output
            openai_api_key: API key cho OpenAI
            openrouter_api_key: API key cho OpenRouter
            groq_api_key: API key cho Groq
            gemini_api_key: API key cho Gemini
            provider: Provider name ("openai", "openrouter", "groq", hoặc "gemini")
            model: Model name
            source_lang: Ngôn ngữ nguồn
            target_lang: Ngôn ngữ đích
            max_chunk_size: Kích thước chunk tối đa
            max_concurrent: Số request đồng thời tối đa
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.provider = provider
        self.model = model
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.max_chunk_size = max_chunk_size
        self.max_concurrent = max_concurrent
        
        # Validate provider
        if not LLMClientFactory.validate_provider(provider):
            supported = ", ".join(LLMClientFactory.PROVIDERS.keys())
            raise ValueError(f"Invalid provider '{provider}'. Supported: {supported}")
        
        # Select correct API key based on provider
        if provider == "openrouter":
            self.api_key = openrouter_api_key
            if not self.api_key:
                raise ValueError("OpenRouter API key not found. Please provide 'openrouter_api_key'.")
        elif provider == "groq":
            self.api_key = groq_api_key
            if not self.api_key:
                raise ValueError("Groq API key not found. Please provide 'groq_api_key'.")
        elif provider == "gemini":
            self.api_key = gemini_api_key
            if not self.api_key:
                raise ValueError("Gemini API key not found. Please provide 'gemini_api_key'.")
        else:  # openai (default)
            self.api_key = openai_api_key
            if not self.api_key:
                raise ValueError("OpenAI API key not found. Please provide 'openai_api_key'.")

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Derive filenames
        file_name = os.path.splitext(os.path.basename(input_file))[0]
        self.checkpoint_file = os.path.join(output_dir, f"{file_name}_checkpoint.json")
        self.output_file = os.path.join(output_dir, f"{file_name}_translated.docx")

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
            self.max_concurrent
        )
        self.injector = Injector(self.input_file, self.checkpoint_file, self.output_file)

    def translate(self):
        """Run the entire translation pipeline"""
        self.extract()
        self.translator.translate()
        self.inject()
    
    async def atranslate(self):
        """Run the entire translation pipeline asynchronously"""
        self.extract()
        await self.translator._translate_all()
        self.inject()

    def extract(self):
        """Extract segments and save checkpoint"""
        self.extractor.extract()

    def inject(self):
        """Inject translated segments into a new DOCX file"""
        self.injector.inject()

    def get_output_path(self) -> str:
        """Return the absolute path of the translated file"""
        return os.path.abspath(self.output_file)
