import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm

st.set_page_config(page_title="Pro Covered Call Screener", layout="wide")

# --- Custom Styling: 0.6 Opacity for a "Tinted" look instead of solid black ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), 
                    url('https://images.unsplash.com/photo-1611974717482-480927df702c?auto=format&fit=crop&q=80&w=2000');
        background-size: cover;
        background-attachment: fixed;
        color: white;
    }
    /* Makes the data table look like it's floating on glass */
    [data-testid="stDataFrame"] {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px;
        padding: 5px;
    }
    /* Fixes header visibility on tinted backgrounds */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("## 📈 Hamilton Trading")
    st.image("https://img.icons8.com/color/512/bullish.png", width=80)
    st.write("---")
    st.caption("Strategy: 0.20-0.30 Delta")

# --- Main UI ---
st.title("🎯 Pro Covered Call Screener")

col1, col2 = st.columns(2)
with col1:
    vix = yf.Ticker("^VIX").fast_info['lastPrice']
    st.metric("VIX (Market Vol)", f"{vix:.2f}")
with col2:
    spy = yf.Ticker("SPY").fast_info['lastPrice']
    st.metric("SPY Price", f"${spy:.2f}")

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
                    'Price': f"${cp:.2f}",   # Left-justified text
                    'Strike': f"${row['strike']:.2f}",
                    'Delta': f"{delta:.2f}",
                    'Yield': f"{roc:.2f}%",
                    'Status': status
                }
        return None
    except: return None

if st.button('🚀 Run Morning Scan'):
    tickers = pd.read_csv('watchlist.txt', header=None)[0].tolist()
    results = []
    progress = st.progress(0)
    limit = 25
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
