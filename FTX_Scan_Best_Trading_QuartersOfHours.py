# HIGHLY EXPERIMENTAL :) IT WILL PRODUCE ONE OUTPUT FILE PER TOKEN AND SHOW THE SUM(%) OF EVOLUTION PER HOUR
# YOU WILL DISCOVER AMAZING STUFF WITH THIS CODE !!!! AND MIGHT BE RICH THANKS TO IT !!!!

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


def scan_one(symbol):
    global num_req
    # print("scan one : " + symbol)

    resolution = 60 * 15  # set the resolution of one japanese candlestick here
    nb_candlesticks = 5010 #24 * 5  # set the number of backward japanese candlesticks to retrieve from FTX api
    delta_time = resolution * nb_candlesticks

    # while not stop_thread:
    list_results.clear()

    try:
        data = ftx_client.get_historical_data(
            market_name=symbol,
            resolution=resolution,
            limit=10000,
            start_time=float(round(time.time())) - delta_time,
            end_time=float(round(time.time())))
    except requests.exceptions.HTTPError:
        log_to_errors(str(datetime.now()) + " HTTPError for " + symbol)
        print(str(datetime.now()) + "HTTPError for" + symbol)
        time.sleep(1)
    except requests.exceptions.ConnectionError:
        log_to_errors(str(datetime.now()) + " ConnectionError for " + symbol)
        print(str(datetime.now()) + " ConnectionError for " + symbol)
        time.sleep(1)
    except ValueError:  # seems not catched
        log_to_errors(str(datetime.now()) + " ValueError for " + symbol)
        print(str(datetime.now()) + " ValueError for " + symbol)
        time.sleep(1)
    except urllib3.exceptions.InvalidChunkLength:  # seems not catched
        log_to_errors(str(datetime.now()) + " InvalidChunkLength for " + symbol)
        print(str(datetime.now()) + " InvalidChunkLength for " + symbol)
        time.sleep(1)
    except urllib3.exceptions.ProtocolError:
        log_to_errors(str(datetime.now()) + " ProtocolError for " + symbol)
        print(str(datetime.now()) + " ProtocolError for " + symbol)
        time.sleep(1)
    except requests.exceptions.ChunkedEncodingError:
        log_to_errors(str(datetime.now()) + " ChunkedEncodingError for " + symbol)
        print(str(datetime.now()) + " ChunkedEncodingError for " + symbol)
        time.sleep(1)

    dframe = pd.DataFrame(data)

    dframe.reindex(index=dframe.index[::-1])
    # dframe = dframe.iloc[::-1]

    close0 = 0
    open0 = 0

    # pd.set_option('display.max_columns', 10)
    # pd.set_option('display.expand_frame_repr', False)
    # print(dframe)

    # print("scanning " + symbol)

    n = -1

    closep = []
    openp = []
    lowp = []
    highp = []
    timep = []

    if dframe.empty:
        return

    show_if_cannot_get_all_candlesticks_data = True
    i = 0
    try:
        for i in range(0, nb_candlesticks):
            closep.append(dframe['close'].iloc[n - i])
            openp.append(dframe['open'].iloc[n - i])
            lowp.append(dframe['low'].iloc[n - i])
            highp.append(dframe['high'].iloc[n - i])
            timep.append(dframe['startTime'].iloc[n - i])
    except IndexError:
        if show_if_cannot_get_all_candlesticks_data:
            log_to_errors(str(datetime.now()) + " cannot get all candlesticks data for " + symbol + " : " + str(i) + " candlesticks have been retrieved instead of " + str(
                nb_candlesticks) + " = " + str(round(i / 15, 2)) + " * 15min instead of " + str(nb_candlesticks / 15))
            print(str(datetime.now()) + " cannot get all candlesticks data for " + symbol + " : " + str(i) + " candlesticks have been retrieved instead of " + str(
                nb_candlesticks) + " = " + str(round(i / 15, 2)) + " * 15min instead of " + str(nb_candlesticks / 15))
            # log_to_errors("i = " + str(i))
        nb_candlesticks = i
        # time.sleep(1)
        pass
    except KeyError:
        log_to_errors(str(datetime.now()) + " cannot get candlesticks data for " + symbol)
        print(str(datetime.now()) + " cannot get candlesticks data for " + symbol)
        time.sleep(1)
        return

    result_ok = True
    # for i in range(0, nb_candlesticks):
    #     if closep[i] > openp[i]:
    #         result_ok = True
    #     else:
    #         result_ok = False
    #         break

    # set the conditions to meet for the scanning of the japanese candlesticks here
    if result_ok:
        close_evol = closep[0] / openp[0]
        dic_evol[symbol] = close_evol
        symbol_filename = str.replace(symbol, "-", "_").replace("/", "_")
        symbol_filename = "scan_" + symbol_filename + ".txt"

        # log_to_file(symbol_filename, "DATE/TIME" + ";SYMBOL" + ";OPEN" + ";HIGH" + ";LOW" + ";CLOSE" + ";EVOL % CLOSE/HIGH")

        hour_evol = {}
        minute_evol = {}

        for i in range(0, nb_candlesticks):
            # list_results.append([timep[i], symbol, openp[i], closep[i], lowp[i], highp[i]])

            o = openp[i]
            c = closep[i]
            evol_close_open = round(((c - o) / c) * 100, 2)

            o = "{:.8f}".format(openp[i], 8).replace('.', ',')
            c = "{:.8f}".format(closep[i], 8).replace('.', ',')
            l = "{:.8f}".format(lowp[i], 8).replace('.', ',')
            h = "{:.8f}".format(highp[i], 8).replace('.', ',')

            # log_to_results(str(timep[i]) + " " + symbol + " O=" + o + " H=" + h + " L=" + l + " C=" + c + " " + str(evol_close_open))

            pddate = pd.to_datetime(timep[i])
            for hour in range(0, 24):
                for minute in [0, 15, 30, 45]:
                    if pddate.hour == hour and pddate.minute == minute:
                        if str(hour) + ":" + str(minute) in minute_evol.keys():
                            current_minute_evol = minute_evol[str(hour) + ":" + str(minute)]
                            new_minute_evol = current_minute_evol + evol_close_open
                            minute_evol[str(hour) + ":" + str(minute)] = new_minute_evol
                        else:
                            minute_evol[str(hour) + ":" + str(minute)] = evol_close_open

                    # print(str(timep[i]) + " " + symbol + " O=" + o + " H=" + h + " L=" + l + " C=" + c + " " + str(evol_close_open))

                    # if symbol == "BTC/USD":
                    # log_to_file(symbol_filename, str(timep[i]) + ";" + symbol + ";" + o + ";" + h + ";" + l + ";" + c + ";" + str(evol_close_open).replace('.', ','))

        sorted_d = sorted(minute_evol.items(), key=operator.itemgetter(1), reverse=True)
        for key, val in sorted_d:
            log_to_file(symbol_filename, key + "h : " + str(round(val, 8)))

        symbol_best_hour = sorted_d[0][0]
        symbol_best_evol = sorted_d[0][1]

        best_minute_evol.append([symbol, symbol_best_hour, symbol_best_evol, nb_candlesticks])

        # log_to_file(symbol_filename, str(sorted_d))

        log_to_file(symbol_filename, "")

    time.sleep(1)


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

    best_minute_evol.sort(key=operator.itemgetter(2), reverse=True)
    # log_to_results(str(best_hourly_evol))
    for symbol, hour, value, nb_candlesticks in best_minute_evol:
        justif = " " * (20 - len(symbol))
        log_to_results(symbol + justif + " " + hour + "h" + (4 * " ") + str(round(value, 2)) + "%" + (4 * " ") + "calculated on " + str(nb_candlesticks) + " candlesticks (" + str(
            round(nb_candlesticks / 24, 2)) + " days)")

    time.sleep(1)

    stop_thread = True


x = threading.Thread(target=main_thread, args=(1,))
x.start()


