"""Context window for coherent translations."""

from collections import deque
from typing import List, Optional


class ContextWindow:
    """Maintains a sliding window of previous segments for context."""
    
    def __init__(self, window_size: int = 0):
        """Initialize context window.
        
        Args:
            window_size: Number of previous segments to keep (0 = disabled)
        """
        self.window_size = window_size
        self.history: deque = deque(maxlen=window_size if window_size > 0 else 1)
    
    def add(self, segment: str):
        """Add a translated segment to history."""
        if self.window_size > 0:
            self.history.append(segment)
    
    def get_context(self) -> Optional[str]:
        """Get context string for prompt.
        
        Returns:
            Formatted context string or None if disabled/empty
        """
        if self.window_size == 0 or not self.history:
            return None
        
        return "\n".join(self.history)
    
    def get_context_segments(self) -> List[str]:
        """Get list of context segments."""
        if self.window_size == 0:
            return []
        return list(self.history)
    
    def clear(self):
        """Clear context history."""
        self.history.clear()
    
    def size(self) -> int:
        """Return current number of segments in context."""
        return len(self.history)
    
    def format_for_prompt(self) -> str:
        """Format context for inclusion in translation prompt.
        
        Returns:
            Formatted string with context marked as reference only
        """
        if self.window_size == 0 or not self.history:
            return ""
        
        context_text = self.get_context()
        return f"""
[CONTEXT - For reference only, do not translate this section]
Previous translated segments:
---
{context_text}
---
[END CONTEXT]
"""
