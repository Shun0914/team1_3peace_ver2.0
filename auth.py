# auth.py（ログインシステム）
import hashlib
import streamlit as st
from db import init_database, get_user_by_username, get_user_by_email, create_user, update_last_login

def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """パスワードの検証"""
    return hash_password(password) == hashed

def login_user(username: str, password: str) -> bool:
    """ユーザーログイン処理"""
    # データベースからユーザー情報を取得
    user = get_user_by_username(username)
    
    if user and verify_password(password, user['password_hash']):
        # ログイン成功時の処理
        st.session_state['logged_in'] = True
        st.session_state['user_id'] = user['user_id']
        st.session_state['username'] = user['username']
        st.session_state['user_email'] = user['email']
        
        # 最終ログイン時刻を更新
        update_last_login(user['user_id'])
        return True
    return False

def register_user(username: str, email: str, password: str) -> bool:
    """ユーザー登録処理"""
    # 既存ユーザーのチェック
    if get_user_by_username(username):
        st.error("このユーザー名は既に使用されています")
        return False
    
    if get_user_by_email(email):
        st.error("このメールアドレスは既に登録されています")
        return False
    
    # パスワードハッシュ化
    password_hash = hash_password(password)
    
    # ユーザー作成
    user_id = create_user(username, email, password_hash)
    
    if user_id:
        # 自動ログイン
        st.session_state['logged_in'] = True
        st.session_state['user_id'] = user_id
        st.session_state['username'] = username
        st.session_state['user_email'] = email
        return True
    return False

def logout_user():
    """ユーザーログアウト処理"""
    # セッション状態をクリア
    keys_to_clear = ['logged_in', 'user_id', 'username', 'user_email']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def is_logged_in() -> bool:
    """ログイン状態の確認"""
    return st.session_state.get('logged_in', False)

def show_login_form():
    """ログインフォームの表示"""
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 14px !important;
        padding: 8px 16px !important;
    }
                
    /* フォーム全体の背景調整 */
    .stForm {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        backdrop-filter: blur(10px) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ロゴ画像配置
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        try:
            st.image("rogo.png", width=450)
        except FileNotFoundError:
            # 画像が見つからない場合は元のテキストを表示
            st.markdown("## 🔐 チャリンジャーログイン")
    
    # 少し余白を追加
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["ログイン", "新規登録"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("ユーザー名")
            password = st.text_input("パスワード", type="password")
            
            if st.form_submit_button("ログイン", type="primary"):
                if username and password:
                    if login_user(username, password):
                        st.success("ログインしました！")
                        st.rerun()
                    else:
                        st.error("ユーザー名またはパスワードが間違っています")
                else:
                    st.error("全ての項目を入力してください")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("ユーザー名", key="reg_username")
            new_email = st.text_input("メールアドレス", key="reg_email")
            new_password = st.text_input("パスワード", type="password", key="reg_password")
            confirm_password = st.text_input("パスワード確認", type="password", key="reg_confirm")
            
            if st.form_submit_button("アカウント作成", type="primary"):
                if new_username and new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("パスワードが一致しません")
                    elif len(new_password) < 6:
                        st.error("パスワードは6文字以上で入力してください")
                    else:
                        if register_user(new_username, new_email, new_password):
                            st.success("アカウントが作成されました！")
                            st.rerun()
                else:
                    st.error("全ての項目を入力してください")