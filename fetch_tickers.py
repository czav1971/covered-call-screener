import pandas as pd
import requests
print('--- Starting Fetch ---')
h = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers=h)
pd.read_html(r.text)[0]['Symbol'].to_csv('watchlist.txt', index=False, header=False)
print('--- SUCCESS: watchlist.txt created ---')