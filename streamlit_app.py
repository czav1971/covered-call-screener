import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm

# Standard Streamlit White Theme (No Custom CSS)
st.set_page_config(page_title="Chris's Covered Call Screener", layout="wide")

# --- Updated Sidebar ---
with st.sidebar:
    st.markdown("## 📊 Chris's Covered Call Screener")
    st.write("---")
    st.caption("0.20-0.30 Delta | Weeklies")
    st.image("https://img.icons8.com/color/512/bullish.png", width=60)

# --- Updated Header Name: "Chris's Command Center" ---
st.title("🎯 Chris's Command Center")

# --- Big Four Metrics ---
m1, m2, m3, m4 = st.columns(4)

try:
    vix_val = yf.Ticker("^VIX").fast_info['lastPrice']
    spy_val = yf.Ticker("SPY").fast_info['lastPrice']
    qqq_val = yf.Ticker("QQQ").fast_info['lastPrice']
    dia_val = yf.Ticker("DIA").fast_info['lastPrice']

    # Using default metric styling for maximum readability on white background
    with m1: st.metric("VIX (Fear)", f"{vix_val:.2f}")
    with m2: st.metric("SPY (S&P 500)", f"${spy_val:.2f}")
    with m3: st.metric("QQQ (Nasdaq 100)", f"${qqq_val:.2f}")
    with m4: st.metric("DIA (Dow Jones)", f"${dia_val:.2f}")
except:
    st.warning("Loading Market Data...")

st.write("---")

# --- Core Screening Logic ---
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
                
                # These match the color-coding you wanted earlier
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

# --- Main All-Market Scan Action ---
if st.button('🚀 Run All-Market Scan'):
    # Load your full watchlist
    tickers = pd.read_csv('watchlist.txt', header=None)[0].tolist()
    results = []
    progress = st.progress(0)
    
    # Scanning first 50 tickers to ensure we see the whole list
    scan_limit = 50 
    
    for i, t in enumerate(tickers[:scan_limit]):
        data = get_scan_data(t)
        if data: results.append(data)
        progress.progress((i + 1) / scan_limit)
    
    if results:
        df = pd.DataFrame(results)
        
        # This is the fix to display the entire list in a scrollable frame
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
            use_container_width=True,
            # This forces the table to be scrollable if it is too long
            height=600 
        )
