import ftx
import pandas as pd
import requests
import threading

client = ftx.FtxClient(
    api_key='replace me',
    api_secret='replace me',
    subaccount_name='replace me'
)
result = client.get_balances()

# print(result)
# for coin in result:
#     # print(coin['coin'], coin['total'])
#     print(coin)

symbolInfo = {}


stop_thread = False


def my_thread(name):
    global symbolInfo, stop_thread

    while not stop_thread:
        markets = requests.get('https://ftx.com/api/markets').json()
        df = pd.DataFrame(markets['result'])
        df.set_index('name')
        for index, row in df.iterrows():
            symbol = row['name']
            price = float(row['last'])
            if symbol in symbolInfo:
                previous_price = symbolInfo[symbol]
                evol = price/previous_price
                if evol != 1:                           # this only shows moving assets (remove this condition if you need non moving assets)
                    print(symbol, "evol = ", evol)

            symbolInfo[symbol] = price

            stop_thread = False


x = threading.Thread(target=my_thread, args=(1,))
x.start()
