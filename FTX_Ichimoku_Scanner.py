import os
from datetime import datetime
from datetime import timedelta

import ftx
import pandas as pd
import requests
import threading
import time
import ta
import math

# import numpy as np

client = ftx.FtxClient(
    api_key='',
    api_secret='',
    subaccount_name='TrixStrategy'
)

# result = client.get_balances()
# print(result)

if os.path.exists("results.txt"):
    os.remove("results.txt")

stop_thread = False


def my_thread(name):
    global client
    while not stop_thread:

        f = open("results.txt", "a")

        markets = requests.get('https://ftx.com/api/markets').json()
        df = pd.DataFrame(markets['result'])
        df.set_index('name')
        for index, row in df.iterrows():
            symbol = row['name']
            # print(symbol)
            # print("scanning", symbol)

            data = client.get_historical_data(
                market_name=symbol,
                resolution=60 * 15,  # 60min * 60sec = 3600 sec
                limit=10000,
                start_time=float(round(time.time())) - 2000 * 3600,  # 1000*3600 for resolution=3600*24 (daily)
                end_time=float(round(time.time())))

            dframe = pd.DataFrame(data)

            # dframe['time'] = pd.to_datetime(dframe['time'], unit='ms')

            # print(dframe)
            try:
                dframe['ICH_SSA'] = ta.trend.ichimoku_a(dframe['high'], dframe['low'], window1=9, window2=26).shift(26)
                dframe['ICH_SSB'] = ta.trend.ichimoku_b(dframe['high'], dframe['low'], window2=26, window3=52).shift(26)
                dframe['ICH_KS'] = ta.trend.ichimoku_base_line(dframe['high'], dframe['low'])
                dframe['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframe['high'], dframe['low'])
                dframe['ICH_CS'] = dframe['close'].shift(-26)

            except KeyError as err:
                print(err)
                continue

            for indexdf, rowdf in dframe.iterrows():
                openp = rowdf['open']
                high = rowdf['high']
                low = rowdf['low']
                close = rowdf['close']
                ssa = rowdf['ICH_SSA']
                ssb = rowdf['ICH_SSB']
                ks = rowdf['ICH_KS']
                ts = rowdf['ICH_TS']
                cs = rowdf['ICH_CS']
                timestamp = pd.to_datetime(rowdf['time'], unit='ms')

                data_hour = timestamp.hour
                data_day = timestamp.day
                data_month = timestamp.month
                data_year = timestamp.year

                now = datetime.now() - timedelta(hours=4)
                now_hour = now.hour
                now_day = now.day
                now_month = now.month
                now_year = now.year

                # if math.isnan(ssa):
                #     print(symbol, "ssa is null")
                #
                # if math.isnan(ssb):
                #     print(symbol, "ssb is null")

                if data_day == now_day and data_month == now_month and data_year == now_year and (data_hour >= now_hour):
                    if openp < ssb < close:
                        print(timestamp, symbol, "O", openp, "H", high, "L", low, "C", close, "SSA", ssa, "SSB", ssb, "KS", ks, "TS", ts, "CS", cs)
                        strn = str(timestamp) + " " + symbol + " O=" + str(openp) + " H=" + str(high) + " L=" + str(low) + " C=" + str(close) + " SSA=" + str(ssa) + " SSB=" + str(
                            ssb) + " KS=" + str(ks) + " TS=" + str(ts) + " CS=" + str(cs)
                        f = open("results.txt", "a")
                        f.write(strn + '\n')
                        f.close()

        f = open("results.txt", "a")
        f.write(100 * '*' + '\n')
        f.close()


x = threading.Thread(target=my_thread, args=(1,))
x.start()
