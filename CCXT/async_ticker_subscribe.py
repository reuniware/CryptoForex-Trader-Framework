# import ccxt
# import pandas as pd
# from datetime import datetime
# import openpyxl
# import time
# import threading
import ccxt.async_support as ccxt  # noqa: E402
import asyncio

# pd.set_option('display.max_columns', 10)
# pd.set_option('display.expand_frame_repr', False)

exchange = ccxt.binance({
    'enableRateLimit': True,  # this option enables the built-in rate limiter
})


async def main(symbol):
    while True:
        ticker = await exchange.fetch_ticker(symbol)
        print(ticker)


asyncio.get_event_loop().run_until_complete(main('BTC/USDT'))
