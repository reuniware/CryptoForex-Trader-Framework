# Raw Package

import numpy as np
import pandas as pd
#Data Source
import yfinance as yf

data = yf.download(tickers = 'JPYAUD=X' ,period ='1d', interval = '15m')
print(data)

data = yf.download(tickers = 'EURUSD=X' ,period ='1d', interval = '15m')
print(data.iloc[-1])
print(data.iloc[-2])
