import typer
from rich.console import Console
from rich.table import Table
from indexer import index_project
from db import init_db, get_db

app = typer.Typer(help="CodeCake: On-Device AI Code Cartographer")
console = Console()

@app.command()
def init():
        """Initialize the local database"""
        init_db()
        console.print("[green]CodeCake database initialized successfully.[/green]")

@app.command()
def index(path: str = "."):
    """Index a directory code structure"""
    console.print(f"[bold blue]Indexing codebase in '{path}'[/bold blue]")
    index_project(path)

    conn = get_db()
    cur = conn.cursor()
    file_count = cur.execute("SELECT COUNT(* FROM files").fetchone()[0]
    symbol_count = cur.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
    conn.close()

    table = Table(title="Indexing Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Files Index", str(file_count))
    table.add_row("Symbols Parsed", str(symbol_count))

    console.print(table)

if __name__ == "__main__":
    app()