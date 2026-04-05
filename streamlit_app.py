import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm

st.set_page_config(page_title="Pro Covered Call Screener", layout="wide")

# --- UI Header ---
st.title("📈 Pro Covered Call Screener")

# --- New Risk Legend Section ---
with st.expander("📝 VIEW RISK LEGEND (Tap to Expand)", expanded=True):
    st.markdown("""
    - 🟩 **GREEN**: High Premium with a Safe Delta (High Probability of Profit).
    - 🟨 **YELLOW**: Moderate Risk (Strike is closer to price / higher chance of assignment).
    - 🟥 **BOLD RED**: High Volatility / Binary Event (High IV - Proceed with Caution).
    """)

col1, col2 = st.columns(2)
with col1:
    vix = yf.Ticker("^VIX").fast_info['lastPrice']
    st.metric("Market Volatility (VIX)", f"{vix:.2f}")
with col2:
    spy = yf.Ticker("SPY").fast_info['lastPrice']
    st.metric("S&P 500 (SPY)", f"${spy:.2f}")

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
                
                # Logic for the color-coded "Status"
                if iv_val > 0.45:
                    status = "🟥 HIGH VOL"
                elif roc > 1.5 and delta < 0.25:
                    status = "🟩 HIGH YIELD/SAFE"
                else:
                    status = "🟨 MODERATE"

                return {
                    'Ticker': f"https://finance.yahoo.com/quote/{ticker}",
                    'Symbol': ticker,
                    'Price': cp,
                    'Strike': row['strike'],
                    'Delta': round(delta, 2),
                    'Yield %': f"{roc:.2f}%",
                    'IV %': f"{iv_val*100:.0f}%",
                    'Risk Status': status
                }
        return None
    except: return None

# --- Main App ---
try:
    tickers = pd.read_csv('watchlist.txt', header=None)[0].tolist()
    
    if st.button('🚀 Start Morning Scan'):
        results = []
        progress = st.progress(0)
        limit = 20 
        for i, t in enumerate(tickers[:limit]):
            data = get_scan_data(t)
            if data: results.append(data)
            progress.progress((i + 1) / limit)
        
        if results:
            df = pd.DataFrame(results)
            st.dataframe(
                df,
                column_config={
                    "Ticker": st.column_config.LinkColumn("Chart", display_text=r"https://finance.yahoo.com/quote/(.*)"),
                    "Price": st.column_config.NumberColumn(format="$%.2f"),
                    "Strike": st.column_config.NumberColumn(format="$%.2f"),
                    "Risk Status": st.column_config.TextColumn("Risk Status"),
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No candidates found in the 0.20-0.30 Delta range.")
except Exception as e:
    st.error(f"Error: {e}")
