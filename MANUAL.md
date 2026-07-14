# DietCode User Manual 📖
### Technical Guide & Developer Workflows

Welcome to the DietCode User Manual. This guide explains how to integrate DietCode into your daily development cycle for codebase exploration, dependency auditing, and executing safe commits.

---

## 🗺️ Developer Onboarding Workflow (Day 1)

When you are assigned to a new or legacy repository, use the following sequence to map the codebase instantly:

### Step 1: Initialize and Scan
First, set up your local cache database and scan all project files:
```bash
dietcode init
dietcode index
```
*DietCode traverses all source directories, ignoring Git configurations, virtual environments, and caches, and parses classes and functions using Tree-sitter.*

### Step 2: Read the Codebase Map
Generate a structural bird's-eye view table of the project:
```bash
dietcode map
```
Use this onboarding map to:
*   Identify the entry point files (files with no direct dependents).
*   Understand the purpose of every file from its 1-sentence summary.
*   Trace direct downstream connections.

### Step 3: Run Concept Queries
If you need to find where a specific functionality is implemented, run a semantic search:
```bash
dietcode search "crawling and indexing files"
```
*Unlike standard grep, semantic search uses a local vector model to find matching code symbols even if they don't contain your exact search words.*

---

## 🚨 Downstream Impact Verification (Safe Commits)

Before making edits to a function or file, you must ensure that your changes do not break other parts of the system.

### Running Change Impact Analysis
To see what files import or rely on a file you are about to edit (e.g., `parser.py`), run:
```bash
dietcode impact parser.py
```
This renders a visual hierarchy tree:
```text
🚨 parser.py
└── indexer.py
    └── cli.py
```
*Interpretation:* Modifying `parser.py` means you must check for regressions in `indexer.py` (which imports it directly) and `cli.py` (which imports `indexer.py` downstream).

---

## 📝 AI-Assisted Feature Engineering (Mission Briefs)

When you are ready to write code (either yourself or via a coding AI), generate a **Mission Brief**.

### Workflow A: Web Chatbot (e.g. ChatGPT/Claude Web)
If you want to copy-paste your prompt into a browser-based AI:
```bash
dietcode brief "Add Rust support" --mode web
```
*   **How it works:** DietCode scans the codebase, resolves the files that must be modified (`parser.py` and `indexer.py`), traces downstream cascades, bundles the code contents of those files, and writes an optimized prompt to `MISSION_BRIEF.md`.
*   **Result:** The AI reads the code, outputs a visual change map, and gives you complete copy-pasteable function replacements.

### Workflow B: Autonomous CLI Agents (e.g. Claude Code)
If you are running an AI agent directly in your terminal:
```bash
dietcode brief "Add Rust support" --mode agent
```
*   **How it works:** DietCode excludes the actual file contents (saving massive tokens) and outputs commands directing the agent's file tools to read and edit the files directly.
*   **Result:** The agent executes the task autonomously in your terminal with minimal token usage.

---

## 🌳 Codebase Structure Exploration

To get a visual roadmap of a new codebase's folders and files, run:
```bash
dietcode tree
```
This prints a clean directory tree (hiding temporary folders like `.venv` or `.git`), and appends the 1-sentence purpose summary next to each file. You can see the entire layout and understand what each module does in a single glance!

---

## 🐚 REPL Shell Quick Tips


To work faster without typing the `dietcode` command prefix:
```bash
dietcode shell
```
Inside the shell:
*   Use `help` to list commands.
*   Run commands sequentially (e.g., `index` then `map` then `search database`).
*   Press `Ctrl-C` or type `exit` to quit.

---

## 🔧 Troubleshooting & FAQ

### Q: Why isn't my new function showing up in `search`?
Run `dietcode index` again. DietCode caches symbols in a local database (`dietcode.db`) and needs to re-index to capture changes.

### Q: Can I ignore specific folders?
Yes, DietCode automatically ignores common directories like `.git`, `node_modules`, `venv`, `.venv`, and `__pycache__` to keep the cache lightweight.

### Q: Where are my model weights stored?
They are cached locally inside the `./model` folder of the repository. This ensures DietCode runs 100% offline without downloading weights again.
