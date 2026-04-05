import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm
import hmac

st.set_page_config(page_title="Chris's Covered Call Screener", layout="wide")

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
    return False

if not check_password():
    st.stop()

# --- CUSTOM THEMING (CLEAN BUTTON FIX) ---
bg_img = "https://raw.githubusercontent.com/czav1971/covered-call-screener/main/stock%20market%20gurus.png"

st.markdown(f"""
    <style>
    .stApp {{
        background-color: #0e1117;
        background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), 
                          url('{bg_img}');
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        background-attachment: fixed;
    }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
    
    /* Blue Labels with slight shadow for readability on busy background */
    h1, h2, h3, p, [data-testid="stMetricLabel"] {{ 
        color: #00BFFF !important; 
        text-shadow: 2px 2px 4px black;
    }}
    
    /* CLEAN BLUE BUTTON - NO SHADOW */
    .stButton>button {{
        color: #0000FF !important;
        background-color: white !important;
        font-weight: bold;
        width: 100%;
        border: none !important;
        box-shadow: none !important; /* Removes outer shadow */
        text-shadow: none !important; /* Removes lettering shadow */
    }}

    .stDataFrame {{ 
        background: white; 
        border-radius: 10px; 
        padding: 5px; 
    }}
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Chris's Command Center")

with st.sidebar:
    st.markdown("## 📊 Options Screener")
    if st.button("Log Out"):
        st.session_state["password_correct"] = False
        st.rerun()

m1, m2, m3, m4 = st.columns(4)

def get_metric_data(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    current = info['lastPrice']
    prev_close = ticker.info.get('previousClose', current)
    change = current - prev_close
    return current, change

try:
    vix_p, _ = get_metric_data("^VIX")
    spy_p, spy_c = get_metric_data("SPY")
    qqq_p, qqq_c = get_metric_data("QQQ")
    dia_p, dia_c = get_metric_data("DIA")

    with m1: st.metric("VIX", f"{vix_p:.2f}")
    with m2: st.metric("SPY", f"${spy_p:.2f}", f"{spy_c:.2f}")
    with m3: st.metric("QQQ", f"${qqq_p:.2f}", f"{qqq_c:.2f}")
    with m4: st.metric("DIA", f"${dia_p:.2f}", f"{dia_c:.2f}")
except:
    st.info("Syncing live market data...")

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
        st.dataframe(
            pd.DataFrame(results), 
            column_config={"Ticker": st.column_config.LinkColumn("Ticker", display_text=r"https://finance.yahoo.com/quote/(.*)")}, 
            hide_index=True, 
            use_container_width=True,
            height=400 
        )
