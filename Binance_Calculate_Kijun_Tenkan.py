import asyncio
from datetime import timedelta

import pandas as pd

from binance import AsyncClient

tab_high = []
tab_low = []


def get_kijun(num_candlestick):
    highest = 0
    lowest = float('inf')
    for j in range(len(tab_high) - 26 - num_candlestick,
                   len(tab_high) - num_candlestick):  # -26-1 pour avoir sur bougie précédente
        # print(tab_high[j])
        if tab_high[j] > highest:
            highest = tab_high[j]
        if tab_low[j] < lowest:
            lowest = tab_low[j]
    kijun = (highest + lowest) / 2
    return kijun


def get_tenkan(num_candlestick):
    highest = 0
    lowest = float('inf')
    for j in range(len(tab_high) - 9 - num_candlestick, len(tab_high) - num_candlestick):
        # print(tab_high[j])
        if tab_high[j] > highest:
            highest = tab_high[j]
        if tab_low[j] < lowest:
            lowest = tab_low[j]
    tenkan = (highest + lowest) / 2
    return tenkan


async def main():
    # exchange_info = await client.get_exchange_info()
    while True:
        client = await AsyncClient.create()
        tickers = await client.get_all_tickers()
        trades = await client.get_recent_trades(symbol='BTCUSDT')
        # print(trades)
        candles = await client.get_klines(symbol='BTCUSDT', interval=client.KLINE_INTERVAL_1HOUR)
        # print(candles)
        i = 0
        # tab_high = []
        # tab_low = []
        for data in candles:
            opentime = data[0]
            open = float(data[1])
            high = float(data[2])
            low = float(data[3])
            close = float(data[4])
            volume = data[5]
            nextclosetime = data[6]
            opentimestamp = pd.to_datetime(opentime, unit='ms') + timedelta(hours=2)
            nextclosetimestamp = pd.to_datetime(nextclosetime, unit='ms') + timedelta(hours=2)
            print(i, opentimestamp, nextclosetimestamp, close, close / open)
            i = i + 1
            tab_high.append(high)
            tab_low.append(low)

        # print(len(tab_high))
        # print(len(tab_high) - 26)

        print("kijun", get_kijun(0))
        print("tenkan", get_tenkan(0))
        print("kijun", get_kijun(1))
        print("tenkan", get_tenkan(1))

        await client.close_connection()

        # 1499040000000,      # Open time
        # "0.01634790",       # Open
        # "0.80000000",       # High
        # "0.01575800",       # Low
        # "0.01577100",       # Close
        # "148976.11427815",  # Volume
        # 1499644799999,      # Close time
        # "2434.19055334",    # Quote asset volume
        # 308,                # Number of trades
        # "1756.87402397",    # Taker buy base asset volume
        # "28.46694368",      # Taker buy quote asset volume
        # "17928899.62484339" # Can be ignored


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
