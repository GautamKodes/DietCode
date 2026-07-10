import sqlite3
DB_FILE = "codecake.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath TEXT UNIQUE,
    last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS symbols(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER,
                name TEXT,
                type TEXT,
                start_line INTEGER,
                end_line INTEGER,
                content TEXT,
                FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE)
                """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    imported_module TEXT,
    FOREIGN KEY (file_id) REFERENCES files (id) ON DELETE CASCADE)""")
    conn.commit()
    conn.close()
