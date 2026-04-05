import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm

st.set_page_config(page_title="Chris's Covered Call Screener", layout="wide")

# --- CUSTOM STYLING (Glassy Dark Grey) ---
st.markdown("""
    <style>
    .stApp {
        background-color: rgba(30, 34, 45, 0.95);
        color: #e0e6ed;
    }
    [data-testid="stDataFrame"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px;
        padding: 5px;
    }
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("## 📊 Chris's Covered Call Screener")
    st.write("---")
    st.caption("Targeting 0.20-0.30 Delta | Weeklies")
    st.image("https://img.icons8.com/color/512/bullish.png", width=60)

# --- Main UI: The Four Pillars Header ---
st.title("🎯 Market Command Center")

# Create 4 columns for the top metrics
m1, m2, m3, m4 = st.columns(4)

try:
    # Fetching the Big Three + VIX
    vix_val = yf.Ticker("^VIX").fast_info['lastPrice']
    spy_val = yf.Ticker("SPY").fast_info['lastPrice']
    qqq_val = yf.Ticker("QQQ").fast_info['lastPrice']
    dia_val = yf.Ticker("DIA").fast_info['lastPrice']

    with m1: st.metric("VIX (Fear)", f"{vix_val:.2f}")
    with m2: st.metric("SPY (S&P)", f"${spy_val:.2f}")
    with m3: st.metric("QQQ (Nasdaq)", f"${qqq_val:.2f}")
    with m4: st.metric("DIA (Dow)", f"${dia_val:.2f}")
except:
    st.warning("Market data loading...")

st.write("---")

# Black-Scholes Logic
def calculate_delta(current_price, strike, days_to_expiry, iv):
    if days_to_expiry <= 0 or iv <= 0: return 0
    t = days_to_expiry / 365.0
    d1 = (np.log(current_price / strike) + (0.5 * iv**2) * t) / (iv * np.sqrt(t))
    return norm.cdf(d1)

def get_scan_data(ticker):
    try:
        tk = yf.Ticker(ticker)
        cp = tk.fast_info['lastPrice']
        exps = tk.options
        if not exps: return None
        target_expiry = exps[0]
        days = (pd.to_datetime(target_expiry) - pd.Timestamp.now()).days
        opts = tk.option_chain(target_expiry).calls
        
        for _, row in opts.iterrows():
            delta = calculate_delta(cp, row['strike'], days, row['impliedVolatility'])
            if 0.20 <= delta <= 0.30:
                roc = (row['lastPrice'] / cp) * 100
                iv_val = row['impliedVolatility']
                
                status = "🟨 MODERATE"
                if iv_val > 0.45: status = "🟥 HIGH VOL"
                elif roc > 1.5 and delta < 0.25: status = "🟩 HIGH YIELD"

                return {
                    'Ticker': f"https://finance.yahoo.com/quote/{ticker}",
                    'Price': f"${cp:.2f}",
                    'Strike': f"${row['strike']:.2f}",
                    'Delta': f"{delta:.2f}",
                    'Yield': f"{roc:.2f}%",
                    'Status': status
                }
        return None
    except: return None

# Main Execution
if st.button('🚀 Run All-Market Scan'):
    tickers = pd.read_csv('watchlist.txt', header=None)[0].tolist()
    results = []
    progress = st.progress(0)
    limit = 35 # Bumping to 35 since we are covering more ground
    
    for i, t in enumerate(tickers[:limit]):
        data = get_scan_data(t)
        if data: results.append(data)
        progress.progress((i + 1) / limit)
    
    if results:
        df = pd.DataFrame(results)
        st.dataframe(
            df,
            column_config={
                "Ticker": st.column_config.LinkColumn("Ticker", display_text=r"https://finance.yahoo.com/quote/(.*)"),
                "Price": st.column_config.TextColumn("Price"),
                "Strike": st.column_config.TextColumn("Strike"),
                "Yield": st.column_config.TextColumn("Yield"),
                "Delta": st.column_config.TextColumn("Delta"),
            },
            hide_index=True,
            use_container_width=True
        )
