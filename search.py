import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from db import get_db
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn

def get_model():
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
    if os.path.exists(local_path):
        return SentenceTransformer(local_path)
    return SentenceTransformer("all-MiniLM-L6-v2")

def generate_embeddings():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS symbol_embeddings (
                symbol_id INTEGER PRIMARY KEY,
                embedding TEXT,
                FOREIGN KEY (symbol_id) REFERENCES symbols (id) ON DELETE CASCADE
            )
        """)
        conn.commit()

        cur.execute("""
            SELECT id, name, content 
            FROM symbols 
            WHERE id NOT IN (SELECT symbol_id FROM symbol_embeddings)
        """)
        symbols = cur.fetchall()

        if not symbols:
            return

        model = get_model()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            transient=True
        ) as progress:
            task = progress.add_task("[bold cyan]Generating semantic search index...", total=len(symbols))
            for sym in symbols:
                progress.update(task, description=f"[bold cyan]Encoding symbol: {sym['name']}")
                text = f"{sym['name']}\n{sym['content']}"
                embedding = model.encode(text)
                embedding_json = json.dumps(embedding.tolist())
                cur.execute("""
                    INSERT OR REPLACE INTO symbol_embeddings (symbol_id, embedding)
                    VALUES (?, ?)
                """, (sym["id"], embedding_json))
                progress.advance(task)
            
        conn.commit()
    finally:
        conn.close()

def semantic_search(query: str, top_n: int = 5):
    generate_embeddings()
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.name, s.type, s.start_line, s.end_line, s.content, f.filepath, se.embedding
        FROM symbols s
        JOIN files f ON s.file_id = f.id
        JOIN symbol_embeddings se ON s.id = se.symbol_id
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return []

    model = get_model()
    query_emb = model.encode(query)

    results = []
    for r in rows:
        emb = np.array(json.loads(r["embedding"]))
        similarity = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
        results.append((similarity, {
            "id": r["id"],
            "name": r["name"],
            "type": r["type"],
            "start_line": r["start_line"],
            "end_line": r["end_line"],
            "content": r["content"],
            "filepath": r["filepath"]
        }))

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_n]

def semantic_search_files(query: str, top_n: int = 3):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT filepath, summary FROM files")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return []

    model = get_model()
    query_emb = model.encode(query)

    results = []
    for r in rows:
        filepath = r["filepath"]
        summary = r["summary"] or ""
        text = f"{os.path.basename(filepath)}: {summary}"
        emb = model.encode(text)
        similarity = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
        results.append((similarity, filepath))

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_n]
