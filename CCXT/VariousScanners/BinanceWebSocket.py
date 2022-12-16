# pip install websocket-client

import threading

import json
import websocket
import ccxt


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

    # print ticker price
    #print(symbol, 'ticker price:', close)

    if symbol in previous:
        previousclose = previous[symbol]
        initialclose = initial[symbol]
        evol = (close - previousclose)/previousclose*100
        evolinit = (close - initialclose)/initialclose*100
        #print(symbol, "is in previous", previousclose, close)
        if evolinit>1:
            #print("evol for", symbol, "=", evol)
            print("evol init for", symbol, "=", evolinit)
        
        if evol > previousevolinit[symbol]:
            previousevolinit[symbol] = evol
            print("growing", symbol, evol)

    else:
        previous[symbol] = close
        initial[symbol] = close
        previousevolinit[symbol] = 0

    
    


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
                if nb_active_assets < 10000 and symbol.endswith("USDT"):
                    #print(symbol, end=' ')
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
