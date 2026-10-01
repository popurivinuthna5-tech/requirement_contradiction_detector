import sqlite3
import json
from contextlib import contextmanager
from typing import Generator
from app.config import DATABASE_PATH

def init_db():
    """Initialize database tables and indices."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT,
                display_name TEXT,
                provider TEXT DEFAULT 'google',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                document_type TEXT NOT NULL,
                file_path TEXT,
                file_size INTEGER DEFAULT 0,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'uploaded',
                requirement_count INTEGER DEFAULT 0,
                error_message TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # 3. Requirements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requirements (
                requirement_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                reference_code TEXT NOT NULL,
                requirement_text TEXT NOT NULL,
                requirement_type TEXT DEFAULT 'Functional',
                section TEXT,
                page_number INTEGER,
                priority TEXT DEFAULT 'Unspecified',
                metadata_json TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # 4. Conflicts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflicts (
                conflict_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                requirement_1_id TEXT NOT NULL,
                requirement_2_id TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                similarity_score REAL DEFAULT 0.0,
                explanation TEXT NOT NULL,
                conflicting_elements TEXT,
                suggested_clarification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (requirement_1_id) REFERENCES requirements(requirement_id) ON DELETE CASCADE,
                FOREIGN KEY (requirement_2_id) REFERENCES requirements(requirement_id) ON DELETE CASCADE
            )
        """)
        
        # Performance Indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_user ON documents(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reqs_user ON requirements(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reqs_doc ON requirements(document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_user ON conflicts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_req1 ON conflicts(requirement_1_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicts_req2 ON conflicts(requirement_2_id)")
        
        conn.commit()

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional database connection."""
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
    finally:
        conn.close()
