# Python Binance API doc : https://python-binance.readthedocs.io/en/latest/
# Binance fees : https://www.binance.com/en/fee/schedule
# Binance Testnet : https://testnet.binance.vision/key/generate

import pandas as pd
from binance import Client, ThreadedWebsocketManager

testnet_api_key = "replace me"
testnet_secret_key = "replace me"

client = Client(testnet_api_key, testnet_secret_key, testnet=True)

account = client.get_account()
# print(account["balances"])
usdtAmount = 0
symbolToTrade = "XRP"
symbolToTradeAmount = 0
for assetData in account["balances"]:
    print(assetData["asset"], assetData["free"], assetData["locked"])
    if assetData["asset"] == "USDT":
        usdtAmount = assetData["free"]
    if assetData["asset"] == symbolToTrade:
        symbolToTradeAmount = assetData["free"]

print("Available USDT = ", usdtAmount)
print("Available ", symbolToTrade, " = ", symbolToTradeAmount)

# # Create test order
# order = client.create_order(
#         symbol='XRPUSDT',
#         side=Client.SIDE_BUY,
#         type=Client.ORDER_TYPE_MARKET,
#         quantity=500
#     )


# socket manager using threads
twm = ThreadedWebsocketManager()
twm.start()


def handle_socket_message(msg):
    # print(msg)
    close_price = msg['k']['c']
    dt = msg['E']
    print(pd.to_datetime(dt, unit='ms'), symbolToTrade + 'USDT' + ' :', close_price)


twm.start_kline_socket(callback=handle_socket_message, symbol=symbolToTrade + 'USDT')

twm.join()


# SAMPLE OUTPUT
# C:\Users\InvestDataSystems\PycharmProjects\OceanicTradingBot\venv\Scripts\python.exe C:/Users/InvestDataSystems/PycharmProjects/OceanicTradingBot/main4.py
# BNB 1000.00000000 0.00000000
# BTC 1.00000000 0.00000000
# BUSD 10000.00000000 0.00000000
# ETH 100.00000000 0.00000000
# LTC 500.00000000 0.00000000
# TRX 500000.00000000 0.00000000
# USDT 9965.44896000 0.00000000
# XRP 50000.00000000 0.00000000
# Available USDT =  9965.44896000
# Available  XRP  =  50000.00000000
# 2021-12-08 12:00:23.896000 XRPUSDT : 0.81310000
# 2021-12-08 12:00:26.685000 XRPUSDT : 0.81350000
# 2021-12-08 12:00:28.921000 XRPUSDT : 0.81360000
# 2021-12-08 12:00:31.320000 XRPUSDT : 0.81370000
# 2021-12-08 12:00:33.947000 XRPUSDT : 0.81370000
# 2021-12-08 12:00:36.556000 XRPUSDT : 0.81370000
# 2021-12-08 12:00:45.434000 XRPUSDT : 0.81380000
# 2021-12-08 12:00:48.010000 XRPUSDT : 0.81390000
# 2021-12-08 12:00:59.950000 XRPUSDT : 0.81400000
# 2021-12-08 12:01:02.043000 XRPUSDT : 0.81430000
# 2021-12-08 12:01:04.018000 XRPUSDT : 0.81440000
# 2021-12-08 12:01:06.062000 XRPUSDT : 0.81500000
# 2021-12-08 12:01:08.146000 XRPUSDT : 0.81520000
# 2021-12-08 12:01:10.537000 XRPUSDT : 0.81540000
# 2021-12-08 12:01:12.591000 XRPUSDT : 0.81510000
# 
# Process finished with exit code -1
