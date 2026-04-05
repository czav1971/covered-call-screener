import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm

st.set_page_config(page_title="Covered Call Screener", layout="wide")
st.title("🎯 S&P 500 Covered Call Screener")

def calculate_delta(current_price, strike, days_to_expiry, iv):
    if days_to_expiry <= 0 or iv <= 0: return 0
    t = days_to_expiry / 365.0
    d1 = (np.log(current_price / strike) + (0.5 * iv**2) * t) / (iv * np.sqrt(t))
    return norm.cdf(d1)

def get_logic_note(delta, iv, price, strike):
    # This writes the "Reasoning" for you
    buffer = ((strike - price) / price) * 100
    if iv > 0.40:
        note = f"🔥 High IV ({iv*100:.0f}%). Higher risk/reward."
    elif delta > 0.27:
        note = f"💰 Aggressive Delta ({delta:.2f}). Focus on premium."
    else:
        note = f"🛡️ Conservative ({delta:.2f} Delta). {buffer:.1f}% price buffer."
    return note

def get_scan_data(ticker):
    try:
        tk = yf.Ticker(ticker)
        current_price = tk.fast_info['lastPrice']
        exps = tk.options
        if not exps: return None
        
        target_expiry = exps[0]
        days_to_expiry = (pd.to_datetime(target_expiry) - pd.Timestamp.now()).days
        opts = tk.option_chain(target_expiry).calls
        
        for _, row in opts.iterrows():
            delta = calculate_delta(current_price, row['strike'], days_to_expiry, row['impliedVolatility'])
            if 0.20 <= delta <= 0.30:
                return {
                    'Ticker': ticker,
                    'Price': f"${current_price:.2f}",
                    'Strike': f"${row['strike']:.2f}",
                    'Delta': f"{delta:.2f}",
                    'Premium': f"${row['lastPrice']:.2f}",
                    'Logic / Reasoning': get_logic_note(delta, row['impliedVolatility'], current_price, row['strike'])
                }
        return None
    except:
        return None

try:
    tickers = pd.read_csv('watchlist.txt', header=None)[0].tolist()
    if st.button('🚀 Run Smart Scan'):
        results = []
        progress_bar = st.progress(0)
        for i, t in enumerate(tickers[:15]):
            data = get_scan_data(t)
            if data: results.append(data)
            progress_bar.progress((i + 1) / 15)
        
        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("No matches in the 0.20-0.30 Delta range.")
except Exception as e:
    st.error(f"Error: {e}")
