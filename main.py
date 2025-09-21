import streamlit as st
import pandas as pd
from datetime import datetime, date, time

# ページ設定
st.set_page_config(page_title="チャジンジャー", page_icon=":guardsman:", layout="wide")

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
            for q in st.session_state.quests:
                if q['id'] == selected['id']:
                    q['status'] = new_status
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
# - りす: 新規クエスト登録フォーム（上部に配置予定）
# - けんた: ステータス変更機能（モーダル内に追加予定）
# - けんた: Gmail API連携（完了通知機能）