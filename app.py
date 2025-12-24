import streamlit as st
import pandas as pd
import numpy as np

# --- 页面配置 ---
st.set_page_config(page_title="高级投资博弈模拟器", layout="wide")

# --- 初始化全局状态 ---
if 'round' not in st.session_state:
    st.session_state.round = 1
if 'players' not in st.session_state:
    st.session_state.players = {}
if 'market_data' not in st.session_state:
    # 默认10年收益率数据（百分比）
    default_data = {
        "比特币": [120, -60, 150, 40, -20, 100, 30, -50, 80, 20],
        "A股": [15, -20, 30, 5, -10, 25, 10, -15, 20, 5],
        "标普500": [12, 10, -5, 15, 20, 8, 12, -10, 15, 10],
        "美债": [3, 2, 4, 1, 2, 3, 2, 5, 2, 3],
        "ACWI": [8, 5, -2, 10, 12, 6, 8, -5, 10, 7],
        "等权组合": [31.6, -12.6, 35.4, 14.2, 0.8, 28.4, 12.4, -13, 25.4, 9]
    }
    st.session_state.market_data = pd.DataFrame(default_data)

# --- 金融计算函数 ---
def calculate_metrics(df):
    metrics = {}
    # 算术平均
    metrics['mean'] = df.mean()
    # 标准差
    metrics['std'] = df.std()
    # 年化收益率 (Geometric Mean)
    metrics['cagr'] = df.apply(lambda x: (np.prod(1 + x/100)**(1/len(x)) - 1) * 100)
    # 相关性矩阵
    metrics['corr'] = df.corr()
    return metrics

metrics = calculate_metrics(st.session_state.market_data)

# --- 侧边栏 ---
st.sidebar.title("🎮 游戏控制中心")
role = st.sidebar.selectbox("切换角色", ["学生端", "老师端"])

# ----------------- 老师端 -----------------
if role == "老师端":
    st.title("👨‍🏫 教学设置与控制")
    pwd = st.text_input("管理密码", type="password")
    if pwd == "8888":
        tab1, tab2 = st.tabs(["数据预设", "轮次控制"])
        
        with tab1:
            st.subheader("预设未来10年收益率 (%)")
            edited_df = st.data_editor(st.session_state.market_data, num_rows="fixed")
            if st.button("保存并更新指标"):
                st.session_state.market_data = edited_df
                st.rerun()
            
            st.divider()
            st.subheader("📊 自动计算的金融指标")
            col_m1, col_m2 = st.columns(2)
            col_m1.write("算术平均 vs 年化收益率 (CAGR)")
            col_m1.dataframe(pd.DataFrame({"算术平均": metrics['mean'], "年化收益": metrics['cagr']}))
            col_m2.write("风险指标 (标准差)")
            col_m2.dataframe(metrics['std'])
            st.write("资产相关性矩阵")
            st.dataframe(metrics['corr'])

        with tab2:
            st.subheader(f"当前阶段：第 {st.session_state.round} 轮")
            next_btn = st.button("➡️ 开启下一轮")
            reset_btn = st.button("🔄 重置全场游戏")
            
            if next_btn and st.session_state.round < 4:
                # 结算当前轮次收益
                for p_name in st.session_state.players:
                    p = st.session_state.players[p_name]
                    # 每一轮模拟一个随机年份的收益率
                    year_idx = st.session_state.round - 1 
                    round_returns = st.session_state.market_data.iloc[year_idx]
                    
                    total_asset_val = 0
                    for asset, val in p['assets'].items():
                        new_val = val * (1 + round_returns[asset]/100)
                        p['assets'][asset] = new_val
                        total_asset_val += new_val
                    
                    # 扣除利息
                    p['cash'] -= p['loan'] * 0.1
                    p['net_worth'] = p['cash'] + total_asset_val
                    
                    # 记录破产
                    if p['net_worth'] <= 0:
                        p['is_bust'] = True
                
                st.session_state.round += 1
                st.success("轮次已切换，数据已更新")
                st.rerun()

            if reset_btn:
                st.session_state.players = {}
                st.session_state.round = 1
                st.rerun()

# ----------------- 学生端 -----------------
else:
    st.title(f"📈 投资博弈：第 {st.session_state.round} 轮")
    name = st.text_input("输入你的姓名登录", key="s_name")
    
    if name:
        if name not in st.session_state.players:
            st.session_state.players[name] = {
                "cash": 100000.0, "loan": 0.0, "net_worth": 100000.0,
                "is_bust": False, "conservative_score": 0,
                "assets": {c: 0.0 for c in st.session_state.market_data.columns}
            }
        
        p = st.session_state.players[name]
        
        if p['is_bust']:
            st.error("💀 你已经破产了！(爆仓者)")
        
        # --- 信息披露区 ---
        st.info("📢 本轮解锁信息：")
        if st.session_state.round >= 1:
            st.write("**[轮次1消息] 各资产历史算术平均收益率：**")
            st.table(metrics['mean'])
        if st.session_state.round >= 2:
            st.write("**[轮次2消息] 风险警示！各资产标准差（波动率）：**")
            st.table(metrics['std'])
        if st.session_state.round >= 3:
            st.warning("**[轮次3消息] 银行杠杆服务已开启！你可以申请借贷。**")
        if st.session_state.round >= 4:
            st.write("**[轮次4消息] 终极情报：资产收益率相关性矩阵：**")
            st.dataframe(metrics['corr'])

        # --- 仪表盘 ---
        c1, c2, c3 = st.columns(3)
        c1.metric("总资产", f"¥{int(p['net_worth'])}")
        c2.metric("现金", f"¥{int(p['cash'])}")
        c3.metric("负债", f"¥{int(p['loan'])}")

        # --- 操作区 ---
        st.divider()
        col_inv, col_loan = st.columns([2, 1])
        
        with col_inv:
            st.subheader("配置你的投资组合")
            selected_asset = st.selectbox("选择资产", st.session_state.market_data.columns)
            inv_amt = st.number_input("金额", min_value=0, step=5000)
            if st.button("确认买入"):
                if inv_amt <= p['cash']:
                    p['assets'][selected_asset] += inv_amt
                    p['cash'] -= inv_amt
                    st.success(f"已买入 {selected_asset}")
                    st.rerun()
                else:
                    st.error("钱不够了！")

        with col_loan:
            st.subheader("金融杠杆")
            if st.session_state.round >= 3:
                loan_amt = st.number_input("借贷金额", min_value=0, max_value=200000, step=10000)
                if st.button("申请贷款"):
                    p['loan'] += loan_amt
                    p['cash'] += loan_amt
                    st.warning("贷款成功，注意每轮10%的利息支出！")
            else:
                st.write("锁定中，第三轮开放")

        # --- 持仓明细 ---
        st.subheader("我的当前持仓")
        st.write(p['assets'])

# --- 全场排行榜 (底部常驻) ---
st.divider()
st.subheader("🏆 实时战报")
if st.session_state.players:
    data_list = []
    for n, info in st.session_state.players.items():
        data_list.append({
            "姓名": n,
            "总资产": info['net_worth'],
            "状态": "爆仓" if info['is_bust'] else "活跃",
            "现金比例": (info['cash'] / info['net_worth']) if info['net_worth'] > 0 else 0
        })
    df_rank = pd.DataFrame(data_list).sort_values("总资产", ascending=False)
    st.dataframe(df_rank)
    
    if st.session_state.round == 4:
        st.header("🏁 最终评奖")
        col_a, col_b, col_c = st.columns(3)
        col_a.success(f"🥇 优胜者：{df_rank.iloc[0]['姓名']}")
        
        bust_players = [n for n, info in st.session_state.players.items() if info['is_bust']]
        if bust_players:
            col_b.error(f"💀 最快爆仓者：{bust_players[0]}")
        
        conservative = df_rank.sort_values("现金比例", ascending=False).iloc[0]['姓名']
        col_c.info(f"🐢 最保守投资者：{conservative}")
