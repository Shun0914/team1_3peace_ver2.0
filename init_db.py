import sqlite3

def init_db(db_name="チャリンジャー.db"):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    # 外部キー制約有効化
    cur.execute("PRAGMA foreign_keys = ON;")

    # User（ユーザー）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS User (
        user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL,
        email         TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role          TEXT NOT NULL CHECK (role IN ('child','parent')),
        created_at    DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP)
    );
    """)

    # Quest（クエスト）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Quest (
        quest_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        title         TEXT NOT NULL,
        description   TEXT,
        reward_amount INTEGER NOT NULL DEFAULT 0,
        deadline      DATETIME,
        created_by    INTEGER NOT NULL,
        created_at    DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
        FOREIGN KEY (created_by) REFERENCES User(user_id) ON DELETE CASCADE
    );
    """)

    # QuestExecution（クエスト実行）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS QuestExecution (
        execution_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        quest_id      INTEGER NOT NULL,
        assigned_to   INTEGER NOT NULL,
        started_at    DATETIME,
        completed_at  DATETIME,
        status        TEXT NOT NULL DEFAULT '未受注'
                      CHECK (status IN ('未受注','進行中','承認待ち','完了')),
        memo          TEXT,
        photo_path    TEXT,
        FOREIGN KEY (quest_id) REFERENCES Quest(quest_id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_to) REFERENCES User(user_id) ON DELETE CASCADE
    );
    """)

    # Reward（報酬）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Reward (
        reward_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        quest_id    INTEGER NOT NULL UNIQUE,
        user_id     INTEGER NOT NULL,
        amount      INTEGER NOT NULL DEFAULT 0,
        paid_at     DATETIME,
        status      TEXT NOT NULL DEFAULT '未払い'
                    CHECK (status IN ('未払い','支払い済み')),
        FOREIGN KEY (quest_id) REFERENCES Quest(quest_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
    );
    """)

    # Achievement（実績）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Achievement (
        achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id        INTEGER NOT NULL,
        total_quests   INTEGER NOT NULL DEFAULT 0,
        total_rewards  INTEGER NOT NULL DEFAULT 0,
        level          INTEGER DEFAULT 1,
        created_at     DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
    );
    """)

    # ApprovalToken（承認トークン）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ApprovalToken (
        token_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        token         TEXT NOT NULL UNIQUE,
        execution_id  INTEGER NOT NULL,
        created_at    DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
        used_at       DATETIME,
        is_valid      BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (execution_id) REFERENCES QuestExecution(execution_id) ON DELETE CASCADE
    );
    """)

    # EmailLog（メールログ）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS EmailLog (
        log_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        execution_id  INTEGER NOT NULL,
        sent_to       TEXT NOT NULL,
        sent_at       DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
        status        TEXT NOT NULL,
        FOREIGN KEY (execution_id) REFERENCES QuestExecution(execution_id) ON DELETE CASCADE
    );
    """)
    

    # インデックス作成
    cur.execute("CREATE INDEX IF NOT EXISTS idx_quest_created_by ON Quest(created_by);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_execution_quest ON QuestExecution(quest_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_execution_assigned_to ON QuestExecution(assigned_to);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_reward_quest ON Reward(quest_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_reward_user ON Reward(user_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_achievement_user ON Achievement(user_id);")

    # init_db.pyに追加
    # 承認トークンテーブル用
    cur.execute("CREATE INDEX IF NOT EXISTS idx_approval_token ON ApprovalToken(token);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_approval_execution ON ApprovalToken(execution_id);")

    # メールログテーブル用（オプション）
    cur.execute("CREATE INDEX IF NOT EXISTS idx_email_execution ON EmailLog(execution_id);")

    conn.commit()
    conn.close()
    print(f"Database '{db_name}' initialized successfully with indexes!")

if __name__ == "__main__":
    init_db()
