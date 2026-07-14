# DietCode 🥤
### Source code cartographer for navigation and safe commits.

DietCode is an offline-ready, privacy-first terminal utility that indexes codebase structures, maps dependencies, performs conceptual semantic searches, and generates token-optimized mission briefs. It runs 100% on-device, safeguarding your IP while keeping your workflow incredibly fast.

---

## 🚀 Key Features

* **Abstract Syntax Tree (AST) Parsing:** Uses Tree-sitter to parse code structures (classes and functions) rather than relying on brittle text matching.
* **On-Device Semantic Search:** Converts code symbols and summaries into vector embeddings using a local Sentence-Transformers model (`all-MiniLM-L6-v2`) for conceptual code searches.
* **Dependency & Impact Cartography:** Builds directed import graphs and traces cascading downstream impact paths (using `rich.tree` visualization).
* **Onboarding & Codebase Maps:** Generates a project-level dashboard summarizing every file, its direct imports, and downstream dependents.
* **Dual-Mode AI Mission Briefs:** Generates prompts in two customized modes:
  * **Web Mode:** Designed for web-based chatbots (e.g. ChatGPT / Claude Web). Includes code blocks and requests human-readable complete functions.
  * **Agent Mode:** Designed for CLI coding agents (e.g. Claude Code / Antigravity). Saves 95%+ of prompt tokens by omitting code contents and giving direct tool commands.
* **Interactive REPL Shell:** Take over your terminal in a persistent session where you can run commands directly without prefixes.

---

## 🛠️ Installation & Setup

To install DietCode globally without needing to manage virtual environments or package conflicts:

```bash
# Clone the repository
git clone https://github.com/GautamKodes/DietCode.git
cd DietCode

# Run the installer
./install.sh
```

This installer will automatically:
1. Set up an isolated Python environment in `~/.dietcode/venv`.
2. Install the CPU-optimized PyTorch runtime (reducing size to ~350MB).
3. Register the global `dietcode` command wrapper in `~/.local/bin/dietcode`.

Make sure `~/.local/bin` is in your shell's `PATH` (e.g. check your `~/.bashrc` or `~/.zshrc`).

---


## 💻 CLI Command Suite

### 📦 1. Index Codebase
Scans the current directory, parses symbols/imports, and generates smart heuristic file summaries:
```bash
dietcode index
```

### 🔍 2. Semantic Search
Perform conceptual queries across your codebase (runs entirely offline):
```bash
dietcode search "verify user session tokens"
```

### 🚨 3. Change Impact Cascades
Trace exactly which downstream files will be affected if you edit a given file:
```bash
dietcode impact parser.py
```

### 🗺️ 4. Onboarding Map
Get a colorized matrix showing every file's purpose, what it imports, and who imports it:
```bash
dietcode map
```

### 📝 5. Generate Mission Briefs
Generate a token-optimized prompt instructing a coding AI how to execute a task:
```bash
# Web Mode (Default - for copy-pasting to ChatGPT/Claude web interfaces)
dietcode brief "Add Rust support" -m web

# Agent Mode (Token-saving - for terminal agents like Claude Code)
dietcode brief "Add Rust support" -m agent
```

### 🐚 6. Interactive REPL Shell
Open a persistent terminal takeover shell where you can run commands instantly:
```bash
dietcode shell
```
*Example shell session:*
```text
dietcode> map
dietcode> search Parser
dietcode> exit
```

---

## 🗃️ Database Schema

DietCode maintains a local SQLite database cache (`dietcode.db`) containing:
* **files:** File paths and their cached 1-sentence purpose summaries.
* **symbols:** Functions, classes, locations, and raw source code.
* **imports:** Dependency relations (imported modules).
* **symbol_embeddings:** JSON-serialized vector embeddings for semantic matches.
* **project_meta:** Cached project overview descriptions.
