import sys

import os
import ccxt
import pandas as pd
from datetime import datetime
import time
import threading
import ta
import argparse

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


def log_to_results_temp(str_to_log):
    fr = open("results_temp.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_temp_log():
    if os.path.exists("results_temp.txt"):
        os.remove("results_temp.txt")


delete_results_temp_log()


exchanges = {}  # a placeholder for your instances
for id in ccxt.exchanges:
    exchange = getattr(ccxt, id)
    exchanges[id] = exchange()
    # print(exchanges[id])
    try:
        ex = exchanges[id]
        # markets = ex.fetch_markets()
        # print(markets)
    except:
        continue

# exit(-500)

parser = argparse.ArgumentParser()
parser.add_argument("-e", "--exchange", help="set exchange", required=False)
parser.add_argument('-g', '--get-exchanges', action='store_true', help="get list of available exchanges")
parser.add_argument('-a', '--get-assets', action='store_true', help="get list of available assets")
parser.add_argument('-f', '--filter-assets', help="filter assets")
args = parser.parse_args()
print("args.exchange =", args.exchange)
print("args.get-exchanges", args.get_exchanges)
print("args.get-assets", args.get_assets)
print("args.filter", args.filter_assets)

print("INELIDA Scanner v1.0 - https://twitter.com/IchimokuTrader")
print("Scan started at :", str(datetime.now()))

# if a debugger is attached then set an arbitraty exchange for debugging
if sys.gettrace() is not None:
    args.exchange = "ftx"

if args.get_exchanges is True:
    for id in ccxt.exchanges:
        print(id, end=' ')
    print("")
    exit(-505)

if args.get_assets is True:
    if args.exchange is None:
        print("Please specify an exchange name")
    else:
        arg_exchange = args.exchange.lower().strip()
        if arg_exchange in exchanges:
            exchange = exchanges[arg_exchange]
            try:
                markets = exchange.fetch_markets()
                nb_active_assets = 0
                for oneline in markets:
                    symbol = oneline['id'] 
                    active = oneline['active']
                    if active is True:
                        print(symbol, end=' ')
                        nb_active_assets += 1
                print("")
                print("number of active assets =", nb_active_assets)
            except (ccxt.ExchangeError, ccxt.NetworkError):
                print("Exchange seems not available (maybe too many requests). Please wait and try again.")
                # exit(-10002)
                time.sleep(5)
            except:
                print(sys.exc_info())
                exit(-10003)
    exit(-510)

filter_assets = ""
if args.filter_assets is not None:
    if args.filter_assets.strip() != "":
        filter_assets = args.filter_assets.strip().upper()

exchange = None
if args.exchange is not None:
    arg_exchange = args.exchange.lower().strip()
    if arg_exchange in exchanges:
        print(arg_exchange, "is in list")
        exchange = exchanges[arg_exchange]
        # exit(-1)
    else:
        print("This exchange is not supported.")
        exit(-1)
else:
    print("no exchange specified.")
    exit(-2)

# exchange = ccxt.binance()
# exchange = ccxt.ftx()

# for tf in exchange.timeframes:
#     print(tf)

# binance.timeframes {'1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m', '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h', '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'}
# exchange.set_sandbox_mode(True)

ok = False
while ok is False:
    try:
        markets = exchange.fetch_markets()
        ok = True
    except (ccxt.ExchangeError, ccxt.NetworkError):
        print("Exchange seems not available (maybe too many requests). Please wait and try again.")
        # exit(-10002)
        time.sleep(5)
    except:
        print(sys.exc_info())
        exit(-10003)

dict_results = {}


def execute_code(symbol, type_of_asset, exchange_id):
    global dict_results

    # print(10 * "*", symbol, type_of_asset, exchange.id, 10 * "*")

    key = symbol + " " + type_of_asset + " " + exchange_id

    price_open_1d = None
    price_high_1d = None
    price_low_1d = None
    price_close_1d = None
    s_price_open_1d = ""
    s_price_high_1d = ""
    s_price_low_1d = ""
    s_price_close_1d = ""
    percent_evol_1d = None
    s_percent_evol_1d = ""


    for tf in exchange.timeframes:

        try:

            result = exchange.fetch_ohlcv(symbol, tf, limit=52 + 26)
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

            if tf == "1d":
                price_open_1d = dframe['open'].iloc[-1]
                price_high_1d = dframe['high'].iloc[-1]
                price_low_1d = dframe['low'].iloc[-1]
                price_close_1d = dframe['close'].iloc[-1]

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
            ssa_chikou = dframe['ICH_SSA'].iloc[-27]
            ssb_chikou = dframe['ICH_SSB'].iloc[-27]
            # print("tenkan_chikou", tenkan_chikou)
            # print("kijun_chikou", kijun_chikou)
            # print("ssa_chikou", ssa_chikou)
            # print("ssb_chikou", ssb_chikou)
            
            if price_close > ssa and price_close > ssb and price_close > tenkan and price_close > kijun \
                    and chikou > ssa_chikou and chikou > ssb_chikou and chikou > price_high_chikou \
                    and chikou > tenkan_chikou and chikou > kijun_chikou:
                # print(tf, "symbol ok", symbol)
                # log_to_results(tf + " " + "symbol ok" + " " + symbol)

                # key = symbol + " " + type_of_asset + " " + exchange_id
                if key in dict_results:
                    dict_results[key] = dict_results[key] + ' ' + tf
                else:
                    dict_results[key] = tf

                # print(str(dict_results))
                # print(exchange_id, symbol, type_of_asset, dict_results[key])

        except:
            # print(tf, symbol, sys.exc_info())  # for getting more details remove this line and add line exit(-1) just before the "pass" function
            pass

    if key in dict_results:
        if price_open_1d is not None and price_high_1d is not None and price_low_1d is not None and price_close_1d is not None:
            s_price_open_1d = "{:.8f}".format(price_open_1d)
            s_price_high_1d = "{:.8f}".format(price_high_1d)
            s_price_low_1d = "{:.8f}".format(price_low_1d)
            s_price_close_1d = "{:.8f}".format(price_close_1d)
            percent_evol_1d = (price_close_1d - price_open_1d)/price_open_1d*100
            s_percent_evol_1d = "[{:.2f}".format(percent_evol_1d) + " %]"
        #print(exchange_id, symbol, type_of_asset, dict_results[key], "{:.8f}".format(price_open_1d, 4), s_price_open_1d, s_price_high_1d, s_price_low_1d, s_price_close_1d)

        str_to_log = str(datetime.now()) + " " + exchange_id + " " + symbol + " " + type_of_asset + " " + dict_results[key] + " " + s_percent_evol_1d

        print(str_to_log)
        log_to_results_temp(str_to_log)


maxthreads = 1
if exchange.id.lower() == "binance":
    print("setting maxthreads for", exchange.id)
    maxthreads = 100
elif exchange.id.lower() == "ftx":
    print("setting maxthreads for", exchange.id)
    maxthreads = 100
elif exchange.id.lower() == "gateio":
    print("setting maxthreads for", exchange.id)
    maxthreads = 100

threadLimiter = threading.BoundedSemaphore(maxthreads)


def scan_one(symbol, type_of_asset, exchange_id):
    threadLimiter.acquire()
    try:
        execute_code(symbol, type_of_asset, exchange_id)
    finally:
        threadLimiter.release()


threads = []

# print(markets)
for oneline in markets:
    symbol = oneline['id']

    active = oneline['active']
    type_of_asset = oneline['type']
    exchange_id = exchange.id.lower()
    base = oneline['base']  # eg. BTC/USDT => base = BTC
    quote = oneline['quote']  # eg. BTC/USDT => quote = USDT
    # print(symbol, "base", base, "quote", quote)

    # print("eval", eval("exchange_id == 'ftx'"))

    # this condition could be commented (and then more assets would be scanned)
    if exchange_id == "ftx":
        if symbol.endswith('HEDGE/USD') or symbol.endswith('CUSDT/USDT') or symbol.endswith('BEAR/USDT') \
                or symbol.endswith('BEAR/USD') or symbol.endswith('BULL/USDT') or symbol.endswith('BULL/USD') \
                or symbol.endswith('HALF/USD') or symbol.endswith('HALF/USDT') or symbol.endswith('SHIT/USDT') \
                or symbol.endswith('SHIT/USD') or symbol.endswith('BEAR2021/USDT') or symbol.endswith('BEAR2021/USD') \
                or symbol.endswith('BVOL/USDT') or symbol.endswith('BVOL/USD'):
            continue

    if active and filter_assets in symbol:#and ((symbol.endswith("USDT")) or (symbol.endswith("USD"))):  # == symbol: #'BTCUSDT':
        try:
            t = threading.Thread(target=scan_one, args=(symbol, type_of_asset, exchange_id))
            threads.append(t)
            t.start()
            # print("thread started for", symbol)
        except:
            pass

start_time = time.time()

for tt in threads:
    tt.join()

end_time = time.time()

print("--- %s seconds ---" % (end_time - start_time))

# log_to_results(str(dict_results))
# print(dict_results)

# for k in dict_results:
#     log_to_results(k + " " + dict_results[k])

delete_results_log()

log_to_results("Scan results at : " + str(datetime.now()))

for k in sorted(dict_results, key=lambda k: len(dict_results[k])):

    value = k
    symbol = value.split()[0]
    type_of_asset = value.split()[1]

    exchange_name = exchange.id.lower()
    str_link = ""

    if type_of_asset in ("future", "swap"):
        str_link = "https://tradingview.com/chart/?symbol=" + exchange_name.upper() + ":" + symbol.replace("-", "") + "&interval=960"
    elif type_of_asset == "spot":
        str_link += "https://tradingview.com/chart/?symbol=" + exchange_name.upper() + ":" + symbol.replace("/", "") + "&interval=960"
    
    strpad = ""
    strpad = " " * (60 - len(str_link))

    log_to_results(k + " " + dict_results[k] + " " + strpad + str_link)
