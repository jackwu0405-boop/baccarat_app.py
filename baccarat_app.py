import random
import streamlit as st
import math

# =========================
# 1. 頁面設定 (維持原樣)
# =========================
st.set_page_config(page_title="AI 極簡預測軸", layout="wide")

st.markdown("""
<style>
    /* 原始樣式保持不變 */
    .stApp { background-color: #0a0a0a; color: #E0E0E0; }
    .main-card { padding: 30px; border-radius: 20px; text-align: center; background: #111; border: 1px solid #222; margin-bottom: 20px; }
    .score-text { font-size: 55px; font-weight: 900; margin: 0; line-height: 1; }
    .status-text { font-size: 22px; font-weight: bold; margin-bottom: 10px; }
    .metric-bar { display: flex; justify-content: space-around; padding: 15px; background: #161616; border-radius: 15px; margin-bottom: 20px; }
    .m-item { text-align: center; }
    .m-label { font-size: 11px; color: #666; margin-bottom: 4px; }
    .m-value { font-size: 18px; font-weight: 600; color: #ddd; }
    .diag-box { padding: 10px; border-radius: 10px; font-size: 14px; text-align: center; background: #1a1a1a; color: #888; border: 1px solid #333; }
    .bead-container { display: flex; flex-wrap: nowrap; overflow-x: auto; padding: 15px 0; gap: 10px; }
    .bead-col { display: flex; flex-direction: column; gap: 8px; flex: 0 0 auto; }
    .bead { width: 32px; height: 32px; line-height: 32px; border-radius: 50%; text-align: center; font-weight: bold; color: white; font-size: 14px; box-shadow: inset -2px -2px 4px rgba(0,0,0,0.3); }
</style>
""", unsafe_allow_html=True)

# =========================
# 2. 初始化牌組
# =========================
if "history" not in st.session_state:
    st.session_state.history = []

if "shoe" not in st.session_state:
    # 8 副牌組，每副牌 A~9=1~9, 10/J/Q/K=0
    deck = [1,2,3,4,5,6,7,8,9,0,0,0,0] * 4
    st.session_state.shoe = deck * 8
    random.shuffle(st.session_state.shoe)

# =========================
# 3. 核心函數：百家樂完整蒙地卡羅模擬
# =========================
def baccarat_hand_result(cards):
    """計算莊閒結果，加入第三張牌規則"""
    # 前兩張牌
    player = (cards[0] + cards[1]) % 10
    banker = (cards[2] + cards[3]) % 10

    # 天然牌判斷
    if player >= 8 or banker >= 8:
        return 'P' if player > banker else 'B' if banker > player else 'T'

    # 玩家第三張牌
    player_third = None
    if player <= 5:
        player_third = cards[4]
        player = (player + player_third) % 10

    # 莊家第三張牌規則
    banker_third = None
    if player_third is None:  # 玩家不補牌
        if banker <= 5:
            banker = (banker + cards[4]) % 10
    else:
        # 莊家補牌判斷表（簡化版）
        b = banker
        p3 = player_third
        if b <= 2: banker = (b + cards[5]) % 10
        elif b == 3 and p3 != 8: banker = (b + cards[5]) % 10
        elif b == 4 and 2 <= p3 <= 7: banker = (b + cards[5]) % 10
        elif b == 5 and 4 <= p3 <= 7: banker = (b + cards[5]) % 10
        elif b == 6 and 6 <= p3 <= 7: banker = (b + cards[5]) % 10
        # b==7 不補牌

    return 'P' if player > banker else 'B' if banker > player else 'T'

def monte_carlo_sim(shoe, n_sim=20000):
    """模擬剩餘牌組莊閒勝率"""
    if len(shoe) < 6:
        return 0.493, 0.507  # 基本概率
    rng = random.Random(len(st.session_state.history))
    p_win, b_win = 0, 0
    for _ in range(n_sim):
        sample = rng.sample(shoe, 6)
        result = baccarat_hand_result(sample)
        if result == 'P': p_win += 1
        elif result == 'B': b_win += 1
    total = p_win + b_win
    return p_win/total, b_win/total

# =========================
# 4. TC 計算 + 動態加權
# =========================
def compute_axis(p_prob, b_prob, shoe):
    delta = (b_prob - p_prob) * 100
    EOR = {1:-0.6,2:-0.4,3:-0.7,4:-1.2,5:0.8,6:0.6,7:0.3,8:0.1,9:-0.1,0:0.2}
    score = sum(EOR.get(c,0) for c in shoe)
    tc = score / max(len(shoe)/52, 0.5)
    
    # 非線性加權
    delta_w = math.tanh(delta/10)  # -1~1
    tc_w = math.tanh(tc/3)         # -1~1
    axis = ((delta_w*0.6 + tc_w*0.4)+1)*5
    axis = round(axis, 1)

    # 短期趨勢修正（連莊/閒）
    history = st.session_state.history[-6:]
    if history:
        last = history[-1]
        streak = 1
        for h in reversed(history[:-1]):
            if h == last: streak += 1
            else: break
        # 修正因子
        if last=='莊': axis += min(streak*0.1,0.5)
        elif last=='閒': axis -= min(streak*0.1,0.5)
        axis = max(0, min(axis,10))
    return axis, tc

# =========================
# 5. 執行模擬
# =========================
p_prob, b_prob = monte_carlo_sim(st.session_state.shoe)
axis_0_10, tc = compute_axis(p_prob, b_prob, st.session_state.shoe)

# =========================
# 6. 原有 UI 完整保留
# =========================
if axis_0_10 >= 6.0: res, clr = "建議投註：莊家", "#ff4b4b"
elif axis_0_10 <= 4.0: res, clr = "建議投註：閒家", "#1c83e1"
else: res, clr = "中性觀望", "#666"

st.markdown(f"""
    <div class="main-card" style="border-bottom: 4px solid {clr};">
        <div class="status-text" style="color:{clr};">{res}</div>
        <div class="score-text">{axis_0_10} <span style="font-size:18px; color:#444;">/ 10</span></div>
    </div>
""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="metric-bar">
        <div class="m-item"><div class="m-label">閒勝率</div><div class="m-value">{p_prob*100:.1f}%</div></div>
        <div class="m-item"><div class="m-label">莊勝率</div><div class="m-value">{b_prob*100:.1f}%</div></div>
        <div class="m-item"><div class="m-label">真實記數 (TC)</div><div class="m-value">{tc:.2f}</div></div>
    </div>
""", unsafe_allow_html=True)

diag = "數據穩定，正常監控中"
if tc > 1.5: diag = "🚨 牌池警告：【小牌】過多，有利於閒家"
elif tc < -1.5: diag = "🚨 牌池警告：【大牌】過多，有利於莊家"
st.markdown(f"<div class='diag-box'>{diag}</div>", unsafe_allow_html=True)

total_rounds = len(st.session_state.history)
st.markdown(f"<p style='text-align:center; color:#555; font-size:12px;'>當前進度：第 {total_rounds} 局</p>", unsafe_allow_html=True)

# =========================
# 7. 操作按鈕和珠盤路（保持原樣）
# =========================
def record_result(r):
    st.session_state.history.append(r)
    for _ in range(6): 
        if st.session_state.shoe: st.session_state.shoe.pop()

def undo_step():
    if st.session_state.history:
        st.session_state.history.pop()
        for _ in range(6): st.session_state.shoe.append(random.randint(0,9))

c1, c2, c3 = st.columns(3)
with c1: st.button("🔵 紀錄【閒】", on_click=lambda: record_result("閒"), use_container_width=True)
with c2: st.button("🔴 紀錄【莊】", on_click=lambda: record_result("莊"), use_container_width=True)
with c3: st.button("🟢 紀錄【和】", on_click=lambda: record_result("和"), use_container_width=True)

c4, c5 = st.columns(2)
with c4: st.button("↩️ 回退一步", on_click=lambda: undo_step(), use_container_width=True)
with c5: st.button("🔄 重新洗牌", on_click=lambda: st.session_state.clear(), use_container_width=True)

# 珠盤路
if st.session_state.history:
    st.write("---")
    st.write("### 珠盤路趨勢 (縱向 6 格)")
    history = st.session_state.history
    columns_data = [history[i:i+6] for i in range(0, len(history), 6)]
    
    def get_bg(v):
        return "#1c83e1" if v=="閒" else "#ff4b4b" if v=="莊" else "#28a745"

    html_beads = '<div class="bead-container">'
    for col in columns_data:
        html_beads += '<div class="bead-col">'
        for val in col:
            html_beads += f'<div class="bead" style="background:{get_bg(val)};">{val}</div>'
        html_beads += '</div>'
    html_beads += '</div>'
    
    st.markdown(html_beads, unsafe_allow_html=True)
