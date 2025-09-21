import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from email_service import EmailService
import os
from dotenv import load_dotenv

# 環境変数のロード
load_dotenv()

# ページ設定
st.set_page_config(page_title="チャジンジャー", page_icon=":guardsman:", layout="wide")

query_params = st.query_params
if 'approve_token' in query_params:
    token = query_params['approve_token']

    if 'use_db' in st.session_state and st.session_state.use_db:
        from email_service import EmailService
        import sqlite3

        conn = sqlite3.connect('チャリンジャー.db')
        cur = conn.cursor()

        cur.execute("""
                    SELECT execution_id, is_valid
                    FROM ApprovalToken
                    WHERE token = ? AND is_valid = TRUE
                    """, (token,))
        result = cur.fetchone()

        if result:
            execution_id = result[0]

            cur.execute("""
                        UPDATE QuestExecution
                        SET status = '完了', completed_at = CURRENT_TIMESTAMP
                        WHERE execution_id = ?
                        """, (execution_id,))
            
            cur.execute("""
                        UPDATE ApprovalToken
                        SET is_valid = FALSE, used_at = CURRENT_TIMESTAMP
                        WHERE token = ?
                        """, (token,))
            
            conn.commit()


            cur.execute("""
                        SELECT q.title FROM Quest q
                        JOIN QuestExecution qe ON q.quest_id = qe.quest_id
                        WHERE qe.execution_id = ?
                        """, (execution_id,))
            quest_title = cur.fetchone()[0]

            st.success(f"✅ クエスト『{quest_title}』を承認しました！")
            st.balloons()
        else:
            st.error("❌ 無効なトークンです。")
        conn.close()

    else:
        if 'approval_tokens' in st.session_state:
            if token in st.session_state.approval_tokens:
                quest_id = st.session_state.approval_tokens[token]

                # クエストのステータスを完了に変更
                for quest in st.session_state.quests:
                    if quest['id'] == quest_id:
                        quest['status'] = '完了'
                        del st.session_state.approval_tokens[token]
                        st.success(f"✅ 「{quest['title']}」を承認しました！")
                        st.balloons()
                        break
            else:
                st.error("❌ 無効なトークンです。")

    st.query_params.clear()

# CSS スタイル定義
st.markdown("""
<style>
    /* カンバンボードの列スタイル */
    .column {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        min-height: 400px;
        border: 1px solid #dee2e6;
    }
    /* 列ヘッダーのスタイル */
    .column-header {
        text-align: center;
        padding: 10px 0;
        font-size: 18px;
        font-weight: bold;
        background-color: #e9ecef;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    /* クエストカードのスタイル */
    .card {
        background-color: white;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        border: 1px solid #ddd;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# アプリタイトル
st.title("チャジンジャー")
st.write("チャットボットアプリケーションへようこそ！")

# セッション状態の初期化（ダミーデータ）
if 'quests' not in st.session_state:
    st.session_state.quests = [
        # 未受注クエスト
        {"id": 1, "title": "部屋の掃除機かけ", "description": "リビングと寝室に掃除機をかける", "status": "未受注", "reward": 500, "deadline": "2025-09-25", "created_by": "お母さん"},
        {"id": 2, "title": "お風呂掃除", "description": "浴槽とタイルを洗剤で掃除する", "status": "未受注", "reward": 800, "deadline": "2025-09-24", "created_by": "お父さん"},
        {"id": 3, "title": "玄関の靴を整理", "description": "靴箱に靴を綺麗に並べる", "status": "未受注", "reward": 200, "deadline": "2025-09-23", "created_by": "お母さん"},
        
        # 進行中クエスト
        {"id": 4, "title": "洗濯物たたみ", "description": "乾いた洗濯物をたたんでタンスにしまう", "status": "進行中", "reward": 300, "deadline": "2025-09-22", "created_by": "お母さん"},
        {"id": 5, "title": "食器洗い", "description": "昼食後の食器を洗って乾かす", "status": "進行中", "reward": 400, "deadline": "2025-09-22", "created_by": "お母さん"},
        
        # 承認待ちクエスト
        {"id": 6, "title": "ゴミ出し", "description": "燃えるゴミと資源ゴミを分別して出す", "status": "承認待ち", "reward": 300, "deadline": "2025-09-21", "created_by": "お父さん"},
        
        # 完了済みクエスト
        {"id": 7, "title": "庭の草むしり", "description": "花壇の雑草を抜く", "status": "完了", "reward": 600, "deadline": "2025-09-20", "created_by": "お父さん"},
        {"id": 8, "title": "窓拭き", "description": "リビングの窓ガラスを拭く", "status": "完了", "reward": 500, "deadline": "2025-09-19", "created_by": "お母さん"}
    ]

# ステータス一覧の初期化
if 'statuses' not in st.session_state:
    st.session_state.statuses = ["未受注", "進行中", "承認待ち", "完了"]

# クエスト発行モーダルの状態管理
if 'show_create_modal' not in st.session_state:
    st.session_state.show_create_modal = False

# 次のクエストIDを管理
if 'next_quest_id' not in st.session_state:
    st.session_state.next_quest_id = max([q['id'] for q in st.session_state.quests]) + 1

# 承認トークン管理用（既存のセッション初期化の後に追加）
if 'approval_tokens' not in st.session_state:
    st.session_state.approval_tokens = {}

# DB使用フラグ（将来的な切り替え用）
if 'use_db' not in st.session_state:
    st.session_state.use_db = False  # 現在はセッション版を使用
# =============================================================================
# クエスト発行ボタン（メイン画面に表示）
# =============================================================================

# ボタンレイアウト
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("クエスト発行する", key="create_quest_btn", type="primary", use_container_width=True):
        st.session_state.show_create_modal = True

# 区切り線
st.markdown("---")
# =============================================================================
# クエスト発行ポップアップ（モーダル）
# =============================================================================
# ポップアップを表示する条件をチェック
if st.session_state.show_create_modal:
    
    # タイトル表示
    with st.container():
        st.markdown("## 🎯 新規クエスト発行")
        st.markdown("---")
        
        # フォーム入力エリア（2列レイアウト）
        form_col1, form_col2 = st.columns([1, 1])
        
        # 左列：依頼側の情報
        with form_col1:
            st.markdown("#### 📝 クエスト情報")
            quest_title = st.text_input(
                "クエストタイトル", 
                placeholder="例: お風呂の掃除をしてください", 
                key="quest_title_input"
            )
            
            quest_description = st.text_area(
                "詳細説明", 
                placeholder="例: お風呂の掃除をしてください。\nシャンプーが少なくなっているので詰め替えもよろしくね。", 
                height=120, 
                key="quest_desc_input"
            )
            
            requester_name = st.text_input(
                "依頼者", 
                placeholder="例: お母さん", 
                key="quest_requester_input"
            )
            
            requester_email = st.text_input(
                "メールアドレス", 
                placeholder="example@email.com", 
                key="quest_email_input"
            )
        
        # 右列：期限・報酬情報
        with form_col2:
            st.markdown("#### ⏰ 期限・報酬")
            quest_date = st.date_input(
                "期限日", 
                value=date.today(), 
                key="quest_date_input"
            )
            
            quest_time = st.time_input(
                "期限時刻", 
                value=time(19, 0), 
                key="quest_time_input"
            )
            
            quest_reward = st.text_input(
                "報酬", 
                placeholder="例: クリームパン 1個", 
                key="quest_reward_input"
            )
        
        # ボタン配置エリア
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ボタンを中央に配置
        btn_col1, btn_col2= st.columns([1, 1])
        
        # クエスト依頼ボタン
        with btn_col1:
            if st.button("クエストを依頼する", key="submit_quest", type="primary", use_container_width=True):
                # 入力値の検証
                if quest_title and quest_description and requester_email and quest_reward:
                    # 新しいクエストを作成
                    new_quest = {
                        "id": st.session_state.next_quest_id,
                        "title": quest_title,
                        "description": quest_description,
                        "status": "未受注",  # 最初は「未受注」で登録します。
                        "reward": quest_reward,  # 文字列として保存
                        "deadline": f"{quest_date} {quest_time.strftime('%H:%M')}",
                        "created_by": requester_name,  # 依頼者名を保存
                        "email": requester_email       # メールアドレスを別項目で保存
                    }
                    
                    # クエストリストに追加
                    st.session_state.quests.append(new_quest)
                    st.session_state.next_quest_id += 1
                    
                    # モーダルを閉じる
                    st.session_state.show_create_modal = False
                    
                    # 成功メッセージを表示して画面をリロード
                    st.success("✅ クエストが正常に発行されました！")
                    st.rerun()
                else:
                    st.error("❌ すべての項目を入力してください")
        
        with btn_col2:
            # キャンセルボタン
            if st.button("❌ キャンセル", key="cancel_quest", use_container_width=True):
                st.session_state.show_create_modal = False
                st.rerun()
        
        st.markdown("---")
    
    # モーダルが表示されている時は、下のコンテンツの表示を抑制
    st.stop()
# =============================================================================
# メインコンテンツ：カンバンボード表示
# =============================================================================

# 4列のカラムレイアウト作成
cols = st.columns(len(st.session_state.statuses))

# 各ステータス列の処理
for i, status in enumerate(st.session_state.statuses):
    with cols[i]:
        # 列ヘッダー表示
        st.markdown(f'<div class="column-header">{status}</div>', unsafe_allow_html=True)
        
        # 現在の列に該当するクエストをフィルタリング
        quests = [quest for quest in st.session_state.quests if quest["status"] == status]

        # 各クエストをカード形式で表示
        for quest in quests:
            # 報酬の表示形式を調整（数値の場合はポイント、文字列の場合はそのまま表示）
            reward_display = f"{quest['reward']}ポイント" if isinstance(quest['reward'], int) else quest['reward']
            
            # HTMLカード + JavaScriptクリック処理
            st.markdown(f'''
            <div class="card" onclick="document.getElementById('btn_{quest["id"]}').click()">
                <h4>{quest["title"]}</h4>
                <p>報酬: {reward_display}</p>
            </div>
            ''', unsafe_allow_html=True)
            
            # 隠しボタン（カードクリック時にトリガーされる）
            if st.button("", key=f"btn_{quest['id']}", help="詳細表示"):
                st.session_state.selected_quest = quest['id']

# =============================================================================
# 詳細モーダル表示
# =============================================================================

# クエストが選択されている場合の詳細表示
if 'selected_quest' in st.session_state:
    # 選択されたクエストの詳細情報を取得
    selected = next((q for q in st.session_state.quests if q['id'] == st.session_state.selected_quest), None)
    
    if selected:
        # 報酬の表示形式を調整
        reward_display = f"{selected['reward']}ポイント" if isinstance(selected['reward'], int) else selected['reward']
        
        # モーダル風の詳細表示（固定位置）
        st.markdown(f"""
        <div style="position: fixed; top: 20%; left: 30%; width: 40%; background-color: white; border: 2px solid #000; border-radius: 10px; padding: 20px; z-index: 1000;">
            <h3>{selected['title']}</h3>
            <p><strong>説明:</strong> {selected['description']}</p>
            <p><strong>報酬:</strong> {reward_display}</p>
            <p><strong>期限:</strong> {selected['deadline']}</p>
            <p><strong>作成者:</strong> {selected['created_by']}</p>
        </div>
        """, unsafe_allow_html=True)

        # ステータス変更 UI
        new_status = st.selectbox(
            "ステータスを変更",
            options=st.session_state.statuses,
            index=st.session_state.statuses.index(selected['status']),
            key="status_select"
        )

        if st.button("更新", key="update_status"):
            # 変更前のステータスを保存
            old_status = selected['status']

            # ステータスを更新
            for q in st.session_state.quests:
                if q['id'] == selected['id']:
                    q['status'] = new_status
                    # ===== メール送信処理を追加 =====
                    # 「進行中」→「承認待ち」の場合にメール送信
                    if old_status == "進行中" and new_status == "承認待ち":
                        try:
                            if 'use_db' in st.session_state and st.session_state.use_db:
                                from email_service import EmailService
                                email_service = EmailService()
                                # 実際のexecution_idとparent_emailが必要
                                # （DB連携後に実装）
                                # email_service.send_approval_email(execution_id, parent_email)
                                st.info("📧 承認依頼メールを送信しました（DB版）")
                            else:
                                import smtplib
                                from email.mime.text import MIMEText
                                from email.mime.multipart import MIMEMultipart
                                import secrets
                                import os
                                from dotenv import load_dotenv
                                
                                load_dotenv()
                                
                                # 承認トークンを生成
                                if 'approval_tokens' not in st.session_state:
                                    st.session_state.approval_tokens = {}
                                
                                token = secrets.token_urlsafe(32)
                                st.session_state.approval_tokens[token] = q['id']
                                
                                # メール設定
                                sender_email = os.getenv('GMAIL_ADDRESS')
                                sender_password = os.getenv('GMAIL_APP_PASSWORD')
                                app_url = os.getenv('APP_URL', 'http://localhost:8501')
                                
                                # 親のメールアドレス（created_byのemailを使用）
                                parent_email = q.get('email', sender_email)  # デフォルトは送信者と同じ
                                
                                # メール作成
                                message = MIMEMultipart("alternative")
                                message["Subject"] = f"【承認依頼】{q['title']}が完了報告されました"
                                message["From"] = sender_email
                                message["To"] = parent_email
                                
                                # 承認URL
                                approval_url = f"{app_url}/?approve_token={token}"
                                
                                # 報酬の表示調整
                                reward_display = f"{q['reward']}ポイント" if isinstance(q['reward'], int) else q['reward']
                                
                                # HTML本文
                                html = f"""
                                <html>
                                <body>
                                    <h2>クエスト完了の承認依頼</h2>
                                    <p>以下のクエストが完了報告されました：</p>
                                    
                                    <div style="border: 1px solid #ddd; padding: 15px; margin: 20px 0; background-color: #f9f9f9;">
                                        <h3 style="color: #333;">{q['title']}</h3>
                                        <p><strong>詳細:</strong> {q['description']}</p>
                                        <p><strong>報酬:</strong> {reward_display}</p>
                                        <p><strong>期限:</strong> {q['deadline']}</p>
                                        <p><strong>依頼者:</strong> {q['created_by']}</p>
                                    </div>
                                    
                                    <p>内容を確認して問題なければ、以下のボタンをクリックして承認してください：</p>
                                    
                                    <div style="text-align: center; margin: 30px 0;">
                                        <a href="{approval_url}" style="display: inline-block; padding: 15px 40px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold;">
                                            ✅ クエストを承認する
                                        </a>
                                    </div>
                                    
                                    <p style="color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                                        このリンクは一度だけ有効です。間違えて承認した場合は、アプリから修正してください。<br>
                                        <a href="{app_url}" style="color: #007bff;">アプリを開く</a>
                                    </p>
                                </body>
                                </html>
                                """
                                
                                part = MIMEText(html, "html")
                                message.attach(part)
                                
                                # メール送信
                                try:
                                    with smtplib.SMTP("smtp.gmail.com", 587) as server:
                                        server.starttls()
                                        server.login(sender_email, sender_password)
                                        server.send_message(message)
                                    st.success(f"📧 承認依頼メールを {parent_email} に送信しました！")
                                except Exception as e:
                                    st.error(f"❌ メール送信エラー: {str(e)}")
                                    st.info("メール設定を確認してください：")
                        except Exception as e:
                            st.error(f"❌ エラーが発生しました: {str(e)}")
                        break
    
            del st.session_state.selected_quest
            st.rerun()
            
        # モーダルを閉じるボタン
        if st.button("閉じる", key="close_modal"):
            del st.session_state.selected_quest
            st.rerun()

# =============================================================================
# TODO: 他メンバーが追加する機能
# =============================================================================
# - しゅんすけ: Gmail API連携（完了通知機能）
# - けんた：DB連携（SQLite）
# - りす：ログイン/ログアウト機能