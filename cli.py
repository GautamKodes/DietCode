import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich import box
from indexer import index_project
from db import init_db, get_db

app = typer.Typer(help="DietCode: On-Device AI Code Intelligence")
console = Console()

LOGO_TEXT = """
    ____  _      __  ______          __
   / __ \\(_)__  / /_/ ____/___  ____/ /__
  / / / / / _ \\/ __/ /   / __ \\/ __  / _ \\
 / /_/ / /  __/ /_/ /___/ /_/ / /_/ /  __/
/_____/_/\\___/\\__/\\____/\\____/\\__,_/\\___/
"""

def print_banner():
    content = f"[bold cyan]{LOGO_TEXT}[/bold cyan]\n[bold white]DietCode[/bold white] • [dim]On-Device AI Code Intelligence[/dim]"
    panel = Panel(
        Align.center(content),
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)

@app.command()
def init():
    print_banner()
    init_db()
    console.print("[green]✓ DietCode database initialized successfully.[/green]")

@app.command()
def index(path: str = "."):
    print_banner()
    console.print(f"[bold blue]Indexing codebase in '{path}'...[/bold blue]")
    index_project(path)

    conn = get_db()
    cur = conn.cursor()
    file_count = cur.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    symbol_count = cur.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
    conn.close()

    table = Table(
        title="Indexing Summary",
        title_style="bold cyan",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold white",
        show_lines=True
    )
    table.add_column("Metric", style="cyan", width=25)
    table.add_column("Count", style="bold green", justify="right", width=10)

    table.add_row("Total Files Indexed", str(file_count))
    table.add_row("Symbols Parsed", str(symbol_count))

    console.print(table)

if __name__ == "__main__":
    app()