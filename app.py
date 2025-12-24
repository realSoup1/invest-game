import streamlit as st
import pandas as pd
import numpy as np

# --- 页面基础配置 ---
st.set_page_config(page_title="财富博弈实战营", layout="wide", initial_sidebar_state="expanded")

# --- 自定义 CSS 提升美观度 ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .portfolio-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border-left: 5px solid #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

# --- 初始化全局状态 ---
if 'round' not in st.session_state:
    st.session_state.round = 1
if 'players' not in st.session_state:
    st.session_state.players = {}
if 'asset_names' not in st.session_state:
    st.session_state.asset_names = ["比特币", "A股", "标普500", "美债", "ACWI", "等权组合"]
if 'market_data' not in st.session_state:
    # 预设数据，保留两位小数
    data = np.random.uniform(-20, 40, size=(10, 6)).round(2)
    st.session_state.market_data = pd.DataFrame(data, columns=st.session_state.asset_names)

# --- 金融指标计算 ---
def get_metrics(df):
    metrics = pd.DataFrame({
        "算术平均(%)": df.mean().round(2),
        "标准差(风险)": df.std().round(2),
        "年化收益(CAGR%)": (df.apply(lambda x: (np.prod(1 + x/100)**(1/len(x)) - 1) * 100)).round(2)
    })
    return metrics

# --- 侧边栏角色切换 ---
with st.sidebar:
    st.title("🧧 财富博弈系统")
    role = st.selectbox("我的身份", ["👨‍🎓 学生端", "👨‍🏫 老师控制台"])
    st.divider()
    if st.button("🔄 刷新全场数据"):
        st.rerun()

# ----------------- 老师控制台 -----------------
if "老师控制台" in role:
    st.title("👨‍🏫 教学后台管理")
    pwd = st.text_input("管理密码", type="password")
    
    if pwd == "8888":
        t1, t2 = st.tabs(["💡 资产名称与数据设定", "🎮 进程控制"])
        
        with t1:
            st.subheader("1. 自定义资产名称")
            new_names = []
            cols = st.columns(3)
            for i, old_name in enumerate(st.session_state.asset_names):
                with cols[i % 3]:
                    name = st.text_input(f"资产 {i+1} 名称", value=old_name)
                    new_names.append(name)
            
            if st.button("确认修改名称"):
                st.session_state.asset_names = new_names
                st.session_state.market_data.columns = new_names
                st.success("资产名称已同步更新！")
                st.rerun()

            st.divider()
            st.subheader("2. 设定未来10年收益率 (%)")
            st.session_state.market_data = st.data_editor(st.session_state.market_data, num_rows="fixed").round(2)
            
        with t2:
            st.subheader(f"当前进度：第 {st.session_state.round} / 4 轮")
            c1, c2 = st.columns(2)
            if c1.button("🔥 结算并进入下一轮", use_container_width=True):
                if st.session_state.round <= 4:
                    year_idx = st.session_state.round - 1
                    round_rets = st.session_state.market_data.iloc[year_idx]
                    for p in st.session_state.players.values():
                        # 计算资产变动
                        current_inv = 0
                        for asset in st.session_state.asset_names:
                            p['assets'][asset] *= (1 + round_rets[asset]/100)
                            current_inv += p['assets'][asset]
                        # 利息与净值更新
                        p['cash'] -= p['loan'] * 0.1
                        p['net_worth'] = p['cash'] + current_inv
                        if p['net_worth'] < 0: p['is_bust'] = True
                    st.session_state.round += 1
                    st.balloons()
                    st.rerun()

            if c2.button("🚫 重置整个游戏", use_container_width=True):
                st.session_state.players = {}
                st.session_state.round = 1
                st.rerun()

# ----------------- 学生端 -----------------
else:
    st.title(f"🚀 投资实战营 - 第 {st.session_state.round} 轮")
    name = st.text_input("输入你的姓名进入市场", key="student_name")
    
    if name:
        if name not in st.session_state.players:
            st.session_state.players[name] = {
                "cash": 100000.0, "loan": 0.0, "net_worth": 100000.0,
                "is_bust": False, "assets": {n: 0.0 for n in st.session_state.asset_names}
            }
        
        p = st.session_state.players[name]
        
        if p['is_bust']:
            st.error("💀 您已爆仓！资产净值归零，请反思杠杆风险。")

        # --- 核心仪表盘 ---
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("当前总资产", f"¥{p['net_worth']:,.2f}")
        col_m2.metric("可用现金", f"¥{p['cash']:,.2f}")
        col_m3.metric("总负债", f"¥{p['loan']:,.2f}", delta="-10% 利息/轮", delta_color="inverse")

        # --- 信息披露卡片 ---
        with st.expander("📊 查看本轮市场内参", expanded=True):
            metrics_df = get_metrics(st.session_state.market_data)
            show_cols = []
            if st.session_state.round >= 1: show_cols.append("算术平均(%)")
            if st.session_state.round >= 2: show_cols.append("标准差(风险)")
            if st.session_state.round >= 4:
                st.write("**相关性矩阵：**")
                st.dataframe(st.session_state.market_data.corr().round(2), use_container_width=True)
            st.table(metrics_df[show_cols])

        # --- 交易操作区 ---
        st.subheader("🎯 资产配置决策")
        t_col1, t_col2 = st.columns([2, 1])
        
        with t_col1:
            asset_choice = st.segmented_control("选择投向", st.session_state.asset_names)
            buy_amt = st.number_input("拟投入金额", min_value=0.0, step=5000.0)
            if st.button("确认买入资产", use_container_width=True):
                if buy_amt <= p['cash']:
                    p['assets'][asset_choice] += buy_amt
                    p['cash'] -= buy_amt
                    st.success(f"成功买入 {asset_choice}")
                    st.rerun()
                else:
                    st.error("现金不足，请先融资！")

        with t_col2:
            if st.session_state.round >= 3:
                loan_req = st.number_input("融资额度", min_value=0, max_value=200000, step=10000)
                if st.button("申请银行贷款", use_container_width=True):
                    p['loan'] += loan_req
                    p['cash'] += loan_req
                    st.warning("贷款已到账")
            else:
                st.info("🏦 银行信贷窗口在第三轮开放")

        # --- 美化后的持仓展示 ---
        st.divider()
        st.subheader("💼 我的投资组合明细")
        
        # 将持仓转换为DataFrame进行美化展示
        portfolio_data = []
        for asset in st.session_state.asset_names:
            val = p['assets'][asset]
            weight = (val / p['net_worth'] * 100) if p['net_worth'] > 0 else 0
            portfolio_data.append({"资产名称": asset, "当前市值": round(val, 2), "配置比例(%)": round(weight, 2)})
        
        pdf = pd.DataFrame(portfolio_data)
        
        # 使用 Streamlit 的列配置功能增加进度条效果
        st.dataframe(
            pdf,
            column_config={
                "配置比例(%)": st.column_config.ProgressColumn(
                    "仓位权重",
                    help="该资产占总资产的百分比",
                    format="%f%%",
                    min_value=0,
                    max_value=100,
                ),
                "当前市值": st.column_config.NumberColumn(format="¥%.2f")
            },
            hide_index=True,
            use_container_width=True
        )

# --- 底部排行榜 ---
if st.session_state.players:
    with st.sidebar:
        st.divider()
        st.subheader("🏆 实时财富榜")
        rank_list = pd.DataFrame([
            {"姓名": k, "总资产": int(v['net_worth'])} 
            for k, v in st.session_state.players.items()
        ]).sort_values("总资产", ascending=False)
        st.dataframe(rank_list, hide_index=True)
