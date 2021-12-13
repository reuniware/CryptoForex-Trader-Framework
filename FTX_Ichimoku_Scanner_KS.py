import os
from datetime import datetime

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

    data = client.get_historical_data(
        market_name=symbol,
        resolution=3600*24,    # 60min * 60sec = 3600 sec ; 3600*24 for scanning in daily timeframe
        limit=10000,                                        # Can be optimized according to the scanned timeframe
        start_time=float(round(time.time())) - 1000*3600,   # Can be optimized according to the scanned timeframe
        end_time=float(round(time.time())))

    dframe = pd.DataFrame(data)

    dframe['time'] = pd.to_datetime(dframe['time'], unit='ms')

    # print(dframe)
    dframe['ICH_SSA'] = ta.trend.ichimoku_a(dframe['high'], dframe['low'])
    dframe['ICH_SSB'] = ta.trend.ichimoku_b(dframe['high'], dframe['low'])
    dframe['ICH_KS'] = ta.trend.ichimoku_base_line(dframe['high'], dframe['low'])
    dframe['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframe['high'], dframe['low'])

    for indexdf, rowdf in dframe.iterrows():
        open = float(rowdf['open'])
        low = rowdf['low']
        close = float(rowdf['close'])
        ssa = rowdf['ICH_SSA']
        ssb = rowdf['ICH_SSB']
        ks = float(rowdf['ICH_KS'])
        ts = rowdf['ICH_TS']
        timestamp = rowdf['time']

        if open < ks < close:
            print(timestamp, symbol, "O", open, "L", low, "C", close, "SSA", ssa, "SSB", ssb, "KS", ks, "TS", ts)
