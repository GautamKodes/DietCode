# DietCode 🥤
### Source code cartographer for navigation and safe commits.

DietCode is an offline-ready, privacy-first terminal utility that indexes codebase structures, maps dependencies, performs conceptual semantic searches, and generates token-optimized mission briefs. It runs 100% on-device, safeguarding your IP while keeping your workflow incredibly fast.

---

## 🚀 Key Features

* **Abstract Syntax Tree (AST) Parsing:** Uses Tree-sitter to parse code structures (classes and functions) rather than relying on brittle text matching.
* **On-Device Semantic Search:** Converts code symbols and summaries into vector embeddings using a local Sentence-Transformers model (`all-MiniLM-L6-v2`) for conceptual code searches.
* **Dependency & Impact Cartography:** Builds directed import graphs and traces cascading downstream impact paths (using `rich.tree` visualization).
* **Onboarding & Codebase Maps:** Generates a project-level dashboard summarizing every file, its direct imports, and downstream dependents.
* **Visual Structure Trees:** Prints a clean project directory tree with file purpose summaries embedded directly next to file names.
* **Dual-Mode AI Mission Briefs:** Generates prompts in two customized modes:
  * **Web Mode:** Designed for web-based chatbots (e.g. ChatGPT / Claude Web). Includes code blocks and requests human-readable complete functions.
  * **Agent Mode:** Designed for CLI coding agents (e.g. Claude Code / Antigravity). Saves 95%+ of prompt tokens by omitting code contents and giving direct tool commands.
* **Interactive REPL Shell:** Take over your terminal in a persistent session where you can run commands directly without prefixes.

---

## 📋 System & Library Dependencies

To run DietCode locally, the following dependencies are required:

### System Requirements
* **Operating System:** Linux / macOS (tested on Linux/Arch).
* **Python:** Python 3.10 or higher.
* **SQLite3:** Built-in with Python.
* **Ollama (Optional):** Required to run local summaries using `qwen2.5-coder:1.5b`. If not available, DietCode falls back to rule-based static syntax heuristics.

### Python Packages (Managed automatically by installer)
* `torch` (CPU-only optimized runtime, ~350MB)
* `sentence-transformers` (Local embedding inference)
* `typer` (CLI structure parser)
* `rich` (Terminal tables, progress bars, panels, and trees)
* `networkx` (Dependency graphing & impact BFS cascades)
* `tree-sitter` & precompiled parser grammars:
  * `tree-sitter-python`
  * `tree-sitter-rust`
  * `tree-sitter-java`
  * `tree-sitter-javascript`
  * `tree-sitter-typescript`

---

## 🛠️ Installation & Setup Instructions

To install DietCode globally:

```bash
# 1. Clone the repository
git clone https://github.com/GautamKodes/DietCode.git
cd DietCode

# 2. Run the installer script
./install.sh
```

### What the installer does:
1. Creates an isolated virtual environment at `~/.dietcode/venv`.
2. Installs PyTorch (CPU-only version) and all required Python packages.
3. Automatically copies local model weights to the global cache directory `~/.dietcode/model/` (ensures 100% offline startup).
4. Creates a global runner script in `~/.local/bin/dietcode`.
5. Prompts to start/configure Ollama and download the local `qwen2.5-coder:1.5b` model if not present.

*Note: Make sure `~/.local/bin` is in your shell's `PATH` (e.g., in your `~/.bashrc` or `~/.zshrc`).*

---

## 💻 CLI Commands (Sample Inputs & Expected Outputs)

### 📦 1. Index Codebase
Scans the current project directory, ignoring build/dependency folders (like `.git`, `node_modules`, `.next`, `out`), parses AST structures, and generates 1-sentence summaries.

* **Command:**
  ```bash
  dietcode index
  ```
* **Sample Input:** Run this inside a project root directory (e.g., the DietCode repo itself).
* **Expected Output:**
  A live progress bar showing file crawl scanning, followed by an Indexing Summary table:
  ```text
               Indexing Summary             
  ╭───────────────────────────┬────────────╮
  │ Metric                    │      Count │
  ├───────────────────────────┼────────────┤
  │ Total Files Indexed       │          8 │
  ├───────────────────────────┼────────────┤
  │ Symbols Parsed            │         28 │
  ╰───────────────────────────┴────────────╯
  ```

---

### 🗺️ 2. Onboarding Map
Generates a colorized grid overview showing every file's purpose, what it imports, and who imports it.

* **Command:**
  ```bash
  dietcode map
  ```
* **Sample Filter Input:** (Filter down to files containing "db")
  ```bash
  dietcode map --filter db
  ```
* **Expected Output:**
  A fullscreen scrollable pager (press `q` to exit) showing:
  ```text
  Codebase File Map
  └── 📄 ./db.py
      ├── Purpose: Handles SQLite database caching and queries.
      ├── Imports (Direct): None
      └── Direct Dependents: search.py, indexer.py, cli.py
  ```


---

### 🔍 3. Semantic Search
Finds matching code functions and classes based on conceptual meaning using local vector embeddings.

* **Command:**
  ```bash
  dietcode search "<QUERY>"
  ```
* **Sample Input:**
  ```bash
  dietcode search "database connection"
  ```
* **Expected Output:**
  A similarity-ranked table showing matching symbols, code location, and scores:
  ```text
                                   Search Results                                 
  ╭─────────┬───────────────────┬────────┬───────────────────────────────────────╮
  │ Simila… │ Symbol            │ Type   │ Filepath                              │
  ├─────────┼───────────────────┼────────┼───────────────────────────────────────┤
  │  0.3695 │ get_db            │ funct… │ ./db.py:5                             │
  │  0.2296 │ init_db           │ funct… │ ./db.py:12                            │
  ╰─────────┴───────────────────┴────────┴───────────────────────────────────────╯
  ```

---

### 🚨 4. Change Impact Cascades
Trace exactly which downstream files import or rely on a file you are about to modify.

* **Command:**
  ```bash
  dietcode impact <FILENAME>
  ```
* **Sample Input:**
  ```bash
  dietcode impact parser.py
  ```
* **Expected Output:**
  A colored dependency cascade tree:
  ```text
  🚨 parser.py
  └── indexer.py
      └── cli.py
  ```

---

### 📝 5. Generate Mission Briefs
Generate a token-optimized markdown prompt guide directing a developer or coding agent on how to execute a feature.

* **Command:**
  ```bash
  dietcode brief "<TASK>" [OPTIONS]
  ```
* **Sample Input:**
  ```bash
  dietcode brief "Make responsive for mobile" --mode agent
  ```
* **Expected Output:**
  Writes `MISSION_BRIEF.md` to the current folder and prints a preview panel containing target files, cascades, and rules.

---

### 🌳 6. Visual Codebase Tree
Displays the repository folder structure with integrated 1-sentence file summaries.

* **Command:**
  ```bash
  dietcode tree
  ```
* **Sample Input:** Run `dietcode tree` inside the repository.
* **Expected Output:**
  ```text
  📁 DietCode
  ├── 📁 components
  │   └── 📁 dashboard
  │       ├── 📄 Sidebar.tsx • Sidebar navigation bar and menus.
  │       └── 📄 Navbar.tsx • Navigation bar links.
  └── 📄 README.md • Project documentation manual.
  ```

---

### 🐚 7. Interactive REPL Shell
Open a persistent terminal takeover shell where you can run commands instantly.

* **Command:**
  ```bash
  dietcode shell
  ```
* **Expected Output:**
  ```text
  dietcode> index
  dietcode> search Parser
  dietcode> exit
  ```

---

### 💬 8. Codebase Q&A (RAG)
Ask codebase-aware questions using local semantic search and your local Ollama LLM.

* **Command:**
  ```bash
  dietcode ask "<QUESTION>"
  ```
* **Sample Input:**
  ```bash
  dietcode ask "How does the database initialize?"
  ```
* **Expected Output:**
  A Markdown-formatted panel answering your question by explaining the specific code:
  ```text
  ╭────────────────────── Local AI Assistant Response ───────────────────────╮
  │ The database is initialized by the `init_db` function inside `db.py` on   │
  │ line 12. It creates the SQLite database connection, sets up tables for    │
  │ `files`, `symbols`, and `imports`, and configures WAL journaling.        │
  ╰──────────────────────────────────────────────────────────────────────────╯
  ```

---



## 🗃️ Database Schema

DietCode maintains a local SQLite database cache (`dietcode.db`) containing:
* **files:** File paths and their cached 1-sentence purpose summaries.
* **symbols:** Functions, classes, locations, and raw source code.
* **imports:** Dependency relations (imported modules).
* **symbol_embeddings:** JSON-serialized vector embeddings for semantic matches.
* **project_meta:** Cached project overview descriptions.
