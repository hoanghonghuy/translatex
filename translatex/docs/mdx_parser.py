"""MDX parser for documentation translation."""

import re
from typing import List, Tuple
from dataclasses import dataclass

from .markdown_parser import MarkdownParser, ContentBlock


@dataclass
class ComponentBlock:
    """A JSX component block in MDX."""
    name: str
    props: str
    content: str
    self_closing: bool = False


class MDXParser(MarkdownParser):
    """Parse and reconstruct MDX content while preserving JSX components."""
    
    # MDX-specific patterns
    IMPORT_PATTERN = re.compile(r'^import\s+.*?(?:from\s+[\'"][^\'"]+[\'"])?;?\s*$', re.MULTILINE)
    EXPORT_PATTERN = re.compile(r'^export\s+.*?;?\s*$', re.MULTILINE)
    
    # JSX component patterns
    SELF_CLOSING_COMPONENT = re.compile(r'<([A-Z][a-zA-Z0-9]*)\s*([^>]*?)\s*/>')
    COMPONENT_OPEN = re.compile(r'<([A-Z][a-zA-Z0-9]*)\s*([^>]*)>')
    COMPONENT_CLOSE = re.compile(r'</([A-Z][a-zA-Z0-9]*)>')
    
    # JSX expression pattern
    JSX_EXPRESSION = re.compile(r'\{[^{}]*\}')
    
    def parse(self, content: str) -> List[ContentBlock]:
        """Parse MDX into content blocks.
        
        Args:
            content: Raw MDX content
            
        Returns:
            List of ContentBlock objects
        """
        blocks = []
        
        # Extract frontmatter first
        frontmatter, content = self.extract_frontmatter(content)
        if frontmatter:
            blocks.append(ContentBlock(
                type="frontmatter",
                content=self._format_frontmatter(frontmatter),
                translatable=False,
                metadata={"parsed": frontmatter}
            ))
        
        # Extract imports
        imports = self.extract_imports(content)
        if imports:
            blocks.append(ContentBlock(
                type="import",
                content="\n".join(imports),
                translatable=False
            ))
            # Remove imports from content
            for imp in imports:
                content = content.replace(imp, "", 1)
        
        # Extract exports
        exports = self.extract_exports(content)
        if exports:
            blocks.append(ContentBlock(
                type="export",
                content="\n".join(exports),
                translatable=False
            ))
            for exp in exports:
                content = content.replace(exp, "", 1)
        
        # Process remaining content with JSX handling
        blocks.extend(self._parse_mdx_content(content))
        
        return blocks
    
    def _format_frontmatter(self, frontmatter: dict) -> str:
        """Format frontmatter dict back to YAML string."""
        import yaml
        return yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
    
    def _parse_mdx_content(self, content: str) -> List[ContentBlock]:
        """Parse MDX content with JSX component handling."""
        blocks = []
        
        # Replace JSX components with placeholders
        components = []
        
        # Handle self-closing components
        def save_self_closing(match):
            name = match.group(1)
            props = match.group(2)
            placeholder = f"__COMPONENT_{len(components)}__"
            components.append(ComponentBlock(name, props, "", self_closing=True))
            return placeholder
        
        content = self.SELF_CLOSING_COMPONENT.sub(save_self_closing, content)
        
        # Handle components with content (simplified - doesn't handle nested)
        content, nested_components = self._extract_components(content, components)
        components.extend(nested_components)
        
        # Replace JSX expressions with placeholders
        jsx_expressions = []
        def save_jsx_expr(match):
            expr = match.group(0)
            placeholder = f"__JSX_EXPR_{len(jsx_expressions)}__"
            jsx_expressions.append(expr)
            return placeholder
        
        content = self.JSX_EXPRESSION.sub(save_jsx_expr, content)
        
        # Now parse as regular markdown
        md_blocks = self._parse_content(content)
        
        # Add component and JSX metadata
        for block in md_blocks:
            if block.type == "text":
                block.metadata["components"] = components
                block.metadata["jsx_expressions"] = jsx_expressions
        
        return md_blocks
    
    def _extract_components(self, content: str, existing_components: list) -> Tuple[str, List[ComponentBlock]]:
        """Extract JSX components with content."""
        components = []
        result = content
        
        # Find all component opens
        opens = list(self.COMPONENT_OPEN.finditer(content))
        
        for open_match in reversed(opens):  # Process from end to preserve indices
            name = open_match.group(1)
            props = open_match.group(2)
            
            # Find matching close
            close_pattern = re.compile(f'</{name}>')
            close_match = close_pattern.search(content, open_match.end())
            
            if close_match:
                component_content = content[open_match.end():close_match.start()]
                full_component = content[open_match.start():close_match.end()]
                
                placeholder = f"__COMPONENT_{len(existing_components) + len(components)}__"
                components.append(ComponentBlock(name, props, component_content, self_closing=False))
                
                result = result[:open_match.start()] + placeholder + result[close_match.end():]
        
        return result, components
    
    def reconstruct(self, blocks: List[ContentBlock]) -> str:
        """Reconstruct MDX from content blocks.
        
        Args:
            blocks: List of ContentBlock objects
            
        Returns:
            Reconstructed MDX string
        """
        parts = []
        
        for block in blocks:
            if block.type == "frontmatter":
                parts.append(f"---\n{block.content}---\n\n")
            elif block.type == "import":
                parts.append(block.content + "\n\n")
            elif block.type == "export":
                parts.append(block.content + "\n\n")
            elif block.type == "text":
                content = block.content
                metadata = block.metadata
                
                # Restore JSX expressions
                for i, expr in enumerate(metadata.get("jsx_expressions", [])):
                    content = content.replace(f"__JSX_EXPR_{i}__", expr)
                
                # Restore components
                for i, comp in enumerate(metadata.get("components", [])):
                    if comp.self_closing:
                        replacement = f"<{comp.name} {comp.props}/>" if comp.props else f"<{comp.name} />"
                    else:
                        replacement = f"<{comp.name} {comp.props}>{comp.content}</{comp.name}>" if comp.props else f"<{comp.name}>{comp.content}</{comp.name}>"
                    content = content.replace(f"__COMPONENT_{i}__", replacement)
                
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
            else:
                parts.append(block.content)
        
        return "".join(parts)
    
    def extract_imports(self, content: str) -> List[str]:
        """Extract import statements from MDX content.
        
        Args:
            content: MDX content
            
        Returns:
            List of import statements
        """
        return self.IMPORT_PATTERN.findall(content)
    
    def extract_exports(self, content: str) -> List[str]:
        """Extract export statements from MDX content.
        
        Args:
            content: MDX content
            
        Returns:
            List of export statements
        """
        return self.EXPORT_PATTERN.findall(content)
