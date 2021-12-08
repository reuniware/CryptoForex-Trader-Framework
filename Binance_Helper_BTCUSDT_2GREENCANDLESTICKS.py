import pandas as pd
from binance.client import Client
import ta

klinesT = Client().get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_30MINUTE, "01 December 2021")

df = pd.DataFrame(klinesT, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])

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

# close_prec_1 = -1
# open_prec_1 = -1
# close_prec_2 = -1
# open_prec_2 = -1

i = 0
for index, row in df.iterrows():
    if i == 0:
        close_prec_2 = df['close'][index]
        open_prec_2 = df['open'][index]
    if i == 1:
        close_prec_1 = df['close'][index]
        open_prec_1 = df['open'][index]
    if i == 2:
        if close_prec_2 > open_prec_2 and close_prec_1 > open_prec_1:
            print("OK : condition 2 bougies vertes précédentes ok ici", index)
        else:
            print("KO : ", index)

    i = i + 1
    if i > 2:
        i = 0
