import os
import json
import urllib.request
import urllib.error
from db import get_db, init_db
from parser import parse_file

IGNORE_DIRS = {".git", "node_modules", "venv", "__pycache__", ".venv", "model"}

def query_ollama(prompt: str):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "qwen2.5-coder:1.5b",
        "prompt": prompt,
        "stream": False
    }
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode("utf-8"), 
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data.get("response", "").strip()
    except Exception:
        return None

def generate_file_summary(filepath: str, symbols: list):
    filename = os.path.basename(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception:
        code = ""

    summary = query_ollama(f"Summarize what this file '{filename}' does in one short sentence under 15 words.")
    if summary:
        return summary

    parts = []
    if "tree_sitter" in code:
        parts.append("Parses abstract syntax trees (AST)")
    if "sqlite3" in code:
        parts.append("Handles SQLite database caching and queries")
    if "networkx" in code:
        parts.append("Builds directed dependency graphs and impact cascades")
    if "sentence_transformers" in code:
        parts.append("Generates local vector embeddings for semantic search")
    if "typer" in code:
        parts.append("Exposes the command-line interface commands")
    if "os.walk" in code or "index_project" in code:
        parts.append("Crawls the workspace directory structure and indexes files")
    if "build_mission_brief" in code or "query_ollama" in code:
        parts.append("Generates token-optimized AI prompts and mission briefs")

    if parts:
        return " and ".join(parts) + "."

    if symbols:
        sym_list = ", ".join([s["name"] for s in symbols])
        return f"Defines helper functions: {sym_list}."

    return f"Configuration or utility file for {filename}."

def generate_project_summary(files_data: list):
    if not files_data:
        return "Empty codebase."

    context_lines = [f"- {f}: {s}" for f, s in files_data]
    context_text = "\n".join(context_lines)
    prompt = f"Summarize this software project in 2 short sentences based on its file directory mapping:\n{context_text}\nKeep it under 30 words."
    
    summary = query_ollama(prompt)
    if summary:
        return summary

    file_names = ", ".join([os.path.basename(f) for f, _ in files_data])
    return f"On-device source code repository composed of {file_names}."

def index_project(root_dir: str):
    init_db()
    conn = get_db()
    cur = conn.cursor()

    indexed_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for filename in filenames:
            if filename.endswith((".py", ".rs")):
                filepath = os.path.join(dirpath, filename)
                try:
                    cur.execute(
                        "INSERT OR IGNORE INTO files (filepath) VALUES (?)",
                        (filepath,)
                    )

                    cur.execute(
                        "SELECT id FROM files WHERE filepath = ?",
                        (filepath,)
                    )
                    file_id = cur.fetchone()["id"]
                    cur.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
                    cur.execute("DELETE FROM imports WHERE file_id = ?", (file_id,))

                    symbols, imports = parse_file(filepath)

                    for sym in symbols:
                        cur.execute("""
                            INSERT INTO symbols (file_id, name, type, start_line, end_line, content) 
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            file_id,
                            sym["name"],
                            sym["type"],
                            sym["start_line"],
                            sym["end_line"],
                            sym["content"]
                        ))

                    for imp in imports:
                        cur.execute("""
                            INSERT INTO imports (file_id, imported_module) 
                            VALUES (?, ?)
                        """, (
                            file_id,
                            imp
                        ))

                    file_summary = generate_file_summary(filepath, symbols)
                    cur.execute(
                        "UPDATE files SET summary = ?, last_indexed = CURRENT_TIMESTAMP WHERE id = ?",
                        (file_summary, file_id)
                    )
                    indexed_files.append((filepath, file_summary))
                except Exception as e:
                    print(f"⚠️ Warning: Failed to index {filepath}: {e}")

    project_summary = generate_project_summary(indexed_files)
    cur.execute(
        "INSERT OR REPLACE INTO project_meta (key, value) VALUES ('summary', ?)",
        (project_summary,)
    )

    conn.commit()
    conn.close()