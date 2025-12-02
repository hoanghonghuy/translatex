"""Tests for MDXParser - Properties 5-6."""

from hypothesis import given, strategies as st, settings

from translatex.docs.mdx_parser import MDXParser


class TestJSXComponentPreservation:
    """Property-based tests for JSX component preservation.
    
    **Feature: dev-docs-translator, Property 5: JSX components preserved**
    **Validates: Requirements 2.2, 2.4**
    """
    
    @given(suffix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=2, max_size=8))
    @settings(max_examples=50)
    def test_self_closing_components_preserved(self, suffix):
        """For any MDX with self-closing components, components SHALL be preserved."""
        component_name = "My" + suffix.capitalize()
        parser = MDXParser()
        
        content = f"""# Title

<{component_name} prop="value" />

Some text after.
"""
        
        blocks = parser.parse(content)
        result = parser.reconstruct(blocks)
        
        # Component should be in result
        assert component_name in result, f"Component {component_name} not preserved"
        assert 'prop="value"' in result, "Props not preserved"


class TestImportPreservation:
    """Property-based tests for import preservation.
    
    **Feature: dev-docs-translator, Property 6: Import statements preserved**
    **Validates: Requirements 2.3**
    """
    
    @given(module=st.text(alphabet="abcdefghijklmnopqrstuvwxyz-", min_size=3, max_size=20))
    @settings(max_examples=100)
    def test_imports_preserved(self, module):
        """For any MDX with imports, imports SHALL be preserved."""
        parser = MDXParser()
        
        content = f"""import Component from '{module}';

# Title

Some content here.
"""
        
        blocks = parser.parse(content)
        result = parser.reconstruct(blocks)
        
        # Import should be preserved
        assert f"import Component from '{module}'" in result, f"Import not preserved"


class TestMDXParserUnit:
    """Unit tests for MDXParser."""
    
    def test_parse_simple_mdx(self):
        """Simple MDX should parse correctly."""
        parser = MDXParser()
        content = """import { Button } from '@components';

# Hello

<Button>Click me</Button>
"""
        
        blocks = parser.parse(content)
        
        assert len(blocks) >= 1
        # Should have import block
        assert any(b.type == "import" for b in blocks)
    
    def test_extract_imports(self):
        """Imports should be extracted correctly."""
        parser = MDXParser()
        content = """import React from 'react';
import { useState } from 'react';

# Content
"""
        
        imports = parser.extract_imports(content)
        
        assert len(imports) >= 1
        assert any("react" in imp for imp in imports)
    
    def test_preserve_jsx_expressions(self):
        """JSX expressions should be preserved."""
        parser = MDXParser()
        content = """# Title

The value is {someVariable}.

More text.
"""
        
        blocks = parser.parse(content)
        result = parser.reconstruct(blocks)
        
        assert "{someVariable}" in result
    
    def test_component_with_content(self):
        """Components with content should be preserved."""
        parser = MDXParser()
        content = """# Title

<Callout type="info">
This is important information.
</Callout>

More text.
"""
        
        blocks = parser.parse(content)
        result = parser.reconstruct(blocks)
        
        assert "<Callout" in result
        assert "</Callout>" in result
        assert 'type="info"' in result
    
    def test_mixed_content(self):
        """Mixed markdown and MDX should work."""
        parser = MDXParser()
        content = """---
title: Test
---

import { Card } from '@ui';

# Getting Started

Here's some `inline code` and a [link](https://example.com).

```javascript
const x = 1;
```

<Card title="Note">
Important note here.
</Card>
"""
        
        blocks = parser.parse(content)
        result = parser.reconstruct(blocks)
        
        # All elements should be preserved
        assert "title: Test" in result
        assert "import { Card }" in result
        assert "`inline code`" in result
        assert "https://example.com" in result
        assert "const x = 1;" in result
        assert "<Card" in result
