"""Rich console UI for TranslateX."""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich import box
from typing import Optional


# Global console instance
console = Console()


def print_banner():
    """Print TranslateX banner - minimal version."""
    console.print("[bold cyan]TranslateX[/bold cyan] - AI Document Translation", style="dim")


def print_config(provider: str, model: str, source_lang: str, target_lang: str, **kwargs):
    """Print configuration info - single line format."""
    from translatex.utils.llm_client_factory import LLMClientFactory
    is_free = LLMClientFactory.is_free_model(model)
    free_tag = " [green](FREE)[/green]" if is_free else ""
    
    console.print(f"[cyan]⚙[/cyan] {provider}/{model}{free_tag} | {source_lang} → {target_lang}")


def print_success(message: str):
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str):
    """Print error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[bold yellow]![/bold yellow] {message}")


def print_info(message: str):
    """Print info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def print_summary(title: str, stats: dict):
    """Print summary - compact single line."""
    parts = []
    for key, value in stats.items():
        if value > 0 or "translated" in key.lower() or "total" in key.lower():
            if "failed" in key.lower() and value > 0:
                parts.append(f"[red]{key}: {value}[/red]")
            elif "cached" in key.lower():
                parts.append(f"[yellow]{key}: {value}[/yellow]")
            else:
                parts.append(f"{key}: {value}")
    
    console.print(f"[dim]{' | '.join(parts)}[/dim]")


def print_file_result(filename: str, status: str, output: str = None, error: str = None):
    """Print single file translation result."""
    if status == "success":
        console.print(f"  [green]✓[/green] {filename}")
        if output:
            console.print(f"    [dim]→ {output}[/dim]")
    elif status == "cached":
        console.print(f"  [yellow]○[/yellow] {filename} [dim](cached)[/dim]")
    else:
        console.print(f"  [red]✗[/red] {filename}")
        if error:
            console.print(f"    [red dim]{error}[/red dim]")


def create_progress() -> Progress:
    """Create a rich progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        console=console,
        transient=False
    )


def print_docs_header(source_dir: str, output_dir: str, file_count: int, asset_count: int = 0):
    """Print docs translation header - compact."""
    console.print(f"[cyan]📁[/cyan] {source_dir} → {output_dir} ({file_count} files, {asset_count} assets)")


def print_docx_header(input_file: str, output_dir: str):
    """Print DOCX translation header - compact."""
    import os
    filename = os.path.basename(input_file)
    console.print(f"[cyan]📄[/cyan] {filename} → {output_dir}/")
