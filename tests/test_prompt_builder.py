"""
Property-based tests for PromptBuilder
Uses Hypothesis for property-based testing
"""
import pytest
from hypothesis import given, strategies as st, settings
from translatex.utils.prompt_builder import PromptBuilder


class TestPromptConsistency:
    """
    **Feature: openrouter-support, Property 6: Prompt consistency across providers**
    *For any* provider, the PromptBuilder SHALL generate identical system and user prompts.
    **Validates: Requirements 4.1**
    """
    
    @given(
        source_lang=st.sampled_from(["English", "Vietnamese", "French", "German", "Japanese"]),
        target_lang=st.sampled_from(["English", "Vietnamese", "French", "German", "Japanese"]),
        text=st.text(min_size=1, max_size=1000)
    )
    @settings(max_examples=100)
    def test_prompt_builder_generates_consistent_prompts(self, source_lang: str, target_lang: str, text: str):
        """Property: PromptBuilder generates identical prompts regardless of when called"""
        builder1 = PromptBuilder(source_lang, target_lang)
        builder2 = PromptBuilder(source_lang, target_lang)
        
        # Same inputs should produce same outputs
        assert builder1.build_system_prompt() == builder2.build_system_prompt()
        assert builder1.build_user_prompt(text) == builder2.build_user_prompt(text)
        assert builder1.build_messages(text) == builder2.build_messages(text)
    
    @given(
        source_lang=st.sampled_from(["English", "Vietnamese", "French"]),
        target_lang=st.sampled_from(["English", "Vietnamese", "French"]),
        text=st.text(min_size=1, max_size=500)
    )
    @settings(max_examples=100)
    def test_system_prompt_contains_language_info(self, source_lang: str, target_lang: str, text: str):
        """Property: System prompt always contains source and target language"""
        builder = PromptBuilder(source_lang, target_lang)
        system_prompt = builder.build_system_prompt()
        
        assert source_lang in system_prompt
        assert target_lang in system_prompt
    
    @given(text=st.text(min_size=1, max_size=500))
    @settings(max_examples=100)
    def test_user_prompt_contains_input_text(self, text: str):
        """Property: User prompt contains the input text"""
        builder = PromptBuilder("English", "Vietnamese")
        assert text in builder.build_user_prompt(text)
    
    @given(text=st.text(min_size=1, max_size=500))
    @settings(max_examples=100)
    def test_messages_structure_is_correct(self, text: str):
        """Property: Messages array has correct structure"""
        builder = PromptBuilder("English", "Vietnamese")
        messages = builder.build_messages(text)
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert text in messages[1]["content"]
    
    def test_system_prompt_contains_marker_instructions(self):
        """System prompt should contain instructions about preserving markers"""
        builder = PromptBuilder("English", "Vietnamese")
        system_prompt = builder.build_system_prompt()
        
        # Check for marker-related instructions
        assert "<R0>" in system_prompt or "marker" in system_prompt.lower()
        assert "preserve" in system_prompt.lower() or "keep" in system_prompt.lower()
