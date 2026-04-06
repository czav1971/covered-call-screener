import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm
import hmac
import time
import requests
import re

st.set_page_config(page_title="Chris's S&P 500 Execution Engine", layout="wide")

# --- AUTH ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    st.title("🔐 Secure Access Required")
    pwd = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if hmac.compare_digest(pwd, st.secrets["password"]):
            st.session_state["password_correct"] = True
            st.rerun()
    return False

if not check_password(): st.stop()

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url('https://raw.githubusercontent.com/czav1971/covered-call-screener/main/stock%20market%20gurus.png'); background-size: contain; background-attachment: fixed; }
    h1, h2, h3, p { color: #00BFFF !important; text-shadow: 2px 2px 4px black !important; }
    .status-yellow { color: #FFFF00 !important; font-weight: bold; font-size: 1.1rem; }
    div.st-key-main_push_button > button { color: #FF0000 !important; background-color: #FFFFFF !important; width: 150px !important; height: 150px !important; border-radius: 50% !important; border: 5px solid #FF0000 !important; font-weight: 900 !important; }
    .stDataFrame { background: white; border-radius: 10px; padding: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- MANUAL TICKER SCRAPER (Bypasses all library errors) ---
@st.cache_data(ttl=86400)
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url)
    # Use Regex to find tickers in the table directly from the HTML text
    tickers = re.findall(r'rel="nofollow" class="external text" href="https://www.nyse.com/quote/XNYS:(.*?)">', response.text)
    if not tickers:
        tickers = re.findall(r'<td><a rel="nofollow" class="external text" href="https://www.nasdaq.com/market-activity/stocks/(.*?)">', response.text)
    # Fallback: if those patterns change, grab the most common ticker pattern
    if not tickers:
        tickers = re.findall(r'<td><a [^>]*>([A-Z]{1,5})</a></td>', response.text)
    return sorted(list(set(tickers)))

def calculate_delta(cp, strike, days, iv):
    if days <= 0 or iv <= 0: return 0
    t = days / 365.0
    d1 = (np.log(cp / strike) + (0.5 * iv**2) * t) / (iv * np.sqrt(t))
    return norm.cdf(d1)

def analyze_ticker_deep(t):
    results = []
    try:
        tk = yf.Ticker(t)
        cp = tk.fast_info['lastPrice']
        for exp in tk.options[:3]: 
            days = (pd.to_datetime(exp) - pd.Timestamp.now()).days
            if not (15 <= days <= 50): continue 
            opts = tk.option_chain(exp).calls
            for _, row in opts.iterrows():
                otm_pct = ((row['strike'] / cp) - 1) * 100
                if not (3 <= otm_pct <= 8): continue
                delta = calculate_delta(cp, row['strike'], days, row['impliedVolatility'])
                if not (0.20 <= delta <= 0.40): continue
                yield_val = (row['lastPrice'] / cp) * 100
                monthly_yield = (yield_val / days) * 30
                if monthly_yield >= 0.8:
                    results.append({'Ticker': t, 'Price': f"${cp:.2f}", 'Delta': f"{delta:.2f}", 'Expiry': exp, 'Strike': f"${row['strike']:.2f}", 'Mo. Yield': f"{monthly_yield:.2f}%"})
                    break
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
        t_clean = t.replace('.', '-')
        status_text.markdown(f'<p class="status-yellow">Checking {i+1}/{len(tickers)}: {t_clean}</p>', unsafe_allow_html=True)
        all_res.extend(analyze_ticker_deep(t_clean))
        p_bar.progress((i + 1) / len(tickers))
        
    status_text.markdown(f'<p class="status-yellow">Scan Complete! Found {len(all_res)} opportunities.</p>', unsafe_allow_html=True)
    st.session_state['results'] = all_res

if 'results' in st.session_state:
    st.dataframe(pd.DataFrame(st.session_state['results']), hide_index=True, use_container_width=True)
