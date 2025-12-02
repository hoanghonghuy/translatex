"""Batch processing for multiple DOCX files."""

from pathlib import Path
from typing import Dict, List, Callable, Any
from dataclasses import dataclass

from .utils.exceptions import BatchError
from .utils.file_logger import get_logger


@dataclass
class BatchResult:
    """Result of batch processing."""
    file: str
    status: str  # "success", "failed", "skipped"
    output_file: str = None
    error: str = None


class BatchProcessor:
    """Processes multiple DOCX files sequentially."""
    
    def __init__(self, translator_factory: Callable, sequential: bool = True):
        """Initialize batch processor.
        
        Args:
            translator_factory: Factory function to create translator instances
            sequential: Process files sequentially (recommended for API limits)
        """
        self.translator_factory = translator_factory
        self.sequential = sequential
    
    def find_docx_files(self, directory: str) -> List[str]:
        """Find all .docx files in directory.
        
        Args:
            directory: Directory path to search
            
        Returns:
            List of .docx file paths
        """
        path = Path(directory)
        if not path.exists():
            raise BatchError(f"Directory not found: {directory}")
        if not path.is_dir():
            raise BatchError(f"Not a directory: {directory}")
        
        docx_files = list(path.glob("*.docx"))
        # Filter out temp files (start with ~$)
        docx_files = [f for f in docx_files if not f.name.startswith("~$")]
        
        return [str(f) for f in sorted(docx_files)]
    
    def process(
        self,
        files: List[str],
        output_dir: str = None,
        on_progress: Callable[[int, int, str], None] = None
    ) -> Dict[str, BatchResult]:
        """Process multiple files.
        
        Args:
            files: List of file paths to process
            output_dir: Output directory (optional)
            on_progress: Callback(current, total, filename) for progress updates
            
        Returns:
            Dict mapping filename to BatchResult
        """
        logger = get_logger()
        results: Dict[str, BatchResult] = {}
        total = len(files)
        
        logger.info(f"Starting batch processing of {total} files")
        
        for idx, file_path in enumerate(files):
            filename = Path(file_path).name
            
            if on_progress:
                on_progress(idx + 1, total, filename)
            
            logger.info(f"Processing [{idx + 1}/{total}]: {filename}")
            
            try:
                # Create translator instance
                translator = self.translator_factory()
                
                # Translate file
                output_file = translator.translate(file_path, output_dir)
                
                results[file_path] = BatchResult(
                    file=file_path,
                    status="success",
                    output_file=output_file
                )
                logger.info(f"Completed: {filename}")
                
            except Exception as e:
                error_msg = str(e)
                results[file_path] = BatchResult(
                    file=file_path,
                    status="failed",
                    error=error_msg
                )
                logger.error(f"Failed: {filename} - {error_msg}")
                # Continue with remaining files
        
        # Log summary
        success_count = sum(1 for r in results.values() if r.status == "success")
        failed_count = sum(1 for r in results.values() if r.status == "failed")
        
        logger.info(f"Batch complete: {success_count} succeeded, {failed_count} failed")
        
        return results
    
    def get_summary(self, results: Dict[str, BatchResult]) -> Dict[str, Any]:
        """Get summary statistics from batch results.
        
        Args:
            results: Results from process()
            
        Returns:
            Summary dict with counts and lists
        """
        success = [r for r in results.values() if r.status == "success"]
        failed = [r for r in results.values() if r.status == "failed"]
        
        return {
            "total": len(results),
            "success_count": len(success),
            "failed_count": len(failed),
            "success_files": [r.file for r in success],
            "failed_files": [(r.file, r.error) for r in failed]
        }
