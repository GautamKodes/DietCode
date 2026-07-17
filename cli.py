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
def map(
    filter_path: str = typer.Option(None, "--filter", "-f", help="Only show files containing this path/pattern")
):
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
    
    if filter_path:
        files = [f for f in files if filter_path.lower() in f["filepath"].lower()]
        
    if not files:
        console.print("[yellow]No files matched the filter or codebase is empty. Run index command first to populate files.[/yellow]")
        return

    tree = Tree("[bold cyan]Codebase File Map[/bold cyan]", guide_style="blue")

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
            imports_text = ", ".join(predecessors) if predecessors else "None"
            
            successors = [os.path.basename(p) for p in G.successors(filepath)]
            dependents_text = ", ".join(successors) if successors else "None"
            
            file_node = tree.add(f"[bold cyan]📄 {filepath}[/bold cyan]")
            file_node.add(f"[bold white]Purpose:[/bold white] {f['summary'] or 'No description.'}")
            file_node.add(f"[bold magenta]Imports (Direct):[/bold magenta] {imports_text}")
            file_node.add(f"[bold yellow]Direct Dependents:[/bold yellow] {dependents_text}")
            
            progress.advance(task_rows)


    with console.pager(styles=True):
        console.print(Panel(project_summary, title="Project Overview", border_style="cyan"))
        console.print(tree)



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
def ask(question: str):
    print_banner()
    from search import semantic_search
    from indexer import query_ollama
    
    with console.status("[bold blue]Retrieving relevant codebase context...[/bold blue]", spinner="dots"):
        results = semantic_search(question, top_n=4)
        
    if not results:
        console.print("[yellow]No relevant context found in the database. Run 'dietcode index' first.[/yellow]")
        return
        
    context_blocks = []
    for score, sym in results:
        context_blocks.append(
            f"File: {sym['filepath']}\n"
            f"Symbol: {sym['name']} ({sym['type']}) at lines {sym['start_line']}-{sym['end_line']}\n"
            f"Content:\n{sym['content']}"
        )
    context_text = "\n\n---\n\n".join(context_blocks)
    
    prompt = (
        "You are an expert software engineer assistant. Answer the user's question about the codebase "
        "using the provided relevant code snippets. Be precise and concise. Refer to file names and line numbers "
        "if helpful.\n\n"
        f"--- CODEBASE CONTEXT ---\n{context_text}\n\n"
        f"--- USER QUESTION ---\n{question}\n\n"
        "Answer:"
    )
    
    with console.status("[bold blue]Consulting local AI assistant (Ollama)...[/bold blue]", spinner="dots"):
        answer = query_ollama(prompt)
        
    if not answer:
        console.print("[red]Error: Could not get a response from local Ollama. Make sure Ollama is running and has the model loaded.[/red]")
        return
        
    console.print(Panel(Markdown(answer), title="Local AI Assistant Response", border_style="green"))


@app.command()
def write(
    task: str,
    file: str = typer.Option(None, "--file", "-f", help="Target file to modify. If not provided, it will be auto-detected.")
):
    print_banner()
    from indexer import query_ollama
    from search import semantic_search_files
    
    target_file = None
    if file:
        if os.path.exists(file):
            target_file = file
        else:
            console.print(f"[red]Error: Specified file '{file}' does not exist.[/red]")
            return
    else:
        with console.status("[bold blue]Detecting target file...[/bold blue]", spinner="dots"):
            search_results = semantic_search_files(task, top_n=1)
            if search_results:
                target_file = search_results[0][1]
                
    if not target_file:
        console.print("[red]Error: Could not auto-detect target file. Please specify it using the --file option.[/red]")
        return
        
    console.print(f"[cyan]Target File detected/selected:[/cyan] [bold white]{target_file}[/bold white]\n")
    
    try:
        with open(target_file, "r", encoding="utf-8") as f_handle:
            current_code = f_handle.read()
    except Exception as e:
        console.print(f"[red]Error: Could not read target file: {e}[/red]")
        return
        
    prompt = (
        f"You are an expert autonomous coding agent. Your task is to perform the following modification:\n"
        f"\"{task}\"\n\n"
        f"Here is the current content of the file '{target_file}':\n"
        f"```\n{current_code}\n```\n\n"
        f"CRITICAL RULES:\n"
        f"1. Return ONLY the complete updated file content. Do NOT include markdown code fences (like ```python or ```), conversational text, or introductions.\n"
        f"2. Do NOT add comments (no # comments).\n"
        f"3. Make sure the output is syntactically correct and fully complete.\n\n"
        f"Updated File Content:"
    )
    
    with console.status(f"[bold blue]Instructing local AI to edit {target_file}...[/bold blue]", spinner="dots"):
        new_code = query_ollama(prompt)
        
    if not new_code:
        console.print("[red]Error: Could not get a response from local Ollama.[/red]")
        return
        
    new_code = new_code.strip()
    if new_code.startswith("```"):
        lines = new_code.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        new_code = "\n".join(lines).strip()
        
    if not new_code or len(new_code) < 10:
        console.print("[red]Error: Local AI returned an empty or invalid code block.[/red]")
        return
        
    console.print(Panel(new_code, title="Proposed Code Update", border_style="cyan"))
    
    confirm = typer.confirm("Would you like to write these changes to the file?")
    if not confirm:
        console.print("[yellow]Write operation cancelled.[/yellow]")
        return
        
    try:
        with open(target_file, "w", encoding="utf-8") as f_handle:
            f_handle.write(new_code)
        console.print(f"[green]✓ Successfully wrote updates to {target_file}.[/green]")
    except Exception as e:
        console.print(f"[red]Error writing to file: {e}[/red]")


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