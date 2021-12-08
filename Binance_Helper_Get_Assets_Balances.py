# Python Binance API doc : https://python-binance.readthedocs.io/en/latest/
# Binance fees : https://www.binance.com/en/fee/schedule
# Binance Testnet : https://testnet.binance.vision/key/generate

from binance import Client

testnet_api_key = "replace me"
testnet_secret_key = "replace me"

client = Client(testnet_api_key, testnet_secret_key, testnet=True)

account = client.get_account()
# print(account["balances"])
for assetData in account["balances"]:
    print(assetData["asset"], assetData["free"], assetData["locked"])

quit(0)

# print(client.get_asset_balance('USDT'))

# SAMPLE OUTPUT :
# C:\Users\InvestDataSystems\PycharmProjects\OceanicTradingBot\venv\Scripts\python.exe C:/Users/InvestDataSystems/PycharmProjects/OceanicTradingBot/main4.py
# BNB 1000.00000000 0.00000000
# BTC 1.00000000 0.00000000
# BUSD 10000.00000000 0.00000000
# ETH 100.00000000 0.00000000
# LTC 500.00000000 0.00000000
# TRX 500000.00000000 0.00000000
# USDT 10000.00000000 0.00000000
# XRP 50000.00000000 0.00000000

# Process finished with exit code 0
