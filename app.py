import streamlit as st
import pandas as pd
import numpy as np
import time

# --- 1. 深度 UI 定制：隐藏系统菜单 ---
# 这段代码会隐藏右上角的三个点菜单、底部的装饰线等
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    [data-testid="stSidebarNav"] {display: none;}
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心：全局共享数据库 (多用户同步关键) ---
@st.cache_resource
def get_global_data():
    """该函数只运行一次，返回一个全场所有用户共享的对象"""
    return {
        "round": 1,
        "asset_names": ["比特币", "A股", "标普500", "美债", "ACWI", "等权组合"],
        "market_data": pd.DataFrame(np.random.uniform(-10, 25, size=(10, 6)).round(2), 
                                   columns=["比特币", "A股", "标普500", "美债", "ACWI", "等权组合"]),
        "players": {}, # 结构: { "姓名": {"pwd": "...", "cash": 100000, "assets": {...}, "loan": 0} }
        "game_active": True
    }

db = get_global_data()

# --- 3. 金融计算函数 ---
def calculate_metrics(df):
    m = pd.DataFrame(index=df.columns)
    m["算术平均(%)"] = df.mean().round(2)
    m["标准差(风险)"] = df.std().round(2)
    m["年化收益(CAGR%)"] = df.apply(lambda x: (np.prod(1 + x/100)**(1/len(x)) - 1) * 100).round(2)
    return m, df.corr().round(2)

# --- 4. 侧边栏：角色切换 ---
with st.sidebar:
    st.title("🧧 投资实战模拟")
    role = st.radio("身份选择", ["👨‍🎓 学生入口", "👨‍🏫 老师后台"])
    st.divider()
    st.write(f"当前阶段: **第 {db['round']} / 4 轮**")
    if st.button("🔄 刷新同步数据"):
        st.rerun()

# --- 5. 老师控制台逻辑 ---
if role == "👨‍🏫 老师后台":
    st.title("👨‍🏫 管理员控制中心")
    master_pwd = st.text_input("请输入管理权限密码", type="password")
    
    if master_pwd == "8888":
        # 老师专属功能：手动刷新、设置
        with st.expander("🛠️ 系统高级设置"):
            if st.button("重启服务器/重置全场游戏"):
                db["players"] = {}
                db["round"] = 1
                st.success("全场数据已清空！")
                st.rerun()

        t1, t2, t3 = st.tabs(["📊 资产与指标", "🎮 进程推演", "👥 玩家监控"])
        
        with t1:
            st.subheader("资产定义与收益率矩阵")
            # 资产重命名
            new_names = st.text_input("资产名称(逗号分隔)", value=",".join(db["asset_names"]))
            if st.button("应用新名称"):
                db["asset_names"] = [n.strip() for n in new_names.split(",")]
                db["market_data"].columns = db["asset_names"]
                st.rerun()
            
            # 收益率编辑
            db["market_data"] = st.data_editor(db["market_data"], use_container_width=True).round(2)
            
            st.divider()
            st.subheader("预估金融指标")
            m_df, c_df = calculate_metrics(db["market_data"])
            st.dataframe(m_df, use_container_width=True)
            st.write("相关性系数：")
            # 移除 .style.background_gradient，改为直接显示数据表格，不再依赖 matplotlib
            st.dataframe(c_df, use_container_width=True)

        with t2:
            st.subheader(f"当前轮次: {db['round']}")
            if st.button("✅ 结算本轮并开启下一轮", use_container_width=True):
                if db["round"] <= 4:
                    rets = db["market_data"].iloc[db["round"]-1]
                    for p in db["players"].values():
                        current_inv = 0
                        for a in db["asset_names"]:
                            p["assets"][a] *= (1 + rets[a]/100)
                            current_inv += p["assets"][a]
                        p["cash"] -= p["loan"] * 0.1
                        p["net_worth"] = p["cash"] + current_inv
                    db["round"] += 1
                    st.balloons()
                    st.rerun()

        with t3:
            st.subheader("全场实时资产明细")
            if db["players"]:
                monitor_df = pd.DataFrame([
                    {"姓名": k, "总资产": int(v['net_worth']), "负债": int(v['loan']), "现金": int(v['cash'])} 
                    for k, v in db["players"].items()
                ]).sort_values("总资产", ascending=False)
                st.dataframe(monitor_df, use_container_width=True)

# --- 6. 学生入口逻辑 ---
else:
    st.title(f"🚀 财富实战营 - 第 {db['round']} 轮")
    
    # --- 登录系统 ---
    col_l, col_r = st.columns(2)
    input_name = col_l.text_input("你的姓名")
    input_pwd = col_r.text_input("个人登录密码", type="password", help="初次登录将自动设定该密码")
    
    if input_name and input_pwd:
        # 判断是否是新玩家
        if input_name not in db["players"]:
            db["players"][input_name] = {
                "pwd": input_pwd,
                "cash": 100000.0, "loan": 0.0, "net_worth": 100000.0,
                "assets": {n: 0.0 for n in db["asset_names"]}
            }
            st.success("新账户注册成功并已登录！")
        
        # 校验密码
        if db["players"][input_name]["pwd"] != input_pwd:
            st.error("密码错误，请重新输入！")
            st.stop()
        
        p = db["players"][input_name]
        
        # --- 学生端 UI ---
        m1, m2, m3 = st.columns(3)
        m1.metric("总资产", f"¥{p['net_worth']:,.2f}")
        m2.metric("可用现金", f"¥{p['cash']:,.2f}")
        m3.metric("本轮利息", f"¥{int(p['loan'] * 0.1)}")

        with st.expander("📉 查看市场信息披露"):
            m_df, c_df = calculate_metrics(db["market_data"])
            if db["round"] == 1: st.table(m_df[["算术平均(%)"]])
            elif db["round"] == 2: st.table(m_df[["算术平均(%)", "标准差(风险)"]])
            elif db["round"] == 3: st.table(m_df[["算术平均(%)", "标准差(风险)"]])
            else:
                st.table(m_df)
                st.write("相关性矩阵:")
                st.dataframe(c_df, use_container_width=True)

        st.divider()
        c_buy, c_portfolio = st.columns([1, 1])
        
        with c_buy:
            st.subheader("交易中心")
            target = st.selectbox("投向资产", db["asset_names"])
            amt = st.number_input("投入金额", min_value=0.0, step=10000.0)
            if st.button("执行买入", use_container_width=True):
                if amt <= p["cash"]:
                    p["assets"][target] += amt
                    p["cash"] -= amt
                    st.success("交易成功")
                    st.rerun()
                else: st.error("现金余额不足")
            
            if db["round"] >= 3:
                l_amt = st.number_input("借贷额度", min_value=0, max_value=200000, step=10000)
                if st.button("确认融资", use_container_width=True):
                    p["loan"] += l_amt
                    p["cash"] += l_amt
                    st.warning("贷款已到账")
        
        with c_portfolio:
            st.subheader("我的组合")
            pf_list = []
            for n in db["asset_names"]:
                v = p["assets"][n]
                w = (v / p["net_worth"] * 100) if p["net_worth"] > 0 else 0
                pf_list.append({"资产": n, "市值": v, "占比": w})
            
            st.dataframe(
                pd.DataFrame(pf_list),
                column_config={
                    "占比": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                    "市值": st.column_config.NumberColumn(format="¥%.0f")
                },
                hide_index=True
            )
