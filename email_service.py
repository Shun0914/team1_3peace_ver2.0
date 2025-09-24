import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime

load_dotenv()

class EmailService:
    def __init__(self, db_name='チャリンジャー.db'):
        self.db_name = db_name
        self.sender_email = os.getenv('GMAIL_ADDRESS')
        self.sender_password = os.getenv('GMAIL_APP_PASSWORD')
        self.app_url = os.getenv('APP_URL')
        
        # デバッグ情報を出力
        print(f"[DEBUG] EmailService初期化:")
        print(f"  DB名: {self.db_name}")
        print(f"  送信者Email: {self.sender_email}")
        print(f"  パスワード設定: {'あり' if self.sender_password else 'なし'}")
        print(f"  APP_URL: {self.app_url}")
    
    def generate_approval_token(self, execution_id):
        """承認トークンを生成してDBに保存"""
        token = secrets.token_urlsafe(32)
        print(f"[DEBUG] トークン生成: {token[:10]}... (execution_id: {execution_id})")

        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO ApprovalToken (execution_id, token, created_at, is_valid)
                VALUES (?, ?, ?, 1)
                """, (execution_id, token, datetime.now()))
            conn.commit()
            print(f"[DEBUG] トークンDB保存成功")
        except Exception as e:
            print(f"[DEBUG] トークンDB保存エラー: {e}")
            conn.rollback()
        finally:
            conn.close()
        return token
    
    def send_approval_email(self, execution_id):
        """承認依頼メールを送信"""
        print(f"[DEBUG] メール送信開始 (execution_id: {execution_id})")
        
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # SQLクエリ実行前にデバッグ
        print(f"[DEBUG] SQLクエリ実行...")
        
        cur.execute("""
            SELECT q.title, q.description, q.reward_amount, u_child.name, u_parent.email
            FROM QuestExecution qe
            JOIN Quest q ON qe.quest_id = q.quest_id
            JOIN User u_child ON qe.assigned_to = u_child.user_id
            JOIN User u_parent ON q.created_by = u_parent.user_id
            WHERE qe.execution_id = ?
        """, (execution_id,))
        quest_data = cur.fetchone()
        
        print(f"[DEBUG] SQLクエリ結果: {quest_data is not None}")
        
        if quest_data:
            print(f"[DEBUG] クエストデータ:")
            print(f"  title: {quest_data[0]}")
            print(f"  child_name: {quest_data[3]}")
            print(f"  parent_email: {quest_data[4]}")
        else:
            # エラー原因を調査
            print(f"[DEBUG] クエストデータが見つからない。原因調査:")
            
            # QuestExecutionの存在確認
            cur.execute("SELECT quest_id, assigned_to FROM QuestExecution WHERE execution_id = ?", (execution_id,))
            qe_result = cur.fetchone()
            if qe_result:
                print(f"  QuestExecution: quest_id={qe_result[0]}, assigned_to={qe_result[1]}")
                
                # Questの存在確認
                cur.execute("SELECT created_by, typeof(created_by) FROM Quest WHERE quest_id = ?", (qe_result[0],))
                q_result = cur.fetchone()
                if q_result:
                    print(f"  Quest: created_by={q_result[0]} (type: {q_result[1]})")
                    
                    # Userの存在確認
                    cur.execute("SELECT user_id, name, email FROM User WHERE user_id = ?", (qe_result[1],))
                    child_result = cur.fetchone()
                    print(f"  Child User: {child_result}")
                    
                    cur.execute("SELECT user_id, name, email FROM User WHERE user_id = ?", (q_result[0],))
                    parent_result = cur.fetchone()
                    print(f"  Parent User: {parent_result}")
                else:
                    print(f"  Quest not found for quest_id={qe_result[0]}")
            else:
                print(f"  QuestExecution not found for execution_id={execution_id}")
        
        conn.close()

        if not quest_data:
            print(f"[DEBUG] メール送信中止: クエストデータなし")
            return False

        title, description, reward, child_name, parent_email = quest_data

        try:
            token = self.generate_approval_token(execution_id)
            
            print(f"[DEBUG] メール作成中...")
            message = MIMEMultipart('alternative')
            message['Subject'] = f"【承認依頼】{title}が完了報告されました"
            message['From'] = self.sender_email
            message['To'] = parent_email

            approval_url = f"{self.app_url}/?approve_token={token}"
            print(f"[DEBUG] 承認URL: {approval_url}")

            # HTML本文
            html = f"""
            <html>
              <body>
                <h2>クエスト完了の承認依頼</h2>
                <p>{child_name}さんが以下のクエストを完了したと報告しています：</p>
                
                <div style="border: 1px solid #ddd; padding: 15px; margin: 20px 0;">
                    <h3>{title}</h3>
                    <p><strong>詳細:</strong> {description}</p>
                    <p><strong>報酬:</strong> {reward}ポイント</p>
                </div>
                
                <p>内容を確認して問題なければ、以下のボタンをクリックして承認してください：</p>
                
                <a href="{approval_url}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">
                    ✅ 承認する
                </a>
                
                <p style="color: #666; font-size: 12px; margin-top: 20px;">
                    このリンクは一度だけ有効です。
                </p>
              </body>
            </html>
            """

            part = MIMEText(html, 'html')
            message.attach(part)
            
            print(f"[DEBUG] SMTP接続開始...")
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                print(f"[DEBUG] SMTP認証...")
                server.login(self.sender_email, self.sender_password)
                print(f"[DEBUG] メール送信実行...")
                server.send_message(message)
                print(f"[DEBUG] メール送信成功！")

            self._log_email_sent(execution_id, parent_email, "success")
            return True
        
        except Exception as e:
            error_msg = f"error: {str(e)}"
            print(f"[DEBUG] メール送信エラー: {error_msg}")
            self._log_email_sent(execution_id, parent_email, error_msg)
            return False
        
    def _log_email_sent(self, execution_id, sent_to, status):
        """メール送信ログをDBに保存"""
        print(f"[DEBUG] メールログ保存: {status}")
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO EmailLog (execution_id, sent_to, status)
                VALUES (?, ?, ?)
                """, (execution_id, sent_to, status))
            conn.commit()
            print(f"[DEBUG] メールログ保存成功")
        except Exception as e:
            print(f"[DEBUG] メールログ保存エラー: {e}")
        finally:
            conn.close()