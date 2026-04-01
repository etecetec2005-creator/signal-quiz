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

# ページ設定
st.set_page_config(page_title="AIクイズで確認 検査標準（信号）", layout="centered")

# 【iPhone SE対応】カテゴリー欄の折り返しと文字サイズ調整用CSS
st.markdown("""
    <style>
    /* 1. カテゴリー選択肢（未選択時・選択済み）の折り返し許可 */
    div[data-baseweb="select"] > div {
        white-space: normal !important;
        font-size: 13px !important;
        line-height: 1.3 !important;
        min-height: 40px !important;
    }
    /* 2. ドロップダウンリスト内の各項目の折り返し許可 */
    ul[role="listbox"] li {
        white-space: normal !important;
        word-wrap: break-word !important;
        font-size: 13px !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    /* 3. 選択ボックス全体のラベル（上の文字） */
    .stSelectbox label {
        font-size: 12px !important;
    }
    /* 4. クイズの選択肢ボタン内の文字折り返し */
    .stButton button div p {
        white-space: normal !important;
        word-break: break-all !important;
        line-height: 1.2 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# カテゴリーリスト
CATEGORIES = [
    "すべて", "単線自動閉そく装置（単線自動閉そく装置）", "特殊自動閉そく装置（軌道回路検知式）", 
    "電子閉そく装置（無線式・簡易無線式）", "電子閉そく装置（無線式）", "電子閉そく装置（簡易無線式）",
    "電気信号機（集中監視あり）（色灯式信号機）", "電気信号機（集中監視なし）（色灯式信号機）",
    "電気信号機（集中監視なし）（中継信号機）", "電気信号機（集中監視なし）（入換信号機）",
    "電気信号機（集中監視なし）（誘導信号機）", "電気信号機（集中監視なし）（進路表示機）",
    "電気信号機（集中監視なし）（進路予告器）", "電気信号機（集中監視なし）（手信号用代用器）",
    "合図器（出発合図器）", "合図器（出発指示合図器）", "合図器（ブレーキ試験合図器）", "合図器（入換合図器）",
    "標識類（灯具あり）（入換信号機識別標識）", "標識類（灯具あり）（入換標識（灯列式））",
    "標識類（灯具あり）（入換標識（線路表示式））", "標識類（灯具あり）（入換標識反応灯）",
    "標識類（灯具あり）（線路表示器）", "標識類（灯具あり）（出発反応標識）", "標識類（灯具あり）（列車停止標識）",
    "標識類（灯具あり）（車両停止標識）", "標識類（灯具あり）（車止標識）", "標識類（灯具なし）（列車停止標識）",
    "標識類（灯具なし）（車両停止標識）", "標識類（灯具なし）（車止標識）", "標識類（灯具なし）（閉そく信号標識）",
    "諸標類（灯具あり）（番線表示灯）", "諸標類（灯具あり）（限界表示灯）", "諸標類（灯具あり）（線路別表示灯）",
    "諸標類（灯具あり）（乗務員呼出表示灯）", "諸標類（灯具あり）（移動・機器取扱い禁止表示器）",
    "諸標類（灯具なし）（番線表示標）", "諸標類（灯具なし）（誤出発防止地上子箇所標）",
    "諸標類（灯具なし）（信号鳴呼位置標）", "諸標類（灯具なし）（停止限界標識）",
    "電気転てつ機（状態監視有り（付属装置含む））", "電気転てつ機（状態監視無し（付属装置含む））",
    "電気転てつ機（YS形（付属装置含む））", "発条転てつ機（付属装置、電磁鎖錠器含む）",
    "転てつ転換鎖錠装置（転てつ転換機（付属装置含む））", "転てつ転換鎖錠装置（転てつ双動機（付属装置含む））",
    "転てつ転換鎖錠装置（標識付転換機（付属装置含む））", "転てつ転換鎖錠装置（脱線器（付属装置含む））",
    "回路制御器", "鉄管装置（転てつ双動機用）", "継電連動装置（連動制御盤）", "継電連動装置（継電連動機器）",
    "電子連動装置（電子連動機（1形））", "電子連動装置（電子連動機（2形））", "電子連動装置（電子連動機（4形））",
    "電子連動装置（電子連動機（ブロック式））", "電子連動装置（集中連動機（中央設備））", "電子連動装置（駅設備）",
    "電子連動装置（集中連動機（駅設備））", "電子連動装置（集約連動機（中央設備））", "電子連動装置（集約連動機（駅設備））",
    "電子連動装置（電子連動機（3形））", "列車集中制御装置（中央設備（4形））", "列車集中制御装置（中央設備（5形））",
    "列車集中制御装置（中央設備（6形））", "列車集中制御装置（駅設備（4形））", "列車集中制御装置（駅設備（5形））",
    "列車集中制御装置（駅設備（6形））", "自動進路制御装置（駅設備）", "列車運行状況表示装置（駅設備）",
    "ATS装置（S形（検測車非走行区間））", "ATS装置（S形（検測車走行区間））", "ATS装置（SW形（検測車非走行区間））",
    "ATS装置（SW形（検測車走行区間））", "ATS装置（SW形（機器））", "ATS装置（P形（検測車非走行区間））",
    "ATS装置（P形（検測車走行区間））", "ATS装置（P形（機器））", "ATS装置（DW形（検測車非走行区間））",
    "ATS装置（DW形（検測車走行区間））", "ATS装置（DW形（機器））", "分岐器速度制限警報装置（SW形（検測車非走行区間））",
    "分岐器速度制限警報装置（SW形（検測車走行区間））", "分岐器速度制限警報装置（SW形（機器））",
    "踏切警報機（踏切警報機柱）", "踏切遮断機（電気踏切遮断機）", "踏切制御子（閉電路形（検測車非走行区間））",
    "踏切制御子（閉電路形（検測車走行区間））", "踏切制御子（開電路形（検測車非走行区間））",
    "踏切制御子（開電路形（検測車走行区間））", "踏切機器類（各種）", "踏切支障報知装置",
    "踏切支障報知装置（踏切障害物検知装置）", "踏切支障報知装置（大型支障物検知装置）", "表示装置（特殊信号発光機）",
    "電子踏切制御器", "踏切電源機器（整流器）", "踏切電源機器（鉛蓄電池）", "踏切電源機器（保安器（F形））",
    "踏切器具箱類（器具箱）", "踏切器具箱類（接続箱）", "直流軌道回路", "パルス軌道回路",
    "AFO軌道回路（AFO軌道回路）", "商用軌道回路", "信号ケーブル", "支持物（コンクリート柱）", "支持物（木柱）",
    "支持物（鉄柱）", "管路", "信号器具箱類（器具箱）", "信号器具箱類（接続箱）", "限界支障報知装置",
    "落石警報裝置", "安全側線緊急防護裝置", "支障報知裝置（変位警報裝置）", "支障報知裝置（風速警報裝置）",
    "支障報知裝置（橋桁防護裝置）", "橫取裝置用停止現示裝置", "トンネル内支障報知裝置", "落下物検知裝置",
    "ホーム用非常ボタン装置", "接近警報装置（旅客用）", "旅客通路用接近表示装置", "固定式列車接近警報装置（表示灯式）",
    "固定式列車接近警報裝置（警報音発生器式）", "諸設備踏切遮断機（電気踏切遮断機）", "諸設備踏切制御子（閉電路形（検測車非走行区間））",
    "諸設備踏切制御子（閉電路形（検測車走行区間））", "諸設備踏切制御子（開電路形（検測車非走行区間））",
    "諸設備踏切制御子（開電路形（検測車走行区間））", "諸設備機器類（各種）", "諸設備機器類（踏切故障検出器）",
    "諸設備電子踏切制御器（電子踏切制御器）", "諸設備踏切支障報知裝置（諸設備踏切障害物検知裝置）",
    "諸設備電源機器（整流器）", "諸設備電源機器（鉛蓄電池）", "諸設備電源機器（保安器（F形））",
    "諸設備器具箱類（器具箱）", "諸設備器具箱類（接続箱）", "抑止表示装置（駅装置）",
    "消防用設備（不活性ガス消火設備）", "消防用設備（ハロゲン化物消火設備）", "ブレーキ支援装置",
    "発動発電機", "配電盤", "整流器", "自動電圧調整器", "蓄電池（鉛蓄電池）", "蓄電池（制御弁式鉛蓄電池）",
    "商用軌道回路（状態監視有り）", "分倍周軌道回路（状態監視有り）", "100Hz 軌道回路（状態監視有り）",
    "商用軌道回路（状態監視無し）", "商用軌道回路（状態監視無し（単線））", "分倍周軌道回路（状態監視無し）",
    "分倍周軌道回路（状態監視無し（単線））", "100Hz 軌道回路（状態監視無し）", "分周軌道回路（状態監視有り）",
    "分周軌道回路（状態監視無し）", "分周軌道回路（状態監視無し（単線））", "機器集中形AF軌道回路（機器集中形AF軌道回路）",
    "機器集中形AF軌道回路（集中機器）", "無絶縁軌道回路（2電圧受電方式）", "長大軌道回路（長大軌道回路）",
    "H・DC軌道回路", "H・AC軌道回路", "列車検知装置（MTD形）", "列車検知装置（MTD形（集中機器））", "80Hzコード軌道回路"
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
        st.error(f"エラー: {e}")
        return []

# ==========================================
# 4. メイン描画
# ==========================================
st.title("🚉 AIクイズで確認 検査標準（信号）")

with st.sidebar:
    st.header("メニュー")
    # ここでカテゴリーを選択
    selected_cat = st.selectbox("カテゴリーを選択", CATEGORIES)
    if st.button("クイズを開始", type="primary"):
        reset_game()
        with st.spinner("AIが生成中..."):
            st.session_state.quiz_list = fetch_quizzes(selected_cat)
    if st.session_state.quiz_list:
        if st.button("リセット"):
            reset_game()
            st.rerun()

if not st.session_state.quiz_list:
    st.info("サイドバーからカテゴリーを選んでください。")
else:
    for idx, q in enumerate(st.session_state.quiz_list):
        st.markdown(f"#### 第 {idx+1} 問")
        st.write(q['question'])
        
        already_answered = idx in st.session_state.user_answers
        
        # 選択肢を1列に並べる（1,2,3,4の順）
        for i in range(4):
            c_num = str(i + 1)
            choice_label = f"{c_num}. {q['choices'][i]}"
            
            if st.button(choice_label, key=f"q{idx}_{i}", disabled=already_answered, use_container_width=True):
                # ユーザーの回答を記録
                st.session_state.user_answers[idx] = choice_label
                if c_num == q['answer']:
                    st.session_state.total_score += 1
                st.rerun()

        # 回答後の表示（履歴）
        if already_answered:
            user_ans = st.session_state.user_answers[idx]
            is_correct = user_ans.startswith(q['answer'])
            
            if is_correct:
                st.success("⭕ 正解！")
            else:
                st.error("❌ 不正解...")
            
            st.markdown(f"**回答履歴:** {user_ans}")
            if not is_correct:
                correct_idx = int(q['answer']) - 1
                st.markdown(f"**正解:** {q['answer']}. {q['choices'][correct_idx]}")
            
            with st.expander("解説を確認する", expanded=True):
                st.write(q['explanation'])
        st.divider()

    # 全問回答後の結果
    if len(st.session_state.user_answers) == len(st.session_state.quiz_list):
        st.balloons()
        st.header("🏁 結果発表")
        st.metric("正解数", f"{st.session_state.total_score} / {len(st.session_state.quiz_list)}")
        if st.button("もう一度挑戦する", type="primary", use_container_width=True):
            reset_game()
            st.rerun()
