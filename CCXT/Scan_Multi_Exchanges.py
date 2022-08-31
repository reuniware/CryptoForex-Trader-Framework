import os
from datetime import datetime
import ccxt

# retrieve data for the BTC/USDT pair on Binance
binance = ccxt.binance()
ftx = ccxt.gateio()

a = ccxt.exchanges
# for ex in a:
#     #print(ex)
#     exchange_class = getattr(ccxt, ex)
#     #print(exchange_class)
#     exchange = exchange_class()
#     exchange.fetch_tickers()

stop_loop = False

while stop_loop is False:
    tb = binance.fetch_tickers()
    #tf = ftx.fetch_tickers()

    for ex in a:
        #print(ex)
        if ex != "hitbtc":
            continue
        exchange_class = getattr(ccxt, ex)
        # print(exchange_class)
        exchange = exchange_class()
        try:
            tf = exchange.fetch_tickers()
        except:
            #print(ex, "exception")
            continue

        for lineb in tb.items():
            symbolb = lineb[1]['symbol']
            askb = lineb[1]['ask']
            #print(symbolb, closeb)

            for linef in tf.items():
                symbolf = linef[1]['symbol']
                bidf = linef[1]['bid']
                #print(symbolf, closef)

                if askb is not None and bidf is not None:
                    if str(symbolb).endswith("/USDT") and symbolb == symbolf and askb > 0 and bidf > 0:
                        evolpc = 100*(bidf - askb)/askb
                        if evolpc > 1:
                            print(ex, symbolb, symbolf, askb, bidf, evolpc)

    stop_loop = True

exit(0)
