import ccxt
import pandas as pd
from datetime import datetime
import openpyxl
import time
import threading

pd.set_option('display.max_columns', 10)
pd.set_option('display.expand_frame_repr', False)

exchange_binance = ccxt.binance()
exchange_ftx = ccxt.ftx()


# exchange.set_sandbox_mode(True)

def get_btc_data(exc):
    try:
        result = exc().fetch_ohlcv('BTC/USDT', '1m', limit=1)
        print(exc + " : " + result)
    except:
        print("Semble ne pas exister sur cet exchange : " + exc.name)


for name in ccxt.exchanges:
    exchange = getattr(ccxt, name)
    # print(exchange().timeframes)
    result = exchange().fetch_ohlcv('BTC/USDT', '1m', limit=1)
    print(result)
    # t = threading.Thread(target=get_btc_data, args=(exchange(),))
    # t.start()

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
