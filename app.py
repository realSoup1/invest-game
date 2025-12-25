import streamlit as st
import pandas as pd
import numpy as np

# --- 1. 界面样式与强制居中 ---
st.set_page_config(page_title="投资博弈系统", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display:none;}
    .stDataFrame div[data-testid="stTable"] th, .stDataFrame div[data-testid="stTable"] td { text-align: center !important; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 初始化全局数据库 ---
@st.cache_resource
def init_global_db():
    # 修改点1：资产固定为 A-E 5类
    assets = ["A资产", "B资产", "C资产", "D资产", "E资产"]
    return {
        "round": 1,
        "is_settled": False,
        "asset_names": assets,
        # 模拟10年数据
        "market_data": pd.DataFrame(np.random.uniform(-10, 25, size=(10, len(assets))).round(2), columns=assets),
        "players": {}, 
    }

db = init_global_db()

# --- 3. 核心计算与格式化工具 ---
def get_raw_metrics(df):
    """计算原始指标数据，不带样式，方便后续按需切割"""
    if df.empty: return pd.DataFrame(), pd.DataFrame()
    m = pd.DataFrame(index=df.columns)
    m["算术平均"] = df.mean()
    m["标准差(风险)"] = df.std()
    # 相关性矩阵 * 100 方便显示百分比
    corr = df.corr() * 100
    return m, corr

def style_df(df):
    """统一应用百分比格式和居中样式"""
    return df.style.format("{:.2f}%").set_properties(**{'text-align': 'center'})

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("🧧 投资博弈系统")
    role = st.radio("切换视图", ["👨‍🎓 学生入口", "👨‍🏫 老师后台"])
    st.divider()
    st.info(f"进度：第 {db['round']} / 4 轮")
    if db["is_settled"]: st.success("当前轮次已结算")
    if st.button("🔄 刷新数据"): st.rerun()

# --- 5. 老师后台 ---
if role == "👨‍🏫 老师后台":
    st.title("👨‍🏫 教学管理后台")
    if st.text_input("管理密码", type="password") == "8888":
        t1, t2, t3 = st.tabs(["⚙️ 数据配置", "🚀 流程控制", "📊 玩家监控"])
        
        with t1:
            st.subheader("资产收益率矩阵 (10年数据)")
            # 允许老师修改数据，保持5类资产
            db["market_data"] = st.data_editor(db["market_data"], use_container_width=True).round(2)
            
            # 修改点3：老师端始终看到所有信息
            m_raw, c_raw = get_raw_metrics(db["market_data"])
            
            c_view1, c_view2 = st.columns(2)
            with c_view1:
                st.write("**核心指标概览**")
                st.dataframe(style_df(m_raw), use_container_width=True)
            with c_view2:
                st.write("**相关性矩阵**")
                st.dataframe(style_df(c_raw), use_container_width=True)

        with t2:
            if not db["is_settled"]:
                if st.button("🔔 结算本轮游戏 (执行十年复利计算)", use_container_width=True):
                    # --- 复利计算逻辑 ---
                    multipliers = (1 + db["market_data"] / 100).prod()
                    
                    for name, p in db["players"].items():
                        final_portfolio_value = 0
                        for asset in db["asset_names"]:
                            invested = p["current"]["assets"].get(asset, 0)
                            final_portfolio_value += invested * multipliers[asset]
                        
                        total_end_assets = final_portfolio_value + p["current"]["cash"]
                        debt_total = p["current"]["loan"] * 1.10 # 10% 利息
                        final_net_worth = total_end_assets - debt_total
                        
                        moc = final_net_worth / 100000.0
                        
                        p["history"][db["round"]] = {
                            "net_worth": int(final_net_worth),
                            "moc": round(moc, 2),
                            "loan": int(p["current"]["loan"]),
                            "cash": int(p["current"]["cash"])
                        }
                    db["is_settled"] = True
                    st.balloons(); st.rerun()
            else:
                if st.button("➡️ 开启下一轮 (重置所有学生资产至10万现金)", use_container_width=True):
                    if db["round"] < 4:
                        db["round"] += 1
                        db["is_settled"] = False
                        for p in db["players"].values():
                            p["current"] = {"cash": 100000, "loan": 0, "assets": {n: 0 for n in db["asset_names"]}, "submitted": False}
                        st.rerun()
                    else: st.warning("四轮游戏已全部结束")

        with t3:
            if db["players"]:
                monitor_data = []
                for name, p in db["players"].items():
                    if db["round"] in p["history"]:
                        h = p["history"][db["round"]]
                        monitor_data.append({
                            "学生姓名": name, "净资产": h["net_worth"], "负债": h["loan"], 
                            "剩余现金": h["cash"], "10年MOC": h["moc"]
                        })
                if monitor_data:
                    st.table(pd.DataFrame(monitor_data))

# --- 6. 学生端 ---
else:
    st.title(f"🚀 第 {db['round']} 轮投资决策")
    name = st.text_input("您的姓名")
    pwd = st.text_input("登录密码", type="password")
    
    if name and pwd:
        if name not in db["players"]:
            db["players"][name] = {"pwd": pwd, "history": {}, "current": {"cash": 100000, "loan": 0, "assets": {n: 0 for n in db["asset_names"]}, "submitted": False}}
        
        p = db["players"][name]
        if p["pwd"] != pwd: st.error("密码错误"); st.stop()

        # 状态展示
        st.markdown(f"### 📥 个人资产概况")
        c1, c2, c3 = st.columns(3)
        c1.metric("初始可用现金", "¥100,000")
        c2.metric("当前现金余额", f"¥{int(p['current']['cash'])}")
        c3.metric("当前负债(上限20万)", f"¥{int(p['current']['loan'])}")

        # 结算后展示
        if db["is_settled"] and db["round"] in p["history"]:
            res = p["history"][db["round"]]
            st.success(f"本轮结算完成！十年后您的净资产为：¥{res['net_worth']:,}，MOC为：{res['moc']}x")
            
            st.write("**历史各轮 MOC 记录：**")
            h_df = pd.DataFrame([{"轮次": f"第{k}轮", "MOC值": f"{v['moc']}x"} for k, v in p["history"].items()])
            st.table(h_df)
            st.info("等待老师开启下一轮...")
            st.stop()

        if p["current"]["submitted"]:
            st.warning("决策已锁定，请耐心等待老师结算...")
            if st.button("重回决策界面"): p["current"]["submitted"] = False; st.rerun()
        else:
            # --- 修改点2：学生端信息分阶段披露逻辑 ---
            with st.expander("📊 查看市场情报 (信息随轮次解锁)", expanded=True):
                m_raw, c_raw = get_raw_metrics(db["market_data"])
                
                if db["round"] == 1:
                    st.info("💡 第1轮情报：仅展示算术平均收益")
                    # 只取 "算术平均" 列
                    st.dataframe(style_df(m_raw[["算术平均"]]), use_container_width=True)
                
                elif db["round"] == 2:
                    st.info("💡 第2轮情报：新增标准差(风险)数据")
                    # 取 "算术平均" 和 "标准差"
                    st.dataframe(style_df(m_raw[["算术平均", "标准差(风险)"]]), use_container_width=True)
                
                elif db["round"] == 3:
                    st.info("💡 第3轮情报：维持基础数据，开放银行借贷功能")
                    st.dataframe(style_df(m_raw[["算术平均", "标准差(风险)"]]), use_container_width=True)
                
                elif db["round"] == 4:
                    st.info("💡 第4轮情报：终极数据解锁 (包含相关性矩阵)")
                    c_info1, c_info2 = st.columns(2)
                    with c_info1:
                        st.write("**收益与风险**")
                        st.dataframe(style_df(m_raw[["算术平均", "标准差(风险)"]]), use_container_width=True)
                    with c_info2:
                        st.write("**资产相关性**")
                        st.dataframe(style_df(c_raw), use_container_width=True)

            col_l, col_r = st.columns(2)
            with col_l:
                st.subheader("🛠️ 投资操作")
                target = st.selectbox("选择资产", db["asset_names"])
                amt = st.number_input("买入金额", min_value=0, step=5000)
                if st.button("执行买入"):
                    if amt <= p["current"]["cash"]:
                        p["current"]["assets"][target] += amt
                        p["current"]["cash"] -= amt
                        st.rerun()
                    else: st.error("现金不足")
                
                # --- 修改点2续：杠杆功能仅在第3、4轮开放 ---
                if db["round"] >= 3:
                    st.divider()
                    st.markdown("**🏦 银行融资窗口 (年利息10%)**")
                    l_amt = st.number_input("申请借贷 (上限20万)", min_value=0, max_value=200000, step=10000)
                    if st.button("确认融资"):
                        if p["current"]["loan"] + l_amt <= 200000:
                            p["current"]["loan"] += l_amt
                            p["current"]["cash"] += l_amt
                            st.rerun()
                        else: st.error("超过最大贷款限额 20 万元")
                elif db["round"] < 3:
                    st.divider()
                    st.caption("🔒 融资杠杆功能将在第 3 轮开放")

            with col_r:
                st.subheader("📁 当前组合预览")
                pf = pd.DataFrame([{"资产代号": n, "已投金额": int(v)} for n, v in p["current"]["assets"].items() if v > 0])
                st.dataframe(pf, use_container_width=True, hide_index=True)
                if st.button("✅ 锁定并提交当前决策", use_container_width=True):
                    p["current"]["submitted"] = True
                    st.rerun()
