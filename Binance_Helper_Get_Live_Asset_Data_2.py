# Python Binance API doc : https://python-binance.readthedocs.io/en/latest/
# Binance fees : https://www.binance.com/en/fee/schedule
# Binance Testnet : https://testnet.binance.vision/key/generate

# This gets live data from Binance and calculates the % of evolution between 2 data sent by the server

import pandas as pd
from binance import Client, ThreadedWebsocketManager

real_api_key = "replace me"
real_secret_key = "replace me"

testnet_api_key = "replace me"
testnet_secret_key = "replace me"

# client = Client(testnet_api_key, testnet_secret_key, testnet=True)
client = Client(real_api_key, real_secret_key)

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

prev_close_price = 0
percent_evol = 0


def handle_socket_message(msg):
    global prev_close_price, percent_evol
    # print(msg)
    close_price = float(msg['k']['c'])
    dt = msg['E']

    if prev_close_price > 0:
        percent_evol = close_price / prev_close_price * 100 - 100
        # print(percent_evol)

    print(pd.to_datetime(dt, unit='ms'), symbolToTrade + 'USDT' + ' :', close_price, percent_evol)

    prev_close_price = close_price


twm.start_kline_socket(callback=handle_socket_message, symbol=symbolToTrade + 'USDT')

twm.join()
