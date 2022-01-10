import ccxt
import pandas as pd
from datetime import datetime
# import openpyxl
import time
import threading

pd.set_option('display.max_columns', 10)
pd.set_option('display.expand_frame_repr', False)

exchange_binance = ccxt.binance()
exchange_ftx = ccxt.ftx()


# exchange.set_sandbox_mode(True)

common_symbols = []

markets1 = exchange_binance.fetch_markets()
markets2 = exchange_ftx.fetch_markets()

for oneline1 in markets1:
    symbol1 = oneline1['symbol']
    # print(oneline['symbol'])
    for oneline2 in markets2:
        symbol2 = oneline2['symbol']
        if symbol1 == symbol2:
            print(symbol1 + " found in both markets")
            common_symbols.append(symbol1)


while True:
    for symbol in common_symbols:

        result = exchange_binance.fetch_ohlcv(symbol, '1m', limit=1)
        # print("binance : " + str(result))
        c1 = result[0][4]
        # print(c1)

        result = exchange_ftx.fetch_ohlcv(symbol, '1m', limit=1)
        # print("ftx : " + str(result))
        try:
            c2 = result[0][4]
        except:
            print("cannot get data from ftx")
            continue

        diff = c2 - c1

        print(symbol + " : " + "{:10.16f}".format(diff))


# for name in ccxt.exchanges:
#     exchange = getattr(ccxt, name)
#     # print(exchange().timeframes)
#     result = exchange().fetch_ohlcv('BTC/USDT', '1m', limit=1)
#     print(result)
#     # t = threading.Thread(target=get_btc_data, args=(exchange(),))
#     # t.start()



# print(ccxt.exchanges)

# print(exchange.timeframes)
# all_markets = exchange.load_markets()
# print(all_markets)

# result_binance = exchange_binance.fetch_ohlcv('BTC/USDT', '1m', limit=1000)
# result_ftx = exchange_ftx.fetch_ohlcv('BTC/USDT', '1m', limit=1000)

i = 0
# for line in result_binance:
#     dt_timestamp = datetime.utcfromtimestamp(int(line[0]) / 1000)
#     o = line[1]
#     h = line[2]
#     l = line[3]
#     c = line[4]
#     v = line[5]
#     i += 1
# print(dt_timestamp, o, h, l, c, v)

# while True:
#     result_binance = exchange_binance.fetch_ohlcv('BTC/USDT', '1m', limit=1)
#     result_ftx = exchange_ftx.fetch_ohlcv('BTC/USDT', '1m', limit=1)
#
#     close1 = result_binance[0][4]
#     close2 = result_ftx[0][4]
#
#     print(close1, close2, close2-close1)
#     time.sleep(1)
