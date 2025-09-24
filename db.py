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