# pip install websocket-client

import threading

import json
import websocket
import ccxt

try:
    # client.get_account()
    print('API keys validated')
except Exception as e:
    print('Invalid API keys!')


# Websocket Functions

# Established connection to Websocket
def on_open(ws):
    print('opened connection')


# Terminate Connection to Websocket
def on_close(ws):
    print('closed connection')


# Listen to Websocket for Price Change, OnTick
def on_message(ws, message):
    global closes
    json_message = json.loads(message)

    # captures the OHLC of the streamed message
    candle = json_message['k']
    symbol = json_message['s']

    # captures "close" flag
    is_candle_closed = candle['x']

    # captures the closing price
    close = candle['c']

    # print ticker price
    print(symbol, 'ticker price:', close)


def scan_one(symbol):
    SOCKET = "wss://stream.binance.com:9443/ws/" + symbol + "@kline_15m"
    ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
    ws.run_forever()


def main_thread():
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
                if nb_active_assets < 10:
                    print(symbol, end=' ')
                    t = threading.Thread(target=scan_one, args=(symbol.lower(),))
                    threads.append(t)
                    t.start()

            print("")
            print("number of active assets =", nb_active_assets)
    except:
        # print(sys.exc_info())
        exit(-10003)

    # maxthreads = 50
    # threadLimiter = threading.BoundedSemaphore(maxthreads)
    # threads = []

    # t = threading.Thread(target=scan_one, args=("xrpusdt",))
    # threads.append(t)
    # t.start()
    #
    # t = threading.Thread(target=scan_one, args=("btcusdt",))
    # threads.append(t)
    # t.start()

    for tt in threads:
        tt.join()


main_thread()
