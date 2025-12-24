import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 界面美化与净化 ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stSidebar"] { min-width: 250px; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 全局共享数据库 ---
@st.cache_resource
def init_global_db():
    initial_assets = ["A", "B", "C", "D", "E"]
    return {
        "round": 1,
        "asset_names": initial_assets,
        "market_data": pd.DataFrame(
            np.random.uniform(-10, 20, size=(10, len(initial_assets))).round(2), 
            columns=initial_assets
        ),
        "players": {}
    }

db = init_global_db()

# --- 3. 金融指标计算 (修复相关性计算逻辑) ---
def get_metrics(df):
    if df.empty or len(df.columns) == 0:
        return pd.DataFrame(), pd.DataFrame()
    
    # 计算基础指标
    m = pd.DataFrame(index=df.columns)
    m["算术平均(%)"] = df.mean().round(2)
    m["标准差(风险)"] = df.std().round(2)
    m["年化收益(CAGR%)"] = df.apply(lambda x: (np.prod(1 + x/100)**(1/len(x)) - 1) * 100).round(2)
    
    # 计算相关性矩阵
    corr_matrix = df.corr().round(2)
    return m, corr_matrix

# --- 4. 侧边栏身份切换 ---
with st.sidebar:
    st.title("🧧 投资博弈系统")
    role = st.radio("身份选择", ["👨‍🎓 学生入口", "👨‍🏫 老师后台"], index=0)
    st.divider()
    st.info(f"游戏进度：第 {db['round']} / 4 轮")
    if st.button("🔄 同步刷新全场"):
        st.rerun()

# --- 5. 老师后台逻辑 (修复模块显示问题) ---
if role == "👨‍🏫 老师后台":
    st.title("👨‍🏫 老师管理后台")
    master_pwd = st.text_input("请输入管理权限密码", type="password")
    
    if master_pwd == "8888":
        tab_setting, tab_control, tab_rank = st.tabs(["⚙️ 资产维度增减", "🚀 轮次控制", "📊 玩家监控"])
        
        with tab_setting:
            st.subheader("🛠️ 资产类别管理")
            
            # 增加资产
            col_add1, col_add2 = st.columns([2, 1])
            new_asset_name = col_add1.text_input("输入新资产名称", placeholder="例如：黄金")
            if col_add2.button("➕ 添加资产") and new_asset_name:
                if new_asset_name not in db["asset_names"]:
                    db["asset_names"].append(new_asset_name)
                    # 给新资产随机生成10年收益数据
                    db["market_data"][new_asset_name] = np.random.uniform(-5, 15, size=10).round(2)
                    # 同播同步存量玩家持仓
                    for p in db["players"].values():
                        p["assets"][new_asset_name] = 0.0
                    st.success(f"已添加资产：{new_asset_name}")
                    st.rerun()

            # 删除资产
            st.write("---")
            asset_to_del = st.selectbox("选择要移除的资产", db["asset_names"])
            if st.button("➖ 确认删除该资产"):
                if len(db["asset_names"]) > 1:
                    db["asset_names"].remove(asset_to_del)
                    db["market_data"] = db["market_data"].drop(columns=[asset_to_del])
                    for p in db["players"].values():
                        if asset_to_del in p["assets"]:
                            del p["assets"][asset_to_del]
                    st.warning(f"已移除资产：{asset_to_del}")
                    st.rerun()
                else:
                    st.error("至少需要保留一个资产类别！")

            st.divider()
            st.subheader("未来10年收益率明细 (%)")
            db["market_data"] = st.data_editor(db["market_data"], use_container_width=True).round(2)
            
            # --- 关键修复：确保此模块在老师端始终显示 ---
            st.divider()
            st.subheader("📈 实时金融指标预览")
            m_df, c_df = get_metrics(db["market_data"])
            
            col_m1, col_m2 = st.columns([1, 1])
            with col_m1:
                st.write("**核心指标 (平均/风险/年化)**")
                st.dataframe(m_df, use_container_width=True)
            with col_m2:
                st.write("**相关性矩阵 (Correlation)**")
                st.dataframe(c_df, use_container_width=True)

        with tab_control:
            st.subheader(f"当前轮次: {db['round']}")
            if st.button("🔥 结算并开启下一轮", use_container_width=True):
                if db["round"] <= 4:
                    rets = db["market_data"].iloc[db["round"]-1]
                    for p_name, p in db["players"].items():
                        inv_val = 0
                        for a in db["asset_names"]:
                            p["assets"][a] *= (1 + rets[a]/100)
                            inv_val += p["assets"][a]
                        p["cash"] -= p["loan"] * 0.1
                        p["net_worth"] = p["cash"] + inv_val
                    db["round"] += 1
                    st.balloons()
                    st.rerun()
            
            if st.button("⚠️ 清空全场数据并重置"):
                db["players"] = {}
                db["round"] = 1
                st.warning("所有玩家数据已重置")

        with tab_rank:
            st.subheader("全场排行")
            if db["players"]:
                rank_data = pd.DataFrame([
                    {"姓名": k, "总资产": int(v['net_worth']), "负债": int(v['loan']), "现金": int(v['cash'])} 
                    for k, v in db["players"].items()
                ]).sort_values("总资产", ascending=False)
                st.dataframe(rank_data, use_container_width=True)

# --- 6. 学生入口逻辑 ---
else:
    st.title(f"🚀 财富实战营 - 第 {db['round']} 轮")
    c_l, c_r = st.columns(2)
    s_name = c_l.text_input("请输入姓名")
    s_pwd = c_r.text_input("登录密码", type="password")
    
    if s_name and s_pwd:
        if s_name not in db["players"]:
            db["players"][s_name] = {
                "pwd": s_pwd, "cash": 100000.0, "loan": 0.0, "net_worth": 100000.0,
                "assets": {n: 0.0 for n in db["asset_names"]}
            }
        
        p = db["players"][s_name]
        if p["pwd"] != s_pwd:
            st.error("密码错误")
            st.stop()
            
        m1, m2, m3 = st.columns(3)
        m1.metric("总资产", f"¥{p['net_worth']:,.2f}")
        m2.metric("现金", f"¥{p['cash']:,.2f}")
        m3.metric("利息支出", f"¥{int(p['loan'] * 0.1)}")

        with st.expander("📊 市场情报披露", expanded=True):
            m_df, c_df = get_metrics(db["market_data"])
            if db["round"] == 1: st.table(m_df[["算术平均(%)"]])
            elif db["round"] == 2: st.table(m_df[["算术平均(%)", "标准差(风险)"]])
            elif db["round"] == 3: st.info("🏦 融资服务已开启"); st.table(m_df[["算术平均(%)", "标准差(风险)"]])
            else:
                st.table(m_df)
                st.write("相关性系数：")
                st.dataframe(c_df, use_container_width=True)

        st.divider()
        op_col, pf_col = st.columns([1, 1])
        with op_col:
            st.subheader("🛒 买入决策")
            target = st.selectbox("选择资产", db["asset_names"])
            buy_val = st.number_input("投入金额", min_value=0.0, step=10000.0)
            if st.button("提交买入指令", use_container_width=True):
                if buy_val <= p["cash"]:
                    p["assets"][target] += buy_val
                    p["cash"] -= buy_val
                    st.success(f"已配置 {target}")
                    st.rerun()
                else: st.error("现金不足")
            
            if db["round"] >= 3:
                loan_val = st.number_input("贷款额度", min_value=0, max_value=300000, step=10000)
                if st.button("确认融资", use_container_width=True):
                    p["loan"] += loan_val
                    p["cash"] += loan_val
                    st.rerun()

        with pf_col:
            st.subheader("💼 我的持仓")
            pf_df = pd.DataFrame([
                {"资产": n, "市值": v, "占比": (v/p['net_worth']*100 if p['net_worth']>0 else 0)}
                for n, v in p["assets"].items()
            ])
            st.dataframe(pf_df, column_config={
                "占比": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                "市值": st.column_config.NumberColumn(format="¥%.0f")
            }, hide_index=True, use_container_width=True)
