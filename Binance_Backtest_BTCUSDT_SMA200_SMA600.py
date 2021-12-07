# https://python-binance.readthedocs.io/en/latest/
# https://www.youtube.com/watch?v=_gNIWHh539A
# Binance fees : https://www.binance.com/en/fee/schedule

import pandas as pd
from binance.client import Client
import ta

klinesT = Client().get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "01 December 2020")

df = pd.DataFrame(klinesT, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])

# [[
#    1499040000000,      // Open time
#    "0.01634790",       // Open
#    "0.80000000",       // High
#    "0.01575800",       // Low
#    "0.01577100",       // Close
#    "148976.11427815",  // Volume
#    1499644799999,      // Close time
#    "2434.19055334",    // Quote asset volume
#    308,                // Number of trades
#    "1756.87402397",    // Taker buy base asset volume
#    "28.46694368",      // Taker buy quote asset volume
#    "17928899.62484339" // Ignore.
#  ]]

del df['ignore']
del df['close_time']
del df['quote_av']
del df['trades']
del df['tb_base_av']
del df['tb_quote_av']

df['close'] = pd.to_numeric(df['close'])
df['high'] = pd.to_numeric(df['high'])
df['low'] = pd.to_numeric(df['low'])
df['open'] = pd.to_numeric(df['open'])

df = df.set_index(df['timestamp'])
df.index = pd.to_datetime(df.index, unit='ms')

df['SMA200'] = ta.trend.sma_indicator(df['close'], 200)
df['SMA600'] = ta.trend.sma_indicator(df['close'], 600)

print(df)

# backtest
usdt = 1000
btc = 0
lastIndex = df.first_valid_index()      # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.first_valid_index.html

for index, row in df.iterrows():
    if df['SMA200'][lastIndex] > df['SMA600'][lastIndex] and usdt > 10:
        btc = usdt / df['close'][index]
        btc = btc - 0.0075 * btc
        usdt = 0
        print("Buy BTC at", df['close'][index], '$ the', index)

    if df['SMA200'][lastIndex] < df['SMA600'][lastIndex] and btc > 0.0001:
        usdt = btc * df['close'][index]
        usdt = usdt - 0.0075 * usdt
        btc = 0
        print("Sell BTC at", df['close'][index], '$ the', index)

    lastIndex = index

finalResult = usdt + btc * df['close'].iloc[-1]     # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.iloc.html
print("Final result", finalResult, "USDT")



