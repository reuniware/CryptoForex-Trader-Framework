# https://towardsdatascience.com/making-a-stock-screener-with-python-4f591b198261
# https://gist.github.com/shashankvemuri

# Imports
import os
import threading

from pandas_datareader import data as pdr
from yahoo_fin import stock_info as si
from pandas import ExcelWriter
import yfinance as yf
import pandas as pd
import datetime
import time
import ta

yf.pdr_override()

# Variables
tickers = si.tickers_sp500()
tickers = [item.replace(".", "-") for item in tickers]  # Yahoo Finance uses dashes instead of dots
index_name = '^GSPC'  # S&P 500
start_date = datetime.datetime.now() - datetime.timedelta(days=365)
end_date = datetime.date.today()
# exportList = pd.DataFrame(columns=['Stock', "RS_Rating", "50 Day MA", "150 Day Ma", "200 Day MA", "52 Week Low", "52 week High"])
returns_multiples = []


# Index Returns
# index_df = pdr.get_data_yahoo(index_name, start_date, end_date)
# index_df['Percent Change'] = index_df['Adj Close'].pct_change()
# index_return = (index_df['Percent Change'] + 1).cumprod()[-1]

def log_to_results(str_to_log):
    fr = open("results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_log():
    if os.path.exists("results.txt"):
        os.remove("results.txt")


def execute_code(ticker, numticker):
    # Download historical data as CSV for each stock (makes the process faster)
    dframe = pdr.get_data_yahoo(ticker, start_date, end_date)
    # df.to_csv(f'{ticker}.csv')

    # print(df)
    dframe['ICH_SSB'] = ta.trend.ichimoku_b(dframe['High'], dframe['Low'], window2=26, window3=52).shift(26)
    dframe['ICH_SSA'] = ta.trend.ichimoku_a(dframe['High'], dframe['Low'], window1=9, window2=26).shift(26)
    dframe['ICH_KS'] = ta.trend.ichimoku_base_line(dframe['High'], dframe['Low'])
    dframe['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframe['High'], dframe['Low'])
    dframe['ICH_CS'] = dframe['Close'].shift(-26)

    ssb = dframe['ICH_SSB'].iloc[-1]
    ssa = dframe['ICH_SSA'].iloc[-1]
    kijun = dframe['ICH_KS'].iloc[-1]
    tenkan = dframe['ICH_TS'].iloc[-1]
    chikou = dframe['ICH_CS'].iloc[-27]
    price_open = dframe['Open'].iloc[-1]
    price_high = dframe['High'].iloc[-1]
    price_low = dframe['Low'].iloc[-1]
    price_close = dframe['Close'].iloc[-1]
    price_open_chikou = dframe['Open'].iloc[-27]
    price_high_chikou = dframe['High'].iloc[-27]
    price_low_chikou = dframe['Low'].iloc[-27]
    price_close_chikou = dframe['Close'].iloc[-27]
    tenkan_chikou = dframe['ICH_TS'].iloc[-27]
    kijun_chikou = dframe['ICH_KS'].iloc[-27]
    ssa_chikou = dframe['ICH_SSA'].iloc[-27]
    ssb_chikou = dframe['ICH_SSB'].iloc[-27]

    evol = (price_close - price_open)/price_open*100
    if evol>0:
        print(numticker, ticker, price_open, price_close, ssa, ssb, evol)
    if price_open < kijun and price_close > kijun:
        print(numticker, ticker, "has got above ks")
        log_to_results(str(numticker) + " " + ticker + " has got above ks")

    #if dframe['Open'].iloc[0] > dframe['ICH_KS'].iloc[0] and dframe['Close'].iloc[0] < dframe['ICH_KS'].iloc[0]:
    #    print(ticker, "is getting below ks")
    #    log_to_results(ticker + " is getting below ks")    
    #print(dframe['Open'].iloc[0], dframe['ICH_KS'].iloc[-1], dframe['Close'].iloc[0], dframe['ICH_KS'].iloc[-1])


threadLimiter = threading.BoundedSemaphore()


def scan_one(ticker, numticker):
    global threadLimiter
    threadLimiter.acquire()
    try:
        execute_code(ticker, numticker)
    finally:
        threadLimiter.release()


def main_thread():
    delete_results_log()

    maxthreads = 1000
    threadLimiter = threading.BoundedSemaphore(maxthreads)
    threads = []

    numticker = 0

    for ticker in tickers:
        numticker += 1
        t = threading.Thread(target=scan_one, args=(ticker, numticker))
        threads.append(t)
        t.start()

    for tt in threads:
        tt.join()

        # print(ticker)
        # print(dframe)

        # sys.exit(0)

        # Calculating returns relative to the market (returns multiple)
        # df['Percent Change'] = df['Adj Close'].pct_change()
        # stock_return = (df['Percent Change'] + 1).cumprod()[-1]

        # returns_multiple = round((stock_return / index_return), 2)
        # returns_multiples.extend([returns_multiple])

        # print(f'Ticker: {ticker}; Returns Multiple against S&P 500: {returns_multiple}\n')
        time.sleep(1)


main_thread()
