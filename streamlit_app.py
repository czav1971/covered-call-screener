import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Covered Call Screener", layout="wide")
st.title("🎯 S&P 500 Covered Call Screener")

def get_best_call(ticker):
    try:
        tk = yf.Ticker(ticker)
        current_price = tk.fast_info['lastPrice']
        exps = tk.options
        if not exps: return None
        
        # Get the first expiration
        opt = tk.option_chain(exps[0]).calls
        # Only look at strikes above current price (OTM)
        otm_calls = opt[opt['strike'] > current_price]
        
        if not otm_calls.empty:
            best = otm_calls.iloc[0] # Closest to the money
            return {
                'Ticker': ticker,
                'Price': round(current_price, 2),
                'Strike': best['strike'],
                'Premium': best['lastPrice'],
                'IV': round(best['impliedVolatility'] * 100, 1)
            }
    except:
        return None

try:
    tickers = pd.read_csv('watchlist.txt', header=None)[0].tolist()
    st.write(f"Screener ready for {len(tickers)} tickers.")
    
    if st.button('🚀 Run Scan (Top 10 Tickers)'):
        results = []
        progress_bar = st.progress(0)
        for i, t in enumerate(tickers[:10]):
            data = get_best_call(t)
            if data: results.append(data)
            progress_bar.progress((i + 1) / 10)
        
        if results:
            st.table(pd.DataFrame(results))
        else:
            st.warning("No data found. Market might be closed or tickers limited.")
except Exception as e:
    st.error(f"Error: {e}")
