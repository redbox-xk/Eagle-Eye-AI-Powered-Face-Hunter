import sqlite3
from pathlib import Path

DB_PATH = Path("data/database.db")

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_name TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        face_id TEXT,
        identity TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_observation(camera_name, face_id, identity):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO observations (camera_name, face_id, identity) VALUES (?, ?, ?)",
        (camera_name, face_id, identity)
    )
    conn.commit()
    conn.close()

def fetch_observations(limit=100):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM observations ORDER BY timestamp DESC LIMIT ?", (limit,))
    results = c.fetchall()
    conn.close()
    return results
