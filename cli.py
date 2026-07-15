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
from graph import get_impact_tree, build_dependency_graph
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
    if console.width < 60:
        logo_content = "[bold bright_cyan]DIETCODE[/bold bright_cyan]"
    else:
        logo_lines = LOGO_TEXT.strip("\n").split("\n")
        styled_logo = ""
        colors = ["bold bright_cyan", "bold cyan", "cyan", "bold blue", "blue"]
        for line, color in zip(logo_lines, colors):
            styled_logo += f"[{color}]{line} [/{color}]\n"
        logo_content = styled_logo.strip("\n")
        
    tagline = "[bold white]DietCode[/bold white] [dim]•[/dim] [italic cyan]Source code cartographer for navigation and safe commits.[/italic cyan]"
    if console.width < 80:
        tagline = "[bold white]DietCode[/bold white]\n[dim]Source code cartographer[/dim]"
    
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
    with console.status(f"[bold blue]Searching semantically for '{query}'...[/bold blue]", spinner="dots"):
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
    with console.status(f"[bold blue]Calculating change impact for '{filepath}'...[/bold blue]", spinner="dots"):
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
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        transient=True
    ) as progress:
        p_task = progress.add_task("[bold cyan]Generating mission brief...", total=100)
        progress.update(p_task, completed=30)
        brief_content = build_mission_brief(task, force_files=files, mode=mode)
        progress.update(p_task, completed=100)
    
    with open("MISSION_BRIEF.md", "w", encoding="utf-8") as f:
        f.write(brief_content)
        
    console.print("[green]✓ MISSION_BRIEF.md written successfully.[/green]\n")
    console.print(Panel(Markdown(brief_content), title="Mission Brief Preview", border_style="green"))

@app.command()
def map():
    print_banner()
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM project_meta WHERE key = 'summary'")
    summary_row = cur.fetchone()
    project_summary = summary_row["value"] if summary_row else "No project overview cached. Run index first."
    
    cur.execute("SELECT filepath, summary FROM files")
    files = cur.fetchall()
    conn.close()
    
    if not files:
        console.print("[yellow]Codebase is empty. Run index command first to populate files.[/yellow]")
        return

    table = Table(
        title="Codebase File Map",
        title_style="bold cyan",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold white",
        show_lines=True,
        expand=True
    )
    table.add_column("File Path", style="cyan", ratio=2, no_wrap=True)
    table.add_column("1-Sentence Purpose", style="white", ratio=4)
    table.add_column("Imports (Direct)", style="magenta", ratio=3)
    table.add_column("Direct Dependents", style="yellow", ratio=3)


    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        transient=True
    ) as progress:
        task_graph = progress.add_task("[bold cyan]Analyzing dependencies...", total=100)
        progress.update(task_graph, completed=20)
        G = build_dependency_graph()
        progress.update(task_graph, completed=100)
        
        task_rows = progress.add_task("[bold cyan]Compiling onboarding file map...", total=len(files))
        for f in files:
            filepath = f["filepath"]
            progress.update(task_rows, description=f"[bold cyan]Mapping: {os.path.basename(filepath)}")
            
            predecessors = [os.path.basename(p) for p in G.predecessors(filepath)]
            imports_text = "\n".join(predecessors) if predecessors else "None"
            
            successors = [os.path.basename(p) for p in G.successors(filepath)]
            dependents_text = "\n".join(successors) if successors else "None"
            
            table.add_row(
                os.path.basename(filepath),
                f["summary"] or "No description.",
                imports_text,
                dependents_text
            )
            progress.advance(task_rows)

    with console.pager(styles=True):
        console.print(Panel(project_summary, title="Project Overview", border_style="cyan"))
        console.print(table)

@app.command()
def tree(path: str = "."):

    print_banner()
    with console.status(f"[bold blue]Generating Codebase Structure Tree...[/bold blue]", spinner="dots"):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT filepath, summary FROM files")
        file_summaries = {r["filepath"]: r["summary"] for r in cur.fetchall()}
        conn.close()
        
        root_path = os.path.abspath(path)
        if not os.path.exists(root_path):
            console.print(f"[red]Error: Path '{path}' does not exist.[/red]")
            return
            
        IGNORE_DIRS = {".git", "node_modules", "venv", "__pycache__", ".venv", "model", "dietcode.egg-info", "build", "dist", ".next", "out"}

        
        root_node = Tree(f"📁 [bold cyan]{os.path.basename(root_path) or root_path}[/bold cyan]")

        
        def build_tree(current_path, parent_tree):
            try:
                entries = sorted(os.listdir(current_path))
            except Exception:
                return
                
            for entry in entries:
                if entry in IGNORE_DIRS:
                    continue
                    
                entry_path = os.path.join(current_path, entry)
                matched_summary = None
                for db_path, summary in file_summaries.items():
                    if os.path.abspath(db_path) == os.path.abspath(entry_path):
                        matched_summary = summary
                        break
                
                if os.path.isdir(entry_path):
                    branch = parent_tree.add(f"📁 [bold blue]{entry}[/bold blue]")
                    build_tree(entry_path, branch)
                else:
                    if entry.endswith((".py", ".rs", ".java", ".js", ".jsx", ".ts", ".tsx")):
                        summary_text = f" [dim]• {matched_summary}[/dim]" if matched_summary else " [dim]• (Unindexed)[/dim]"
                        parent_tree.add(f"📄 [green]{entry}[/green]{summary_text}")
                    else:
                        summary_text = f" [dim]• {matched_summary}[/dim]" if matched_summary else ""
                        parent_tree.add(f"📄 [white]{entry}[/white]{summary_text}")
                        
        build_tree(root_path, root_node)
        
    console.print(root_node)

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
            if len(args) == 1 and args[0].lower() == "help":
                args = ["--help"]
                
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