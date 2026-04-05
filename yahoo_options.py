import yfinance as yf
import pandas as pd

def get_options_data(ticker_symbol):
    print(f"--- Fetching Data for {ticker_symbol} ---")
    
    # 1. Initialize the ticker
    ticker = yf.Ticker(ticker_symbol)
    
    # 2. Get available expiration dates
    expirations = ticker.options
    if not expirations:
        print("No options found. Check the ticker symbol.")
        return
    
    # We'll look at the closest upcoming expiration date
    target_date = expirations[0]
    print(f"Targeting Expiration: {target_date}")
    
    # 3. Pull the option chain
    opt_chain = ticker.option_chain(target_date)
    
    # 4. Filter for Strike, Price, Volume, and Open Interest
    calls = opt_chain.calls
    df = calls[['strike', 'lastPrice', 'volume', 'openInterest']]
    
    # Show only the top 15 most active contracts
    active_options = df[df['volume'] > 0].sort_values(by='volume', ascending=False).head(15)
    
    print(f"\nTop 15 Active Calls for {target_date}:")
    print(active_options.to_string(index=False))

if __name__ == "__main__":
    get_options_data("SPY")
