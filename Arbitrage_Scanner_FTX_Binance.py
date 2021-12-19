import ftx
import pandas as pd
import requests
from binance.client import Client

client = ftx.FtxClient(
    api_key='',
    api_secret='',
    subaccount_name=''
)

prices_binance = {}

info_binance = Client().get_all_tickers()
# print(info)
for data in info_binance:
    prices_binance[data['symbol']] = data['price']

markets_ftx = requests.get('https://ftx.com/api/markets').json()
df = pd.DataFrame(markets_ftx['result'])

# print(df)

# On itère sur les données FTX
for index, row in df.iterrows():
    symbol = row['name']
    last = row['last']
    bid = row['bid']
    ask = row['ask']  # prix achat
    price_ftx = row['price']  # prix vente
    stype = row['type']

    if stype == 'spot' and not(symbol.endswith("BEAR/USDT")) and not(symbol.endswith("BULL/USDT")):

        for data in info_binance:
            symbolBinance = data['symbol']
            priceBinance = float(data['price'])
            symbolFtx = symbol.replace('/', '')
            symbolFtx = symbolFtx.replace('-', '')
            if symbolFtx == symbolBinance:
                diff = (priceBinance - price_ftx)/price_ftx * 100
                print("symbol on FTX and BINANCE : FTX =", symbol, "BINANCE =", symbolBinance)
                print("price on FTX=", "{:f}".format(price_ftx), " price on BINANCE=", "{:f}".format(priceBinance), str(diff))
                print("")

