import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime

# DBパスの設定（環境変数 or デフォルト）
DB_PATH = Path(os.getenv("DATABASE_PATH", Path(__file__).parent / "チャリンジャー.db"))

def _ensure_dir():
    """DBディレクトリが存在しない場合は作成"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

@contextmanager #SQLite接続用コンテキストマネージャ
def get_conn(timeout: int = 30):
    _ensure_dir()
    conn = sqlite3.connect(
        str(DB_PATH),
        timeout=timeout,
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    conn.row_factory = sqlite3.Row # dict形式アクセス可能
    try: # パフォーマンス設定
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 30000;") # 30秒
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """データベースの初期化とテーブル作成（ユーザーテーブルのみ）"""
    with get_conn() as conn:
        # ユーザーテーブルの作成
        conn.execute("""
            CREATE TABLE IF NOT EXISTS User (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # インデックスの作成（検索高速化）
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON User (email);")

def get_user_by_username(username: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM User WHERE username = ?", (username,))
        return cur.fetchone()

def get_user_by_email(email: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM User WHERE email = ?", (email,))
        return cur.fetchone()

def create_user(username: str, email: str, password_hash: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO User (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        return cur.lastrowid

def update_last_login(user_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE User SET last_login = ? WHERE user_id = ?",
            (datetime.now(), user_id)
        )

