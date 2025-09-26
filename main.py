import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from db import get_conn
from email_service import EmailService
import base64
import os
from dotenv import load_dotenv
from auth import show_login_form, is_logged_in, logout_user
from db import init_database
import time as time_module

# 環境変数のロード
load_dotenv()

# ページ設定
st.set_page_config(page_title="チャリンジャー", page_icon=":guardsman:", layout="wide")

# CSSファイル読み込み
def load_custom_styles():
    st.markdown("""
    <style>
    /* 全体のフォント設定 */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }

    /* 通常のボタンスタイル */
    .stButton > button {
        background-color: #47D7E8 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        background-color: #3bc5d8 !important;
        box-shadow: 0 4px 8px rgba(71, 215, 232, 0.3) !important;
    }

    /* プライマリボタン（決定ボタン）スタイル */
    .stButton > button[kind="primary"] {
        background-color: #F85CE0 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #e64bd1 !important;
        box-shadow: 0 4px 8px rgba(248, 92, 224, 0.3) !important;
    }

    /* フォームボタンのスタイル */
    .stFormSubmitButton > button {
        background-color: #F85CE0 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        width: 100% !important;
    }

    .stFormSubmitButton > button:hover {
        background-color: #e64bd1 !important;
        box-shadow: 0 4px 8px rgba(248, 92, 224, 0.3) !important;
    }

    /* タブスタイル */
    .stTabs [data-baseweb="tab-list"] button {
        background-color: #47D7E8 !important;
        color: white !important;
        border-radius: 8px 8px 0 0 !important;
        border: none !important;
        margin-right: 2px !important;
        font-weight: bold !important;
    }

    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: #3bc5d8 !important;
    }

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #F85CE0 !important;
        color: white !important;
    }

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
        background-color: white !important;
        border: 2px solid #47D7E8 !important;
        color: #488af8 !important;
        border-radius: 8px;
        margin-bottom: 15px;
    }

    /* クエストカードのスタイル */
    .card {
        background-color: white;
        border: 1px solid #47D7E8 !important;
        color: #488af8 !important;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* テキスト入力フィールドのスタイル */
    .stTextInput > div > div > input {
        border: 2px solid #47D7E8 !important;
        border-radius: 8px !important;
    }

    .stTextArea > div > div > textarea {
        border: 2px solid #47D7E8 !important;
        border-radius: 8px !important;
    }

    /* セレクトボックスのスタイル */
    .stSelectbox > div > div {
        border: 2px solid #47D7E8 !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)
load_custom_styles()

def add_background_image():
    if os.path.exists("bg.png"):
        with open("bg.png", "rb") as image_file:
            encoded_bg = base64.b64encode(image_file.read()).decode()
        
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_bg}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """, unsafe_allow_html=True)

# この関数を load_custom_styles() の直後に呼び出してください
add_background_image()

# =============================================================================
# 承認トークン処理（ログイン前に実行）
# =============================================================================
query_params = st.query_params
token = None

if 'approve_token' in query_params:
    token = query_params['approve_token'][0] if isinstance(query_params['approve_token'], list) else query_params['approve_token']

if token:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT execution_id, is_valid
            FROM ApprovalToken
            WHERE token = ? AND is_valid = TRUE
        """, (token,))
        result = cur.fetchone()

        if result:
            execution_id = result["execution_id"]

            # クエスト情報を取得
            cur.execute("""
                SELECT q.title, u.username as child_name
                FROM Quest q
                JOIN QuestExecution qe ON q.quest_id = qe.quest_id
                JOIN User u ON qe.assigned_to = u.user_id
                WHERE qe.execution_id = ?
            """, (execution_id,))
            quest_info = cur.fetchone()

            # ステータス更新
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

            # 承認完了メッセージ（ログイン不要）
            st.markdown(f"""
                <div style="text-align: center; padding: 50px;">
                    <h1>✅ 承認完了</h1>
                    <p style="font-size: 20px;">
                        {quest_info['child_name']}さんのクエスト<br>
                        「{quest_info['title']}」<br>
                        を承認しました！
                    </p>
                    <p style="color: gray; margin-top: 30px;">
                        このページは閉じていただいて構いません。
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            st.balloons()
            # ここで処理を終了（ログイン画面を表示しない）
            st.stop()
        else:
            st.error("❌ 無効なトークンです。")
            st.markdown("""
                <div style="text-align: center; padding: 20px;">
                    <p>このリンクは既に使用されているか、無効です。</p>
                    <p style="color: gray;">このページは閉じていただいて構いません。</p>
                </div>
            """, unsafe_allow_html=True)
            st.stop()

# =============================================================================
# データベースの初期化とログイン状態の確認
# =============================================================================
# データベースの初期化（最初に実行）
init_database()

if not is_logged_in():
    # ログインしていない場合：ログイン画面を表示
    show_login_form()
    st.stop()
    
# ステータス一覧
statuses = ["未受注", "進行中", "承認待ち", "完了"]


# =============================================================================
# ログイン後のアプリケーション
# =============================================================================

# ヘッダー部分
# ロゴ画像を中央に配置
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    try:
        st.image("rogo.png", width=450)
    except FileNotFoundError:
        # 画像が見つからない場合は元のテキストを表示
        st.markdown("## 🔐 チャリンジャー")

# ユーザー情報とログアウトボタン
with st.sidebar:
    if 'username' in st.session_state:
        st.success(f"ログイン中: {st.session_state['username']}")
        if st.button("🚪 ログアウト", key="logout_btn"):
            logout_user()
            st.rerun()
    else:
        st.info("ログインが必要です")
        
# DBからクエストと実行状況を取得
def load_quests_from_db():
    with get_conn() as conn:
        cur = conn.cursor()
        current_user_id = st.session_state.get('user_id', 1)

        cur.execute("""
            SELECT q.quest_id, q.title, q.description, q.reward_amount, q.created_by,  
                    qe.execution_id,qe.status, qe.assigned_to, q.created_at, q.deadline
            FROM Quest q
            LEFT JOIN QuestExecution qe ON q.quest_id = qe.quest_id
            WHERE q.created_by = ? OR qe.assigned_to = ?
            ORDER BY q.quest_id
        """, (current_user_id, current_user_id))

        rows = cur.fetchall()
        quests = []
        for row in rows:
            quests.append({
                "id": row["quest_id"],
                "execution_id": row["execution_id"],
                "title": row["title"],
                "description": row["description"],
                "reward": row["reward_amount"],
                "created_by": row["created_by"],
                "status": row["status"] if row["status"] else "未受注",
                "assigned_to": row["assigned_to"],
                "created_at": row["created_at"],
                "deadline": row["deadline"]
            })
        return quests
    
quests = load_quests_from_db()

# =============================================================================
# クエスト発行ボタン（メイン画面に表示）
# =============================================================================

# ボタンレイアウト
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("クエスト発行する", key="create_quest_btn", type="primary", use_container_width=True):
        st.session_state.show_create_modal = True

# =============================================================================
# クエスト発行ポップアップ（モーダル）
# =============================================================================
if 'show_create_modal' not in st.session_state:
    st.session_state.show_create_modal = False

# ポップアップを表示する条件をチェック
if st.session_state.show_create_modal:
    
    # タイトル表示
    with st.container():
        st.markdown("## 新規クエスト発行")
        
        # フォーム入力エリア（2列レイアウト）
        form_col1, form_col2 = st.columns([1, 1])
        
        # 左列：依頼側の情報
        with form_col1:
            st.markdown("#### クエスト情報")
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
            requester_email = st.text_input(
                "メールアドレス", 
                value=st.session_state.get("user_email", ""),
                placeholder="example@email.com", 
                key="quest_email_input"
            )

        # 右列：期限・報酬情報
        with form_col2:
            st.markdown("#### 期限・報酬")
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
                    with get_conn() as conn:
                        cur = conn.cursor()

                        # Quest登録(ログインユーザIDを使用)
                        current_user_id = st.session_state.get('user_id', 1)
                        cur.execute("INSERT INTO Quest (title, description, reward_amount, deadline, created_by, created_at, requester_email) VALUES (?,?,?,?,?,CURRENT_TIMESTAMP,?)",
                                    (quest_title, quest_description, quest_reward, quest_date, current_user_id, requester_email))
                        quest_id = cur.lastrowid

                        # QuestExecution登録
                        assigned_user_id = current_user_id
                        cur.execute("INSERT INTO QuestExecution (quest_id, assigned_to, status) VALUES (?,?,?)", 
                                    (quest_id, assigned_user_id, "未受注"))

                    # 成功メッセージを表示して画面をリロード
                    st.success("✅ クエストが正常に発行されました！")
                    # モーダルを閉じる
                    st.session_state.show_create_modal = False
                    st.rerun()
                else:
                    st.error("❌ すべての項目を入力してください")
        
        with btn_col2:
            # キャンセルボタン
            if st.button("キャンセル", key="cancel_quest", use_container_width=True):
                st.session_state.show_create_modal = False
                st.rerun()
        
    
    # モーダルが表示されている時は、下のコンテンツの表示を抑制
    st.stop()
# =============================================================================
# メインコンテンツ：カンバンボード表示
# =============================================================================

# 自動更新のコード部分
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time_module.time()

current_time = time_module.time()
if current_time - st.session_state.last_refresh > 5:
    st.session_state.last_refresh = current_time
    st.rerun()

# 4列のカラムレイアウト作成
cols = st.columns(len(statuses))

# 各ステータス列の処理
for i, status in enumerate(statuses):
    with cols[i]:
        # 列ヘッダー表示
        st.markdown(f'<div class="column-header">{status}</div>', unsafe_allow_html=True)
        # 現在の列に該当するクエストをフィルタリング
        filtered = [q for q in quests if q["status"] == status]

        # 各クエストをカード形式で表示
        for q in filtered:
        
            # 報酬の表示形式を調整（数値の場合はポイント、文字列の場合はそのまま表示）
            reward_display = f"{q['reward']}" if isinstance(q['reward'], int) else q['reward']
            
            quest_key = f"quest_card_{q['id']}"
            
            # カード形式のボタンを作成
            if st.button(
                f"**{q['title']}**\n\n報酬: {reward_display}",
                key=quest_key,
                use_container_width=True
            ):
                st.session_state.selected_quest = q['id']
                st.rerun()

# =============================================================================
# 詳細モーダル表示
# =============================================================================

# クエストが選択されている場合の詳細表示
if 'selected_quest' in st.session_state:
    # 選択されたクエストの詳細情報を取得
    selected = next((q for q in quests if q['id'] == st.session_state.selected_quest), None)
    
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
            <p><strong>依頼者:</strong> {selected['created_by']}</p>
        </div>
        """, unsafe_allow_html=True)

        # ステータス変更 UI
        new_status = st.selectbox(
            "ステータスを変更",
            options=statuses,
            index=statuses.index(selected['status']),
            key="status_select"
        )

        if st.button("更新", key="update_status"):
            # 変更前のステータスを保存
            old_status = selected['status']
            with get_conn() as conn:
                cur = conn.cursor()

                # QuestExecutionのステータスを更新
                cur.execute("UPDATE QuestExecution SET status=? Where quest_id=?", (new_status, selected['id']))
            st.success(f"ステータスを 「{new_status}」に更新しました")

            # ===== メール送信処理を追加 =====（約262行目）
            if old_status == "進行中" and new_status == "承認待ち":
                try:
                    email_service = EmailService()
                    
                    # 既に取得済みのexecution_idを直接使用
                    execution_id = selected['execution_id']

                    # EmailServiceを使ってメール送信
                    success = email_service.send_approval_email(execution_id)

                    if success:
                        st.info("📧 承認依頼メールを送信しました")
                    else:
                        st.error("❌ メール送信に失敗しました")
                            
                except Exception as e:
                    st.error(f"❌ メール送信エラー: {str(e)}")
                    print(f"Mail sending error details: {e}")  # デバッグ用
                    
        # モーダルを閉じるボタン
        if st.button("閉じる", key="close_modal"):
            del st.session_state.selected_quest
            st.rerun()