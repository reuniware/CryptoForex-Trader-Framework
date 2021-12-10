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

symbolInfoInit = {}
symbolInfo = {}
symbolEvol = {}
initial_time = datetime.now()

stop_thread = False


def my_thread(name):
    global symbolInfo, symbolInfoInit, symbolEvol, stop_thread

    while not stop_thread:
        markets = requests.get('https://ftx.com/api/markets').json()
        df = pd.DataFrame(markets['result'])
        df.set_index('name')
        for index, row in df.iterrows():
            symbol = row['name']
            price = float(row['last'])

            if symbol in symbolInfo:
                if price > symbolInfo[symbol]:
                    symbolInfo[symbol] = price
                    print(datetime.now(), "growing", symbol, "evol=", price/symbolInfoInit[symbol], "init price=", symbolInfoInit[symbol], "current price=", price, "scan time=", datetime.now() - initial_time)
            else:
                symbolInfoInit[symbol] = price
                symbolInfo[symbol] = price

            stop_thread = False


x = threading.Thread(target=my_thread, args=(1,))
x.start()
