import random
import streamlit as st

# =========================
# 1. 頁面設定 (RWD 響應式優化)
# =========================
st.set_page_config(page_title="AI 預測軸穩定版", layout="wide")

# 強化的 CSS 控制
st.markdown("""
<style>
    /* 全螢幕背景與字體 */
    .main { background-color: #0e1117; }
    
    /* 預測軸：字體大小隨螢幕寬度調整 */
    .axis-box { 
        font-size: clamp(24px, 5vw, 45px); 
        font-weight: 900; 
        text-align: center; 
        padding: 20px; 
        border-radius: 20px; 
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }

    /* 數據面板卡片化 */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* 按鈕美化：高度增加方便手機點擊 */
    .stButton > button {
        height: 60px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        margin-bottom: 10px;
    }

    /* 局數標籤 */
    .round-info { 
        background: #262730; 
        color: #00ffcc; 
        padding: 12px; 
        border-radius: 10px; 
        font-size: 18px; 
        text-align: center;
        width: 100%;
        margin-bottom: 15px;
        border: 1px solid #444;
    }

    /* 珠盤路容器：支援手機橫向滑動 */
    .bead-container {
        display: flex;
        flex-wrap: nowrap;
        overflow-x: auto;
        padding: 10px 0;
        gap: 8px;
    }
    .bead-column {
        display: flex;
        flex-direction: column;
        gap: 8px;
        flex: 0 0 auto;
    }
    .bead {
        width: 35px; height: 35px; line-height: 35px;
        border-radius: 50%; text-align: center; font-weight: bold;
        color: white; font-size: 14px;
        box-shadow: inset -2px -2px 4px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 AI 百家樂預測軸 Pro")

# =========================
# 2. 狀態初始化
# =========================
if "history" not in st.session_state:
    st.session_state.history = []
if "shoe" not in st.session_state:
    deck = [1,2,3,4,5,6,7,8,9,0,0,0,0] * 4
    st.session_state.shoe = deck * 8
    random.shuffle(st.session_state.shoe)

def result_color(v):
    return "#1c83e1" if v == "閒" else "#ff4b4b" if v == "莊" else "#28a745"

# =========================
# 3. 穩定運算邏輯
# =========================
def get_stable_monte_carlo(sim=10000):
    shoe = st.session_state.shoe
    if len(shoe) < 12: return 0.493, 0.507
    seed_val = len(st.session_state.history)
    rng = random.Random(seed_val)
    p_win, b_win = 0, 0
    for _ in range(sim):
        s = rng.sample(shoe, 6)
        pv = (s[0] + s[1]) % 10
        bv = (s[2] + s[3]) % 10
        if pv <= 5: pv = (pv + s[4]) % 10
        if bv <= 5: bv = (bv + s[5]) % 10
        if pv > bv: p_win += 1
        elif bv > pv: b_win += 1
    total = p_win + b_win
    return (0.5, 0.5) if total == 0 else (p_win / total, b_win / total)

p_prob, b_prob = get_stable_monte_carlo()
delta = (b_prob - p_prob) * 100
EOR = {1:-0.6, 2:-0.4, 3:-0.7, 4:-1.2, 5:0.8, 6:0.6, 7:0.3, 8:0.1, 9:-0.1, 0:0.2}
score = sum(EOR.get(c, 0) for c in st.session_state.shoe)
tc = score / max(len(st.session_state.shoe) / 52, 0.5)

d_norm = max(min(delta / 2, 1), -1)
tc_norm = max(min(tc / 3, 1), -1)
axis_score = d_norm * 0.6 + tc_norm * 0.4
axis_0_10 = round((axis_score + 1) * 5, 1)

# =========================
# 4. 預測軸顯示
# =========================
if axis_0_10 >= 6.5: label, color = "強烈偏向【莊】", "#ff4b4b"
elif axis_0_10 >= 5.5: label, color = "微幅偏向【莊】", "#ff4b4b"
elif axis_0_10 <= 3.5: label, color = "強烈偏向【閒】", "#1c83e1"
elif axis_0_10 <= 4.5: label, color = "微幅偏向【閒】", "#1c83e1"
else: label, color = "中性觀望", "#555"

st.markdown(
    f"<div class='axis-box' style='background:{color}; color:white;'>"
    f"預測軸：{axis_0_10} / 10<br><span style='font-size:0.6em; opacity:0.9;'>{label}</span></div>",
    unsafe_allow_html=True
)

# =========================
# 5. 數據面板 (手機會自動變 2x2 或 1 欄)
# =========================
c1, c2, c3 = st.columns([1,1,1])
c1.metric("閒勝率", f"{p_prob*100:.1f}%")
c2.metric("莊勝率", f"{b_prob*100:.1f}%")
c3.metric("TC 數值", f"{tc:.2f}")

# =========================
# 6. 操作區 (重點優化)
# =========================
st.write("")
total_rounds = len(st.session_state.history)
st.markdown(f"<div class='round-info'>目前進度：第 {total_rounds} 局</div>", unsafe_allow_html=True)

# 手機版建議按鈕排列
col1, col2, col3 = st.columns(3)
with col1: st.button("🔵 閒", on_click=lambda: record_result("閒"), use_container_width=True)
with col2: st.button("🔴 莊", on_click=lambda: record_result("莊"), use_container_width=True)
with col3: st.button("🟢 和", on_click=lambda: record_result("和"), use_container_width=True)

col4, col5 = st.columns(2)
with col4: st.button("↩️ 回退", on_click=lambda: undo_step(), use_container_width=True)
with col5: st.button("🔄 洗牌", on_click=lambda: st.session_state.clear(), use_container_width=True)

def record_result(r):
    st.session_state.history.append(r)
    for _ in range(6): 
        if st.session_state.shoe: st.session_state.shoe.pop()

def undo_step():
    if st.session_state.history:
        st.session_state.history.pop()
        for _ in range(6): st.session_state.shoe.append(random.randint(0,9))

# =========================
# 7. 珠盤路 (可橫向捲動版)
# =========================
if st.session_state.history:
    st.write("### 歷史趨勢 (可橫向滑動)")
    # 將歷史紀錄每 6 個切成一組（一列）
    history = st.session_state.history
    columns_data = [history[i:i+6] for i in range(0, len(history), 6)]
    
    html_beads = '<div class="bead-container">'
    for col in columns_data:
        html_beads += '<div class="bead-column">'
        for val in col:
            html_beads += f'<div class="bead" style="background:{result_color(val)};">{val}</div>'
        html_beads += '</div>'
    html_beads += '</div>'
    
    st.markdown(html_beads, unsafe_allow_html=True)