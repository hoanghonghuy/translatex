"""Tests for CheckpointManager - Properties 1 & 2."""

import os
import tempfile
from hypothesis import given, strategies as st, settings

from translatex.utils.checkpoint import CheckpointManager


class TestCheckpointSaveProperty:
    """Property-based tests for checkpoint save.
    
    **Feature: advanced-features, Property 1: Checkpoint saves progress**
    **Validates: Requirements 1.1, 1.3**
    """
    
    @given(
        segments=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=20),
        translated_ratio=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=100)
    def test_checkpoint_saves_all_translated_segments(self, segments, translated_ratio):
        """For any interrupted translation, checkpoint SHALL contain all translated segments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_file = os.path.join(tmpdir, "checkpoint.json")
            manager = CheckpointManager(checkpoint_file)
            
            # Simulate partial translation
            num_translated = int(len(segments) * translated_ratio)
            translated_indices = set(range(num_translated))
            translations = {i: f"translated_{i}" for i in translated_indices}
            
            # Save checkpoint
            manager.save(segments, translated_indices, translations)
            
            # Load and verify
            loaded_indices, loaded_translations = manager.load()
            
            assert loaded_indices == translated_indices, "All translated indices should be saved"
            assert len(loaded_translations) == len(translations), "All translations should be saved"
            for idx in translated_indices:
                assert idx in loaded_indices, f"Index {idx} should be in checkpoint"


class TestResumeSkipsProperty:
    """Property-based tests for resume behavior.
    
    **Feature: advanced-features, Property 2: Resume skips translated segments**
    **Validates: Requirements 1.3**
    """
    
    @given(
        total_segments=st.integers(min_value=5, max_value=50),
        completed_count=st.integers(min_value=1, max_value=4)
    )
    @settings(max_examples=100)
    def test_resume_identifies_untranslated_segments(self, total_segments, completed_count):
        """For any resume operation, only untranslated segments SHALL be identified for processing."""
        completed_count = min(completed_count, total_segments - 1)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_file = os.path.join(tmpdir, "checkpoint.json")
            manager = CheckpointManager(checkpoint_file)
            
            segments = [f"segment_{i}" for i in range(total_segments)]
            translated_indices = set(range(completed_count))
            translations = {i: f"translated_{i}" for i in translated_indices}
            
            # Save checkpoint
            manager.save(segments, translated_indices, translations)
            
            # Load checkpoint
            loaded_indices, _ = manager.load()
            
            # Calculate untranslated
            all_indices = set(range(total_segments))
            untranslated = all_indices - loaded_indices
            
            # Verify
            assert len(untranslated) == total_segments - completed_count
            for idx in range(completed_count):
                assert idx not in untranslated, f"Translated index {idx} should be skipped"
            for idx in range(completed_count, total_segments):
                assert idx in untranslated, f"Untranslated index {idx} should be processed"


class TestCheckpointUnit:
    """Unit tests for CheckpointManager."""
    
    def test_exists_returns_false_for_new(self):
        """exists() should return False for non-existent checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_file = os.path.join(tmpdir, "checkpoint.json")
            manager = CheckpointManager(checkpoint_file)
            assert not manager.exists()
    
    def test_exists_returns_true_after_save(self):
        """exists() should return True after save."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_file = os.path.join(tmpdir, "checkpoint.json")
            manager = CheckpointManager(checkpoint_file)
            
            manager.save(["seg1", "seg2"], {0}, {0: "trans1"})
            assert manager.exists()
    
    def test_clear_removes_checkpoint(self):
        """clear() should remove checkpoint file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_file = os.path.join(tmpdir, "checkpoint.json")
            manager = CheckpointManager(checkpoint_file)
            
            manager.save(["seg1"], {0}, {0: "trans1"})
            assert manager.exists()
            
            manager.clear()
            assert not manager.exists()
    
    def test_get_progress(self):
        """get_progress() should return summary info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_file = os.path.join(tmpdir, "checkpoint.json")
            manager = CheckpointManager(checkpoint_file)
            
            segments = ["seg1", "seg2", "seg3", "seg4", "seg5"]
            manager.save(segments, {0, 1, 2}, {0: "t1", 1: "t2", 2: "t3"})
            
            progress = manager.get_progress()
            assert progress["total"] == 5
            assert progress["completed"] == 3
    
    def test_validate_same_segments(self):
        """validate() should return True for same segments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_file = os.path.join(tmpdir, "checkpoint.json")
            manager = CheckpointManager(checkpoint_file)
            
            segments = ["seg1", "seg2", "seg3"]
            manager.save(segments, {0}, {0: "t1"})
            
            assert manager.validate(segments)
    
    def test_validate_different_segments(self):
        """validate() should return False for different segments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_file = os.path.join(tmpdir, "checkpoint.json")
            manager = CheckpointManager(checkpoint_file)
            
            segments1 = ["seg1", "seg2", "seg3"]
            segments2 = ["seg1", "seg2", "seg4"]  # Different
            
            manager.save(segments1, {0}, {0: "t1"})
            
            assert not manager.validate(segments2)
