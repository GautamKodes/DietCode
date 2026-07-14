import os
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich import box
from rich.markdown import Markdown
from rich.tree import Tree
from indexer import index_project
from db import init_db, get_db
from search import semantic_search
from graph import get_impact_tree
from brief import build_mission_brief

app = typer.Typer(help="DietCode: Source code cartographer for navigation and safe commits.")
console = Console()

LOGO_TEXT = """
    ____  _      __  ______          __
   / __ \\(_)__  / /_/ ____/___  ____/ /__
  / / / / / _ \\/ __/ /   / __ \\/ __  / _ \\
 / /_/ / /  __/ /_/ /___/ /_/ / /_/ /  __/
/_____/_/\\___/\\__/\\____/\\____/\\__,_/\\___/
"""

def print_banner():
    logo_lines = LOGO_TEXT.strip("\n").split("\n")
    styled_logo = ""
    colors = ["bold bright_cyan", "bold cyan", "cyan", "bold blue", "blue"]
    for line, color in zip(logo_lines, colors):
        styled_logo += f"[{color}]{line}[/{color}]\n"
        
    tagline = "[bold white]DietCode[/bold white] [dim]•[/dim] [italic cyan]Source code cartographer for navigation and safe commits.[/italic cyan]"
    
    panel = Panel(
        Align.center(f"{styled_logo}\n{tagline}"),
        box=box.DOUBLE,
        border_style="cyan",
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

@app.command()
def search(query: str):
    print_banner()
    console.print(f"[bold blue]Searching semantically for '{query}'...[/bold blue]")
    results = semantic_search(query)
    
    if not results:
        console.print("[yellow]No matching code symbols found.[/yellow]")
        return

    table = Table(
        title="Search Results",
        title_style="bold cyan",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold white",
        show_lines=True
    )
    table.add_column("Similarity", style="bold green", justify="right", width=10)
    table.add_column("Symbol", style="cyan", width=20)
    table.add_column("Type", style="magenta", width=10)
    table.add_column("Filepath", style="dim", width=40)

    for score, sym in results:
        table.add_row(
            f"{score:.4f}",
            sym["name"],
            sym["type"],
            f"{sym['filepath']}:{sym['start_line']}"
        )
    console.print(table)

@app.command()
def impact(filepath: str):
    print_banner()
    console.print(f"[bold blue]Calculating change impact for '{filepath}'...[/bold blue]")
    
    T = get_impact_tree(filepath)
    if not T or len(T.nodes) <= 1:
        console.print("[yellow]No downstream impact detected. This file is not imported by any other project files.[/yellow]")
        return
        
    resolved_target = list(T.nodes)[0]
    root_name = os.path.basename(resolved_target)
    tree = Tree(f"[bold red]🚨 {root_name}[/bold red]")
    
    def add_branches(graph, node, rich_node):
        for successor in graph.successors(node):
            branch = rich_node.add(f"[cyan]{os.path.basename(successor)}[/cyan]")
            add_branches(graph, successor, branch)
            
    add_branches(T, resolved_target, tree)
    console.print(tree)

@app.command()
def brief(
    task: str,
    files: str = typer.Option(None, "--files", "-f", help="Force specific files or symbols to be targeted"),
    mode: str = typer.Option("web", "--mode", "-m", help="Target mode: 'web' (human copy-paste layout) or 'agent' (token-efficient agent layout)")
):
    print_banner()
    console.print(f"[bold blue]Generating mission brief for: '{task}' in '{mode}' mode...[/bold blue]")
    brief_content = build_mission_brief(task, force_files=files, mode=mode)
    
    with open("MISSION_BRIEF.md", "w", encoding="utf-8") as f:
        f.write(brief_content)
        
    console.print("[green]✓ MISSION_BRIEF.md written successfully.[/green]\n")
    console.print(Panel(Markdown(brief_content), title="Mission Brief Preview", border_style="green"))

@app.command()
def map():
    print_banner()
    console.print("[bold blue]Generating Codebase Dependency & Onboarding Map...[/bold blue]\n")
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT value FROM project_meta WHERE key = 'summary'")
    summary_row = cur.fetchone()
    project_summary = summary_row["value"] if summary_row else "No project overview cached. Run index first."
    
    cur.execute("SELECT id, filepath, summary FROM files")
    files = cur.fetchall()
    
    if not files:
        console.print("[yellow]Codebase is empty. Run index command first to populate files.[/yellow]")
        conn.close()
        return

    console.print(Panel(project_summary, title="Project Overview", border_style="cyan"))

    table = Table(
        title="Codebase File Map",
        title_style="bold cyan",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold white",
        show_lines=True
    )
    table.add_column("File Path", style="cyan", width=25)
    table.add_column("1-Sentence Purpose", style="white", width=40)
    table.add_column("Imports (Direct)", style="magenta", width=20)
    table.add_column("Direct Dependents", style="yellow", width=20)

    for f in files:
        file_id = f["id"]
        filepath = f["filepath"]
        summary = f["summary"] or "No description."
        
        cur.execute("SELECT imported_module FROM imports WHERE file_id = ?", (file_id,))
        direct_imports = [imp["imported_module"] for imp in cur.fetchall()]
        imports_text = ", ".join(direct_imports) if direct_imports else "None"
        
        filename = os.path.basename(filepath)
        module_name = os.path.splitext(filename)[0]
        cur.execute("""
            SELECT files.filepath 
            FROM imports 
            JOIN files ON imports.file_id = files.id
            WHERE imports.imported_module = ? OR imports.imported_module LIKE ?
        """, (module_name, f"%.{module_name}"))
        dependents = [os.path.basename(dep["filepath"]) for dep in cur.fetchall()]
        dependents_text = ", ".join(dependents) if dependents else "None"
        
        table.add_row(
            os.path.basename(filepath),
            summary,
            imports_text,
            dependents_text
        )
        
    conn.close()
    console.print(table)

@app.command()
def shell():
    print_banner()
    console.print("[bold green]Welcome to the DietCode Interactive Shell![/bold green]")
    console.print("Type [cyan]help[/cyan] to see commands, or [cyan]exit[/cyan] to quit.\n")
    
    import shlex
    while True:
        try:
            user_input = console.input("[bold blue]dietcode>[/bold blue] ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                break
            
            args = shlex.split(user_input)
            try:
                app(args)
            except SystemExit:
                pass
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' or Ctrl-D to quit.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    app()