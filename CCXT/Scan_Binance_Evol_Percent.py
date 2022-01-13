import ccxt
# import pandas as pd
# from datetime import datetime
# import openpyxl
# import time
import threading
import ccxt.async_support as ccxt_async  # noqa: E402
import asyncio

# pd.set_option('display.max_columns', 10)
# pd.set_option('display.expand_frame_repr', False)

exchange = ccxt_async.binance({
    'enableRateLimit': True,  # this option enables the built-in rate limiter
})

askprice = {}
bidprice = {}


async def main(all_symbols):
    # print(symbol)
    # ticker = await exchange.fetch_ticker(symbol)
    tickers = await exchange.fetch_tickers(symbols=all_symbols)
    # print(tickers)
    for symbol in tickers:
        ask = tickers[symbol]['ask']
        datetime = tickers[symbol]['datetime']
        bid = tickers[symbol]['bid']
        askVolume = tickers[symbol]['askVolume']
        bidVolume = tickers[symbol]['bidVolume']
        # print(symbol, "ask", ask, "bid", bid, "askvol", askVolume, "bidvol", bidVolume)

        previous_ask = 0
        previous_bid = 0
        if symbol in askprice.keys() and symbol in bidprice.keys():
            previous_ask = askprice[symbol]
            previous_bid = bidprice[symbol]

        if previous_ask > 0 and previous_bid > 0:
            if ask / previous_ask > 1.005:
                print(exchange.name, symbol, "diff(t/t-1) =", "{:.8f}".format(round(ask - previous_ask, 8)), "{:.8f}".format(bid - previous_bid), "{:.8f}".format(ask/previous_ask), "%")

        askprice[symbol] = ask
        bidprice[symbol] = bid


binance_exchange = ccxt.binance()
markets = binance_exchange.fetch_markets()

while True:
    all_symbols = []
    for oneline in markets:
        symbol = oneline['symbol']
        all_symbols.append(symbol)
        # if symbol == "BTC/USDT":
        #     all_symbols.append(symbol)
    asyncio.get_event_loop().run_until_complete(main(all_symbols))
    # _thread = threading.Thread(target=asyncio.run, args=(main(symbol),))
    # _thread.start()

# asyncio.get_event_loop().run_until_complete(main('TRX/USDT'))
