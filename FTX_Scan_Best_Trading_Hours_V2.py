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

import urllib3


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


def log_to_debug(str_to_log):
    fr = open("debug.txt", "a")
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
    subaccount_name='TrixStrategy'
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

for fg in glob.glob("debug.txt"):
    os.remove(fg)

list_results = []
results_count = 0

stop_thread = False

dic_evol = {}
dic_timestamp = {}
dic_last_price = {}
num_req = 0

best_hourly_evol = []
best_minute_evol = []

log_data_history_to_files = False   # This option is for logging data history to one file per symbol (eg. scan_ETH_USD.txt)


def scan_one(symbol):
    global num_req
    # print("scan one : " + symbol)

    resolution = 60 * 1  # set the resolution of one japanese candlestick here
    max_block_of_5000_download = 2  # set to -1 for unlimited blocks (all data history)

    list_results.clear()

    unixtime_endtime = time.time()
    converted_endtime = datetime.utcfromtimestamp(unixtime_endtime)
    # print("current unix time = " + str(unixtime_endtime))
    # print("converted_endtime = " + str(converted_endtime))
    tosubtract = resolution * 5000  # 60 * 60 * 1 * 5000
    # print("to substract in seconds = " + str(tosubtract))
    newunixtime_starttime = unixtime_endtime - tosubtract
    converted_starttime = datetime.utcfromtimestamp(newunixtime_starttime)
    # print("new unix time = " + str(newunixtime_starttime))
    # print("new converted_starttime = " + str(converted_starttime))

    data = []

    end_of_data_reached = False

    symbol_filename = "scan_" + str.replace(symbol, "-", "_").replace("/", "_") + ".txt"

    current_block_of_5000_download = 0
    max_block_of_5000_download_reached = False

    while not end_of_data_reached and not max_block_of_5000_download_reached:

        downloaded_data = ftx_client.get_historical_data(
            market_name=symbol,
            resolution=resolution,
            limit=1000000,
            start_time=newunixtime_starttime,
            end_time=unixtime_endtime)

        converted_endtime = datetime.utcfromtimestamp(unixtime_endtime)
        converted_starttime = datetime.utcfromtimestamp(newunixtime_starttime)

        print(symbol + " : downloaded_data size = " + str(len(downloaded_data)) + " from " + str(converted_starttime) + " to " + str(converted_endtime))
        data.extend(downloaded_data)

        unixtime_endtime = newunixtime_starttime
        newunixtime_starttime = newunixtime_starttime - tosubtract

        if len(downloaded_data) == 0:
            print(symbol + " : end of data from server reached")
            end_of_data_reached = True

        if max_block_of_5000_download != -1:
            current_block_of_5000_download += 1
            if current_block_of_5000_download >= max_block_of_5000_download:
                print(symbol + " : max number of block of 5000 reached")
                max_block_of_5000_download_reached = True

    data.sort(key=lambda x: pd.to_datetime(x['startTime']))

    if log_data_history_to_files:
        for oneline in data:
            log_to_file(symbol_filename, str(oneline))

    dframe = pd.DataFrame(data)

    dframe.reindex(index=dframe.index[::-1])

    n = -1

    closep = []
    openp = []
    lowp = []
    highp = []
    timep = []

    if dframe.empty:
        return

    i = 0
    for i in range(0, len(data)):
        closep.append(dframe['close'].iloc[n - i])
        openp.append(dframe['open'].iloc[n - i])
        lowp.append(dframe['low'].iloc[n - i])
        highp.append(dframe['high'].iloc[n - i])
        timep.append(dframe['startTime'].iloc[n - i])

    hour_evol = {}

    for i in range(0, len(data)):
        # list_results.append([timep[i], symbol, openp[i], closep[i], lowp[i], highp[i]])

        o = openp[i]
        c = closep[i]
        evol_close_open = round(((c - o) / c) * 100, 2)

        o = "{:.8f}".format(openp[i], 8).replace('.', ',')
        c = "{:.8f}".format(closep[i], 8).replace('.', ',')
        l = "{:.8f}".format(lowp[i], 8).replace('.', ',')
        h = "{:.8f}".format(highp[i], 8).replace('.', ',')

        # log_to_results(str(timep[i]) + " " + symbol + " O=" + o + " H=" + h + " L=" + l + " C=" + c + " " + str(evol_close_open))
        # log_to_results(str(timep[i]) + " " + symbol + " O=" + o + " H=" + h + " L=" + l + " C=" + c + " " + str(evol_close_open))

        pddate = pd.to_datetime(timep[i])
        for hour in range(0, 24):
            if pddate.hour == hour:
                if str(hour) in hour_evol.keys():
                    current_hour_evol = hour_evol[str(hour)]
                    new_hour_evol = current_hour_evol + evol_close_open
                    hour_evol[str(hour)] = new_hour_evol
                else:
                    hour_evol["{:0>2d}".format(hour)] = evol_close_open

                # print(str(timep[i]) + " " + symbol + " O=" + o + " H=" + h + " L=" + l + " C=" + c + " " + str(evol_close_open))

                # if symbol == "BTC/USD":
                # log_to_file(symbol_filename, str(timep[i]) + ";" + symbol + ";" + o + ";" + h + ";" + l + ";" + c + ";" + str(evol_close_open).replace('.', ','))

    sorted_d = sorted(hour_evol.items(), key=operator.itemgetter(1), reverse=True)
    for key, val in sorted_d:
        log_to_file(symbol_filename, key + "h : " + str(round(val, 8)))

    symbol_best_hour = sorted_d[0][0]
    symbol_best_evol = sorted_d[0][1]

    best_hourly_evol.append([symbol, symbol_best_hour, symbol_best_evol, len(data)])

    # log_to_file(symbol_filename, str(sorted_d))

    log_to_file(symbol_filename, "")


threads = []


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
        # if not symbol == "ETH/USD":
        #     continue

        if not symbol.endswith("/USD"):
            continue

        try:
            t = threading.Thread(target=scan_one, args=(symbol,))
            threads.append(t)
            t.start()
        except requests.exceptions.ConnectionError:
            continue

    for tt in threads:
        tt.join()

    print(str(datetime.now()) + " All threads started.")
    log_to_results(str(datetime.now()) + " All threads started.")

    print(str(datetime.now()) + " All threads finished.")
    log_to_results(str(datetime.now()) + " All threads finished.")

    best_hourly_evol.sort(key=operator.itemgetter(2), reverse=True)
    # log_to_results(str(best_hourly_evol))
    for symbol, hour, value, nb_candlesticks in best_hourly_evol:
        justif = " " * (20 - len(symbol))
        log_to_results(symbol + justif + " " + hour + "h" + (4 * " ") + str(round(value, 2)) + "%" + (4 * " ") + "calculated on " + str(nb_candlesticks) + " candlesticks (" + str(
            round(nb_candlesticks / 24, 2)) + " days)")

    time.sleep(1)

    stop_thread = True


x = threading.Thread(target=main_thread, args=(1,))
x.start()
