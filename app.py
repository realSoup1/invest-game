import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 基础配置与样式 ---
st.set_page_config(page_title="投资复利博弈模拟器", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    [data-testid="stExpander"] { background-color: #f0f2f6; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 初始化全局变量 ---
if 'round' not in st.session_state:
    st.session_state.round = 1
if 'players' not in st.session_state:
    st.session_state.players = {}
if 'asset_names' not in st.session_state:
    st.session_state.asset_names = ["比特币", "A股", "标普500", "美债", "ACWI", "等权组合"]
if 'market_data' not in st.session_state:
    # 初始化随机收益率数据
    init_data = np.random.uniform(-15, 30, size=(10, 6)).round(2)
    st.session_state.market_data = pd.DataFrame(init_data, columns=st.session_state.asset_names)

# --- 3. 核心计算函数 ---
def get_full_metrics(df):
    """计算所有金融指标"""
    metrics = pd.DataFrame(index=df.columns)
    # 算术平均
    metrics["算术平均收益(%)"] = df.mean().round(2)
    # 标准差
    metrics["标准差(波动率)"] = df.std().round(2)
    # 年化收益率 (Geometric Mean)
    metrics["年化收益(CAGR%)"] = df.apply(
        lambda x: (np.prod(1 + x/100)**(1/len(x)) - 1) * 100
    ).round(2)
    # 相关性矩阵
    corr_matrix = df.corr().round(2)
    return metrics, corr_matrix

# --- 4. 侧边栏 ---
with st.sidebar:
    st.header("🎮 游戏中心")
    role = st.selectbox("身份切换", ["👨‍🎓 学生端", "👨‍🏫 老师控制台"])
    st.divider()
    st.info(f"当前轮次: 第 {st.session_state.round} / 4 轮")
    if st.button("🔄 强制刷新"): st.rerun()

# --- 5. 老师控制台逻辑 ---
if role == "老师控制台":
    st.title("👨‍🏫 老师后台管理系统")
    pwd = st.text_input("请输入管理密码", type="password")
    
    if pwd == "8888":
        tab_setting, tab_metrics, tab_control = st.tabs(["⚙️ 数据设定", "📊 实时指标预览", "🚀 进程管理"])
        
        with tab_setting:
            st.subheader("1. 修改资产名称")
            new_names = []
            cols = st.columns(3)
            for i, old_name in enumerate(st.session_state.asset_names):
                with cols[i % 3]:
                    n = st.text_input(f"资产 {i+1}", value=old_name, key=f"name_{i}")
                    new_names.append(n)
            
            if st.button("同步更名"):
                # 如果改名，需更新数据表列名和已有玩家的持仓键值
                old_names = st.session_state.asset_names
                st.session_state.asset_names = new_names
                st.session_state.market_data.columns = new_names
                # 更新玩家持仓中的Key (防止报错)
                for p in st.session_state.players.values():
                    new_assets = {}
                    for k, v in zip(new_names, p['assets'].values()):
                        new_assets[k] = v
                    p['assets'] = new_assets
                st.success("更名成功！")
                st.rerun()

            st.divider()
            st.subheader("2. 设定未来10年收益率 (%)")
            st.session_state.market_data = st.data_editor(
                st.session_state.market_data, 
                num_rows="fixed",
                use_container_width=True
            ).round(2)

        with tab_metrics:
            st.subheader("📈 自动化金融指标分析 (上帝视角)")
            m_df, c_df = get_full_metrics(st.session_state.market_data)
            
            c1, c2 = st.columns([1, 1])
            with c1:
                st.write("**收益与风险指标**")
                st.dataframe(m_df, use_container_width=True)
            with c2:
                st.write("**年化收益率排行榜**")
                st.bar_chart(m_df["年化收益(CAGR%)"])
            
            st.write("**资产相关性矩阵**")
            st.dataframe(c_df.style.background_gradient(cmap='RdYlGn', axis=None), use_container_width=True)

        with tab_control:
            st.subheader("轮次推进")
            curr_r = st.session_state.round
            if st.button(f"🔊 结算第 {curr_r} 轮并进入下一轮", use_container_width=True):
                if curr_r <= 4:
                    # 按照设定好的收益率进行结算
                    rets = st.session_state.market_data.iloc[curr_r - 1]
                    for p in st.session_state.players.values():
                        # 资产增值
                        inv_sum = 0
                        for a in st.session_state.asset_names:
                            p['assets'][a] *= (1 + rets[a]/100)
                            inv_sum += p['assets'][a]
                        # 扣利息
                        p['cash'] -= p['loan'] * 0.1
                        p['net_worth'] = p['cash'] + inv_sum
                    st.session_state.round += 1
                    st.balloons()
                    st.rerun()
            
            if st.button("🗑️ 清空所有数据重新开始"):
                st.session_state.players = {}
                st.session_state.round = 1
                st.rerun()

# --- 6. 学生端逻辑 ---
else:
    st.title(f"💰 财富实战：第 {st.session_state.round} 轮")
    s_name = st.text_input("请输入姓名登录", key="s_login")
    
    if s_name:
        if s_name not in st.session_state.players:
            st.session_state.players[s_name] = {
                "cash": 100000.0, "loan": 0.0, "net_worth": 100000.0,
                "assets": {n: 0.0 for n in st.session_state.asset_names}
            }
        
        p = st.session_state.players[s_name]
        
        # 仪表盘
        m1, m2, m3 = st.columns(3)
        m1.metric("总资产 (Net Worth)", f"¥{p['net_worth']:,.2f}")
        m2.metric("可用现金", f"¥{p['cash']:,.2f}")
        m3.metric("当前负债", f"¥{p['loan']:,.2f}", delta="-10% 利息/轮")

        # 信息披露
        m_df, c_df = get_full_metrics(st.session_state.market_data)
        with st.expander("🔍 市场情报局 (分阶段解锁)", expanded=True):
            if st.session_state.round == 1:
                st.write("**本轮已知：算术平均收益率**")
                st.table(m_df[["算术平均收益(%)"]])
            elif st.session_state.round == 2:
                st.write("**本轮已知：收益率 + 标准差(波动)**")
                st.table(m_df[["算术平均收益(%)", "标准差(波动率)"]])
            elif st.session_state.round == 3:
                st.write("**本轮已知：收益率 + 标准差 + 杠杆开启**")
                st.table(m_df[["算术平均收益(%)", "标准差(波动率)"]])
            else:
                st.write("**最终轮已知：全维度指标 + 相关性矩阵**")
                st.table(m_df)
                st.write("相关性矩阵:")
                st.dataframe(c_df, use_container_width=True)

        # 操作区
        st.divider()
        op_col, pf_col = st.columns([1, 1])
        
        with op_col:
            st.subheader("🛒 投资决策")
            target = st.radio("选择资产", st.session_state.asset_names, horizontal=True)
            amt = st.number_input("投入金额", min_value=0.0, step=10000.0)
            if st.button("确认买入", use_container_width=True):
                if amt <= p['cash']:
                    p['assets'][target] += amt
                    p['cash'] -= amt
                    st.success(f"成功买入 {target}")
                    st.rerun()
                else:
                    st.error("余额不足！")
            
            if st.session_state.round >= 3:
                l_amt = st.number_input("融资贷款金额", min_value=0, max_value=200000, step=10000)
                if st.button("向银行借款", use_container_width=True):
                    p['loan'] += l_amt
                    p['cash'] += l_amt
                    st.warning("贷款成功")

        with pf_col:
            st.subheader("💼 我的持仓结构")
            # 转换持仓数据
            p_data = []
            for n in st.session_state.asset_names:
                v = p['assets'][n]
                w = (v / p['net_worth'] * 100) if p['net_worth'] > 0 else 0
                p_data.append({"资产": n, "价值": v, "比例": w})
            
            pdf = pd.DataFrame(p_data)
            st.dataframe(
                pdf,
                column_config={
                    "比例": st.column_config.ProgressColumn("分配比例", format="%.1f%%", min_value=0, max_value=100),
                    "价值": st.column_config.NumberColumn(format="¥%.2f")
                },
                hide_index=True, use_container_width=True
            )

# --- 7. 全场排名 ---
if st.session_state.players:
    st.divider()
    st.subheader("🏆 全场实时战报")
    rank_df = pd.DataFrame([
        {"姓名": k, "总资产": v['net_worth'], "负债": v['loan']} 
        for k, v in st.session_state.players.items()
    ]).sort_values("总资产", ascending=False)
    st.dataframe(rank_df, use_container_width=True, hide_index=True)
