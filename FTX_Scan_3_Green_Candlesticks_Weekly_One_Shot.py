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
import operator


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


def log_to_file(str_file, str_to_log):
    fr = open(str_file, "a")
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

for fg in glob.glob("scan_*.txt"):
    os.remove(fg)

list_results = []
results_count = 0

stop_thread = False

dic_evol = {}
dic_timestamp = {}
dic_last_price = {}
num_req = 0


def scan_one(symbol):
    global num_req
    # print("scan one : " + symbol)

    resolution = 60 * 60 * 24 * 7                  # set the resolution of one japanese candlestick here
    nb_candlesticks = 3                        # set the number of backward japanese candlesticks to retrieve from FTX api
    delta_time = resolution * nb_candlesticks

    # while not stop_thread:
    #     try:
    data = ftx_client.get_historical_data(
        market_name=symbol,
        resolution=resolution,
        limit=10000,
        start_time=float(round(time.time())) - delta_time,
        end_time=float(round(time.time())))

    dframe = pd.DataFrame(data)

    dframe.reindex(index=dframe.index[::-1])
    # dframe = dframe.iloc[::-1]

    close0 = 0
    open0 = 0
    try:
        # pd.set_option('display.max_columns', 10)
        # pd.set_option('display.expand_frame_repr', False)
        # print(dframe)

        n = -1

        closep = []
        openp = []
        lowp = []
        highp = []
        timep = []

        for i in range(0, nb_candlesticks):
            closep.append(dframe['close'].iloc[n - i])
            openp.append(dframe['open'].iloc[n - i])
            lowp.append(dframe['low'].iloc[n - i])
            highp.append(dframe['high'].iloc[n - i])
            timep.append(dframe['startTime'].iloc[n - i])

        # set the conditions to meet for the scanning of the japanese candlesticks here
        if closep[0] > openp[0] and closep[1] > openp[1] and closep[2] > openp[2]:
            close_evol = closep[0] / openp[0]
            dic_evol[symbol] = close_evol
            for i in range(0, nb_candlesticks):
                list_results.append([timep[i], symbol, openp[i], closep[i], lowp[i]])

    except BaseException as e:
        log_to_errors(str(datetime.now()) + " " + symbol + " Exception (1) : " + format(e) + " : " + str(close0) + " " + str(open0))
        pass

        # except Exception as e:
        #     # log_to_errors(str(datetime.now()) + " " + symbol + " Exception (2) : " + str(e))
        #     continue
        #
        # finally:
        #     time.sleep(0.25)


def main_thread(name):
    global ftx_client, list_results, results_count, num_req, stop_thread

    # while not stop_thread:

    markets = requests.get('https://ftx.com/api/markets').json()
    df = pd.DataFrame(markets['result'])
    df.set_index('name')

    for index, row in df.iterrows():
        symbol = row['name']
        symbol_type = row['type']

        # filter for specific symbols here
        if not symbol.endswith("-PERP"):
            continue

        try:
            y = threading.Thread(target=scan_one, args=(symbol,))
            y.start()
        except requests.exceptions.ConnectionError:
            continue

    print("All threads started.")

    while not stop_thread:
        sorted_d = dict(sorted(dic_evol.items(), key=operator.itemgetter(1), reverse=True))
        # log_to_results(str(datetime.now()) + " (" + str(num_req) + ') EVOL CLOSE/OPEN : ' + str(sorted_d))
        # print(str(datetime.now()) + " (" + str(num_req) + ') EVOL CLOSE/OPEN : ' + str(sorted_d))
        for key, value in sorted_d.items():
            log_to_results(str(datetime.now()) + " " + key + " " + str(value))
            print(str(datetime.now()) + " " + key + " " + str(value))

            for t, symbol, o, c, l in list_results:
                if symbol == key:
                    evol_close_open = round(((c - o) / c) * 100, 2)
                    j_s = " " * (16 - len(str(symbol)))
                    o = "{:.8f}".format(o)
                    j_o = " " * (15 - len(str(o)))
                    c = "{:.8f}".format(c)
                    j_c = " " * (15 - len(str(c)))
                    l = "{:.8f}".format(l)
                    j_l = " " * (15 - len(str(l)))
                    if evol_close_open > 0:
                        evol_close_open = "+" + "{:.2f}".format(evol_close_open)
                    print(10 * ' ', t, j_s + symbol, j_o, "O=", o, j_c, "C=", c, j_l, "L=" + l + "\t\t\t" + str(evol_close_open) + "%")

        print("All results written ok")

        stop_thread = True


x = threading.Thread(target=main_thread, args=(1,))
x.start()
