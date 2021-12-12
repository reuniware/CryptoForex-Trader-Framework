import os
from datetime import datetime

# import ftx
import pandas as pd
import requests
import threading

# import numpy as np

# client = ftx.FtxClient(
#     api_key='',
#     api_secret='',
#     subaccount_name=''
# )
# result = client.get_balances()

symbolInfoInit = {}
symbolInfo = {}
symbolEvol = {}
initial_time = datetime.now()

stop_thread = False


def my_thread(name):
    global symbolInfo, symbolInfoInit, symbolEvol, stop_thread

    symbol_growing = {}

    if os.path.exists("results.txt"):
        os.remove("results.txt")

    while not stop_thread:
        insert_separator = False

        markets = requests.get('https://ftx.com/api/markets').json()
        df = pd.DataFrame(markets['result'])
        df.set_index('name')
        for index, row in df.iterrows():
            symbol = row['name']
            price = float(row['last'])

            if symbol in symbolInfo:
                if price > symbolInfo[symbol]:
                    symbolInfo[symbol] = price
                    # print(datetime.now(), "growing", symbol, "evol=", price/symbolInfoInit[symbol], "init price=", symbolInfoInit[symbol], "current price=", price, "scan time=", datetime.now() - initial_time)
                    symbol_growing[symbol] = price / symbolInfoInit[symbol]
                    insert_separator = True
                else:
                    symbol_growing[symbol] = 0
            else:
                symbolInfoInit[symbol] = price
                symbolInfo[symbol] = price
                symbol_growing[symbol] = 0

            stop_thread = False

        f = open("results.txt", "a")

        sort_orders = sorted(symbol_growing.items(), key=lambda x: x[1], reverse=True)
        show = True
        k = 0
        for i in sort_orders:
            if i[1] > 0:
                symbol = i[0]
                evol = round(i[1] * 100 - 100, 2)
                curr_price = symbolInfo[symbol]

                percent_avg_evol_per_sec = 0
                diff_sec = (datetime.now() - initial_time).seconds
                if diff_sec > 0:
                    # percent_avg_evol_per_sec = round((symbolInfo[symbol]/symbolInfoInit[symbol]*100-100) / diff_sec, 3)
                    percent_avg_evol_per_sec = (symbolInfo[symbol] / symbolInfoInit[symbol] * 100 - 100) / diff_sec

                print(datetime.now(), k, symbol, (24 - len(symbol)) * " ", str(evol) + " %", (16 - len(str(evol) + " %")) * " ", "init price=", symbolInfoInit[symbol],
                      (12 - len(str(symbolInfoInit[symbol]))) * " ", "current price=", curr_price, (12 - len(str(curr_price))) * " ", "scan time=",
                      datetime.now() - initial_time, 4 * " ", "percent_avg_evol_per_min=", str(60 * percent_avg_evol_per_sec) + " %")

                strn = str(datetime.now()) + ' ' + str(k) + ' ' + symbol + ' ' + (24 - len(symbol)) * " " + ' ' + str(evol) + " %" + ' ' + (
                        16 - len(str(evol) + " %")) * " " + ' ' + "init price=" + ' ' + str(symbolInfoInit[symbol]) + ' ' + (
                               12 - len(str(symbolInfoInit[symbol]))) * " " + ' ' + "current price=" + ' ' + str(curr_price) + ' ' + (
                               12 - len(str(curr_price))) * " " + ' ' + "scan time=" + ' ' + str(
                    datetime.now() - initial_time) + ' ' + 4 * " " + ' ' + "percent_avg_evol_per_min=" + ' ' + str(60 * percent_avg_evol_per_sec) + " %"

                f.write(strn + '\n')

        if insert_separator:
            f.write(100*'*' + '\n')

        f.close()

        insert_separator = False


x = threading.Thread(target=my_thread, args=(1,))
x.start()
