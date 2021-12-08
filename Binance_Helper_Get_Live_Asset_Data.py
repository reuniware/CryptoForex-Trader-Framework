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
