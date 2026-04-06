import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm
import hmac

st.set_page_config(page_title="Chris's Covered Call Command Center", layout="wide")

# --- AUTH ---
def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else: st.session_state["password_correct"] = False
    if st.session_state.get("password_correct", False): return True
    st.title("🔐 Secure Access Required")
    st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
    return False

if not check_password(): st.stop()

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url('https://raw.githubusercontent.com/czav1971/covered-call-screener/main/stock%20market%20gurus.png'); background-size: contain; background-attachment: fixed; }
    h1, h2, h3, p, [data-testid="stMetricLabel"] { color: #00BFFF !important; text-shadow: 2px 2px 4px black !important; }
    .status-yellow { color: #FFFF00 !important; font-weight: bold; font-size: 1.1rem; }
    div.st-key-main_push_button > button { color: #FF0000 !important; background-color: #FFFFFF !important; width: 150px !important; height: 150px !important; border-radius: 50% !important; border: 5px solid #FF0000 !important; font-weight: 900 !important; }
    div.st-key-main_push_button > button p { color: #FF0000 !important; }
    .stDataFrame { background: white; border-radius: 10px; padding: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- MATH ENGINE ---
def calculate_delta(cp, strike, days, iv):
    if days <= 0 or iv <= 0: return 0
    t = days / 365.0
    d1 = (np.log(cp / strike) + (0.5 * iv**2) * t) / (iv * np.sqrt(t))
    return norm.cdf(d1)

def get_iv_rank(tk):
    hist = tk.history(period="1y")
    if hist.empty: return 50
    vols = hist['Close'].pct_change().rolling(window=20).std() * np.sqrt(252)
    curr_v = vols.iloc[-1]
    low, high = vols.min(), vols.max()
    if high == low: return 50
    return ((curr_v - low) / (high - low)) * 100

def analyze_ticker_deep(t):
    results = []
    status_text = st.empty()
    status_text.markdown(f'<p class="status-yellow">Analyzing {t} Chain...</p>', unsafe_allow_html=True)
    
    try:
        tk = yf.Ticker(t)
        cp = tk.fast_info['lastPrice']
        iv_rank = get_iv_rank(tk)
        
        for exp in tk.options[:8]: 
            days = (pd.to_datetime(exp) - pd.Timestamp.now()).days
            if not (20 <= days <= 50): continue 
            
            opts = tk.option_chain(exp).calls
            for _, row in opts.iterrows():
                otm_pct = ((row['strike'] / cp) - 1) * 100
                if not (3 <= otm_pct <= 7): continue
                
                delta = calculate_delta(cp, row['strike'], days, row['impliedVolatility'])
                if not (0.20 <= delta <= 0.40): continue
                
                yield_val = (row['lastPrice'] / cp) * 100
                monthly_yield = (yield_val / days) * 30
                
                tag = "⭐ BEST FIT" if (0.25 <= delta <= 0.35 and 30 <= iv_rank <= 60) else "✅ QUALIFIED"
                if monthly_yield < 1.0: tag = "⚠️ LOW YIELD"
                
                results.append({
                    'Ticker': f"https://finance.yahoo.com/quote/{t}",
                    'Price': f"${cp:.2f}",
                    'Delta': f"{delta:.2f}",
                    'Expiry': exp,
                    'Strike': f"${row['strike']:.2f}",
                    'DTE': days,
                    'OTM %': f"{otm_pct:.1f}%",
                    'Mo. Yield': f"{monthly_yield:.2f}%",
                    'IV Rank': f"{iv_rank:.0f}",
                    'Status': tag
                })
    except: pass
    status_text.empty()
    return results

# --- UI ---
st.title("🎯 Chris's Command Center")
if st.button('PUSH ME', key="main_push_button"):
    tickers = pd.read_csv('watchlist.txt', header=None)[0].tolist()
    all_res = []
    p_bar = st.progress(0)
    for i, t in enumerate(tickers):
        all_res.extend(analyze_ticker_deep(t))
        p_bar.progress((i + 1) / len(tickers))
    st.session_state['results'] = all_res

if 'results' in st.session_state:
    # Explicitly ordering columns: Delta -> Expiry -> Strike
    df = pd.DataFrame(st.session_state['results'])
    cols = ['Ticker', 'Price', 'Delta', 'Expiry', 'Strike', 'DTE', 'OTM %', 'Mo. Yield', 'IV Rank', 'Status']
    df = df[cols] 
    st.dataframe(df, hide_index=True, use_container_width=True)

st.markdown('<div style="background: rgba(0,0,0,0.7); padding: 20px; border-radius: 15px; border: 1px solid #00BFFF; margin-top: 30px;">', unsafe_allow_html=True)
st.write("### 🔍 Manual Chain Deep-Dive")
manual_ticker = st.text_input("Enter symbol:", "").upper()
if manual_ticker and st.button(f"Scan {manual_ticker} Chain", key="manual_check_btn"):
    st.session_state['results'] = analyze_ticker_deep(manual_ticker)
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
