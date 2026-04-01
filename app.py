import streamlit as st
import requests
import json
import re

# ==========================================
# 1. 初期設定とSecretsの読み込み
# ==========================================
# st.secrets から設定を読み込む（コードに直接書かない）
API_KEY = st.secrets["JAPANAI_API_KEY"]
API_URL = "https://api.japan-ai.co.jp/chat/v2"
ARTIFACT_ID = "0ba8d856-0804-4778-ab66-6eef6537915a"
MODEL_NAME = "gemini-2.5-pro"

st.set_page_config(page_title="社内資料クイズアプリ", layout="wide")
st.title("📖 社内資料クイズ生成")

# セッション状態の初期化（クイズデータを保持するため）
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []

# ==========================================
# 2. クイズ生成ロジック
# ==========================================
def generate_quizzes(category):
    prompt = f"データセット資料に基づき、「{category}」に関する4択クイズを【5問】作成してください。"
    if category == "すべて":
        prompt += "\n指示：資料内の異なる設備項目から満遍なく5つ選び、それぞれ1問ずつ作成してください。"
    
    prompt += ("\n各問題は必ず以下のフォーマットで記述し、問題の間には「===」を入れて区切ってください。"
               "\n【問題】:（問題文）\n【選択肢1】:（内容）\n【選択肢2】:（内容）\n【選択肢3】:（内容）\n【選択肢4】:（内容）"
               "\n【正解】:（数字1～4）\n【解説】:（解説文）")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.8,
        "artifactIds": [ARTIFACT_ID]
    }

    with st.spinner("AIが問題を生成中..."):
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            ai_text = response.json().get("chatMessage", "")
            
            # クイズごとに分割してパース
            blocks = ai_text.split("===")
            quizzes = []
            for block in blocks:
                if "【問題】" in block:
                    quizzes.append({
                        "question": parse_tag(block, "【問題】"),
                        "choices": [
                            parse_tag(block, "【選択肢1】"),
                            parse_tag(block, "【選択肢2】"),
                            parse_tag(block, "【選択肢3】"),
                            parse_tag(block, "【選択肢4】")
                        ],
                        "answer": parse_tag(block, "【正解】"),
                        "explanation": parse_tag(block, "【解説】")
                    })
            return quizzes
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            return []

def parse_tag(text, tag):
    # VBAのQ_ParseTagと同様の処理
    pattern = rf"{tag}:?\s*(.*?)(?=\n【|$)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

# ==========================================
# 3. 画面レイアウト
# ==========================================
with st.sidebar:
    category = st.selectbox("カテゴリを選択", ["すべて", "無線式", "簡易無線式", "その他"]) # 必要に応じて変更
    if st.button("クイズ生成", type="primary"):
        st.session_state.quiz_data = generate_quizzes(category)

if st.session_state.quiz_data:
    for i, q in enumerate(st.session_state.quiz_data):
        with st.container():
            st.markdown(f"### 第 {i+1} 問")
            st.write(q["question"])
            
            # ラジオボタンで回答選択
            user_choice = st.radio(f"選択肢 (問{i+1})", 
                                  [f"{j+1}: {c}" for j, c in enumerate(q["choices"])],
                                  key=f"q_{i}", index=None)
            
            if st.button(f"解答を表示 (問{i+1})"):
                if user_choice:
                    user_ans_num = user_choice.split(":")[0]
                    if user_ans_num == q["answer"]:
                        st.success("✨ 正解！")
                    else:
                        st.error(f"❌ 残念！ 正解は {q['answer']} です。")
                    st.info(f"**解説:** {q['explanation']}")
                else:
                    st.warning("回答を選択してください。")
            st.divider()
else:
    st.info("左のサイドバーからカテゴリを選択して「クイズ生成」を押してください。")
