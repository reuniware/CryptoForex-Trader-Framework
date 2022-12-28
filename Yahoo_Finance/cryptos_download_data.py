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
import ta

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

dict_evol = {}
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
            dict_evol[symbol] = current_day_evol
            #print("data downloaded for", symbol, current_day_evol, "%")

            dframe = yf.download(tickers=symbol, period='56d', interval='1d', progress=False)
            # # print(data)
            dframe['ICH_SSB'] = ta.trend.ichimoku_b(dframe['High'], dframe['Low'], window2=26, window3=52).shift(26)
            # print(dframe['ICH_SSB'])
            dframe['ICH_SSA'] = ta.trend.ichimoku_a(dframe['High'], dframe['Low'], window1=9, window2=26).shift(26)
            # print(dframe['ICH_SSA'])
            dframe['ICH_KS'] = ta.trend.ichimoku_base_line(dframe['High'], dframe['Low'])
            # print(dframe['ICH_KS'])
            dframe['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframe['High'], dframe['Low'])
            # print(dframe['ICH_TS'])
            dframe['ICH_CS'] = dframe['Close'].shift(-26)
            # print(dframe['ICH_CS'])
            ssb = dframe['ICH_SSB'].iloc[-1]
            ssa = dframe['ICH_SSA'].iloc[-1]
            kijun = dframe['ICH_KS'].iloc[-1]
            tenkan = dframe['ICH_TS'].iloc[-1]
            chikou = dframe['ICH_CS'].iloc[-27]
            # print("SSB", ssb)  # SSB at the current price
            # print("SSA", ssa)  # SSB at the current price
            # print("KS", kijun)  # SSB at the current price
            # print("TS", tenkan)  # SSB at the current price
            # print("CS", chikou)  # SSB at the current price
            price_open = dframe['Open'].iloc[-1]
            price_high = dframe['High'].iloc[-1]
            price_low = dframe['Low'].iloc[-1]
            price_close = dframe['Close'].iloc[-1]

            if price_close > ssb and price_close > ssa and price_close > tenkan and price_close > kijun:
                print(symbol, "price above ssb and ssa and tenkan and kijun")

            time.sleep(0.25/4)

except:
    print(sys.exc_info())
    print("end of getting cryptos from yf")

for k in sorted(dict_evol, key=lambda k: dict_evol[k], reverse=True):
    print(k, dict_evol[k])
