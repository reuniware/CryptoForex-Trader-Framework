import os
from datetime import datetime
from datetime import timedelta

import ftx
import pandas as pd
import requests
import threading
import time
import ta

# import numpy as np

client = ftx.FtxClient(
    api_key='',
    api_secret='',
    subaccount_name=''
)

# result = client.get_balances()
# print(result)

markets = requests.get('https://ftx.com/api/markets').json()
df = pd.DataFrame(markets['result'])
df.set_index('name')
for index, row in df.iterrows():
    symbol = row['name']
    # print(symbol)
    # print("scanning", symbol)

    data = client.get_historical_data(
        market_name=symbol,
        resolution=60 * 60,  # 60min * 60sec = 3600 sec
        limit=10000,
        start_time=float(round(time.time())) - 150 * 3600,  # 1000*3600 for resolution=3600*24 (daily)
        end_time=float(round(time.time())))

    dframe = pd.DataFrame(data)

    # dframe['time'] = pd.to_datetime(dframe['time'], unit='ms')

    # print(dframe)
    dframe['ICH_SSA'] = ta.trend.ichimoku_a(dframe['high'], dframe['low'])
    dframe['ICH_SSB'] = ta.trend.ichimoku_b(dframe['high'], dframe['low'])
    dframe['ICH_KS'] = ta.trend.ichimoku_base_line(dframe['high'], dframe['low'])
    dframe['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframe['high'], dframe['low'])

    for indexdf, rowdf in dframe.iterrows():
        open = float(rowdf['open'])
        high = rowdf['high']
        low = rowdf['low']
        close = float(rowdf['close'])
        ssa = rowdf['ICH_SSA']
        ssb = rowdf['ICH_SSB']
        ks = float(rowdf['ICH_KS'])
        ts = rowdf['ICH_TS']
        timestamp = pd.to_datetime(rowdf['time'], unit='ms')

        data_hour = timestamp.hour
        data_day = timestamp.day
        data_month = timestamp.month
        data_year = timestamp.year

        now = datetime.now() - timedelta(hours=2)
        now_hour = now.hour
        now_day = now.day
        now_month = now.month
        now_year = now.year

        if data_day == now_day and data_month == now_month and data_year == now_year and (data_hour >= now_hour):
            if open < ks < close:
                print(timestamp, symbol, "O", open, "H", high, "L", low, "C", close, "SSA", ssa, "SSB", ssb, "KS", ks, "TS", ts)
