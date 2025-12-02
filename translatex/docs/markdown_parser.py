"""Markdown parser for documentation translation."""

import re
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import yaml


@dataclass
class ContentBlock:
    """A block of content in a markdown file."""
    type: str  # "text", "code", "frontmatter", "html", "link", "image"
    content: str
    language: str = None  # For code blocks
    translatable: bool = True
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        # Code blocks, links, images are not translatable
        if self.type in ("code", "link", "image", "frontmatter_raw"):
            self.translatable = False


class MarkdownParser:
    """Parse and reconstruct Markdown content while preserving structure."""
    
    # Regex patterns
    FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    CODE_BLOCK_PATTERN = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
    INLINE_CODE_PATTERN = re.compile(r'`([^`]+)`')
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    URL_PATTERN = re.compile(r'https?://[^\s<>\[\]()]+')
    HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
    
    # Fields in frontmatter that should be translated
    TRANSLATABLE_FRONTMATTER_FIELDS = ["title", "description", "summary", "excerpt"]
    
    def __init__(self, translatable_fields: List[str] = None):
        """Initialize parser.
        
        Args:
            translatable_fields: Frontmatter fields to translate
        """
        self.translatable_fields = translatable_fields or self.TRANSLATABLE_FRONTMATTER_FIELDS
    
    def parse(self, content: str) -> List[ContentBlock]:
        """Parse markdown into content blocks.
        
        Args:
            content: Raw markdown content
            
        Returns:
            List of ContentBlock objects
        """
        blocks = []
        
        # Extract frontmatter first
        frontmatter, content = self.extract_frontmatter(content)
        if frontmatter:
            blocks.append(ContentBlock(
                type="frontmatter",
                content=yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False),
                translatable=False,
                metadata={"parsed": frontmatter}
            ))
        
        # Process remaining content
        blocks.extend(self._parse_content(content))
        
        return blocks
    
    def _parse_content(self, content: str) -> List[ContentBlock]:
        """Parse content into blocks, preserving code and special elements."""
        blocks = []
        
        # Replace code blocks with placeholders
        code_blocks = []
        def save_code_block(match):
            lang = match.group(1) or ""
            code = match.group(2)
            placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
            code_blocks.append((lang, code))
            return placeholder
        
        content = self.CODE_BLOCK_PATTERN.sub(save_code_block, content)
        
        # Replace inline code with placeholders
        inline_codes = []
        def save_inline_code(match):
            code = match.group(1)
            placeholder = f"__INLINE_CODE_{len(inline_codes)}__"
            inline_codes.append(code)
            return placeholder
        
        content = self.INLINE_CODE_PATTERN.sub(save_inline_code, content)
        
        # Replace URLs with placeholders
        urls = []
        def save_url(match):
            url = match.group(0)
            placeholder = f"__URL_{len(urls)}__"
            urls.append(url)
            return placeholder
        
        content = self.URL_PATTERN.sub(save_url, content)
        
        # Replace links with placeholders (preserve link text for translation)
        links = []
        def save_link(match):
            text = match.group(1)
            url = match.group(2)
            placeholder = f"__LINK_{len(links)}__"
            links.append((text, url))
            return f"[{text}]({placeholder})"
        
        content = self.LINK_PATTERN.sub(save_link, content)
        
        # Replace images with placeholders
        images = []
        def save_image(match):
            alt = match.group(1)
            url = match.group(2)
            placeholder = f"__IMAGE_{len(images)}__"
            images.append((alt, url))
            return placeholder
        
        content = self.IMAGE_PATTERN.sub(save_image, content)
        
        # Create text block with metadata for reconstruction
        blocks.append(ContentBlock(
            type="text",
            content=content,
            translatable=True,
            metadata={
                "code_blocks": code_blocks,
                "inline_codes": inline_codes,
                "urls": urls,
                "links": links,
                "images": images
            }
        ))
        
        return blocks
    
    def reconstruct(self, blocks: List[ContentBlock]) -> str:
        """Reconstruct markdown from content blocks.
        
        Args:
            blocks: List of ContentBlock objects
            
        Returns:
            Reconstructed markdown string
        """
        parts = []
        
        for block in blocks:
            if block.type == "frontmatter":
                parts.append(f"---\n{block.content}---\n\n")
            elif block.type == "text":
                content = block.content
                metadata = block.metadata
                
                # Restore images
                for i, (alt, url) in enumerate(metadata.get("images", [])):
                    content = content.replace(f"__IMAGE_{i}__", f"![{alt}]({url})")
                
                # Restore links
                for i, (text, url) in enumerate(metadata.get("links", [])):
                    content = content.replace(f"__LINK_{i}__", url)
                
                # Restore URLs
                for i, url in enumerate(metadata.get("urls", [])):
                    content = content.replace(f"__URL_{i}__", url)
                
                # Restore inline code
                for i, code in enumerate(metadata.get("inline_codes", [])):
                    content = content.replace(f"__INLINE_CODE_{i}__", f"`{code}`")
                
                # Restore code blocks
                for i, (lang, code) in enumerate(metadata.get("code_blocks", [])):
                    content = content.replace(f"__CODE_BLOCK_{i}__", f"```{lang}\n{code}```")
                
                parts.append(content)
            elif block.type == "code":
                lang = block.language or ""
                parts.append(f"```{lang}\n{block.content}```")
            else:
                parts.append(block.content)
        
        return "".join(parts)
    
    def extract_frontmatter(self, content: str) -> Tuple[Optional[dict], str]:
        """Extract YAML frontmatter from content.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Tuple of (frontmatter dict or None, remaining content)
        """
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            return None, content
        
        try:
            frontmatter = yaml.safe_load(match.group(1))
            remaining = content[match.end():]
            return frontmatter, remaining
        except yaml.YAMLError:
            return None, content
    
    def get_translatable_text(self, blocks: List[ContentBlock]) -> List[Tuple[int, str]]:
        """Get list of translatable text segments with their block indices.
        
        Args:
            blocks: List of ContentBlock objects
            
        Returns:
            List of (block_index, text) tuples
        """
        segments = []
        for i, block in enumerate(blocks):
            if block.translatable and block.content.strip():
                segments.append((i, block.content))
        return segments
    
    def update_translated_text(self, blocks: List[ContentBlock], translations: dict) -> List[ContentBlock]:
        """Update blocks with translated text.
        
        Args:
            blocks: Original content blocks
            translations: Dict mapping block_index to translated text
            
        Returns:
            Updated content blocks
        """
        for idx, translated in translations.items():
            if 0 <= idx < len(blocks):
                blocks[idx].content = translated
        return blocks
