import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm

st.set_page_config(page_title="Covered Call Screener", layout="wide")
st.title("🎯 S&P 500 Covered Call Screener (0.20 - 0.30 Delta)")

def calculate_delta(current_price, strike, days_to_expiry, iv):
    if days_to_expiry <= 0 or iv <= 0: return 0
    t = days_to_expiry / 365.0
    d1 = (np.log(current_price / strike) + (0.5 * iv**2) * t) / (iv * np.sqrt(t))
    return norm.cdf(d1)

def get_scan_data(ticker):
    try:
        tk = yf.Ticker(ticker)
        current_price = tk.fast_info['lastPrice']
        exps = tk.options
        if not exps: return None
        
        target_expiry = exps[0]
        expiry_dt = pd.to_datetime(target_expiry)
        days_to_expiry = (expiry_dt - pd.Timestamp.now()).days
        
        opts = tk.option_chain(target_expiry).calls
        results = []
        
        for _, row in opts.iterrows():
            delta = calculate_delta(current_price, row['strike'], days_to_expiry, row['impliedVolatility'])
            # Target the 0.20 to 0.30 range
            if 0.20 <= delta <= 0.30:
                return {
                    'Ticker': ticker,
                    'Price': f"${current_price:.2f}",
                    'Strike': f"${row['strike']:.2f}",
                    'Expiry': target_expiry,
                    'Delta': f"{delta:.2f}",
                    'Premium': f"${row['lastPrice']:.2f}",
                    'IV': f"{row['impliedVolatility']*100:.1f}%"
                }
        return None
    except:
        return None

try:
    tickers = pd.read_csv('watchlist.txt', header=None)[0].tolist()
    if st.button('🚀 Run Delta Scan'):
        results = []
        progress_bar = st.progress(0)
        # Testing top 15 for speed
        for i, t in enumerate(tickers[:15]):
            data = get_scan_data(t)
            if data: results.append(data)
            progress_bar.progress((i + 1) / 15)
        
        if results:
            st.table(pd.DataFrame(results))
        else:
            st.warning("No strikes found in the 0.20-0.30 Delta range for these tickers.")
except Exception as e:
    st.error(f"Error: {e}")
