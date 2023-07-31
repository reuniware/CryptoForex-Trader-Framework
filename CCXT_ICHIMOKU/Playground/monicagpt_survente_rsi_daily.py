import requests
import pandas as pd
import numpy as np
import ta
from ta.momentum import RSIIndicator
from datetime import datetime

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

def get_rsi(pair):
    url = 'https://api.binance.com/api/v3/klines'
    params = {'symbol': pair, 'interval': '4h', 'limit': 1000}
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    close_prices = df['close'].astype(float)
    rsi_indicator = RSIIndicator(close_prices, window=14)
    rsi = rsi_indicator.rsi()
    return rsi.iloc[-1]

pairs = get_all_binance_pairs()

for pair in pairs:
    try:
        rsi = get_rsi(pair)
        if rsi < 30:
            print(f'{pair} est en survente RSI ({rsi:.2f}) à {str(datetime.now()).split(".")[0]}')
        elif rsi > 70:
            print(f'{pair} est en surachat RSI ({rsi:.2f}) à {str(datetime.now()).split(".")[0]}')
        #else:
        #    print(f'{pair} RSI ({rsi:.2f})')
    except Exception as e:
        print(f'Erreur pour {pair}: {str(e)}')
