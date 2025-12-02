"""Tests for MarkdownParser - Properties 1-4."""

import tempfile
import os
from hypothesis import given, strategies as st, settings

from translatex.docs.markdown_parser import MarkdownParser, ContentBlock


class TestCodeBlockPreservation:
    """Property-based tests for code block preservation.
    
    **Feature: dev-docs-translator, Property 1: Code blocks preserved**
    **Validates: Requirements 1.2, 4.1**
    """
    
    @given(
        code=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_=(){}[];", min_size=1, max_size=100),
        lang=st.sampled_from(["python", "javascript", "bash", "typescript", "json", ""])
    )
    @settings(max_examples=100)
    def test_code_blocks_preserved(self, code, lang):
        """For any markdown with code blocks, code blocks SHALL be preserved."""
        parser = MarkdownParser()
        
        # Create markdown with code block
        content = f"# Title\n\nSome text\n\n```{lang}\n{code}\n```\n\nMore text"
        
        # Parse
        blocks = parser.parse(content)
        
        # Reconstruct
        result = parser.reconstruct(blocks)
        
        # Verify code block is preserved
        expected_block = f"```{lang}\n{code}\n```"
        assert expected_block in result, f"Code block not preserved: {expected_block}"


class TestInlineCodePreservation:
    """Property-based tests for inline code preservation.
    
    **Feature: dev-docs-translator, Property 2: Inline code preserved**
    **Validates: Requirements 1.3**
    """
    
    @given(code=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_.", min_size=1, max_size=30))
    @settings(max_examples=100)
    def test_inline_code_preserved(self, code):
        """For any markdown with inline code, inline code SHALL be preserved."""
        parser = MarkdownParser()
        
        content = f"Use the `{code}` command to run."
        
        blocks = parser.parse(content)
        result = parser.reconstruct(blocks)
        
        assert f"`{code}`" in result, f"Inline code not preserved: `{code}`"


class TestLinksPreservation:
    """Property-based tests for links preservation.
    
    **Feature: dev-docs-translator, Property 3: Links and images preserved**
    **Validates: Requirements 1.4**
    """
    
    @given(
        text=st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=1, max_size=20),
        url=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789/-_.", min_size=5, max_size=30)
    )
    @settings(max_examples=100)
    def test_links_preserved(self, text, url):
        """For any markdown with links, links SHALL be preserved."""
        parser = MarkdownParser()
        
        full_url = f"https://example.com/{url}"
        content = f"Check out [{text}]({full_url}) for more info."
        
        blocks = parser.parse(content)
        result = parser.reconstruct(blocks)
        
        # URL should be preserved
        assert full_url in result, f"URL not preserved: {full_url}"
    
    @given(
        alt=st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=1, max_size=20),
        filename=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_", min_size=3, max_size=15)
    )
    @settings(max_examples=100)
    def test_images_preserved(self, alt, filename):
        """For any markdown with images, images SHALL be preserved."""
        parser = MarkdownParser()
        
        img_path = f"/images/{filename}.png"
        content = f"See the diagram below:\n\n![{alt}]({img_path})\n\nAs shown above."
        
        blocks = parser.parse(content)
        result = parser.reconstruct(blocks)
        
        # Image path should be preserved
        assert img_path in result, f"Image path not preserved: {img_path}"


class TestFrontmatterPreservation:
    """Property-based tests for frontmatter preservation.
    
    **Feature: dev-docs-translator, Property 4: Frontmatter structure preserved**
    **Validates: Requirements 1.5**
    """
    
    @given(
        title=st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=3, max_size=30),
        slug=st.text(alphabet="abcdefghijklmnopqrstuvwxyz-", min_size=3, max_size=20)
    )
    @settings(max_examples=100)
    def test_frontmatter_structure_preserved(self, title, slug):
        """For any markdown with frontmatter, structure SHALL be preserved."""
        parser = MarkdownParser()
        
        content = f"""---
title: {title}
slug: {slug}
---

# Content here
"""
        
        blocks = parser.parse(content)
        result = parser.reconstruct(blocks)
        
        # Frontmatter markers should be preserved
        assert result.startswith("---\n"), "Frontmatter start marker missing"
        assert "---\n\n" in result, "Frontmatter end marker missing"
        # Slug should be preserved (not translated)
        assert slug in result, f"Slug not preserved: {slug}"


class TestMarkdownParserUnit:
    """Unit tests for MarkdownParser."""
    
    def test_parse_simple_markdown(self):
        """Simple markdown should parse correctly."""
        parser = MarkdownParser()
        content = "# Hello\n\nThis is a test."
        
        blocks = parser.parse(content)
        
        assert len(blocks) >= 1
        assert any(b.type == "text" for b in blocks)
    
    def test_extract_frontmatter(self):
        """Frontmatter should be extracted correctly."""
        parser = MarkdownParser()
        content = """---
title: Test
description: A test file
---

# Content
"""
        
        frontmatter, remaining = parser.extract_frontmatter(content)
        
        assert frontmatter is not None
        assert frontmatter["title"] == "Test"
        assert "# Content" in remaining
    
    def test_no_frontmatter(self):
        """Content without frontmatter should work."""
        parser = MarkdownParser()
        content = "# Just a heading\n\nSome text."
        
        frontmatter, remaining = parser.extract_frontmatter(content)
        
        assert frontmatter is None
        assert remaining == content
    
    def test_multiple_code_blocks(self):
        """Multiple code blocks should all be preserved."""
        parser = MarkdownParser()
        content = """# Example

```python
def hello():
    print("Hello")
```

Some text

```javascript
console.log("World");
```
"""
        
        blocks = parser.parse(content)
        result = parser.reconstruct(blocks)
        
        assert 'def hello():' in result
        assert 'console.log("World")' in result
    
    def test_url_preservation(self):
        """URLs should be preserved unchanged."""
        parser = MarkdownParser()
        content = "Visit https://example.com/path?query=1 for more."
        
        blocks = parser.parse(content)
        result = parser.reconstruct(blocks)
        
        assert "https://example.com/path?query=1" in result
