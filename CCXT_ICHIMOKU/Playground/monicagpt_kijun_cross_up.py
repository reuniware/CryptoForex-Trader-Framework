import requests
import pandas as pd
import numpy as np
import ta
from ta.trend import IchimokuIndicator

def get_all_binance_pairs():
    url = 'https://api.binance.com/api/v3/exchangeInfo'
    response = requests.get(url)
    data = response.json()
    symbols = data['symbols']
    pairs = []
    for symbol in symbols:
        if symbol['status'] == 'TRADING':
            pairs.append(symbol['symbol'])
    return pairs

def get_kijun_sen(pair):
    url = 'https://api.binance.com/api/v3/klines'
    params = {'symbol': pair, 'interval': '1d', 'limit': 1000}
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    ichimoku_indicator = IchimokuIndicator(df['high'], df['low'], window1=9, window2=26, window3=52)
    kijun_sen = ichimoku_indicator.ichimoku_base_line()

    if float(df['open'].iloc[-1]) < kijun_sen.iloc[-1]:
        if float(df['close'].iloc[-1]) > kijun_sen.iloc[-1]:
            print(pair + " : open below and close above")

    return kijun_sen.iloc[-1]

pairs = get_all_binance_pairs()

for pair in pairs:
    try:
        kijun_sen = get_kijun_sen(pair)
        #print(f'La Kijun Sen actuelle en daily pour {pair} est {kijun_sen:.8f}')
    except Exception as e:
        print(f'Une erreur s\'est produite pour {pair} : {e}')
