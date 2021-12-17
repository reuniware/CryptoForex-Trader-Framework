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

stop_thread = False


def my_thread(name):
    global client
    while not stop_thread:

        f = open("results.txt", "a")

        markets = requests.get('https://ftx.com/api/markets').json()
        df = pd.DataFrame(markets['result'])
        df.set_index('name')
        for index, row in df.iterrows():
            symbol = row['name']
            # print(symbol)
            # print("scanning", symbol)

            data = client.get_historical_data(
                market_name=symbol,
                resolution=60 * 60 * 4,  # 60min * 60sec = 3600 sec
                limit=10000,
                start_time=float(round(time.time())) - 2000 * 3600,  # 1000*3600 for resolution=3600*24 (daily)
                end_time=float(round(time.time())))

            dframe = pd.DataFrame(data)

            # dframe['time'] = pd.to_datetime(dframe['time'], unit='ms')

            # print(dframe)
            try:
                dframe['ICH_SSA'] = ta.trend.ichimoku_a(dframe['high'], dframe['low'], window1=9, window2=26).shift(26)
                dframe['ICH_SSB'] = ta.trend.ichimoku_b(dframe['high'], dframe['low'], window2=26, window3=52).shift(26)
                dframe['ICH_KS'] = ta.trend.ichimoku_base_line(dframe['high'], dframe['low'])
                dframe['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframe['high'], dframe['low'])
                dframe['ICH_CS'] = dframe['close'].shift(-26)

            except KeyError as err:
                print(err)
                continue

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
                    cs = dframe['ICH_CS'].iloc[-26-1]     # chikou span concernant bougie n en cours
                    cs2 = dframe['ICH_CS'].iloc[-26-2]    # chikou span concernant bougie n-1
                    ssbchikou = dframe['ICH_SSB'].iloc[-26-1+2]
                    ssbchikou2 = dframe['ICH_SSB'].iloc[-26-2+2]
                    ssbchikou3 = dframe['ICH_SSB'].iloc[-26-3+2]
                    closechikou = dframe['close'].iloc[-26]
                    closechikou2 = dframe['close'].iloc[-26-1]
                except IndexError as error:
                    cs = 0
                    print(symbol + " EXCEPTION " + str(error))
                    fe = open("errors.txt", "a")
                    fe.write(symbol + " EXCEPTION " + str(error) + '\n')
                    fe.close()
                    quit(0)
                    continue

                timestamp = pd.to_datetime(rowdf['time'], unit='ms')

                # print(str(timestamp) + " " + symbol + " " + str(cs) + " " + str(cs2) + " " + str(ssbchikou) + " " + str(ssbchikou2) + " " + str(ssbchikou3))
                print(str(timestamp) + " " + symbol + " closecs=" + str(closechikou) + " closecs2=" + str(closechikou2) + " " + str(cs) + " " + str(cs2) + " " + str(ssbchikou) + " " + str(ssbchikou2) + " " + str(ssbchikou3))

                filename = "CS_" + symbol.replace('/', '_') + ".txt"
                if os.path.exists(filename):
                    os.remove(filename)

                # now_cs = datetime.now() - timedelta(hours=4 * 26)
                # # print("now_cs=" + str(now_cs))
                # # quit(0)
                # if timestamp.year == now_cs.year and timestamp.month == now_cs.year and timestamp.day == now_cs.day and timestamp.hour == now_cs.hour:
                #     print(str(cs))

                data_hour = timestamp.hour
                data_day = timestamp.day
                data_month = timestamp.month
                data_year = timestamp.year

                now = datetime.now() - timedelta(hours=4)
                now_hour = now.hour
                now_day = now.day
                now_month = now.month
                now_year = now.year

                # if math.isnan(ssa):
                #     print(symbol, "ssa is null")
                #
                # if math.isnan(ssb):
                #     print(symbol, "ssb is null")

                evol = round(((close - openp) / openp) * 100, 4)

                scan = True

                if scan:
                    if data_day == now_day and data_month == now_month and data_year == now_year and (data_hour >= now_hour):
                        if openp < ssb < close:
                            if cs>ssbchikou:
                                print("CS>SSBCHIKOU:")
                            print(timestamp, symbol, "O", openp, "H", high, "L", low, "C", close, "SSA", ssa, "SSB", ssb, "KS", ks, "TS", ts, "CS", cs, "EVOL%", evol)
                            strn = str(timestamp) + " " + symbol + " O=" + str(openp) + " H=" + str(high) + " L=" + str(low) + " C=" + str(close) + " SSA=" + str(
                                ssa) + " SSB=" + str(
                                ssb) + " KS=" + str(ks) + " TS=" + str(ts) + " CS=" + str(cs) + " EVOL%=" + str(evol)
                            fr = open("results.txt", "a")
                            fr.write(strn + '\n')
                            fr.close()
                else:
                    if data_day == now_day and data_month == now_month and data_year == now_year and (data_hour >= now_hour):
                        print(timestamp, symbol, "O", openp, "H", high, "L", low, "C", close, "SSA", ssa, "SSB", ssb, "KS", ks, "TS", ts, "CS", cs)
                        strn = str(timestamp) + " " + symbol + " O=" + str(openp) + " H=" + str(high) + " L=" + str(low) + " C=" + str(close) + " SSA=" + str(ssa) + " SSB=" + str(
                            ssb) + " KS=" + str(ks) + " TS=" + str(ts) + " CS=" + str(cs) + " EVOL%" + str(evol)
                        fr = open("results.txt", "a")
                        fr.write(strn + '\n')
                        fr.close()

        fr = open("results.txt", "a")
        fr.write(100 * '*' + '\n')
        fr.close()


x = threading.Thread(target=my_thread, args=(1,))
x.start()
