import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Covered Call Screener", layout="wide")
st.title("🎯 S&P 500 Covered Call Screener")

def get_scan_data(ticker):
    try:
        tk = yf.Ticker(ticker)
        current_price = tk.fast_info['lastPrice']
        
        # Get all expiration dates
        exps = tk.options
        if not exps: return None
        
        # We'll pick the first available expiry for this scan
        target_expiry = exps[0] 
        
        # Get the call options for that date
        opts = tk.option_chain(target_expiry).calls
        
        # Filter for the first Strike that is HIGHER than current price (OTM)
        otm_calls = opts[opts['strike'] > current_price]
        
        if not otm_calls.empty:
            suggested_call = otm_calls.iloc[0] # The "Next Strike Up"
            return {
                'Ticker': ticker,
                'Current Price': f"${current_price:.2f}",
                'Suggested Strike': f"${suggested_call['strike']:.2f}",
                'Expiry Date': target_expiry,
                'Premium (Bid)': f"${suggested_call['bid']:.2f}"
            }
    except:
        return None

try:
    tickers = pd.read_csv('watchlist.txt', header=None)[0].tolist()
    st.write(f"Ready to scan {len(tickers)} tickers.")
    
    if st.button('🚀 Run Market Scan'):
        results = []
        progress_bar = st.progress(0)
        
        # Scanning the first 20 for a quick Sunday test
        test_limit = 20 
        for i, t in enumerate(tickers[:test_limit]):
            data = get_scan_data(t)
            if data: results.append(data)
            progress_bar.progress((i + 1) / test_limit)
        
        if results:
            df = pd.DataFrame(results)
            st.table(df)
        else:
            st.warning("No data found. Check back when markets are open!")
except Exception as e:
    st.error(f"Error: {e}")
