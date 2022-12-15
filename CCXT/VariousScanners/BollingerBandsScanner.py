import sys

import os
import ccxt
import pandas as pd
from datetime import datetime
import time
import threading
import ta
import argparse
import signal
from ta.volatility import BollingerBands

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.expand_frame_repr', True)


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)


signal.signal(signal.SIGINT, signal_handler)


def log_to_errors(str_to_log):
    fr = open("errors.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_results(str_to_log):
    fr = open("results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_results_evol(str_to_log):
    fr = open("results_evol.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_log():
    if os.path.exists("results.txt"):
        os.remove("results.txt")


def delete_results_evol_log():
    if os.path.exists("results_evol.txt"):
        os.remove("results_evol.txt")


def delete_errors_log():
    if os.path.exists("errors.txt"):
        os.remove("errors.txt")


def log_to_results_temp(str_to_log, exchange_id):
    fr = open("results_temp_" + exchange_id + ".txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_temp_log(exchange_id):
    if os.path.exists("results_temp_" + exchange_id + ".txt"):
        os.remove("results_temp_" + exchange_id + ".txt")


delete_errors_log()

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


# function not used for now (but might be useful for a counter such as 1/xxx 2/xxx etc...)
def get_number_of_active_assets_for_exchange(exchange_id):
    nb_active_assets = 0
    arg_exchange = exchange_id
    if arg_exchange in exchanges:
        exchange = exchanges[arg_exchange]
        try:
            markets = exchange.fetch_markets()
            for oneline in markets:
                symbol = oneline['id']
                active = oneline['active']
                if active is True:
                    # print(symbol, end=' ')
                    nb_active_assets += 1
            # print("")
            # print("number of active assets =", nb_active_assets)
        except (ccxt.ExchangeError, ccxt.NetworkError, ccxt.DDoSProtection):
            print("Exchange seems not available (maybe too many requests). Will stop now.")
            # exit(-10002)
            os.kill(os.getpid(), 9)
            sys.exit(-999)
            # time.sleep(5)
        except:
            print(sys.exc_info())
            exit(-10003)
    return nb_active_assets


# print(get_number_of_active_assets_for_exchange("binance"))
# exit(-1000)

parser = argparse.ArgumentParser()
parser.add_argument("-e", "--exchange", help="set exchange", required=False)
parser.add_argument('-g', '--get-exchanges', action='store_true', help="get list of available exchanges")
parser.add_argument('-a', '--get-assets', action='store_true', help="get list of available assets")
parser.add_argument('-f', '--filter-assets', help="filter assets")
parser.add_argument('-r', '--retry', action='store_true', help="retry until exchange is available (again)")
args = parser.parse_args()
print("args.exchange =", args.exchange)
print("args.get-exchanges", args.get_exchanges)
print("args.get-assets", args.get_assets)
print("args.filter", args.filter_assets)
print("args.retry", args.retry)

print("INELIDA Bollinger Bands Scanner v1.0 - https://www.botmonster.fr")
print("Scan started at :", str(datetime.now()))

# if a debugger is attached then set arbitrary arguments for debugging (exchange...)
if sys.gettrace() is not None:
    args.exchange = "binance"
    args.filter_assets = "*usdt"

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
            except (ccxt.ExchangeError, ccxt.NetworkError, ccxt.DDoSProtection):
                print("Exchange seems not available (maybe too many requests). Will stop now.")
                # exit(-10002)
                os.kill(os.getpid(), 9)
                sys.exit(-999)
                # time.sleep(5)
            except:
                print(sys.exc_info())
                exit(-10003)
    exit(-510)

filter_assets = ""
if args.filter_assets is not None:
    if args.filter_assets.strip() != "":
        filter_assets = args.filter_assets.strip().upper()
        if ("*" in filter_assets and filter_assets.startswith("*") == False and filter_assets.endswith("*") == False) \
                or ("*" in filter_assets and filter_assets.startswith("*") == True and filter_assets.endswith("*") == True):
            print("Only one '*' wildcard must be at the start or at the end of the string and not in the middle (not supported).")
            exit(-10004)

retry = args.retry
# end of arguments parsing here

debug_delays = False
delay_thread = 0.1  # delay between each start of a thread (in seconds, eg. 0.5 for 500ms, 1 for 1s...)
delay_request = 0.250  # delay between each request inside of a thread

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

delete_results_temp_log(exchange.id)

# exchange = ccxt.binance()
# exchange = ccxt.ftx()

# for tf in exchange.timeframes:
#     print(tf)

# binance.timeframes {'1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m', '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h', '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'}
# exchange.set_sandbox_mode(True)


dict_results = {}
dict_results_binary = {}
dict_results_evol = {}
highest_percent_evol = 0


def execute_code(symbol, type_of_asset, exchange_id):
    global dict_results, highest_percent_evol

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

    binary_result = ""

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

            # Add Bollinger Bands features
            indicator_bb = BollingerBands(close=dframe["close"], window=20, window_dev=2)
            dframe['bb_middle'] = indicator_bb.bollinger_mavg()
            dframe['bb_high'] = indicator_bb.bollinger_hband()
            dframe['bb_low'] = indicator_bb.bollinger_lband()
            # print(dframe['bb_middle'])

            price_open = dframe['open'].iloc[-1]
            price_high = dframe['high'].iloc[-1]
            price_low = dframe['low'].iloc[-1]
            price_close = dframe['close'].iloc[-1]
            # print("price_open", price_open)
            # print("price_high", price_high)
            # print("price_low", price_low)
            # print("price_close", price_close)

            condition = price_open > dframe['bb_high'].iloc[-1] and price_close < dframe['bb_high'].iloc[-1]

            if condition:
                print(symbol, tf, "[A atteint la bande haute]", "[Short possible]", "BBHIGH=", "{:.4f}".format(dframe['bb_high'].iloc[-1]), "current price=", "{:.4f}".format(price_close), "BBMID(TP)=", "{:.4f}".format(dframe['bb_middle'].iloc[-1]))
            # dev force condition - end

            condition = price_open < dframe['bb_low'].iloc[-1] and price_close > dframe['bb_low'].iloc[-1]

            if condition:
                print(symbol, tf, "[A atteint la bande basse]",  "[Long possible]", "BBLOW=", "{:.4f}".format(dframe['bb_low'].iloc[-1]), "current price=", "{:.4f}".format(price_close), "BBMID(TP)=", "{:.4f}".format(dframe['bb_middle'].iloc[-1]))


            if not condition:
                binary_result += "0"

            if condition:
                binary_result += "1"

                if key in dict_results:
                    dict_results[key] = dict_results[key] + ' ' + tf
                else:
                    dict_results[key] = tf

                # print(str(dict_results))
                # print(exchange_id, symbol, type_of_asset, dict_results[key])

        except:
            # print(tf, symbol, sys.exc_info())  # for getting more details remove this line and add line exit(-1) just before the "pass" function
            log_to_errors(str(datetime.now()) + " " + tf + " " + symbol + " " + str(sys.exc_info()))
            binary_result += "0"
            pass

        if delay_request > 0:
            if debug_delays:
                print("applying delay_request of", delay_thread, "s after request on timeframe", tf, symbol)
            time.sleep(delay_request)

    # if key is in dict_results then that means that it has been detected
    if key in dict_results:
        if price_open_1d is not None and price_high_1d is not None and price_low_1d is not None and price_close_1d is not None:
            s_price_open_1d = "{:.8f}".format(price_open_1d)
            s_price_high_1d = "{:.8f}".format(price_high_1d)
            s_price_low_1d = "{:.8f}".format(price_low_1d)
            s_price_close_1d = "{:.8f}".format(price_close_1d)
            percent_evol_1d = (price_close_1d - price_open_1d) / price_open_1d * 100
            s_percent_evol_1d = "[{:.2f}".format(percent_evol_1d) + " %]"
        # print(exchange_id, symbol, type_of_asset, dict_results[key], "{:.8f}".format(price_open_1d, 4), s_price_open_1d, s_price_high_1d, s_price_low_1d, s_price_close_1d)

        str_to_log = str(datetime.now()) + " " + exchange_id + " " + symbol + " " + type_of_asset + " " + dict_results[key] + " " + s_percent_evol_1d

        symbol = key.split(" ")[0]
        str_link = ""  # "https://tradingview.com/chart/?symbol=" + exchange_id.upper() + ":" + symbol.replace("-", "").replace("/", "")
        #print(str_to_log + " " + str_link)

        # print(str_to_log + " " + "[Scoring = " + binary_result + " " + str(len(binary_result)) + str(int("".join(reversed(binary_result)), 2)) + "]")
        if percent_evol_1d > highest_percent_evol:
            highest_percent_evol = percent_evol_1d
            str_to_log += " *** new highest evol in %"

        log_to_results_temp(str_to_log + " " + str(price_close), exchange_id)

        # we reverse binary_result (higher timeframes have more importance than lower timeframes, for sorting, and tf scanning start with lower timeframes...)
        dict_results_binary[key] = str_to_log + " #" + "".join(reversed(binary_result))

    # if key is in dict_results then that means that it has been detected
    if key in dict_results:
        if symbol not in dict_results_evol:
            dict_results_evol[key] = percent_evol_1d


threadLimiter = threading.BoundedSemaphore()


def scan_one(symbol, type_of_asset, exchange_id):
    global threadLimiter
    threadLimiter.acquire()
    try:
        execute_code(symbol, type_of_asset, exchange_id)
    finally:
        threadLimiter.release()


def main_thread():
    maxthreads = 1
    delay_thread = 0
    delay_request = 0
    if exchange.id.lower() == "binance":
        maxthreads = 200
        print("setting maxthreads =", maxthreads, "for", exchange.id)
        delay_thread = 0  # 0.1  # delay between each start of a thread (in seconds, eg. 0.5 for 500ms, 1 for 1s...)
        delay_request = 0  # 0.250 # delay between each request inside of a thread
        print("setting delay_thread =", delay_thread, "for", exchange.id)
        print("setting delay_request =", delay_request, "for", exchange.id)
    elif exchange.id.lower() == "ftx":
        maxthreads = 100
        print("setting maxthreads =", maxthreads, "for", exchange.id)
        delay_thread = 0.1  # delay between each start of a thread (in seconds, eg. 0.5 for 500ms, 1 for 1s...)
        delay_request = 0.250  # delay between each request inside of a thread
        print("setting delay_thread =", delay_thread, "for", exchange.id)
        print("setting delay_request =", delay_request, "for", exchange.id)
    elif exchange.id.lower() == "gateio":
        maxthreads = 100
        print("setting maxthreads =", maxthreads, "for", exchange.id)
        delay_thread = 0.1  # delay between each start of a thread (in seconds, eg. 0.5 for 500ms, 1 for 1s...)
        delay_request = 0.250  # delay between each request inside of a thread
        print("setting delay_thread =", delay_thread, "for", exchange.id)
        print("setting delay_request =", delay_request, "for", exchange.id)
    elif exchange.id.lower() == "bitforex":
        maxthreads = 1
        print("setting maxthreads =", maxthreads, "for", exchange.id)
        delay_thread = 1  # delay between each start of a thread (in seconds, eg. 0.5 for 500ms, 1 for 1s...)
        delay_request = 1  # delay between each request inside of a thread
        print("setting delay_thread =", delay_thread, "for", exchange.id)
        print("setting delay_request =", delay_request, "for", exchange.id)
    else:
        maxthreads = 25
        print("setting default maxthreads =", maxthreads, "for", exchange.id)
        print("setting default delay_thread =", delay_thread, "for", exchange.id)
        print("setting default delay_request =", delay_request, "for", exchange.id)

    delete_results_log()
    delete_results_evol_log()
    log_to_results("Scan results at : " + str(datetime.now()))

    threadLimiter = threading.BoundedSemaphore(maxthreads)
    # print(threadLimiter)

    ok = False
    while ok is False:
        try:
            markets = exchange.fetch_markets()
            ok = True
            print("markets data obtained successfully")
        except (ccxt.ExchangeError, ccxt.NetworkError, ccxt.DDoSProtection):
            print("Exchange seems not available (maybe too many requests). Please wait and try again.")
            # exit(-10002)
            if retry is False:
                print("will not retry.")
                exit(-777)
            else:
                print("will retry in 5 sec")
                time.sleep(5)
        except:
            print(sys.exc_info())
            exit(-778)

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

        condition_ok = active and filter_assets in symbol
        if filter_assets.startswith("*"):
            new_filter_assets = filter_assets.replace("*", "")
            new_filter_assets = new_filter_assets.upper()
            condition_ok = active and symbol.endswith(new_filter_assets)
        elif filter_assets.endswith("*"):
            new_filter_assets = filter_assets.replace("*", "")
            new_filter_assets = new_filter_assets.upper()
            condition_ok = active and symbol.startswith(new_filter_assets)

        if condition_ok:  # and symbol == ("BTCUSDT"):  # and ((symbol.endswith("USDT")) or (symbol.endswith("USD"))):  # == symbol: #'BTCUSDT':
            try:
                t = threading.Thread(target=scan_one, args=(symbol, type_of_asset, exchange_id))
                threads.append(t)
                t.start()
                # print("thread started for", symbol)
                if delay_thread > 0:
                    if debug_delays:
                        print("applying delay_thread of", delay_thread, "s before next thread start")
                    time.sleep(delay_thread)

            except:
                pass

    start_time = time.time()

    for tt in threads:
        tt.join()

    end_time = time.time()

    print("--- %s seconds ---" % (end_time - start_time))

    for k in sorted(dict_results_binary, key=lambda k: int(dict_results_binary[k].split("#")[1], 2)):
        symbol = k.split(" ")[0]
        str_link = ""  # "https://tradingview.com/chart/?symbol=" + exchange_id.upper() + ":" + symbol.replace("-", "").replace("/", "")
        value = dict_results_binary[k]
        nspaces = 175 - len(str_link) - len(k + " " + dict_results_binary[k].split("#")[0])
        # if trending == True and ("1m" in value or "3m" in value or "5m" in value or "15m" in value):
        #     log_to_results(k + " " + dict_results_binary[k].split("#")[0] + nspaces * " " + str_link)
        # elif trending == False:
        log_to_results(k + " " + dict_results_binary[k].split("#")[0] + nspaces * " " + str_link)

    for k in sorted(dict_results_evol, key=lambda k: dict_results_evol[k]):
        symbol = k.split(" ")[0]
        str_link = ""  # "https://tradingview.com/chart/?symbol=" + exchange_id.upper() + ":" + symbol.replace("-", "").replace("/", "")
        log_to_results_evol(k + " " + "{:.2f}".format(dict_results_evol[k]) + " %" + 5 * " " + str_link)


mainThread = threading.Thread(target=main_thread, args=())
mainThread.start()
