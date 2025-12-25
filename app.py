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
    assets = ["A资产", "B资产", "C资产", "D资产", "E资产"]
    
    # --- 预置的未来10年收益率数据 ---
    data = {
        "A资产": [-7.4, -0.8, 45.7, 46.3, 25.5, -39.5, 26.4, 51.8, 22.5, -24.8],
        "B资产": [-11.3, 21.8, -25.3, 36.1, 27.2, -5.2, -21.6, -11.4, 14.7, 17.4],
        "C资产": [9.5, 19.4, -6.2, 28.9, 16.3, 26.9, -19.4, 24.2, 23.3, 17.5],
        "D资产": [15.0, 31.3, -12.4, 16.2, 12.6, 10.0, -19.3, 20.0, 3.6, 28.6],
        "E资产": [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0]
    }
    
    return {
        "round": 1,
        "is_settled": False,
        "asset_names": assets,
        "market_data": pd.DataFrame(data),
        "players": {}, 
    }

db = init_global_db()

# --- 3. 核心计算与格式化工具 ---
def get_raw_metrics(df):
    """计算原始指标数据"""
    if df.empty: return pd.DataFrame(), pd.DataFrame()
    m = pd.DataFrame(index=df.columns)
    m["算术平均"] = df.mean()
    m["标准差(风险)"] = df.std()
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
            db["market_data"] = st.data_editor(db["market_data"], use_container_width=True).round(2)
            
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
                if st.button("🔔 结算本轮游戏 (计算MOC、波动率与夏普)", use_container_width=True):
                    # --- 复杂的逐年结算逻辑 (为了计算波动率) ---
                    # 获取每年的收益率倍数 (1 + r/100)
                    annual_multipliers = 1 + db["market_data"] / 100
                    
                    for name, p in db["players"].items():
                        # 1. 初始化模拟状态
                        current_holdings = p["current"]["assets"].copy() # 资产持有量
                        current_cash = p["current"]["cash"] # 现金持有量
                        
                        # 记录每年年末的总资产价值 (用于算波动率)
                        # 初始价值 (T=0)
                        portfolio_values = [current_cash + sum(current_holdings.values())]
                        
                        # 2. 逐年模拟 (T=1 到 T=10)
                        for year in range(10):
                            # 获取当年的各资产收益率
                            year_rates = annual_multipliers.iloc[year]
                            
                            # 更新持仓价值
                            for asset in db["asset_names"]:
                                current_holdings[asset] *= year_rates[asset]
                            
                            # 计算当年总值 (假设未投资现金收益为0)
                            total_val = current_cash + sum(current_holdings.values())
                            portfolio_values.append(total_val)
                        
                        # 3. 计算金融指标
                        # 计算10个年度的收益率序列
                        yearly_returns = []
                        for i in range(1, 11):
                            r = (portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                            yearly_returns.append(r)
                        
                        # A. 波动率 (标准差)
                        volatility = np.std(yearly_returns)
                        
                        # B. 年化收益率 CAGR (用于计算夏普)
                        start_val = portfolio_values[0]
                        end_val = portfolio_values[-1]
                        cagr = (end_val / start_val) ** (1/10) - 1 if start_val > 0 else 0
                        
                        # C. 夏普比率 (Rf = 4%)
                        risk_free_rate = 0.04
                        if volatility == 0:
                            sharpe = 0
                        else:
                            sharpe = (cagr - risk_free_rate) / volatility

                        # D. 最终净资产与MOC
                        # 扣除负债和 4% 利息
                        debt_repayment = p["current"]["loan"] * 1.04 
                        final_net_worth = end_val - debt_repayment
                        moc = final_net_worth / 100000.0
                        
                        # 4. 存入历史记录
                        p["history"][db["round"]] = {
                            "net_worth": int(final_net_worth),
                            "moc": round(moc, 2),
                            "volatility": volatility, # 存入波动率
                            "sharpe": round(sharpe, 2), # 存入夏普
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
                            "学生姓名": name, 
                            "净资产": h["net_worth"], 
                            "MOC": h["moc"],
                            "波动率": f"{h['volatility']*100:.2f}%",  # 新增展示
                            "夏普比率": h["sharpe"],                  # 新增展示
                            "负债": h["loan"]
                        })
                if monitor_data:
                    st.write(f"**第 {db['round']} 轮 - 玩家详细表现**")
                    st.dataframe(pd.DataFrame(monitor_data).style.set_properties(**{'text-align': 'center'}), use_container_width=True)

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
            st.success("本轮结算完成！以下是您的十年投资成绩单：")
            
            # --- 结果核心指标展示 ---
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("期末净资产", f"¥{res['net_worth']:,}")
            rc2.metric("投资回报倍数 (MOC)", f"{res['moc']}x")
            rc3.metric("组合波动率 (风险)", f"{res['volatility']*100:.2f}%") # 学生端新增波动率
            
            st.write("**📜 历史战绩记录：**")
            # 历史表格也加上波动率
            h_data = []
            for k, v in p["history"].items():
                h_data.append({
                    "轮次": f"第{k}轮", 
                    "MOC值": f"{v['moc']}x",
                    "波动率": f"{v['volatility']*100:.2f}%"
                })
            st.table(pd.DataFrame(h_data))
            
            st.info("请等待老师开启下一轮...")
            st.stop()

        if p["current"]["submitted"]:
            st.warning("决策已锁定，请耐心等待老师结算...")
            if st.button("重回决策界面"): p["current"]["submitted"] = False; st.rerun()
        else:
            with st.expander("📊 查看市场情报 (信息随轮次解锁)", expanded=True):
                m_raw, c_raw = get_raw_metrics(db["market_data"])
                
                if db["round"] == 1:
                    st.info("💡 第1轮情报：仅展示算术平均收益")
                    st.dataframe(style_df(m_raw[["算术平均"]]), use_container_width=True)
                
                elif db["round"] == 2:
                    st.info("💡 第2轮情报：新增标准差(风险)数据")
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
                
                # --- 杠杆功能 ---
                if db["round"] >= 3:
                    st.divider()
                    # 修改点：利率改为 4%
                    st.markdown("**🏦 银行融资窗口 (年利息 4%)**")
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
