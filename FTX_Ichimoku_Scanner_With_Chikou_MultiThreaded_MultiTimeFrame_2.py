import glob, os
from datetime import datetime
from datetime import timedelta
from binance.client import Client
from binance.enums import HistoricalKlinesType
import binance

import pandas as pd
import requests
import threading
import time
import ta
import math
import ftx

from enum import Enum


class ScanType(Enum):
    UP = 0
    DOWN = 1


client = ftx.FtxClient(
    api_key='',
    api_secret='',
    subaccount_name=''
)

# Set this variable to ScanType.UP for scanning uptrend assets or to ScanType.DOWN for scanning downtrend assets
scan_type = ScanType.UP

# Set this variable to False to scan in spot mode
scan_futures = False
scan_spot = True


def log_to_results(str_to_log):
    fr = open("results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_errors(str_to_log):
    fr = open("errors.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_trades(str_to_log):
    fr = open("trades.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_evol(str_to_log):
    fr = open("evol.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


if os.path.exists("results.txt"):
    os.remove("results.txt")

if os.path.exists("errors.txt"):
    os.remove("errors.txt")

if os.path.exists("trades.txt"):
    os.remove("trades.txt")

if os.path.exists("evol.txt"):
    os.remove("evol.txt")

for fg in glob.glob("CS_*.txt"):
    os.remove(fg)

print("Scanning type =", scan_type.name)
# log_to_results("Scanning type = " + scan_type.name)

results_count = 0

stop_thread = False

list_results = []

array_futures = []

# Set the timeframe to scan on the following line
interval_for_klinesT = Client.KLINE_INTERVAL_1HOUR
print("Scanning timeframe =", str(interval_for_klinesT))

days_ago_for_klinest = "80 day ago UTC"  # for daily download by default
if interval_for_klinesT == Client.KLINE_INTERVAL_1MINUTE:
    days_ago_for_klinest = "80 minute ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_3MINUTE:
    days_ago_for_klinest = "240 minute ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_5MINUTE:
    days_ago_for_klinest = "400 minute ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_15MINUTE:
    days_ago_for_klinest = "1200 minute ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_30MINUTE:
    days_ago_for_klinest = "2400 minute ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_1HOUR:
    days_ago_for_klinest = "80 hour ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_2HOUR:
    days_ago_for_klinest = "160 hour ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_4HOUR:
    days_ago_for_klinest = "320 hour ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_6HOUR:
    days_ago_for_klinest = "480 hour ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_8HOUR:
    days_ago_for_klinest = "640 hour ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_12HOUR:
    days_ago_for_klinest = "960 hour ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_1DAY:
    days_ago_for_klinest = "80 day ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_3DAY:
    days_ago_for_klinest = "240 day ago UTC"

dict_evol = {}
new_results_found = False


def execute_code(symbol):
    global results_count, dict_evol
    global new_results_found
    symbol_type = "n/a"

    HISTORY_RESOLUTION_MINUTE = 60
    HISTORY_RESOLUTION_3MINUTE = 60 * 3
    HISTORY_RESOLUTION_5MINUTE = 60 * 5
    HISTORY_RESOLUTION_15MINUTE = 60 * 15
    HISTORY_RESOLUTION_30MINUTE = 60 * 30
    HISTORY_RESOLUTION_HOUR = 60 * 60
    HISTORY_RESOLUTION_4HOUR = 60 * 60 * 4
    HISTORY_RESOLUTION_DAY = 60 * 60 * 24

    if interval_for_klinesT == Client.KLINE_INTERVAL_1MINUTE:
        history_resolution = HISTORY_RESOLUTION_MINUTE
    elif interval_for_klinesT == Client.KLINE_INTERVAL_5MINUTE:
        history_resolution = HISTORY_RESOLUTION_5MINUTE
    elif interval_for_klinesT == Client.KLINE_INTERVAL_15MINUTE:
        history_resolution = HISTORY_RESOLUTION_15MINUTE
    elif interval_for_klinesT == Client.KLINE_INTERVAL_1HOUR:
        history_resolution = HISTORY_RESOLUTION_HOUR
    elif interval_for_klinesT == Client.KLINE_INTERVAL_4HOUR:
        history_resolution = HISTORY_RESOLUTION_4HOUR
    elif interval_for_klinesT == Client.KLINE_INTERVAL_1DAY:
        history_resolution = HISTORY_RESOLUTION_DAY

    # history_resolution = history_resolution  # define the resolution used for the scan here
    delta_time = 0
    if history_resolution == HISTORY_RESOLUTION_MINUTE:  # using this resolution seems not ok, must be improved
        delta_time = 1
    if history_resolution == HISTORY_RESOLUTION_3MINUTE:  # using this resolution seems not ok, must be improved
        delta_time = 3
    elif history_resolution == HISTORY_RESOLUTION_5MINUTE:  # using this resolution seems not ok, must be improved
        delta_time = 5
    elif history_resolution == HISTORY_RESOLUTION_15MINUTE:
        delta_time = 15
    elif history_resolution == HISTORY_RESOLUTION_HOUR:
        delta_time = 60
    elif history_resolution == HISTORY_RESOLUTION_4HOUR:
        delta_time = 60 * 4
    elif history_resolution == HISTORY_RESOLUTION_DAY:
        delta_time = 60 * 24

    try:
        data = client.get_historical_data(market_name=symbol, resolution=history_resolution,  # 60min * 60sec = 3600 sec
                                          limit=1000000, start_time=float(round(time.time())) - delta_time * 5000,
                                          # 1000*3600 for resolution=3600*24 (daily) # 3600*3 for resolution=60*5 (5min) # 3600*3*15 for 60*15 # 3600 * 3 * 15 * 2 for 60*60
                                          end_time=float(round(time.time())))

        #if interval_for_klinesT != Client.KLINE_INTERVAL_1DAY:
        dataH1 = client.get_historical_data(market_name=symbol, resolution=HISTORY_RESOLUTION_HOUR,
                                                   # 60min * 60sec = 3600 sec
                                                   limit=1000000,
                                                   start_time=float(round(time.time())) - 60 * 24 * 5000,
                                                   # 1000*3600 for resolution=3600*24 (daily) # 3600*3 for resolution=60*5 (5min) # 3600*3*15 for 60*15 # 3600 * 3 * 15 * 2 for 60*60
                                                   end_time=float(round(time.time())))

        dataH4 = client.get_historical_data(market_name=symbol, resolution=HISTORY_RESOLUTION_4HOUR,
                                                   # 60min * 60sec = 3600 sec
                                                   limit=1000000,
                                                   start_time=float(round(time.time())) - 60 * 24 * 5000,
                                                   # 1000*3600 for resolution=3600*24 (daily) # 3600*3 for resolution=60*5 (5min) # 3600*3*15 for 60*15 # 3600 * 3 * 15 * 2 for 60*60
                                                   end_time=float(round(time.time())))

        dataDaily = client.get_historical_data(market_name=symbol, resolution=HISTORY_RESOLUTION_DAY,
                                                   # 60min * 60sec = 3600 sec
                                                   limit=1000000,
                                                   start_time=float(round(time.time())) - 60 * 24 * 5000,
                                                   # 1000*3600 for resolution=3600*24 (daily) # 3600*3 for resolution=60*5 (5min) # 3600*3*15 for 60*15 # 3600 * 3 * 15 * 2 for 60*60
                                                   end_time=float(round(time.time())))

        dataWeekly = client.get_historical_data(market_name=symbol, resolution=HISTORY_RESOLUTION_DAY * 7,
                                                   # 60min * 60sec = 3600 sec
                                                   limit=1000000,
                                                   start_time=float(round(time.time())) - 60 * 24 * 7 * 5000,
                                                   # 1000*3600 for resolution=3600*24 (daily) # 3600*3 for resolution=60*5 (5min) # 3600*3*15 for 60*15 # 3600 * 3 * 15 * 2 for 60*60
                                                   end_time=float(round(time.time())))

        # print(" (ok)")

        dframe = pd.DataFrame(data)
        dframeH1 = pd.DataFrame(dataH1)
        dframeH4 = pd.DataFrame(dataH4)
        dframeDaily = pd.DataFrame(dataDaily)
        dframeWeekly = pd.DataFrame(dataWeekly)

        try:
            dframe['close'] = pd.to_numeric(dframe['close'])
            dframeH1['close'] = pd.to_numeric(dframeH1['close'])
            dframeH4['close'] = pd.to_numeric(dframeH4['close'])
            dframeDaily['close'] = pd.to_numeric(dframeDaily['close'])
            dframeWeekly['close'] = pd.to_numeric(dframeWeekly['close'])
        except:
            print(symbol, "ERREUR DFRAME CLOSE")
            # print(dframe)
            return

        try:
            dframe['high'] = pd.to_numeric(dframe['high'])
            dframeH1['high'] = pd.to_numeric(dframeH1['high'])
            dframeH4['high'] = pd.to_numeric(dframeH4['high'])
            dframeDaily['high'] = pd.to_numeric(dframeDaily['high'])
            dframeWeekly['high'] = pd.to_numeric(dframeWeekly['high'])
        except:
            # print(symbol, "ERREUR DFRAME HIGH")
            return

        try:
            dframe['low'] = pd.to_numeric(dframe['low'])
            dframeH1['low'] = pd.to_numeric(dframeH1['low'])
            dframeH4['low'] = pd.to_numeric(dframeH4['low'])
            dframeDaily['low'] = pd.to_numeric(dframeDaily['low'])
            dframeWeekly['low'] = pd.to_numeric(dframeWeekly['low'])
        except:
            # print(symbol, "ERREUR DFRAME LOW")
            return

        try:
            dframe['open'] = pd.to_numeric(dframe['open'])
            dframeH1['open'] = pd.to_numeric(dframeH1['open'])
            dframeH4['open'] = pd.to_numeric(dframeH4['open'])
            dframeDaily['open'] = pd.to_numeric(dframeDaily['open'])
            dframeWeekly['open'] = pd.to_numeric(dframeWeekly['open'])
        except:
            # print(symbol, "ERREUR DFRAME OPEN")
            return

        dframe = dframe.set_index(dframe['startTime'])
        dframeH1 = dframeH1.set_index(dframeH1['startTime'])
        dframeH4 = dframeH4.set_index(dframeH4['startTime'])
        dframeDaily = dframeDaily.set_index(dframeDaily['startTime'])
        dframeWeekly = dframeWeekly.set_index(dframeWeekly['startTime'])
        # dframe.index = pd.to_datetime(dframe.index, unit='ms')

    except requests.exceptions.HTTPError:
        print("Erreur (HTTPError) tentative obtention données historiques pour " + symbol)
        log_to_errors("Erreur (HTTPError) tentative obtention données historiques pour " + symbol)
        return
    except requests.exceptions.ConnectionError:
        print("Erreur (ConnectionError) tentative obtention données historiques pour " + symbol)
        log_to_errors("Erreur (ConnectionError) tentative obtention données historiques pour " + symbol)
        return
    except binance.exceptions.BinanceAPIException:
        # in case the symbol does not exist in futures then this exception is thrown
        print(symbol + " Does not exist")
        return

    # a = time.time()
    # my_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(a))
    # my_time_2 = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(a - delta_time))

    # dframe = pd.DataFrame(data)

    # dframe['time'] = pd.to_datetime(dframe['time'], unit='ms')

    # print(dframe)
    try:
        dframe['ICH_SSA'] = ta.trend.ichimoku_a(dframe['high'], dframe['low'], window1=9, window2=26).shift(25)
        dframe['ICH_SSB'] = ta.trend.ichimoku_b(dframe['high'], dframe['low'], window2=26, window3=52).shift(25)
        dframe['ICH_KS'] = ta.trend.ichimoku_base_line(dframe['high'], dframe['low'])
        dframe['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframe['high'], dframe['low'])
        dframe['ICH_CS'] = dframe['close'].shift(-25)

        dframeH1['ICH_SSA'] = ta.trend.ichimoku_a(dframeH1['high'], dframeH1['low'], window1=9,window2=26).shift(25)
        dframeH1['ICH_SSB'] = ta.trend.ichimoku_b(dframeH1['high'], dframeH1['low'], window2=26,window3=52).shift(25)
        dframeH1['ICH_KS'] = ta.trend.ichimoku_base_line(dframeH1['high'], dframeH1['low'])
        dframeH1['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframeH1['high'], dframeH1['low'])
        dframeH1['ICH_CS'] = dframeH1['close'].shift(-25)

        dframeH4['ICH_SSA'] = ta.trend.ichimoku_a(dframeH4['high'], dframeH4['low'], window1=9,window2=26).shift(25)
        dframeH4['ICH_SSB'] = ta.trend.ichimoku_b(dframeH4['high'], dframeH4['low'], window2=26,window3=52).shift(25)
        dframeH4['ICH_KS'] = ta.trend.ichimoku_base_line(dframeH4['high'], dframeH4['low'])
        dframeH4['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframeH4['high'], dframeH4['low'])
        dframeH4['ICH_CS'] = dframeH4['close'].shift(-25)

        dframeDaily['ICH_SSA'] = ta.trend.ichimoku_a(dframeDaily['high'], dframeDaily['low'], window1=9,window2=26).shift(25)
        dframeDaily['ICH_SSB'] = ta.trend.ichimoku_b(dframeDaily['high'], dframeDaily['low'], window2=26,window3=52).shift(25)
        dframeDaily['ICH_KS'] = ta.trend.ichimoku_base_line(dframeDaily['high'], dframeDaily['low'])
        dframeDaily['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframeDaily['high'], dframeDaily['low'])
        dframeDaily['ICH_CS'] = dframeDaily['close'].shift(-25)

        dframeWeekly['ICH_SSA'] = ta.trend.ichimoku_a(dframeWeekly['high'], dframeWeekly['low'], window1=9,window2=26).shift(25)
        dframeWeekly['ICH_SSB'] = ta.trend.ichimoku_b(dframeWeekly['high'], dframeWeekly['low'], window2=26,window3=52).shift(25)
        dframeWeekly['ICH_KS'] = ta.trend.ichimoku_base_line(dframeWeekly['high'], dframeWeekly['low'])
        dframeWeekly['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframeWeekly['high'], dframeWeekly['low'])
        dframeWeekly['ICH_CS'] = dframeWeekly['close'].shift(-25)

    except KeyError as err:
        print("ERR001", err)
        return

    for indexdf, rowdf in dframeH1.iterrows():
        ssaH1 = dframeH1['ICH_SSA'].iloc[-1]
        ssbH1 = dframeH1['ICH_SSB'].iloc[-1]
        #print(symbol, "ssaH1, ssbH1", ssaH1, ssbH1)
        ksH1 = rowdf['ICH_KS']
        tsH1 = rowdf['ICH_TS']

    for indexdf, rowdf in dframeH4.iterrows():
        ssaH4 = dframeH4['ICH_SSA'].iloc[-1]
        ssbH4 = dframeH4['ICH_SSB'].iloc[-1]
        #print(symbol, "ssaH4, ssbH4", ssaH4, ssbH4)
        ksH4 = rowdf['ICH_KS']
        tsH4 = rowdf['ICH_TS']

    for indexdf, rowdf in dframeDaily.iterrows():
        ssaDaily = dframeDaily['ICH_SSA'].iloc[-1]
        ssbDaily = dframeDaily['ICH_SSB'].iloc[-1]
        #print(symbol, "ssaDaily, ssbDaily", ssaDaily, ssbDaily)
        ksDaily = rowdf['ICH_KS']
        tsDaily = rowdf['ICH_TS']

    for indexdf, rowdf in dframeWeekly.iterrows():
        ssaWeekly = dframeWeekly['ICH_SSA'].iloc[-1]
        ssbWeekly = dframeWeekly['ICH_SSB'].iloc[-1]
        #print(symbol, "ssaDaily, ssbDaily", ssaDaily, ssbDaily)
        ksWeekly = rowdf['ICH_KS']
        tsWeekly = rowdf['ICH_TS']

    for indexdf, rowdf in dframe.iterrows():

        openp = rowdf['open']
        high = rowdf['high']
        low = rowdf['low']
        close = rowdf['close']
        ssa = rowdf['ICH_SSA']
        ssb = rowdf['ICH_SSB']
        ks = rowdf['ICH_KS']
        ts = rowdf['ICH_TS']
        # cs = rowdf['ICH_CS']

        try:

            ssa = dframe['ICH_SSA'].iloc[-1]  # bougie n-1 car bougie 0 donne nan ?
            ssb = dframe['ICH_SSB'].iloc[-1]  # bougie n-1 car bougie 0 donne nan ?

            ssa2 = dframe['ICH_SSA'].iloc[-2]  # bougie n-1 car bougie 0 donne nan ?
            ssa3 = dframe['ICH_SSA'].iloc[-3]  # bougie n-1 car bougie 0 donne nan ?
            ssa4 = dframe['ICH_SSA'].iloc[-4]  # bougie n-1 car bougie 0 donne nan ?
            ssa5 = dframe['ICH_SSA'].iloc[-5]  # bougie n-1 car bougie 0 donne nan ?

            ssb2 = dframe['ICH_SSB'].iloc[-2]  # bougie n-1 car bougie 0 donne nan ?
            ssb3 = dframe['ICH_SSB'].iloc[-3]  # bougie n-1 car bougie 0 donne nan ?
            ssb4 = dframe['ICH_SSB'].iloc[-4]  # bougie n-1 car bougie 0 donne nan ?
            ssb5 = dframe['ICH_SSB'].iloc[-5]  # bougie n-1 car bougie 0 donne nan ?

            # print(ssa, ssb, ssa2, ssb2)
            cs = dframe['ICH_CS'].iloc[-26]  # cs bougie n en cours
            cs2 = dframe['ICH_CS'].iloc[-27]  # cs bougie n-1
            cs3 = dframe['ICH_CS'].iloc[-28]  # cs bougie n en cours
            # print(cs, cs2)

            csH1 = dframeH1['ICH_CS'].iloc[-26]  # cs bougie n en cours
            csH4 = dframeH4['ICH_CS'].iloc[-26]  # cs bougie n en cours
            csDaily = dframeDaily['ICH_CS'].iloc[-26]  # cs bougie n en cours
            csWeekly = dframeDaily['ICH_CS'].iloc[-26]  # cs bougie n en cours
            
            ssbchikou = dframe['ICH_SSB'].iloc[-26]
            ssbchikou2 = dframe['ICH_SSB'].iloc[-27]
            ssbchikou3 = dframe['ICH_SSB'].iloc[-28]
            ssbchikou4 = dframe['ICH_SSB'].iloc[-29]
            ssbchikou5 = dframe['ICH_SSB'].iloc[-30]
            ssbchikou6 = dframe['ICH_SSB'].iloc[-31]
            # print(ssbchikou, ssbchikou2, ssbchikou3, ssbchikou4, ssbchikou5, ssbchikou6)

            ssachikou = dframe['ICH_SSA'].iloc[-26]
            ssachikou2 = dframe['ICH_SSA'].iloc[-27]
            ssachikou3 = dframe['ICH_SSA'].iloc[-28]
            # print(ssachikou, ssachikou2, ssachikou3)

            closechikou = dframe['close'].iloc[-26]
            closechikou2 = dframe['close'].iloc[-27]
            # print(closechikou, closechikou2)

            openchikou = dframe['open'].iloc[-26]
            openchikou2 = dframe['open'].iloc[-27]

            lowchikou = dframe['low'].iloc[-26]
            lowchikou2 = dframe['low'].iloc[-27]

            highchikou = dframe['high'].iloc[-26]
            highchikou2 = dframe['high'].iloc[-27]

            kijunchikou = dframe['ICH_KS'].iloc[-26]
            kijunchikou2 = dframe['ICH_KS'].iloc[-27]
            kijunchikou3 = dframe['ICH_KS'].iloc[-28]
            # print(kijunchikou, kijunchikou2, kijunchikou3)

            tenkanchikou = dframe['ICH_TS'].iloc[-26]
            tenkanchikou2 = dframe['ICH_TS'].iloc[-27]
            tenkanchikou3 = dframe['ICH_TS'].iloc[-28]
            # print(tenkanchikou, tenkanchikou2, tenkanchikou3)

            timestamp = pd.to_datetime(rowdf['time'], unit='ms')
            # print(timestamp, openp, close, ssa, ssb)


        except IndexError as error:
            print("ERR002", symbol + " EXCEPTION " + str(error))
            log_to_errors(symbol + " EXCEPTION " + str(error) + '\n')
            # quit(0)
            break

        timestamp = pd.to_datetime(rowdf['time'], unit='ms')
        # timestamp = pd.to_datetime(rowdf['timestamp'], unit='ms')

        error_nan_values = False
        # To check the values of Ichimoku data (use TradingView with Ichimoku Cloud to compare them)
        # log_to_results(str(timestamp) + " " + symbol + " closecs=" + str(closechikou) + " closecs2=" + str(closechikou2) + " CS=" + str(cs) + " CS2=" + str(cs2) + " SSBCS=" + str(ssbchikou) + " SSBCS2=" + str(ssbchikou2) + " SSBCS3=" + str(ssbchikou3) + " KSCS=" + str(kijunchikou)+ " KSCS2=" + str(kijunchikou2)+ " KSCS3=" + str(kijunchikou3) + " TSCS=" + str(tenkanchikou)+ " TSCS2=" + str(tenkanchikou2)+ " TSCS3=" + str(tenkanchikou3) + " SSACS=" + str(ssachikou) + " SSACS2=" + str(ssachikou2) + " SSACS3=" + str(ssachikou3) + " SSA=" + str(ssa) + " SSB=" + str(ssb))
        # exit()

        if math.isnan(ssa) or math.isnan(ssb) or math.isnan(closechikou) or math.isnan(closechikou2) or math.isnan(
                cs) or math.isnan(cs2) or math.isnan(ssbchikou) or math.isnan(ssbchikou2) or math.isnan(
                ssbchikou3) or math.isnan(kijunchikou) or math.isnan(kijunchikou2) or math.isnan(
                kijunchikou3) or math.isnan(tenkanchikou) or math.isnan(tenkanchikou2) or math.isnan(
                tenkanchikou3) or math.isnan(ssachikou) or math.isnan(ssbchikou2) or math.isnan(ssachikou3):
            print(symbol + " THERE ARE NAN VALUES IN ICHIMOKU DATA")
            log_to_errors(symbol + " THERE ARE NAN VALUES IN ICHIMOKU DATA" + '\n')
            error_nan_values = True
            # quit(0)

        if error_nan_values:
            break

        filename = "CS_" + symbol.replace('/', '_') + ".txt"
        if os.path.exists(filename):
            os.remove(filename)

        # now_cs = datetime.datetime_result_min() - timedelta(hours=4 * 26)
        # # print("now_cs=" + str(now_cs))
        # # quit(0)
        # if timestamp.year == now_cs.year and timestamp.month == now_cs.year and timestamp.day == now_cs.day and timestamp.hour == now_cs.hour:
        #     print(str(cs))

        data_minute = timestamp.minute
        data_hour = timestamp.hour
        data_day = timestamp.day
        data_month = timestamp.month
        data_year = timestamp.year

        if interval_for_klinesT == Client.KLINE_INTERVAL_1MINUTE:
            datetime_result_min = datetime.now() - timedelta(minutes=1)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_3MINUTE:
            # datetime_result_min = datetime.now() - timedelta(minutes=15)
            datetime_result_min = datetime.now() - timedelta(minutes=3)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_5MINUTE:
            # datetime_result_min = datetime.now() - timedelta(minutes=15)
            datetime_result_min = datetime.now() - timedelta(minutes=5)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_15MINUTE:
            # datetime_result_min = datetime.now() - timedelta(hours=1)
            datetime_result_min = datetime.now() - timedelta(minutes=15)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_30MINUTE:
            # datetime_result_min = datetime.now() - timedelta(hours=1)
            datetime_result_min = datetime.now() - timedelta(minutes=30)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_1HOUR:
            datetime_result_min = datetime.now() - timedelta(hours=1)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_2HOUR:
            datetime_result_min = datetime.now() - timedelta(hours=2)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_4HOUR:
            datetime_result_min = datetime.now() - timedelta(hours=4)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_6HOUR:
            datetime_result_min = datetime.now() - timedelta(hours=6)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_8HOUR:
            datetime_result_min = datetime.now() - timedelta(hours=8)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_12HOUR:
            datetime_result_min = datetime.now() - timedelta(hours=12)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_1DAY:
            datetime_result_min = datetime.now() - timedelta(hours=timestamp.hour)
        elif interval_for_klinesT == Client.KLINE_INTERVAL_3DAY:
            datetime_result_min = datetime.now() - timedelta(hours=72)
        else:
            datetime_result_min = datetime.now() - timedelta(hours=1)  # We should never get here

        datetime_result_min_minute = datetime_result_min.minute
        datetime_result_min_hour = datetime_result_min.hour
        datetime_result_min_day = datetime_result_min.day
        datetime_result_min_month = datetime_result_min.month
        datetime_result_min_year = datetime_result_min.year

        # if math.isnan(ssa):
        #     print(symbol, "ssa is null")
        #
        # if math.isnan(ssb):
        #     print(symbol, "ssb is null")

        evol_co = round(((close - openp) / openp) * 100, 4)

        scan = True

        if interval_for_klinesT == Client.KLINE_INTERVAL_1MINUTE:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour == datetime_result_min_hour and data_minute >= datetime_result_min_minute
        elif interval_for_klinesT == Client.KLINE_INTERVAL_3MINUTE:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour == datetime_result_min_hour and data_minute >= datetime_result_min_minute
        elif interval_for_klinesT == Client.KLINE_INTERVAL_5MINUTE:
            # print("comparing : " + str(data_hour) + " " + str(data_minute) + " to " + str(datetime_result_min_hour) + " " + str(datetime_result_min_minute))
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour == datetime_result_min_hour and data_minute >= datetime_result_min_minute
        elif interval_for_klinesT == Client.KLINE_INTERVAL_15MINUTE:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour == datetime_result_min_hour and data_minute >= datetime_result_min_minute
        elif interval_for_klinesT == Client.KLINE_INTERVAL_30MINUTE:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour == datetime_result_min_hour and data_minute >= datetime_result_min_minute
        elif interval_for_klinesT == Client.KLINE_INTERVAL_1HOUR:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour > datetime_result_min_hour  # and data_minute >= datetime_result_min_minute
        elif interval_for_klinesT == Client.KLINE_INTERVAL_2HOUR:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour > datetime_result_min_hour  # and data_minute >= datetime_result_min_minute
        elif interval_for_klinesT == Client.KLINE_INTERVAL_4HOUR:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour > datetime_result_min_hour  # and data_minute >= datetime_result_min_minute
        elif interval_for_klinesT == Client.KLINE_INTERVAL_6HOUR:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour > datetime_result_min_hour  # and data_minute >= datetime_result_min_minute
        elif interval_for_klinesT == Client.KLINE_INTERVAL_8HOUR:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour > datetime_result_min_hour  # and data_minute >= datetime_result_min_minute
        elif interval_for_klinesT == Client.KLINE_INTERVAL_12HOUR:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour > datetime_result_min_hour  # and data_minute >= datetime_result_min_minute
        elif interval_for_klinesT == Client.KLINE_INTERVAL_1DAY:
            result_ok = data_day >= datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year  # and data_hour >= datetime_result_min_hour
        elif interval_for_klinesT == Client.KLINE_INTERVAL_3DAY:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year  # and data_hour >= datetime_result_min_hour
        else:
            result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour >= datetime_result_min_hour

        # if symbol == "ETHUSDT":
        #    print ("ETHUSDT SSACHIKOU = " + str(ssachikou))
        #    print ("ETHUSDT SSBCHIKOU = " + str(ssbchikou))

        if scan:
            if result_ok:
                #print(symbol, "result ok")
                # if openp < ssb < close or openp > ssb and close > ssb:
                # Define your own criterias for filtering assets on the line below

                if scan_type == ScanType.UP:
                    condition_is_satisfied = openp <= ksH4 and close >= ksH4
                    #condition_is_satisfied = openp >= ksDaily and close >= ksDaily and openp > ksWeekly and close > ksWeekly and openp > ssaDaily and close > ssaDaily and openp > ssbDaily and close > ssbDaily and openp > ssaWeekly and close > ssaWeekly and openp > ssbWeekly and close > ssbWeekly
                    #if condition_is_satisfied is True:
                    #    log_to_results(symbol + " " + "openp <= ksDaily and close <= ksDaily")

                elif scan_type == ScanType.DOWN:
                    condition_is_satisfied = openp < ks and close < ks and close < ts and close < openp and close < ssa and close < ssb and cs < lowchikou and cs < kijunchikou and cs < ssbchikou and cs < ssachikou and cs < tenkanchikou

                    #log_to_results(symbol + " ssa daily = " + str(ssaDaily) + " ssb daily = " + str(ssbDaily) + " ks daily = " + str(ksDaily) + " ts daily = " + str(tsDaily))
                    #log_to_results(symbol + " ssa w  = " + str(ssaWeekly) + " ssb w = " + str(ssbWeekly) + " ks w = " + str(ksWeekly) + " ts w = " + str(tsWeekly))
                    #log_to_results(symbol + " ssa w  = " + str(ssaWeekly) + " ssb w = " + str(ssbWeekly) + " ks w = " + str(ksWeekly) + " ts w = " + str(tsWeekly))

                if condition_is_satisfied:

                    cs_results = ""

                    str_result = str(timestamp) + " " + symbol + " " + symbol_type + " SSA=" + str(ssa) + " SSB=" + str(
                        ssb) + " KS=" + str(ks) + " TS=" + str(ts) + " O=" + str(
                        openp) + " H=" + str(high) + " L=" + str(low) + " SSBCS=" + str(
                        ssbchikou)# + " C=" + str(close) + " CS=" + str(cs) + " EVOL%=" + str(evol_co)     # We don't concatenate the variable parts (for comparisons in list_results)

                    if not (str_result in list_results):
                        if not new_results_found:
                            new_results_found = True
                        results_count = results_count + 1
                        list_results.append(str_result)
                        #log_to_results(str_result)

                        str_result = cs_results + "\n" + str(results_count) + " " + str_result + " C=" + str(
                            close) + " CS=" + str(cs) + " EVOL(C/O)%=" + str(
                            evol_co)  # We add the data with variable parts

                        tf = str(interval_for_klinesT)
                        log_to_results("tf=" + tf)
                        interval = ""
                        if tf=="1m":
                            interval = 1
                        elif tf=="3m":
                            interval = 3
                        elif tf=="5m":
                            interval = 5
                        elif tf=="15m":
                            interval = 15
                        elif tf=="30m":
                            interval = 30
                        elif tf=="1h":
                            interval = 60
                        elif tf=="2h":
                            interval = 120
                        elif tf=="3h":
                            interval = 180
                        elif tf=="4h":
                            interval = 240
                        elif tf=="1d":
                            interval = 960

                        if scan_futures:
                            str_result += "\nhttps://tradingview.com/chart/?symbol=FTX%3A" + symbol.replace("-", "") + "&interval=" + str(interval)
                        else:
                            str_result += "\nhttps://tradingview.com/chart/?symbol=FTX%3A" + symbol.replace("/", "") + "&interval=" + str(interval)

                        print(str_result + "\n")
                        log_to_results(str(datetime.now()) + ":" + str_result + "\n")

                        dict_evol[symbol] = evol_co

        else:
            # if result_ok:
            print(timestamp, symbol, "O", openp, "H", high, "L", low, "C", close, "SSA", ssa, "SSB", ssb, "KS", ks,
                  "TS", ts, "CS", cs, "SSB CS", ssbchikou)
            str_result = str(timestamp) + " " + symbol + " O=" + str(openp) + " H=" + str(high) + " L=" + str(
                low) + " C=" + str(close) + " SSA=" + str(
                ssa) + " SSB=" + str(ssb) + " KS=" + str(ks) + " TS=" + str(ts) + " CS=" + str(cs) + " SSB CS=" + str(
                ssbchikou) + " EVOL%(C/O)=" + str(evol_co)

            log_to_results(str(datetime.now()) + ":" + str_result)


# Set loop_scan to True to scan in loop
loop_scan = True

maxthreads = 75
threadLimiter = threading.BoundedSemaphore(maxthreads)


def scan_one(symbol):
    threadLimiter.acquire()
    try:
        execute_code(symbol)
    finally:
        threadLimiter.release()


threads = []


def main_thread(name):
    global client, list_results, results_count, stop_thread, interval_for_klinesT
    global new_results_found

    log_to_evol(str(datetime.now()))

    while not stop_thread:

        # dict_evol = {}

        # new_results_found = False

        # info_binance = Client().get_all_tickers()
        # print(info_binance)
        # exit()

        markets = requests.get('https://ftx.com/api/markets').json()
        df = pd.DataFrame(markets['result'])
        df.set_index('name')

        # df = pd.DataFrame(info_binance)
        # df.set_index('symbol')

        for index, row in df.iterrows():

            # symbol = row['symbol']
            # symbol_type = "n/a"  #row['type']

            symbol = row['name']
            symbol_type = row['type']

            if scan_futures is True and not (symbol_type == "future"):
                # print("this is not future, this is ", symbol_type)
                continue

            if scan_spot is True and not (symbol_type == "spot"):
                # print("this is not future, this is ", symbol_type)
                continue

            # print(symbol, symbol_type)

            # filtering symbols to scan here
            # if not symbol.endswith('USDT') or symbol.endswith("DOWNUSDT") or symbol.endswith("UPUSDT"):
            #    continue

            #if symbol != 'BTC/USD':
            #    continue
            # else:
            #    print(symbol, "found")

            # if scan_futures:
            # print(symbol, "trying to scan in futures", end=" ")
            #  print(symbol, "trying to scan in futures")
            # else:
            # print(symbol, "trying to scan", end=" ")
            #  print(symbol, "trying to scan")

            if symbol.endswith("BEAR/USD") or symbol.endswith("BULL/USD") or symbol.endswith("HEDGE/USD"):
                continue
            if symbol.endswith("BEAR/USDT") or symbol.endswith("BULL/USDT") or symbol.endswith("HEDGE/USDT"):
                continue
            if symbol.endswith("HALF/USDT") or symbol.endswith("HALF/USD"):
                continue

            disable = False

            if disable == False:

                try:
                    t = threading.Thread(target=scan_one, args=(symbol,))
                    threads.append(t)
                    t.start()
                except requests.exceptions.ConnectionError:
                    continue

        for tt in threads:
            tt.join()

        print(str(datetime.now()) + " All threads finished.")
        log_to_results(str(datetime.now()) + " All threads finished.")

        time.sleep(1)

        if loop_scan is False:
            stop_thread = True
        else:
            stop_thread = False
        #####

        if new_results_found:
            log_to_results(100 * '*' + "\n")

        new_dict = sorted(dict_evol.items(), key=lambda kv: (kv[1], kv[0]))
        if new_dict:
            print(str(datetime.now()) + " " + str(new_dict))
            log_to_evol(str(datetime.now()) + " " + str(new_dict))

        # Remove the line below to scan in loop
        # stop_thread = True


x = threading.Thread(target=main_thread, args=(1,))
x.start()



