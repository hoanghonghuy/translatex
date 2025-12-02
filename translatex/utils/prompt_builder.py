class PromptBuilder:
    """Xây dựng prompts cho LLM API với hỗ trợ glossary"""
    
    # Default technical terms to keep unchanged
    DEFAULT_KEEP_TERMS = [
        "API", "URL", "HTTP", "HTTPS", "JSON", "XML", "HTML", "CSS", "JavaScript",
        "TypeScript", "Python", "React", "Next.js", "Node.js", "npm", "yarn",
        "Git", "GitHub", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
        "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Redis",
        "REST", "GraphQL", "WebSocket", "OAuth", "JWT", "SSL", "TLS",
        "CI/CD", "DevOps", "Agile", "Scrum", "Sprint",
    ]
    
    def __init__(self, source_lang: str, target_lang: str, glossary: dict = None, keep_terms: list = None):
        """
        Khởi tạo PromptBuilder
        
        Args:
            source_lang: Ngôn ngữ nguồn
            target_lang: Ngôn ngữ đích
            glossary: Dict mapping source terms to target translations
            keep_terms: List of terms to keep unchanged (not translate)
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.glossary = glossary or {}
        self.keep_terms = keep_terms or self.DEFAULT_KEEP_TERMS
    
    def build_system_prompt(self) -> str:
        """Xây dựng system prompt cho translation"""
        prompt = (
            f"You are a professional translator from {self.source_lang} to {self.target_lang}.\n\n"
            f"TRANSLATION GUIDELINES:\n"
            f"- Translate naturally and fluently, preserving the original meaning and tone\n"
            f"- Maintain the context and style appropriate for technical documentation\n"
            f"- Ensure the translation reads naturally in {self.target_lang}\n\n"
        )
        
        # Add glossary if provided
        if self.glossary:
            prompt += "GLOSSARY (use these exact translations):\n"
            for source, target in self.glossary.items():
                prompt += f"- {source} → {target}\n"
            prompt += "\n"
        
        # Add keep terms
        if self.keep_terms:
            prompt += "DO NOT TRANSLATE these terms (keep as-is):\n"
            prompt += ", ".join(self.keep_terms[:30])  # Limit to avoid too long prompt
            prompt += "\n\n"
        
        prompt += (
            f"ALSO DO NOT TRANSLATE:\n"
            f"- URLs, file paths, code snippets, commands\n"
            f"- Variable names, function names, class names\n"
            f"- Brand names, product names, proper nouns\n"
            f"- Text inside backticks (`code`)\n\n"
            f"CRITICAL - MARKER PRESERVATION RULES:\n"
            f"The text contains XML-like markers that MUST be preserved:\n"
            f"- Opening tags: <R0>, <R1>, <SEG0>, <CELL0-0-0-0>, etc.\n"
            f"- Closing tags: </R0>, </R1>, </SEG0>, </CELL0-0-0-0>, etc.\n\n"
            f"STRICT RULES:\n"
            f"1. COPY every marker EXACTLY (including numbers and format)\n"
            f"2. NEVER remove, modify, or merge markers\n"
            f"3. NEVER add new markers that don't exist in input\n"
            f"4. Translate ONLY the text between <Rx> and </Rx> tags\n"
            f"5. Keep whitespace inside markers exactly as input\n"
            f"6. If input has <R0>text</R0>, output MUST have <R0>translated</R0>\n\n"
            f"EXAMPLE:\n"
            f"Input:  <R0>Hello </R0><R1>world</R1>\n"
            f"Output: <R0>Xin chào </R0><R1>thế giới</R1>\n\n"
            f"WRONG OUTPUT (missing markers):\n"
            f"[X] Xin chào thế giới\n"
            f"[X] <R0>Xin chào thế giới</R0>"
        )
        
        return prompt
    
    def build_user_prompt(self, text: str) -> str:
        """Xây dựng user prompt"""
        return f"Translate the following text:\n\n{text}"
    
    def build_messages(self, text: str) -> list[dict]:
        """Xây dựng messages array cho LLM API"""
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(text)}
        ]
