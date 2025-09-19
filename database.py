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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER,
                    username TEXT,
                    UNIQUE(post_id, username)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER,
                    username TEXT,
                    content TEXT,
                    created_at TEXT
                )
            """)
            # Insert default users if they don't exist
            conn.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'admin123')")
            conn.execute("INSERT OR IGNORE INTO users VALUES ('user', '123')")
            # Update existing admin password
            conn.execute("UPDATE users SET password = 'admin123' WHERE username = 'admin'")
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
            posts = [dict(row) for row in cursor.fetchall()]
            for post in posts:
                post['likes_count'] = self.get_likes_count(post['id'])
            return posts
    
    def get_post(self, post_id: int) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
            row = cursor.fetchone()
            if row:
                post = dict(row)
                post['likes_count'] = self.get_likes_count(post_id)
                post['comments'] = self.get_comments(post_id)
                return post
            return None
    
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
    
    def toggle_like(self, post_id: int, username: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            # Check if like exists
            cursor = conn.execute("SELECT id FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
            if cursor.fetchone():
                # Remove like
                conn.execute("DELETE FROM likes WHERE post_id = ? AND username = ?", (post_id, username))
                return False
            else:
                # Add like
                conn.execute("INSERT INTO likes (post_id, username) VALUES (?, ?)", (post_id, username))
                return True
    
    def get_likes_count(self, post_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post_id,))
            return cursor.fetchone()[0]
    
    def add_comment(self, post_id: int, username: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO comments (post_id, username, content, created_at) VALUES (?, ?, ?, ?)",
                (post_id, username, content, datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
    
    def get_comments(self, post_id: int) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY id DESC", (post_id,))
            return [dict(row) for row in cursor.fetchall()]

db = Database()