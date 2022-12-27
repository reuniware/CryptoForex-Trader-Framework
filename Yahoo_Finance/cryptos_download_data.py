# import yfinance as yf
# import requests
import sys
import time

from requests_html import HTMLSession
import pandas as pd
import numpy as np
from yahoofinancials import YahooFinancials
import datetime
from datetime import timedelta
import yfinance as yf

# crypto_codes = yf.symbols("crypto")
# print(yf.Tickers("crypto"))

# yahoo_financials = YahooFinancials('BTC-USD')
# data = yahoo_financials.get_historical_price_data("2019-07-10", "2022-12-30", "daily")
# btc_df = pd.DataFrame(data['BTC-USD']['prices'])
# btc_df = btc_df.drop('date', axis=1).set_index('formatted_date')
# btc_df.head()
# print(btc_df)
# #exit(55)

today = datetime.date.today()
year = '{:04d}'.format(today.year)
month = '{:02d}'.format(today.month)
day = '{:02d}'.format(today.day)
end_date_str = year + "-" + month + "-" + day
start_date = pd.to_datetime(end_date_str, format="%Y-%m-%d") - pd.DateOffset(days=1)
year = '{:04d}'.format(start_date.year)
month = '{:02d}'.format(start_date.month)
day = '{:02d}'.format(start_date.day)
start_date_str = year + "-" + month + "-" + day

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
            data = yahoo_financials.get_historical_price_data(start_date_str, end_date_str, "daily")  # daily weekly monthly
            symbol_df = pd.DataFrame(data[symbol]['prices'])
            symbol_df = symbol_df.drop('date', axis=1).set_index('formatted_date')
            # symbol_df.head()
            # print(symbol_df)
            close_price = symbol_df.iloc[-1]['close']
            open_price = symbol_df.iloc[-1]['open']
            current_day_evol = (close_price - open_price) / open_price * 100
            if current_day_evol > 5:
                print("data downloaded for", symbol, current_day_evol, "%")
            # data = yf.download(tickers=symbol, period='10d', interval='15m')
            # print(data)
            time.sleep(0.25)
except:
    print(sys.exc_info())
    print("end of getting cryptos from yf")
