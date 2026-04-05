import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm
import hmac

st.set_page_config(page_title="Chris's Covered Call Screener", layout="wide")

# --- PASSWORD LOGIC ---
def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.title("🔐 Secure Access Required")
    st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

# --- DASHBOARD ---
st.title("🎯 Chris's Command Center")

with st.sidebar:
    st.markdown("## 📊 Navigation")
    if st.button("Log Out"):
        st.session_state["password_correct"] = False
        st.rerun()

m1, m2, m3, m4 = st.columns(4)
try:
    vix = yf.Ticker("^VIX").fast_info['lastPrice']
    spy = yf.Ticker("SPY").fast_info['lastPrice']
    qqq = yf.Ticker("QQQ").fast_info['lastPrice']
    dia = yf.Ticker("DIA").fast_info['lastPrice']
    with m1: st.metric("VIX", f"{vix:.2f}")
    with m2: st.metric("SPY", f"${spy:.2f}")
    with m3: st.metric("QQQ", f"${qqq:.2f}")
    with m4: st.metric("DIA", f"${dia:.2f}")
except:
    st.info("Fetching market data...")

def calculate_delta(cp, strike, days, iv):
    if days <= 0 or iv <= 0: return 0
    t = days / 365.0
    d1 = (np.log(cp / strike) + (0.5 * iv**2) * t) / (iv * np.sqrt(t))
    return norm.cdf(d1)

if st.button('🚀 Run All-Market Scan'):
    tickers = pd.read_csv('watchlist.txt', header=None)[0].tolist()
    results = []
    progress = st.progress(0)
    for i, t in enumerate(tickers[:40]):
        try:
            tk = yf.Ticker(t)
            cp = tk.fast_info['lastPrice']
            days = (pd.to_datetime(tk.options[0]) - pd.Timestamp.now()).days
            opts = tk.option_chain(tk.options[0]).calls
            for _, row in opts.iterrows():
                delta = calculate_delta(cp, row['strike'], days, row['impliedVolatility'])
                if 0.20 <= delta <= 0.30:
                    yield_val = (row['lastPrice'] / cp) * 100
                    status = "🟨 MODERATE"
                    if row['impliedVolatility'] > 0.45: status = "🟥 HIGH VOL"
                    elif yield_val > 1.5: status = "🟩 HIGH YIELD"
                    results.append({'Ticker': f"https://finance.yahoo.com/quote/{t}", 'Price': f"${cp:.2f}", 'Strike': f"${row['strike']:.2f}", 'Delta': f"{delta:.2f}", 'Yield': f"{yield_val:.2f}%", 'Status': status})
                    break
        except: continue
        progress.progress((i + 1) / 40)
    
    if results:
        st.dataframe(pd.DataFrame(results), column_config={"Ticker": st.column_config.LinkColumn("Ticker", display_text=r"https://finance.yahoo.com/quote/(.*)")}, hide_index=True, use_container_width=True, height=600)
