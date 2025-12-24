import streamlit as st
import pandas as pd
import random

# --- 页面配置 ---
st.set_page_config(page_title="投资复利实战游戏", layout="wide")

# --- 模拟数据库 (在实际应用中建议连接外部DB，此处为演示简化版) ---
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'round': 1,
        'market_status': "等待开课",
        'price_change': {"科技股": 0, "房地产": 0, "黄金": 0, "国债": 0},
        'history': []
    }

if 'players' not in st.session_state:
    st.session_state.players = {}

# --- 游戏逻辑定义 ---
def next_round(changes):
    st.session_state.game_state['round'] += 1
    st.session_state.game_state['price_change'] = changes
    # 更新所有玩家资产
    for p_name in st.session_state.players:
        p = st.session_state.players[p_name]
        for asset, change in changes.items():
            p['assets'][asset] *= (1 + change)
        # 扣除利息 (10% 利率)
        interest = p['loan'] * 0.1
        p['cash'] -= interest
        p['net_worth'] = p['cash'] + sum(p['assets'].values())

# --- 侧边栏：角色选择 ---
role = st.sidebar.radio("选择你的角色", ["我是同学", "我是老师"])

# ----------------- 老师控制台 -----------------
if role == "我是老师":
    st.title("👨‍🏫 投资游戏控制中心")
    
    curr_round = st.session_state.game_state['round']
    st.subheader(f"当前阶段：第 {curr_round} 轮")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: s_tech = st.number_input("科技股涨跌(%)", value=20)
    with col2: s_house = st.number_input("房地产涨跌(%)", value=10)
    with col3: s_gold = st.number_input("黄金涨跌(%)", value=5)
    with col4: s_bond = st.number_input("国债涨跌(%)", value=3)
    
    if st.button("确定本轮波动并进入下一轮"):
        changes = {
            "科技股": s_tech/100,
            "房地产": s_house/100,
            "黄金": s_gold/100,
            "国债": s_bond/100
        }
        next_round(changes)
        st.success("市场已更新！请通知同学查看资产变动。")

    st.divider()
    st.subheader("📊 实时排行榜")
    if st.session_state.players:
        leaderboard = pd.DataFrame([
            {"姓名": k, "总资产": v['net_worth'], "现金": v['cash'], "负债": v['loan']} 
            for k, v in st.session_state.players.items()
        ]).sort_values(by="总资产", ascending=False)
        st.table(leaderboard)

# ----------------- 同学操作端 -----------------
else:
    st.title("💰 财富增长实战营")
    
    player_name = st.text_input("请输入你的姓名/代号登录", key="login_name")
    
    if player_name:
        if player_name not in st.session_state.players:
            st.session_state.players[player_name] = {
                "cash": 100000.0,
                "loan": 0.0,
                "assets": {"科技股": 0.0, "房地产": 0.0, "黄金": 0.0, "国债": 0.0},
                "net_worth": 100000.0
            }
        
        p = st.session_state.players[player_name]
        
        # 资产概览卡片
        c1, c2, c3 = st.columns(3)
        c1.metric("当前净资产", f"¥{p['net_worth']:,.0f}")
        c2.metric("剩余现金", f"¥{p['cash']:,.0f}")
        c3.metric("本轮轮次", f"第 {st.session_state.game_state['round']} 轮")

        st.divider()
        
        # 投资操作区
        st.subheader("🛒 资产配置区")
        asset_to_buy = st.selectbox("选择要投资的资产", ["科技股", "房地产", "黄金", "国债"])
        buy_amount = st.number_input("投入金额", min_value=0.0, max_value=float(p['cash'] + 100000), step=10000.0)
        
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("确认买入"):
            if buy_amount <= p['cash']:
                p['assets'][asset_to_buy] += buy_amount
                p['cash'] -= buy_amount
                st.success(f"成功买入 {asset_to_buy}！")
            else:
                st.error("余额不足，请先申请借贷！")
        
        if col_b2.button("申请借贷 (5万)"):
            p['loan'] += 50000
            p['cash'] += 50000
            st.warning("已借入5万，每轮将产生10%利息支出！")

        # 当前持仓明细
        st.subheader("📋 我的持仓明细")
        asset_df = pd.DataFrame([p['assets']]).T
        asset_df.columns = ["当前价值"]
        st.table(asset_df)

        st.info("💡 提示：等待老师点击'进入下一轮'，你的资产价值就会随市场波动发生变化。")
