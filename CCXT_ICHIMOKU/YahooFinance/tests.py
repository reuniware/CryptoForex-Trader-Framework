# import yfinance as yf
# import requests
from requests_html import HTMLSession
import pandas as pd
import numpy as np

# crypto_codes = yf.symbols("crypto")
# print(yf.Tickers("crypto"))

session = HTMLSession()
num_currencies = 250
try:
    for i in range(0, 250):
        req = "https://finance.yahoo.com/crypto?offset=" + str(num_currencies * i) + "&count=" + str(num_currencies)
        resp = session.get(req)
        tables = pd.read_html(resp.html.raw_html)
        df = tables[0].copy()
        symbols_yf = df.Symbol.tolist()
        print(symbols_yf[:250])
        print(df.head(250))
except:
    print("end of getting cryptos from yf")
