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

# --- THEMES & TARGETED STYLING ---
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
    
    h1, h2, h3, p, [data-testid="stMetricLabel"] {{ 
        color: #00BFFF !important; 
        text-shadow: 2px 2px 4px black !important;
    }}

    /* ONLY TARGET THE 'PUSH ME' BUTTON USING ITS KEY */
    div.st-key-main_push_button > button {{
        color: #FF0000 !important;
        background-color: #FFFFFF !important;
        font-weight: 900 !important;
        font-size: 18px !important;
        width: 150px !important;
        height: 150px !important;
        border-radius: 50% !important;
        border: 5px solid #FF0000 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: none !important;
        text-shadow: none !important;
    }}
    
    div.st-key-main_push_button > button p {{
        margin: 0 !important;
        color: #FF0000 !important;
        text-shadow: none !important;
    }}

    div.st-key-main_push_button > button:hover {{
        background-color: #FF0000 !important;
        color: #FFFFFF !important;
    }}
    
    div.st-key-main_push_button > button:hover p {{ color: #FFFFFF !important; }}

    /* LEAVE SIDEBAR BUTTONS NORMAL */
    section[data-testid="stSidebar"] div.stButton > button {{
        width: auto !important;
        height: auto !important;
        border-radius: 4px !important;
        padding: 0.25rem 0.75rem !important;
    }}

    .stDataFrame {{ background: white; border-radius: 10px; padding: 5px; }}
    </style>
    """, unsafe_allow_html=True)

st.title("🎯 Chris's Command Center")

with st.sidebar:
    st.markdown("## 📊 Options Screener")
    # Added a unique key "logout_btn" to keep it separate
    if st.button("Log Out", key="logout_btn"):
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

def scan_logic(ticker_list):
    results = []
    total = len(ticker_list)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, t in enumerate(ticker_list):
        status_text.text(f"Scanning {i+1} of {total}: {t}")
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
        progress_bar.progress((i + 1) / total)
    
    status_text.text(f"Scan Complete.")
    return results

st.write("### Watchlist Scan")
# Added the unique key 'main_push_button' for the CSS to find
if st.button('PUSH ME', key="main_push_button"):
    tickers = pd.read_csv('watchlist.txt', header=None)[0].tolist()
    res = scan_logic(tickers)
    if res: st.session_state['scan_results'] = res

if 'scan_results' in st.session_state:
    st.dataframe(pd.DataFrame(st.session_state['scan_results']), 
                 column_config={"Ticker": st.column_config.LinkColumn("Ticker", display_text=r"https://finance.yahoo.com/quote/(.*)")}, 
                 hide_index=True, use_container_width=True)

st.markdown('<div style="background: rgba(0,0,0,0.7); padding: 20px; border-radius: 15px; border: 1px solid #00BFFF; margin-top: 30px;">', unsafe_allow_html=True)
st.write("### 🔍 Manual Ticker Analysis")
manual_ticker = st.text_input("Enter symbol:", "").upper()
if manual_ticker:
    if st.button(f"Analyze {manual_ticker}", key="manual_check_btn"):
        res = scan_logic([manual_ticker])
        if res: st.session_state['scan_results'] = res
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
