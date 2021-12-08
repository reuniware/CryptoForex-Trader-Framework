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
    close_price = msg['k']['c']
    dt = msg['k']['t']
    print(pd.to_datetime(dt, unit='ms'), symbolToTrade + 'USDT' + ' :', close_price)


twm.start_kline_socket(callback=handle_socket_message, symbol=symbolToTrade + 'USDT')

twm.join()


# SAMPLE OUTPUT
# C:\Users\InvestDataSystems\PycharmProjects\OceanicTradingBot\venv\Scripts\python.exe C:/Users/InvestDataSystems/PycharmProjects/OceanicTradingBot/main3.py
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
# 2021-12-08 11:50:00 XRPUSDT : 0.81090000
# 2021-12-08 11:50:00 XRPUSDT : 0.81070000
# 2021-12-08 11:50:00 XRPUSDT : 0.81030000
# 2021-12-08 11:50:00 XRPUSDT : 0.81040000
# 2021-12-08 11:50:00 XRPUSDT : 0.81020000
