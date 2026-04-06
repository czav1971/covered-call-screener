import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm
import hmac
import time

st.set_page_config(page_title="Chris's S&P 500 Execution Engine", layout="wide")

# --- AUTH ---
def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else: st.session_state["password_correct"] = False
    if st.session_state.get("password_correct", False): return True
    st.title("🔐 Secure Access Required")
    st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
    return False

if not check_password(): st.stop()

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url('https://raw.githubusercontent.com/czav1971/covered-call-screener/main/stock%20market%20gurus.png'); background-size: contain; background-attachment: fixed; }
    h1, h2, h3, p, [data-testid="stMetricLabel"] { color: #00BFFF !important; text-shadow: 2px 2px 4px black !important; }
    .status-yellow { color: #FFFF00 !important; font-weight: bold; font-size: 1.1rem; }
    div.st-key-main_push_button > button { color: #FF0000 !important; background-color: #FFFFFF !important; width: 150px !important; height: 150px !important; border-radius: 50% !important; border: 5px solid #FF0000 !important; font-weight: 900 !important; }
    div.st-key-main_push_button > button p { color: #FF0000 !important; }
    .stDataFrame { background: white; border-radius: 10px; padding: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE LOGIC ---
def calculate_delta(cp, strike, days, iv):
    if days <= 0 or iv <= 0: return 0
    t = days / 365.0
    d1 = (np.log(cp / strike) + (0.5 * iv**2) * t) / (iv * np.sqrt(t))
    return norm.cdf(d1)

@st.cache_data(ttl=86400)
def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url)
    return table[0]['Symbol'].tolist()

def analyze_ticker_deep(t):
    results = []
    try:
        tk = yf.Ticker(t)
        info = tk.info
        
        # QUALITY FILTER (Liquidity & Stability)
        if info.get('averageVolume', 0) < 1000000: return []
        
        cp = tk.fast_info['lastPrice']
        for exp in tk.options[:5]: 
            days = (pd.to_datetime(exp) - pd.Timestamp.now()).days
            if not (20 <= days <= 45): continue 
            
            opts = tk.option_chain(exp).calls
            for _, row in opts.iterrows():
                otm_pct = ((row['strike'] / cp) - 1) * 100
                if not (3 <= otm_pct <= 7): continue
                
                delta = calculate_delta(cp, row['strike'], days, row['impliedVolatility'])
                if not (0.25 <= delta <= 0.35): continue
                
                yield_val = (row['lastPrice'] / cp) * 100
                monthly_yield = (yield_val / days) * 30
                if not (1.0 <= monthly_yield <= 2.5): continue
                
                results.append({
                    'Ticker': f"https://finance.yahoo.com/quote/{t}",
                    'Price': f"${cp:.2f}",
                    'Delta': f"{delta:.2f}",
                    'Expiry': exp,
                    'Strike': f"${row['strike']:.2f}",
                    'OTM %': f"{otm_pct:.1f}%",
                    'Mo. Yield': f"{monthly_yield:.2f}%",
                    'Status': "⭐ PRIME"
                })
                break # Just find the best one per ticker
    except: pass
    return results

# --- UI ---
st.title("🎯 Chris's S&P 500 Discovery Engine")

if st.button('SCAN ENTIRE S&P 500', key="main_push_button"):
    tickers = get_sp500_tickers()
    all_res = []
    p_bar = st.progress(0)
    status_text = st.empty()
    
    for i, t in enumerate(tickers):
        status_text.markdown(f'<p class="status-yellow">Checking {i+1}/503: {t}</p>', unsafe_allow_html=True)
        all_res.extend(analyze_ticker_deep(t))
        p_bar.progress((i + 1) / len(tickers))
        if i % 50 == 0: time.sleep(1) # Rate limit safety
        
    status_text.markdown(f'<p class="status-yellow">Scan Complete! Found {len(all_res)} opportunities.</p>', unsafe_allow_html=True)
    st.session_state['results'] = all_res

if 'results' in st.session_state:
    df = pd.DataFrame(st.session_state['results'])
    if not df.empty:
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("No stocks currently match your 1-2% monthly yield and 3-7% OTM criteria.")

st.markdown('<div style="background: rgba(0,0,0,0.7); padding: 20px; border-radius: 15px; border: 1px solid #00BFFF; margin-top: 30px;">', unsafe_allow_html=True)
st.write("### 🔍 Manual Deep-Dive")
manual_ticker = st.text_input("Enter symbol:", "").upper()
if manual_ticker and st.button(f"Scan {manual_ticker}", key="manual_check_btn"):
    st.session_state['results'] = analyze_ticker_deep(manual_ticker)
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
