import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "blog.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    author TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    image_path TEXT
                )
            """)
            # Add image_path column if it doesn't exist
            try:
                conn.execute("ALTER TABLE posts ADD COLUMN image_path TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL
                )
            """)
            # Insert default users if they don't exist
            conn.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'password')")
            conn.execute("INSERT OR IGNORE INTO users VALUES ('user', '123')")
            conn.commit()
    
    def create_post(self, title: str, content: str, author: str, image_path: str = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO posts (title, content, author, created_at, image_path) VALUES (?, ?, ?, ?, ?)",
                (title, content, author, datetime.now().strftime("%Y-%m-%d %H:%M"), image_path)
            )
            return cursor.lastrowid
    
    def get_all_posts(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM posts ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_post(self, post_id: int) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def verify_user(self, username: str, password: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT password FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return row and row[0] == password
    
    def delete_post(self, post_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            return cursor.rowcount > 0
    
    def get_all_users(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT username FROM users ORDER BY username")
            return [dict(row) for row in cursor.fetchall()]
    
    def create_user(self, username: str, password: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT INTO users VALUES (?, ?)", (username, password))
                return True
        except sqlite3.IntegrityError:
            return False
    
    def delete_user(self, username: str) -> bool:
        if username == 'admin':  # Protect admin account
            return False
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM users WHERE username = ?", (username,))
            return cursor.rowcount > 0

db = Database()