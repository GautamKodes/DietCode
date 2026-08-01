const commands = {
  index: `$ dietcode index . --deep-scan
⠹ Scanning workspace files...
⠹ Parsing Abstract Syntax Trees (AST)...
[1/4] Constructing Abstract Syntax Tree...
[2/4] Generating Local Vector Embeddings...
⠹ Generating file summaries...
⠹ Generating project overview...

               Indexing Summary             
  ╭───────────────────────────┬────────────╮
  │ Metric                    │      Count │
  ├───────────────────────────┼────────────┤
  │ Total Files Indexed       │          8 │
  ├───────────────────────────┼────────────┤
  │ Symbols Parsed            │         28 │
  ╰───────────────────────────┴────────────╯
✓ Codebase indexed successfully. Cached in local SQLite database (dietcode.db).`,

  tree: `$ dietcode tree
📁 DietCode
├── 📄 brief.py • Generates token-optimized AI prompts and mission briefs.
├── 📄 cli.py • Exposes the command-line interface commands.
├── 📄 db.py • Handles SQLite database caching and queries.
├── 📄 graph.py • Builds directed dependency graphs and impact cascades.
├── 📄 indexer.py • Crawls the workspace directory structure and indexes files.
├── 📄 parser.py • Parses abstract syntax trees (AST).
├── 📄 search.py • Generates local vector embeddings for semantic search.
└── 📄 setup.py • Configuration or utility file for setup.py.`,

  map: `$ dietcode map
Codebase File Map
└── 📄 ./db.py
    ├── Purpose: Handles SQLite database caching and queries.
    ├── Imports (Direct): None
    └── Direct Dependents: search.py, indexer.py, cli.py, brief.py, graph.py`,

  search: `$ dietcode search "identify auth bypass risk"
Found 3 Matches (Local):
1. src/auth/validator.rs:88 - Potential loose match in permission logic.
2. src/auth/session.rs:14 - Verify session validation signature checks.
3. src/api/middleware.rs:20 - Token verification filter logic.`,

  impact: `$ dietcode impact parser.py
🚨 parser.py
└── indexer.py
    └── cli.py`,

  ask: `$ dietcode ask "How is the database initialized?"
Retrieving relevant codebase context...
Consulting local AI assistant (Ollama)...

╭────────────────────── Local AI Assistant Response ───────────────────────╮
│ The database is initialized by the \`init_db\` function inside \`db.py\` on   │
│ line 12. It creates the SQLite database connection, sets up tables for    │
│ \`files\`, \`symbols\`, and \`imports\`, and configures WAL journaling.        │
╰──────────────────────────────────────────────────────────────────────────╯`,

  clone: `$ dietcode clone-check
Analyzing code similarity pairs...

                            Duplicate Logic Analysis                            
  ╭────────────┬────────────────┬────────────────┬───────────────┬───────────────╮
  │ Similarity │ Symbol A       │ Symbol B       │ Location A    │ Location B    │
  ├────────────┼────────────────┼────────────────┼───────────────┼───────────────┤
  │      82.2% │ get_impact_tr… │ get_impact_pa… │ ./graph.py:91 │ ./graph.py:1… │
  ╰────────────┴────────────────┴────────────────┴───────────────┴───────────────╯`
};

const defaultText = "Welcome to DietCode CLI v1.0. Type or select a command to begin exploring.";

document.addEventListener("DOMContentLoaded", () => {
  const terminalBody = document.getElementById("terminal-text-demo");
  const buttons = document.querySelectorAll(".demo-btn:not(.btn-reset)");
  const resetButton = document.getElementById("btn-demo-reset");

  function runCommand(cmdKey) {
    buttons.forEach(btn => btn.classList.remove("active"));
    const activeBtn = document.querySelector(`.demo-btn[data-cmd="${cmdKey}"]`);
    if (activeBtn) activeBtn.classList.add("active");

    terminalBody.textContent = "";
    const lines = commands[cmdKey].split("\n");
    let currentLine = 0;

    function printNextLine() {
      if (currentLine < lines.length) {
        terminalBody.textContent += lines[currentLine] + "\n";
        currentLine++;
        setTimeout(printNextLine, 50);
      }
    }
    printNextLine();
  }

  buttons.forEach(button => {
    button.addEventListener("click", () => {
      const cmdKey = button.getAttribute("data-cmd");
      runCommand(cmdKey);
    });
  });

  if (resetButton) {
    resetButton.addEventListener("click", () => {
      buttons.forEach(btn => btn.classList.remove("active"));
      terminalBody.textContent = defaultText;
    });
  }

  if (terminalBody) {
    terminalBody.textContent = defaultText;
  }
  
  simulateHeroTerminal();
});

function simulateHeroTerminal() {
  const heroText = document.getElementById("terminal-text");
  if (!heroText) return;

  const lines = [
    "$ dietcode index . --deep-scan",
    "[1/4] Constructing Abstract Syntax Tree...",
    "[2/4] Generating Local Vector Embeddings...",
    "✓ Indexing complete.",
    "",
    "$ dietcode search \"identify auth bypass risk\"",
    "Found 3 Matches (Local):",
    "1. src/auth/validator.rs:88 - Potential loose match in permission logic."
  ];

  let currentLine = 0;
  function printNext() {
    if (currentLine < lines.length) {
      heroText.textContent += lines[currentLine] + "\n";
      currentLine++;
      setTimeout(printNext, 120);
    }
  }
  printNext();
}

function copyToClipboard(elementId, btnId) {
  const text = document.getElementById(elementId).innerText;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById(btnId);
    const originalText = btn.innerText;
    btn.innerText = "Copied!";
    setTimeout(() => {
      btn.innerText = originalText;
    }, 2000);
  });
}
window.copyToClipboard = copyToClipboard;
