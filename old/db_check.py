#!/usr/bin/env python3
# db_check.py - DB内容確認用スクリプト

import sqlite3

def check_db_content():
    conn = sqlite3.connect('チャリンジャー.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=== DB内容確認 ===")
    
    # 1. Userテーブルの確認
    print("\n1. Userテーブル:")
    cur.execute("SELECT * FROM User")
    users = cur.fetchall()
    for user in users:
        print(f"  user_id: {user['user_id']}, name: {user['name']}, email: {user['email']}, role: {user['role']}")
    
    # 2. Questテーブルの確認
    print("\n2. Questテーブル:")
    cur.execute("SELECT quest_id, title, created_by, reward_amount FROM Quest")
    quests = cur.fetchall()
    for quest in quests:
        print(f"  quest_id: {quest['quest_id']}, title: {quest['title']}, created_by: {quest['created_by']} (type: {type(quest['created_by'])})")
    
    # 3. QuestExecutionテーブルの確認
    print("\n3. QuestExecutionテーブル:")
    cur.execute("SELECT execution_id, quest_id, assigned_to, status FROM QuestExecution")
    executions = cur.fetchall()
    for exec in executions:
        print(f"  execution_id: {exec['execution_id']}, quest_id: {exec['quest_id']}, assigned_to: {exec['assigned_to']}, status: {exec['status']}")
    
    # 4. JOIN動作テスト（EmailServiceで使用するクエリ）
    print("\n4. EmailService JOIN テスト:")
    test_execution_id = 1  # 存在しそうなexecution_id
    cur.execute("""
        SELECT q.title, q.description, q.reward_amount, u_child.name, u_parent.email
        FROM QuestExecution qe
        JOIN Quest q ON qe.quest_id = q.quest_id
        JOIN User u_child ON qe.assigned_to = u_child.user_id
        JOIN User u_parent ON q.created_by = u_parent.user_id
        WHERE qe.execution_id = ?
    """, (test_execution_id,))
    result = cur.fetchone()
    
    if result:
        print(f"  ✅ JOIN成功: title={result[0]}, parent_email={result[4]}")
    else:
        print(f"  ❌ JOIN失敗: execution_id={test_execution_id} でデータが見つからない")
        
        # 原因を調査
        print("  原因調査:")
        cur.execute("SELECT COUNT(*) FROM QuestExecution WHERE execution_id = ?", (test_execution_id,))
        count = cur.fetchone()[0]
        print(f"    QuestExecution existence: {count}")
        
        if count > 0:
            # created_byの型をチェック
            cur.execute("SELECT q.created_by, typeof(q.created_by) FROM Quest q JOIN QuestExecution qe ON q.quest_id = qe.quest_id WHERE qe.execution_id = ?", (test_execution_id,))
            created_by_info = cur.fetchone()
            if created_by_info:
                print(f"    created_by: {created_by_info[0]} (type: {created_by_info[1]})")
    
    # 5. ApprovalTokenとEmailLogテーブルの確認
    print("\n5. ApprovalTokenテーブル:")
    cur.execute("SELECT COUNT(*) FROM ApprovalToken")
    token_count = cur.fetchone()[0]
    print(f"  レコード数: {token_count}")
    
    print("\n6. EmailLogテーブル:")
    cur.execute("SELECT COUNT(*) FROM EmailLog")
    log_count = cur.fetchone()[0]
    print(f"  レコード数: {log_count}")
    
    if log_count > 0:
        cur.execute("SELECT * FROM EmailLog ORDER BY sent_at DESC LIMIT 3")
        logs = cur.fetchall()
        print("  最新のログ:")
        for log in logs:
            print(f"    {log['sent_at']}: {log['sent_to']} - {log['status']}")
    
    conn.close()

if __name__ == "__main__":
    check_db_content()