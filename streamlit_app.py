import streamlit as st
import pandas as pd

st.set_page_config(page_title="Covered Call Screener", layout="wide")
st.title("🎯 S&P 500 Covered Call Screener")

try:
    df = pd.read_csv('watchlist.txt', header=None, names=['Ticker'])
    st.write(f"Loaded {len(df)} tickers. Click 'Run Scan' to fetch option data.")
    
    if st.button('Run Scan'):
        st.info("Scanning market data... (This uses the logic in your yahoo_options.py)")
        # For now, we show the list to prove it's connected
        st.dataframe(df)
except Exception as e:
    st.error(f"Could not load watchlist: {e}")
