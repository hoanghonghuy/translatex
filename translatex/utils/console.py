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
    """Print TranslateX banner."""
    banner = """
╔════════════════════════════════════════════════════════════╗
║                      TranslateX                            ║
║         AI-powered Document Translation Tool               ║
╚════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def print_config(provider: str, model: str, source_lang: str, target_lang: str, **kwargs):
    """Print configuration info."""
    table = Table(show_header=False, box=box.ROUNDED, border_style="dim")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Provider", provider)
    table.add_row("Model", model)
    table.add_row("Languages", f"{source_lang} → {target_lang}")
    
    for key, value in kwargs.items():
        if value is not None:
            table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(Panel(table, title="[bold]Configuration[/bold]", border_style="blue"))


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
    """Print summary table."""
    table = Table(title=title, box=box.ROUNDED, border_style="green")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white", justify="right")
    
    for key, value in stats.items():
        # Color code based on key
        if "failed" in key.lower():
            value_style = "red" if value > 0 else "green"
        elif "success" in key.lower() or "translated" in key.lower():
            value_style = "green"
        elif "cached" in key.lower():
            value_style = "yellow"
        else:
            value_style = "white"
        
        table.add_row(key, f"[{value_style}]{value}[/{value_style}]")
    
    console.print(table)


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
    """Print docs translation header."""
    console.print()
    console.print(Panel(
        f"[cyan]Source:[/cyan] {source_dir}\n"
        f"[cyan]Output:[/cyan] {output_dir}\n"
        f"[cyan]Files:[/cyan] {file_count} documentation files\n"
        f"[cyan]Assets:[/cyan] {asset_count} files copied",
        title="[bold]Documentation Translation[/bold]",
        border_style="blue"
    ))
    console.print()


def print_docx_header(input_file: str, output_dir: str):
    """Print DOCX translation header."""
    console.print()
    console.print(Panel(
        f"[cyan]Input:[/cyan] {input_file}\n"
        f"[cyan]Output:[/cyan] {output_dir}",
        title="[bold]DOCX Translation[/bold]",
        border_style="blue"
    ))
    console.print()
