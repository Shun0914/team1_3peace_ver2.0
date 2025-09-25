import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

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
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # インデックスの作成（検索高速化）
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);")

def get_user_by_username(username: str):
    """ユーザー名でユーザー情報を取得"""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (username,)
        )
        return cursor.fetchone()

def get_user_by_email(email: str):
    """メールアドレスでユーザー情報を取得"""
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT * FROM users WHERE email = ? AND is_active = 1",
            (email,)
        )
        return cursor.fetchone()

def create_user(username: str, email: str, password_hash: str):
    """新規ユーザーを作成"""
    with get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO users (username, email, password_hash) 
               VALUES (?, ?, ?)""",
            (username, email, password_hash)
        )
        return cursor.lastrowid

def update_last_login(user_id: int):
    """ユーザーの最終ログイン時刻を更新"""
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )