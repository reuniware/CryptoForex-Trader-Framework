import os
from datetime import datetime
from datetime import timedelta

import ftx
import pandas as pd
import requests
import threading
import time
import ta
import math
import glob
from enum import Enum

# import numpy as np

client = ftx.FtxClient(
    api_key='',
    api_secret='',
    subaccount_name=''
)

# result = client.get_balances()
# print(result)

if os.path.exists("results.txt"):
    os.remove("results.txt")

if os.path.exists("errors.txt"):
    os.remove("errors.txt")

for fg in glob.glob("CS_*.txt"):
    os.remove(fg)


list_results = []
results_count = 0

stop_thread = False

pd.set_option('max_columns', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
# pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


def my_thread(name):
    global client, list_results, results_count, stop_thread
    while not stop_thread:

        f = open("results.txt", "a")

        markets = requests.get('https://ftx.com/api/markets').json()
        df = pd.DataFrame(markets['result'])

        print(df)
        f.write(str(df))

        stop_thread = True


x = threading.Thread(target=my_thread, args=(1,))
x.start()
