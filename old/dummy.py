# init_dummy_quests.py
from db import get_conn

def insert_dummy_quests():
    # ダミークエストデータ
    dummy_quests = [
        # 未受注
        {"id": 1, "title": "部屋の掃除機かけ", "description": "リビングと寝室に掃除機をかける", "status": "未受注", "reward": 500, "deadline": "2025-09-25", "created_by": 1},
        {"id": 2, "title": "お風呂掃除", "description": "浴槽とタイルを洗剤で掃除する", "status": "未受注", "reward": 800, "deadline": "2025-09-24", "created_by": 1},
        {"id": 3, "title": "玄関の靴を整理", "description": "靴箱に靴を綺麗に並べる", "status": "未受注", "reward": 200, "deadline": "2025-09-23", "created_by": 1},
        # 進行中
        {"id": 4, "title": "洗濯物たたみ", "description": "乾いた洗濯物をたたんでタンスにしまう", "status": "進行中", "reward": 300, "deadline": "2025-09-22", "created_by": 1},
        {"id": 5, "title": "食器洗い", "description": "昼食後の食器を洗って乾かす", "status": "進行中", "reward": 400, "deadline": "2025-09-22", "created_by": 1},
        # 承認待ち
        {"id": 6, "title": "ゴミ出し", "description": "燃えるゴミと資源ゴミを分別して出す", "status": "承認待ち", "reward": 300, "deadline": "2025-09-21", "created_by": 1},
        # 完了済み
        {"id": 7, "title": "庭の草むしり", "description": "花壇の雑草を抜く", "status": "完了", "reward": 600, "deadline": "2025-09-20", "created_by": 1},
        {"id": 8, "title": "窓拭き", "description": "リビングの窓ガラスを拭く", "status": "完了", "reward": 500, "deadline": "2025-09-19", "created_by": 1}
    ]

    with get_conn() as conn:
        cur = conn.cursor()

        # 先にダミーのユーザーを作成（外部キー制約対応）
        cur.execute("""
        INSERT OR IGNORE INTO User (user_id, name, email, password_hash, role)
        VALUES (?, ?, ?, ?, ?)
        """, (1, "お母さん", "shunsuke.shimojo914@gmail.com", "dummyhash", "parent"))

        # ダミークエストを挿入
        for q in dummy_quests:
            cur.execute("""
            INSERT OR IGNORE INTO Quest (quest_id, title, description, reward_amount, deadline, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (q["id"], q["title"], q["description"], q["reward"], q["deadline"], q["created_by"]))

        # QuestExecution にデータ登録
        for q in dummy_quests:
            # assigned_to はとりあえず作成者1固定
            cur.execute("""
                INSERT OR IGNORE INTO QuestExecution (quest_id, assigned_to, status)
                VALUES (?, ?, ?)
            """, (q["id"], 1, q["status"]))
    print("✅ ダミークエストをDBに挿入しました！")

if __name__ == "__main__":
    insert_dummy_quests()
