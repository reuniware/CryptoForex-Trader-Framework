# import yfinance as yf
# import requests
from requests_html import HTMLSession
import pandas as pd
import numpy as np
from yahoofinancials import YahooFinancials

# crypto_codes = yf.symbols("crypto")
# print(yf.Tickers("crypto"))

# yahoo_financials = YahooFinancials('BTC-USD')
# data = yahoo_financials.get_historical_price_data("2019-07-10", "2022-12-30", "daily")
# btc_df = pd.DataFrame(data['BTC-USD']['prices'])
# btc_df = btc_df.drop('date', axis=1).set_index('formatted_date')
# btc_df.head()
# print(btc_df)
# #exit(55)

session = HTMLSession()
num_currencies = 250
try:
    for i in range(0, 250):
        req = "https://finance.yahoo.com/crypto?offset=" + str(num_currencies * i) + "&count=" + str(num_currencies)
        resp = session.get(req)
        tables = pd.read_html(resp.html.raw_html)
        df = tables[0].copy()
        symbols_yf = df.Symbol.tolist()
        # print(symbols_yf[:250])
        # print(df.head(250))
        for symbol in symbols_yf:
            yahoo_financials = YahooFinancials(symbol)
            data = yahoo_financials.get_historical_price_data("2000-07-10", "2022-12-30", "daily")  # daily weekly monthly
            symbol_df = pd.DataFrame(data[symbol]['prices'])
            symbol_df = symbol_df.drop('date', axis=1).set_index('formatted_date')
            #symbol_df.head()
            #print(symbol_df)
            print("data downloaded for", symbol)
except:
    print("end of getting cryptos from yf")
