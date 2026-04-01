import streamlit as st
import requests
import re

# ==========================================
# 1. 設定と機密情報
# ==========================================
API_KEY = st.secrets["JAPANAI_API_KEY"]
API_URL = "https://api.japan-ai.co.jp/chat/v2"
ARTIFACT_ID = "0ba8d856-0804-4778-ab66-6eef6537915a"
MODEL_NAME = "gemini-2.5-pro"

st.set_page_config(page_title="AIクイズ 検査標準（信号）", layout="centered")

# ==========================================
# iPhone SE 最適化 CSS（改行・文字切れ対策）
# ==========================================
st.markdown("""
    <style>
    /* 1. 選択ボックスの「選択済みテキスト」の省略を解除し改行を強制 */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        display: block !important;
        line-height: 1.4 !important;
    }
    
    /* 2. 選択ボックス自体の高さを自動調整 */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        height: auto !important;
        min-height: 3rem !important;
        padding: 5px 0 !important;
    }

    /* 3. ドロップダウン（開いた時）のリスト項目もすべて改行を許可 */
    div[data-baseweb="popover"] li div {
        white-space: normal !important;
        word-break: break-all !important;
        line-height: 1.4 !important;
    }
    
    div[data-baseweb="popover"] li {
        height: auto !important;
        min-height: 44px !important;
        border-bottom: 1px solid #f0f2f6;
    }

    /* 4. サイドバーの幅をモバイルに最適化 */
    section[data-testid="stSidebar"] {
        width: 80vw !important;
    }

    /* 5. クイズ回答ボタンの文字も確実に改行 */
    .stButton > button div p {
        white-space: normal !important;
        word-break: break-word !important;
        text-align: left !important;
    }
    </style>
    """, unsafe_allow_html=True)

# カテゴリーリスト
CATEGORIES = [
    "すべて", "単線自動閉そく装置", "特殊自動閉そく装置", "電子閉そく装置（無線式・簡易無線式）",
    "電気信号機（色灯式信号機）", "合図器", "標識類", "諸標類", "電気転てつ機", 
    "転てつ転換鎖錠装置", "回路制御器", "継電連動装置", "電子連動装置", "列車集中制御装置", 
    "ATS装置", "踏切警報機", "踏切遮断機", "踏切制御子", "踏切支障報知装置", "軌道回路", 
    "信号ケーブル", "支持物", "管路", "限界支障報知装置", "落石警報裝置", "ホーム用非常ボタン装置", 
    "接近警報装置", "蓄電池", "列車検知装置"
]

# ==========================================
# 2. セッション状態の管理
# ==========================================
if "quiz_list" not in st.session_state:
    st.session_state.quiz_list = []
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "total_score" not in st.session_state:
    st.session_state.total_score = 0

def reset_game():
    st.session_state.quiz_list = []
    st.session_state.user_answers = {}
    st.session_state.total_score = 0

# ==========================================
# 3. AI連携・パース
# ==========================================
def parse_tag(text, tag):
    pattern = rf"{tag}:?\s*(.*?)(?=\n【|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

def fetch_quizzes(category):
    prompt = f"資料に基づき、「{category}」に関する4択クイズを5問作成してください。\n"
    prompt += ("【問題】:（問題文）\n【選択肢1】:（内容）\n【選択肢2】:（内容）\n【選択肢3】:（内容）\n【選択肢4】:（内容）\n"
               "【正解】:（数字1～4）\n【解説】:（解説文）\nの形式で、各問題の間には「===」を入れてください。")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False, "temperature": 0.8, "artifactIds": [ARTIFACT_ID]}
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        ai_text = response.json().get("chatMessage", "")
        blocks = ai_text.split("===")
        res = []
        for b in blocks:
            if "【問題】" in b:
                res.append({
                    "question": parse_tag(b, "【問題】"),
                    "choices": [parse_tag(b, f"【選択肢{i}】") for i in range(1, 5)],
                    "answer": parse_tag(b, "【正解】"),
                    "explanation": parse_tag(b, "【解説】")
                })
        return res
    except Exception as e:
        st.error(f"エラーが発生しました。")
        return []

# ==========================================
# 4. メイン描画
# ==========================================
st.title("🚉 AIクイズ 検査標準（信号）")

with st.sidebar:
    st.header("メニュー")
    selected_cat = st.selectbox("カテゴリーを選択", CATEGORIES)
    
    if st.button("クイズを開始", type="primary", use_container_width=True):
        reset_game()
        with st.spinner("AIがクイズを生成中..."):
            st.session_state.quiz_list = fetch_quizzes(selected_cat)
    
    if st.session_state.quiz_list:
        if st.button("リセットして戻る", use_container_width=True):
            reset_game()
            st.rerun()

if not st.session_state.quiz_list:
    st.info("左側のメニューからカテゴリーを選んで開始してください。")
else:
    for idx, q in enumerate(st.session_state.quiz_list):
        st.markdown(f"#### 第 {idx+1} 問")
        st.write(q['question'])
        
        already_answered = idx in st.session_state.user_answers
        
        for i in range(4):
            c_num = str(i + 1)
            choice_label = f"{c_num}. {q['choices'][i]}"
            
            if st.button(choice_label, key=f"q{idx}_{i}", disabled=already_answered, use_container_width=True):
                st.session_state.user_answers[idx] = choice_label
                if c_num == q['answer']:
                    st.session_state.total_score += 1
                st.rerun()

        if already_answered:
            user_ans = st.session_state.user_answers[idx]
            is_correct = user_ans.startswith(q['answer'])
            if is_correct:
                st.success("⭕ 正解！")
            else:
                st.error("❌ 不正解...")
            
            with st.expander("解説を確認する", expanded=True):
                st.write(q['explanation'])
        st.divider()

    # ==========================================
    # 結果発表セクション（条件付き演出）
    # ==========================================
    if len(st.session_state.user_answers) == len(st.session_state.quiz_list):
        st.header("🏁 結果発表")
        score = st.session_state.total_score
        full_marks = len(st.session_state.quiz_list)
        
        st.metric("正解数", f"{score} / {full_marks}")

        if score >= 4:
            st.balloons() # 4問以上は風船
            st.success("おめでとうございます！素晴らしい成績です。")
        else:
            st.snow() # 3問以下は雪（静かな演出）
            st.warning("お疲れ様でした。もう一度復習してみましょう。")

        if st.button("もう一度挑戦", type="primary", use_container_width=True):
            reset_game()
            st.rerun()
