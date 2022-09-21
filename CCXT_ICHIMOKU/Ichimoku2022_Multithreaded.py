import sys

import os
import ccxt
import pandas as pd
from datetime import datetime
import time
import threading
import ta

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.expand_frame_repr', True)


def log_to_results(str_to_log):
    fr = open("results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_log():
    if os.path.exists("results.txt"):
        os.remove("results.txt")

delete_results_log()

# exchange = ccxt.binance()
exchange = ccxt.ftx()

# for tf in exchange.timeframes:
#     print(tf)

# binance.timeframes {'1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m', '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h', '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'}
# exchange.set_sandbox_mode(True)

markets = exchange.fetch_markets()

dict_results = {}


def execute_code(symbol, type_of_asset):
    global dict_results

    #print(10 * "*", symbol, type_of_asset, exchange.name, 10 * "*")

    for tf in exchange.timeframes:

        try:

            result = exchange.fetch_ohlcv(symbol, tf, limit=52)
            # print(tf, symbol, result)
            dframe = pd.DataFrame(result)
            # print(dframe[0])  # UTC timestamp in milliseconds, integer
            # print(dframe[1])
            # print(dframe[2])
            # print(dframe[3])
            # print(dframe[4])

            dframe['timestamp'] = pd.to_numeric(dframe[0])
            dframe['open'] = pd.to_numeric(dframe[1])
            dframe['high'] = pd.to_numeric(dframe[2])
            dframe['low'] = pd.to_numeric(dframe[3])
            dframe['close'] = pd.to_numeric(dframe[4])

            dframe['ICH_SSB'] = ta.trend.ichimoku_b(dframe['high'], dframe['low'], window2=26, window3=52).shift(26)
            # print(dframe['ICH_SSB'])

            dframe['ICH_SSA'] = ta.trend.ichimoku_a(dframe['high'], dframe['low'], window1=9, window2=26).shift(26)
            # print(dframe['ICH_SSA'])

            dframe['ICH_KS'] = ta.trend.ichimoku_base_line(dframe['high'], dframe['low'])
            # print(dframe['ICH_KS'])

            dframe['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframe['high'], dframe['low'])
            # print(dframe['ICH_TS'])

            dframe['ICH_CS'] = dframe['close'].shift(-26)
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

            price_open = dframe['open'].iloc[-1]
            price_high = dframe['high'].iloc[-1]
            price_low = dframe['low'].iloc[-1]
            price_close = dframe['close'].iloc[-1]
            # print("price_open", price_open)
            # print("price_high", price_high)
            # print("price_low", price_low)
            # print("price_close", price_close)

            price_open_chikou = dframe['open'].iloc[-27]
            price_high_chikou = dframe['high'].iloc[-27]
            price_low_chikou = dframe['low'].iloc[-27]
            price_close_chikou = dframe['close'].iloc[-27]
            # print("price_open_chikou", price_open_chikou)
            # print("price_high_chikou", price_high_chikou)
            # print("price_low_chikou", price_low_chikou)
            # print("price_close_chikou", price_close_chikou)

            tenkan_chikou = dframe['ICH_TS'].iloc[-27]
            kijun_chikou = dframe['ICH_KS'].iloc[-27]
            ssa_ichimoku = dframe['ICH_SSA'].iloc[-27]
            ssb_ichimoku = dframe['ICH_SSB'].iloc[-27]
            # print("tenkan_chikou", tenkan_chikou)
            # print("kijun_chikou", kijun_chikou)
            # print("ssa_ichimoku", ssa_ichimoku)
            # print("ssb_ichimoku", ssb_ichimoku)

            if price_close > ssa and price_close > ssb and price_close > tenkan and price_close > kijun:
                # print(tf, "symbol ok", symbol)
                # log_to_results(tf + " " + "symbol ok" + " " + symbol)

                str_link = ""
                if exchange.name.lower() == "ftx":
                    if type_of_asset == "future":
                        str_link = "https://tradingview.com/chart/?symbol=FTX%3A" + symbol.replace("-", "") #+ "&interval=" + str(interval)
                    elif type_of_asset == "spot":
                        str_link += "https://tradingview.com/chart/?symbol=FTX%3A" + symbol.replace("/", "") #+ "&interval=" + str(interval)

                key = symbol + " " + type_of_asset
                if key in dict_results:
                    dict_results[key] = dict_results[key] + ' ' + tf
                else:
                    dict_results[key] = tf

                #print(str(dict_results))
                print(type_of_asset, symbol, dict_results[key])

        except:
            # print(tf, symbol, sys.exc_info())  # for getting more details remove this line and add line exit(-1) just before the "pass" function
            pass


maxthreads = 500
threadLimiter = threading.BoundedSemaphore(maxthreads)


def scan_one(symbol, type_of_asset):
    threadLimiter.acquire()
    try:
        execute_code(symbol, type_of_asset)
    finally:
        threadLimiter.release()


threads = []

# print(markets)
for oneline in markets:
    symbol = oneline['id']

    active = oneline['active']
    type_of_asset = oneline['type']

    if active and type_of_asset == "future": # and (symbol.endswith("USDT") or (symbol.endswith("USD"))):  # == symbol: #'BTCUSDT':
        try:
            t = threading.Thread(target=scan_one, args=(symbol, type_of_asset))
            threads.append(t)
            t.start()
        except:
            pass

for tt in threads:
    tt.join()

# log_to_results(str(dict_results))
# print(dict_results)

# for k in dict_results:
#     log_to_results(k + " " + dict_results[k])

for k in sorted(dict_results, key=lambda k: len(dict_results[k])):
    log_to_results(k + " " + dict_results[k])
