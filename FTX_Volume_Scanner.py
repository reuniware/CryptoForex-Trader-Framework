import glob, os
from datetime import datetime
from datetime import timedelta

import ftx
import pandas as pd
import requests
import threading
import time
import ta
import math


def log_to_results(str_to_log):
    fr = open("results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_errors(str_to_log):
    fr = open("errors.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_trades(str_to_log):
    fr = open("trades.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_evol(str_to_log):
    fr = open("evol.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


# import numpy as npfrom binance.client import Client

ftx_client = ftx.FtxClient(
    api_key='',
    api_secret='',
    subaccount_name=''
)

# result = client.get_balances()
# print(result)

if os.path.exists("results.txt"):
    os.remove("results.txt")

if os.path.exists("errors.txt"):
    os.remove("errors.txt")

if os.path.exists("trades.txt"):
    os.remove("trades.txt")

if os.path.exists("evol.txt"):
    os.remove("evol.txt")

for fg in glob.glob("CS_*.txt"):
    os.remove(fg)

list_results = []
results_count = 0

stop_thread = False


def my_thread(name):
    global ftx_client, list_results, results_count

    log_to_evol(str(datetime.now()))

    while not stop_thread:

        dict_evol = {}

        new_results_found = False

        markets = requests.get('https://ftx.com/api/markets').json()
        df = pd.DataFrame(markets['result'])
        df.set_index('name')

        for index, row in df.iterrows():
            symbol = row['name']
            symbol_type = row['type']

            # print("scanning", symbol, symbol_type)

            delta_time = 60 * 60 * 2

            data = ftx_client.get_historical_data(
                market_name=symbol,
                resolution=60 * 60,
                limit=10000,
                start_time=float(round(time.time())) - delta_time,
                end_time=float(round(time.time())))

            pd.set_option('display.max_columns', 10)
            pd.set_option('display.expand_frame_repr', False)

            dframe = pd.DataFrame(data)

            # dframe.reindex(index=dframe.index[::-1])
            dframe = dframe.iloc[::-1]

            # print(dframe)

            # for indexdf, rowdf in dframe.iterrows():
            #     print(rowdf)

            # print(symbol, dframe['startTime'].iloc[0], dframe['open'].iloc[0], dframe['high'].iloc[0], dframe['low'].iloc[0], dframe['close'].iloc[0], dframe['volume'].iloc[0])
            # print(symbol, dframe['startTime'].iloc[-1], dframe['open'].iloc[-1], dframe['high'].iloc[-1], dframe['low'].iloc[-1], dframe['close'].iloc[-1], dframe['volume'].iloc[-1])

            try:
                if dframe['volume'].iloc[0] < 1000000:
                    continue
            except:
                continue

            try:
                if not math.isnan(dframe['volume'].iloc[0]) and not math.isnan(dframe['volume'].iloc[-1]):
                    if dframe['volume'].iloc[-1] > 0:
                        print(symbol + " VOL EVOL = " + str(dframe['volume'].iloc[0] / dframe['volume'].iloc[-1]) + "    " + str(dframe['volume'].iloc[0]) + " " + str(
                            dframe['volume'].iloc[-1]))
                        log_to_results(symbol + " VOL EVOL = " + str(dframe['volume'].iloc[0] / dframe['volume'].iloc[-1]) + "    " + str(dframe['volume'].iloc[0]) + " " + str(
                            dframe['volume'].iloc[-1]))
            except:
                continue

            # if len(data) > 1:
            #     print(data[1])
            #     for info in data:
            #         startTime = info['startTime']
            #         vol = info['volume']
            #         print(startTime, vol)
            # else:
            #     print("no data for", symbol)


x = threading.Thread(target=my_thread, args=(1,))
x.start()
