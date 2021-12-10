from datetime import datetime

import ftx
import pandas as pd
import requests
import threading

client = ftx.FtxClient(
    api_key='',
    api_secret='',
    subaccount_name=''
)
result = client.get_balances()

# print(result)

# for coin in result:
#     # print(coin['coin'], coin['total'])
#     print(coin)

symbolInfoInit = {}
symbolInfo = {}
symbolEvol = {}
initial_time = datetime.now()

stop_thread = False


def my_thread(name):
    global symbolInfo, symbolInfoInit, symbolEvol, stop_thread

    nb_req = 0

    while not stop_thread:
        markets = requests.get('https://ftx.com/api/markets').json()
        df = pd.DataFrame(markets['result'])
        df.set_index('name')
        for index, row in df.iterrows():
            symbol = row['name']
            price = float(row['last'])
            if symbol in symbolInfo:
                previous_price = symbolInfo[symbol]
                evol = price / previous_price
                if symbol in symbolEvol:
                    symbolEvol[symbol] = (symbolEvol[symbol] + evol) / 2
                else:
                    symbolEvol[symbol] = evol

                if symbolEvol[symbol] > 1.0025:   # Only prices that has evolved more that 2.5% since the start of this scanner are listed ; Feel free to change this value
                    print(datetime.now(), symbol, symbolEvol[symbol], 'initial price =', symbolInfoInit[symbol], 'current price =', price, 'total scan time =', datetime.now() - initial_time)
            else:
                symbolInfoInit[symbol] = price

            symbolInfo[symbol] = price

            stop_thread = False


x = threading.Thread(target=my_thread, args=(1,))
x.start()
