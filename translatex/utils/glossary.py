"""Custom glossary management for TranslateX."""

import yaml
from pathlib import Path
from typing import Dict, Optional

from .exceptions import GlossaryError
from .file_logger import get_logger


# Default technical terms
DEFAULT_TERMS = {
    "API": "API",
    "SDK": "SDK",
    "UI": "UI",
    "UX": "UX",
    "URL": "URL",
    "HTTP": "HTTP",
    "HTTPS": "HTTPS",
    "JSON": "JSON",
    "XML": "XML",
    "HTML": "HTML",
    "CSS": "CSS",
    "JavaScript": "JavaScript",
    "TypeScript": "TypeScript",
    "Python": "Python",
    "React": "React",
    "Vue": "Vue",
    "Angular": "Angular",
    "Node.js": "Node.js",
    "npm": "npm",
    "Git": "Git",
    "GitHub": "GitHub",
    "Docker": "Docker",
    "Kubernetes": "Kubernetes",
    "AWS": "AWS",
    "Azure": "Azure",
    "GCP": "GCP",
}


class GlossaryLoader:
    """Loads and manages custom terminology translations."""
    
    def __init__(self, glossary_file: Optional[str] = None):
        """Initialize glossary loader.
        
        Args:
            glossary_file: Path to glossary YAML file (optional)
        """
        self.glossary_file = glossary_file
        self.terms: Dict[str, str] = {}
        self._load()
    
    def _load(self):
        """Load glossary from file or use defaults."""
        logger = get_logger()
        
        # Start with defaults
        self.terms = DEFAULT_TERMS.copy()
        
        if not self.glossary_file:
            logger.info("No glossary file specified, using default terms")
            return
        
        path = Path(self.glossary_file)
        if not path.exists():
            logger.info(f"Glossary file not found: {self.glossary_file}, using default terms")
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            
            # Merge custom terms (override defaults)
            custom_terms = data.get("terms", {})
            self.terms.update(custom_terms)
            logger.debug(f"Loaded {len(custom_terms)} custom terms from glossary")
        except yaml.YAMLError as e:
            logger.warning(f"Invalid glossary YAML: {e}, using default terms")
        except IOError as e:
            logger.warning(f"Failed to read glossary: {e}, using default terms")
    
    def get_terms(self) -> Dict[str, str]:
        """Get all glossary terms."""
        return self.terms.copy()
    
    def format_for_prompt(self) -> str:
        """Format glossary terms for inclusion in translation prompt.
        
        Returns:
            Formatted string with glossary terms
        """
        if not self.terms:
            return ""
        
        terms_list = "\n".join(f"- {src} -> {tgt}" for src, tgt in self.terms.items())
        
        return f"""
[GLOSSARY - Use these exact translations for technical terms]
{terms_list}
[END GLOSSARY]
"""
    
    def lookup(self, term: str) -> Optional[str]:
        """Look up a specific term.
        
        Args:
            term: Term to look up
            
        Returns:
            Translation if found, None otherwise
        """
        return self.terms.get(term)
    
    def add_term(self, source: str, translation: str):
        """Add a term to the glossary (runtime only)."""
        self.terms[source] = translation
    
    def size(self) -> int:
        """Return number of terms in glossary."""
        return len(self.terms)
