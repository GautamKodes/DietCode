import os
from db import get_db
from parser import parse_file

IGNORE_DIRS = {".git", "node_modules", "venv", "__pycache__", ".venv"}

def index_project(root_dir: str):
    conn = get_db()
    cur = conn.cursor()

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for filename in filenames:
            if filename.endswith(".py"):
                filepath = os.path.join(dirpath, filename)
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

    conn.commit()
    conn.close()