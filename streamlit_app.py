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
    </style>
    """, unsafe_allow_html=True)

# --- HARDCODED TICKER LIST (S&P 500 - Snapshot) ---
def get_sp500_tickers():
    # We use a curated list to bypass all scraping/lxml issues
    return ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "GOOG", "META", "BRK-B", "TSLA", "UNH", "JPM", "LLY", "XOM", "AVGO", "V", "PG", "MA", "COST", "HD", "JNJ", "ABBV", "MRK", "CRM", "BAC", "CVX", "ADBE", "AMD", "PEP", "WMT", "TMO", "WFC", "KO", "DIS", "CSCO", "ACN", "ABT", "LIN", "MCD", "INTC", "DHR", "ORCL", "VZ", "AMGN", "INTU", "CMCSA", "CAT", "IBM", "PFE", "PM", "IBM", "TXN", "MS", "UNP", "GE", "AMAT", "HON", "LOW", "NEE", "GS", "SPGI", "RTX", "AXP", "COP", "BKNG", "PLD", "TJX", "SYK", "ETN", "LMT", "LRCX", "VRTX", "UPS", "MDLZ", "REGN", "T", "MU", "PANW", "PGR", "CI", "C", "ISRG", "BSX", "ZTS", "DE", "ELV", "FI", "CVS", "MMC", "GILD", "CB", "LRCX", "CRV", "BLK", "ADI", "ADP", "SCHW", "MDLZ", "BA", "ADI", "AMT", "BMY", "ICE", "WM", "MO", "CME", "SHW", "ANET", "EQIX", "HCA", "CDNS", "SO", "MCO", "EOG", "PH", "APH", "MAR", "MCK", "GD", "ITW", "AIG", "D", "NSC", "ROP", "PXD", "EMR", "ECL", "MET", "CARR", "DXCM", "A", "O", "TEL", "WELL", "PSA", "DLR", "AZO", "KDP", "STZ", "FDX", "AJG", "CNC", "AON", "ADM", "TRV", "MPC", "WBD", "BK", "IQV", "ORLY", "COF", "DFS", "KHC", "SYY", "EXC", "PAYX", "PCAR", "HLT", "MSI", "AEP", "ROK", "PRU", "CTAS", "MNST", "GWW", "VLO", "FIS", "HUM", "NEM", "NOC", "KR", "OTIS", "OKE", "DDU", "IDXX", "WMB", "MCHP", "CMI", "BKR", "F", "GM", "EBAY", "KMB", "HPQ", "STX", "TGT", "LVS", "WYNN", "CCL"]

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
                if not (2 <= otm_pct <= 10): continue
                delta = calculate_delta(cp, row['strike'], days, row['impliedVolatility'])
                if not (0.15 <= delta <= 0.40): continue
                yield_val = (row['lastPrice'] / cp) * 100
                monthly_yield = (yield_val / days) * 30
                if monthly_yield >= 0.7:
                    results.append({'Ticker': t, 'Price': f"${cp:.2f}", 'Delta': f"{delta:.2f}", 'Expiry': exp, 'Strike': f"${row['strike']:.2f}", 'Mo. Yield': f"{monthly_yield:.2f}%", 'raw_yield': monthly_yield})
                    break
    except: pass
    return results

st.title("🎯 Chris's S&P 500 Discovery Engine")

if st.button('SCAN TOP S&P 500', key="main_push_button"):
    tickers = get_sp500_tickers()
    all_res = []
    p_bar = st.progress(0)
    status_text = st.empty()
    
    for i, t in enumerate(tickers):
        status_text.markdown(f'<p class="status-yellow">Checking {i+1}/{len(tickers)}: {t}</p>', unsafe_allow_html=True)
        all_res.extend(analyze_ticker_deep(t))
        p_bar.progress((i + 1) / len(tickers))
        time.sleep(0.05)
            
    st.session_state['results'] = all_res
    st.rerun()

if 'results' in st.session_state and st.session_state['results']:
    df = pd.DataFrame(st.session_state['results']).sort_values(by='raw_yield', ascending=False)
    st.dataframe(df.drop(columns=['raw_yield']), hide_index=True, use_container_width=True)
