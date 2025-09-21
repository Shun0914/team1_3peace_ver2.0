import streamlit as st
import pandas as pd

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
    st.session_state.statuses = ["受注中", "進行中", "承認待ち", "完了"]

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
            # HTMLカード + JavaScriptクリック処理
            st.markdown(f'''
            <div class="card" onclick="document.getElementById('btn_{quest["id"]}').click()">
                <h4>{quest["title"]}</h4>
                <p>報酬: {quest["reward"]}ポイント</p>
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
        # モーダル風の詳細表示（固定位置）
        st.markdown(f"""
        <div style="position: fixed; top: 20%; left: 30%; width: 40%; background-color: white; border: 2px solid #000; border-radius: 10px; padding: 20px; z-index: 1000;">
            <h3>{selected['title']}</h3>
            <p><strong>説明:</strong> {selected['description']}</p>
            <p><strong>報酬:</strong> {selected['reward']}ポイント</p>
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