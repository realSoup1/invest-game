import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 界面极致净化 (仅隐藏顶部菜单，保留侧边栏) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    /* 调整侧边栏宽度，确保老师端按钮清晰可见 */
    [data-testid="stSidebar"] { min-width: 250px; }
    /* 美化数据看板 */
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 全局数据库同步 (支撑100人同时在线的关键) ---
@st.cache_resource
def init_global_db():
    # 只要服务器不重启，这个字典在所有人的网页间共享
    return {
        "round": 1,
        "asset_names": ["比特币", "A股", "标普500", "美债", "ACWI", "等权组合"],
        "market_data": pd.DataFrame(np.random.uniform(-10, 20, size=(10, 6)).round(2), 
                                   columns=["比特币", "A股", "标普500", "美债", "ACWI", "等权组合"]),
        "players": {} # { "姓名": {"pwd": "...", "cash": 100000, "assets": {...}, "loan": 0, "net_worth": 100000} }
    }

db = init_global_db()

# --- 3. 金融指标计算逻辑 ---
def get_metrics(df):
    m = pd.DataFrame(index=df.columns)
    m["算术平均(%)"] = df.mean().round(2)
    m["标准差(风险)"] = df.std().round(2)
    m["年化收益(CAGR%)"] = df.apply(lambda x: (np.prod(1 + x/100)**(1/len(x)) - 1) * 100).round(2)
    return m, df.corr().round(2)

# --- 4. 侧边栏身份切换 (已修复无法显示的问题) ---
with st.sidebar:
    st.title("🧧 投资博弈系统")
    # 使用 Radio 进行身份切换，确保老师端入口始终存在
    role = st.radio("身份选择", ["👨‍🎓 学生入口", "👨‍🏫 老师后台"], index=0)
    st.divider()
    st.info(f"游戏进度：第 {db['round']} / 4 轮")
    if st.button("🔄 同步全场数据"):
        st.rerun()

# --- 5. 老师后台逻辑 ---
if role == "👨‍🏫 老师后台":
    st.title("👨‍🏫 老师管理后台")
    master_pwd = st.text_input("请输入管理权限密码", type="password")
    
    if master_pwd == "8888":
        tab_setting, tab_control, tab_rank = st.tabs(["⚙️ 资产设定", "🚀 轮次控制", "📊 玩家监控"])
        
        with tab_setting:
            st.subheader("资产名称修改 (逗号隔开)")
            raw_names = st.text_input("资产列表", value=",".join(db["asset_names"]))
            if st.button("应用新名称"):
                db["asset_names"] = [n.strip() for n in raw_names.split(",")]
                db["market_data"].columns = db["asset_names"]
                st.rerun()
            
            st.divider()
            st.subheader("未来10年收益率设定 (%)")
            db["market_data"] = st.data_editor(db["market_data"], use_container_width=True).round(2)
            
            st.divider()
            st.subheader("当前数据指标预览")
            m_df, c_df = get_metrics(db["market_data"])
            st.dataframe(m_df, use_container_width=True)
            st.write("相关性矩阵：")
            st.dataframe(c_df, use_container_width=True)

        with tab_control:
            st.subheader(f"当前轮次: {db['round']}")
            if st.button("🔥 结算并开启下一轮", use_container_width=True):
                if db["round"] <= 4:
                    # 核心结算逻辑
                    rets = db["market_data"].iloc[db["round"]-1]
                    for p_name, p in db["players"].items():
                        inv_val = 0
                        for a in db["asset_names"]:
                            p["assets"][a] *= (1 + rets[a]/100)
                            inv_val += p["assets"][a]
                        p["cash"] -= p["loan"] * 0.1 # 扣除10%利息
                        p["net_worth"] = p["cash"] + inv_val
                    db["round"] += 1
                    st.balloons()
                    st.rerun()
            
            if st.button("⚠️ 清空全场数据并重置"):
                db["players"] = {}
                db["round"] = 1
                st.warning("所有玩家数据已重置")

        with tab_rank:
            st.subheader("全场玩家资产明细")
            if db["players"]:
                rank_data = pd.DataFrame([
                    {"姓名": k, "总资产": int(v['net_worth']), "负债": int(v['loan']), "现金": int(v['cash'])} 
                    for k, v in db["players"].items()
                ]).sort_values("总资产", ascending=False)
                st.dataframe(rank_data, use_container_width=True)

# --- 6. 学生入口逻辑 ---
else:
    st.title(f"🚀 财富实战营 - 第 {db['round']} 轮")
    
    # 登录模块
    c_l, c_r = st.columns(2)
    s_name = c_l.text_input("请输入姓名")
    s_pwd = c_r.text_input("登录密码", type="password", help="首次登录即为注册")
    
    if s_name and s_pwd:
        # 自动注册/登录
        if s_name not in db["players"]:
            db["players"][s_name] = {
                "pwd": s_pwd, "cash": 100000.0, "loan": 0.0, "net_worth": 100000.0,
                "assets": {n: 0.0 for n in db["asset_names"]}
            }
            st.toast("账户注册并登录成功！")
        
        # 验证密码
        p = db["players"][s_name]
        if p["pwd"] != s_pwd:
            st.error("密码不正确，请重新输入")
            st.stop()
            
        # 仪表盘
        col1, col2, col3 = st.columns(3)
        col1.metric("我的总资产", f"¥{p['net_worth']:,.2f}")
        col2.metric("剩余可用现金", f"¥{p['cash']:,.2f}")
        col3.metric("本轮利息支出", f"¥{int(p['loan'] * 0.1)}")

        # 信息披露 (随轮次解锁)
        with st.expander("📊 市场情报披露 (点击展开)", expanded=True):
            m_df, c_df = get_metrics(db["market_data"])
            if db["round"] == 1: st.table(m_df[["算术平均(%)"]])
            elif db["round"] == 2: st.table(m_df[["算术平均(%)", "标准差(风险)"]])
            elif db["round"] == 3: st.info("🏦 银行窗口已开放，支持贷款融资"); st.table(m_df[["算术平均(%)", "标准差(风险)"]])
            else:
                st.write("终极数据披露：")
                st.table(m_df)
                st.write("相关性系数：")
                st.dataframe(c_df, use_container_width=True)

        # 投资操作
        st.divider()
        op_col, pf_col = st.columns([1, 1])
        with op_col:
            st.subheader("🛒 买入决策")
            target = st.selectbox("选择投向资产", db["asset_names"])
            buy_val = st.number_input("投入金额", min_value=0.0, step=10000.0)
            if st.button("提交买入指令", use_container_width=True):
                if buy_val <= p["cash"]:
                    p["assets"][target] += buy_val
                    p["cash"] -= buy_val
                    st.success(f"已成功配置 {target}")
                    st.rerun()
                else: st.error("现金不足！")
            
            if db["round"] >= 3:
                loan_val = st.number_input("申请贷款额度", min_value=0, max_value=300000, step=10000)
                if st.button("确认融资", use_container_width=True):
                    p["loan"] += loan_val
                    p["cash"] += loan_val
                    st.warning("贷款到账，注意利息风险")

        with pf_col:
            st.subheader("💼 持仓透视")
            pf_df = pd.DataFrame([
                {"资产": n, "市值": v, "占比": (v/p['net_worth']*100 if p['net_worth']>0 else 0)}
                for n, v in p["assets"].items()
            ])
            st.dataframe(pf_df, column_config={
                "占比": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                "市值": st.column_config.NumberColumn(format="¥%.0f")
            }, hide_index=True, use_container_width=True)
