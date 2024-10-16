# Original work :
# https://github.com/yulz008/orb_cryptoBot
# This version is globalized to target all crypto assets available from Binance
# This version does not trade (the original work trades BTCUSDT)

#https://herrmann.tech/en/blog/2021/02/05/how-to-deal-with-international-data-formats-in-python.html

# pip install websocket-client
import sys
import threading

import json
import websocket
import ccxt

import time
from pa import Price_Action
import os

import signal

from datetime import datetime

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)

def log_to_results(str_to_log):
    fr = open("results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_log():
    if os.path.exists("results.txt"):
        os.remove("results.txt")


def log_to_pumps(str_to_log):
    fr = open("results_pumps.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_log_pumps():
    if os.path.exists("results_pumps.txt"):
        os.remove("results_pumps.txt")


def log_to_dumps(str_to_log):
    fr = open("results_dumps.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_log_dumps():
    if os.path.exists("results_dumps.txt"):
        os.remove("results_dumps.txt")


def log_to_pumps_and_dumps(str_to_log):
    fr = open("results_pumps_and_dumps.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_log_pumps_and_dumps():
    if os.path.exists("results_pumps_and_dumps.txt"):
        os.remove("results_pumps_and_dumps.txt")


def log_to_growing_up(str_to_log):
    fr = open("results_growing_up.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_log_growing_up():
    if os.path.exists("results_growing_up.txt"):
        os.remove("results_growing_up.txt")


def log_to_growing_down(str_to_log):
    fr = open("results_growing_down.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_log_growing_down():
    if os.path.exists("results_growing_down.txt"):
        os.remove("results_growing_down.txt")


price_action = Price_Action()


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

# Websocket Functions

# Established connection to Websocket
def on_open(ws):
    # print('opened connection')
    return


# Terminate Connection to Websocket
def on_close(ws):
    # print('closed connection')
    return


initial = {}
previous = {}
previousevolinit = {}
initialtime = {}

show_growing_up = False
log_growing_up = True
show_growing_down = False
log_growing_down = True
show_pumping = True
pump_trigger = 0.30  # If the evolution (in %) of price between 2 ticks is greater or equals to this value
show_dumping = True
dump_trigger = 0.30  # If the evolution (in %) of price between 2 ticks is greater or equals to this value

higherclose = {}
nbgrow = {}

# Listen to Websocket for Price Change, OnTick
def on_message(ws, message):
    global closes, totalevol

    json_message = json.loads(message)

    # captures the OHLC of the streamed message
    candle = json_message['k']
    symbol = json_message['s']

    # captures "close" flag
    is_candle_closed = candle['x']

    # captures the closing price
    close = float(candle['c'])
    openp = float(candle['o'])

    # print ticker price
    # print(symbol, 'ticker price:', close)
    if close > openp:
        evol = (close-openp)/openp*100
        if evol > 1:
            print(symbol, "green", evol, "%")
            log_to_results(str(datetime.now()) + " " + symbol + " " + "green" + " " + str(evol) + " " + "%")

    if symbol in higherclose:
        if close > higherclose[symbol]:
            nbgrow[symbol] = nbgrow[symbol] + 1
            higherclose[symbol] = close
            print(symbol, "growing", nbgrow[symbol])
    else:
        higherclose[symbol] = close
        nbgrow[symbol] = 0

    if is_candle_closed:
        try:
            y = price_action.open_range_breakout(message)
            if y == 11:
                print(symbol, "LONG POSITION SIGNAL !", "TP=5%=", close + (close / 100) * 5, "SL=2%=", close - (close / 100) * 2)
                log_to_results(symbol + " " + "LONG POSITION SIGNAL !" + " " + "TP=5%=" + " " + str(close + (close / 100) * 5) + " " + "SL=2%=" + " " + str(close - (close / 100) * 2))
            if y == 10:
                print(symbol, "SHORT POSITION SIGNAL !", "TP=5%=", close - (close / 100) * 5, "SL=2%=", close + (close / 100) * 2)
                log_to_results(symbol + " " + "SHORT POSITION SIGNAL !" + " " + "TP=5%=" + " " + str(close - (close / 100) * 5) + " " + "SL=2%=" + " " + str(close + (close / 100) * 2))
        except:
            print(sys.exc_info())
            sys.exit(-10003)


def scan_one(symbol):
    SOCKET = "wss://stream.binance.com:9443/ws/" + symbol + "@kline_1m"
    ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
    ws.run_forever()


def main_thread():
    delete_results_log()
    delete_results_log_pumps()
    delete_results_log_dumps()
    delete_results_log_pumps_and_dumps()
    delete_results_log_growing_up()
    delete_results_log_growing_down()

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
            exit(-1)

    threads = []

    exchange = exchanges["binance"]
    try:
        markets = exchange.fetch_markets()
        nb_active_assets = 0
        for oneline in markets:
            symbol = oneline['id']
            active = oneline['active']
            if active is True:
                nb_active_assets += 1
                if nb_active_assets < 10000 and symbol.endswith("USDT"):
                    # print(symbol, end=' ')
                    t = threading.Thread(target=scan_one, args=(symbol.lower(),))
                    threads.append(t)
                    t.start()

        print("")
        print("number of active assets =", nb_active_assets)
    except:
        # print(sys.exc_info())
        exit(-10003)

    for tt in threads:
        tt.join()


main_thread()
