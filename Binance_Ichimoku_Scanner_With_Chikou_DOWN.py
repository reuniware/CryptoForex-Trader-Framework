import glob, os
from datetime import datetime
from datetime import timedelta
from binance.client import Client

import pandas as pd
import requests
import threading
import time
import ta
import math


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

HISTORY_RESOLUTION_MINUTE = 60
HISTORY_RESOLUTION_3MINUTE = 60 * 3
HISTORY_RESOLUTION_5MINUTE = 60 * 5
HISTORY_RESOLUTION_15MINUTE = 60 * 15
HISTORY_RESOLUTION_HOUR = 60 * 60
HISTORY_RESOLUTION_4HOUR = 60 * 60 * 4
HISTORY_RESOLUTION_DAY = 60 * 60 * 24

list_results = []
results_count = 0

stop_thread = False


def my_thread(name):
    global client, list_results, results_count, stop_thread

    log_to_evol(str(datetime.now()))

    while not stop_thread:

        dict_evol = {}

        new_results_found = False

        info_binance = Client().get_all_tickers()
        #print(info_binance)
        #exit()

        df = pd.DataFrame(info_binance)
        df.set_index('symbol')

        for index, row in df.iterrows():

            symbol = row['symbol']
            symbol_type = "n/a" #row['type']

            # filtering symbols to scan here
            if not (symbol.endswith('USDT')):
                continue

            #if not (symbol.endswith("-PERP")):
                #continue

            symbols_to_exclude = ["BEAR/USD", "BULL/USD", "HEDGE/USD", "HALF/USD", "BEAR/USDT", "BULL/USDT", "HEDGE/USDT", "HALF/USDT", "-PERP", "-1231", "BEAR2021/USD",
                                  "SHIT/USD", "VOL/USD", "VOL/USDT"]

            exclude_symbols = False

            go_to_next_symbol = False
            if exclude_symbols:
                for ste in symbols_to_exclude:
                    if symbol.endswith(ste):
                        go_to_next_symbol = True

            if go_to_next_symbol:
                continue

            print("scanning", symbol, symbol_type)

            # if symbol.endswith("BEAR/USD") or symbol.endswith("BULL/USD") or symbol.endswith("HEDGE/USD") or symbol.endswith():
            #     continue

            # Define the resolution for data downloading and scanning on the line below
            history_resolution = HISTORY_RESOLUTION_3MINUTE  # define the resolution used for the scan here
            delta_time = 0
            if history_resolution == HISTORY_RESOLUTION_MINUTE:         # using this resolution seems not ok, must be improved
                #delta_time = 60 * 5
                delta_time = 60
            elif history_resolution == HISTORY_RESOLUTION_3MINUTE:
                delta_time = 60 * 3  
            elif history_resolution == HISTORY_RESOLUTION_5MINUTE:      # using this resolution seems not ok, must be improved
                #delta_time = 60 * 5 * 25
                delta_time = 60 * 5
            elif history_resolution == HISTORY_RESOLUTION_15MINUTE:
                #delta_time = 60 * 60 * 15 * 3
                delta_time = 60 * 60 * 15
            elif history_resolution == HISTORY_RESOLUTION_HOUR:
                #delta_time = 60 * 60 * 3 * 15 * 2
                delta_time = 60 * 60
            elif history_resolution == HISTORY_RESOLUTION_4HOUR:
                delta_time = 60 * 60 * 3 * 15 * 2 * 4
            elif history_resolution == HISTORY_RESOLUTION_DAY:
                delta_time = 60 * 60 * 2000

            if history_resolution == HISTORY_RESOLUTION_MINUTE:
                interval_for_klinesT = Client.KLINE_INTERVAL_1MINUTE 
            elif history_resolution == HISTORY_RESOLUTION_3MINUTE:
                interval_for_klinesT = Client.KLINE_INTERVAL_3MINUTE
            elif history_resolution == HISTORY_RESOLUTION_5MINUTE:
                interval_for_klinesT = Client.KLINE_INTERVAL_5MINUTE
            elif history_resolution == HISTORY_RESOLUTION_15MINUTE:
                interval_for_klinesT = Client.KLINE_INTERVAL_15MINUTE
            elif history_resolution == HISTORY_RESOLUTION_HOUR:
                interval_for_klinesT = Client.KLINE_INTERVAL_1HOUR
            elif history_resolution == HISTORY_RESOLUTION_4HOUR:
                interval_for_klinesT = Client.KLINE_INTERVAL_4HOUR
            elif history_resolution == HISTORY_RESOLUTION_DAY:
                interval_for_klinesT = Client.KLINE_INTERVAL_1DAY
            else:
                print("What should I set for Client KLINE_INTERVAL ?")
                exit()

            days_ago_for_klinest = "13 day ago UTC" # for daily download by default
            if interval_for_klinesT == Client.KLINE_INTERVAL_1MINUTE:
                days_ago_for_klinest = "120 minute ago UTC"
            elif interval_for_klinesT == Client.KLINE_INTERVAL_3MINUTE:
                days_ago_for_klinest = "360 minute ago UTC"
            elif interval_for_klinesT == Client.KLINE_INTERVAL_5MINUTE:
                days_ago_for_klinest = "400 minute ago UTC"
            elif interval_for_klinesT == Client.KLINE_INTERVAL_15MINUTE:
                days_ago_for_klinest = "1200 minute ago UTC"

            try:                
                #klinesT = Client().get_historical_klines(symbol, interval_for_klinesT, "09 May 2022")
                klinesT = Client().get_historical_klines(symbol, interval_for_klinesT, days_ago_for_klinest)
                dframe = pd.DataFrame(klinesT, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])

                del dframe['ignore']
                del dframe['close_time']
                del dframe['quote_av']
                del dframe['trades']
                del dframe['tb_base_av']
                del dframe['tb_quote_av']

                dframe['close'] = pd.to_numeric(dframe['close'])
                dframe['high'] = pd.to_numeric(dframe['high'])
                dframe['low'] = pd.to_numeric(dframe['low'])
                dframe['open'] = pd.to_numeric(dframe['open'])

                dframe = dframe.set_index(dframe['timestamp'])
                dframe.index = pd.to_datetime(dframe.index, unit='ms')

            except requests.exceptions.HTTPError:
                print("Erreur (HTTPError) tentative obtention données historiques pour " + symbol)
                log_to_errors("Erreur (HTTPError) tentative obtention données historiques pour " + symbol)
                continue
            except requests.exceptions.ConnectionError:
                print("Erreur (ConnectionError) tentative obtention données historiques pour " + symbol)
                log_to_errors("Erreur (ConnectionError) tentative obtention données historiques pour " + symbol)
                continue

            # a = time.time()
            # my_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(a))
            # my_time_2 = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(a - delta_time))

            #dframe = pd.DataFrame(data)

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
                    cs = dframe['ICH_CS'].iloc[-26 - 1]  # chikou span concernant bougie n en cours
                    cs2 = dframe['ICH_CS'].iloc[-26 - 2]  # chikou span concernant bougie n-1
                    ssbchikou = dframe['ICH_SSB'].iloc[-26 - 1 + 2]
                    ssbchikou2 = dframe['ICH_SSB'].iloc[-26 - 2 + 2]
                    ssbchikou3 = dframe['ICH_SSB'].iloc[-26 - 3 + 2]
                    closechikou = dframe['close'].iloc[-26]
                    closechikou2 = dframe['close'].iloc[-26 - 1]
                    openchikou = dframe['open'].iloc[-26]
                    openchikou2 = dframe['open'].iloc[-26 - 1]
                    lowchikou = dframe['low'].iloc[-26]
                    lowchikou2 = dframe['low'].iloc[-26 - 1]
                    highchikou = dframe['high'].iloc[-26]
                    highchikou2 = dframe['high'].iloc[-26 - 1]
                    kijunchikou = dframe['ICH_KS'].iloc[-26 - 1 + 1]
                    kijunchikou2 = dframe['ICH_KS'].iloc[-26 - 2 + 1]
                    kijunchikou3 = dframe['ICH_KS'].iloc[-26 - 3 + 1]
                    tenkanchikou = dframe['ICH_TS'].iloc[-26 - 1 + 1]
                    tenkanchikou2 = dframe['ICH_TS'].iloc[-26 - 2 + 1]
                    tenkanchikou3 = dframe['ICH_TS'].iloc[-26 - 3 + 1]
                    ssachikou = dframe['ICH_SSA'].iloc[-26 - 1 + 2]
                    ssachikou2 = dframe['ICH_SSA'].iloc[-26 - 2 + 2]
                    ssachikou3 = dframe['ICH_SSA'].iloc[-26 - 3 + 2]

                except IndexError as error:
                    print(symbol + " EXCEPTION " + str(error))
                    log_to_errors(symbol + " EXCEPTION " + str(error) + '\n')
                    # quit(0)
                    continue

                #timestamp = pd.to_datetime(rowdf['time'], unit='ms')
                timestamp = pd.to_datetime(rowdf['timestamp'], unit='ms')

                error_nan_values = False
                # To check the values of Ichimoku data (use TradingView with Ichimoku Cloud to compare them)
                # print(str(timestamp) + " " + symbol + " closecs=" + str(closechikou) + " closecs2=" + str(closechikou2) + " CS=" + str(cs) + " CS2=" + str(cs2) + " SSBCS=" + str(ssbchikou) + " SSBCS2=" + str(ssbchikou2) + " SSBCS3=" + str(ssbchikou3) + " KSCS=" + str(kijunchikou)+ " KSCS2=" + str(kijunchikou2)+ " KSCS3=" + str(kijunchikou3) + " TSCS=" + str(tenkanchikou)+ " TSCS2=" + str(tenkanchikou2)+ " TSCS3=" + str(tenkanchikou3) + " SSACS=" + str(ssachikou) + " SSACS2=" + str(ssachikou2) + " SSACS3=" + str(ssachikou3))
                if math.isnan(closechikou) or math.isnan(closechikou2) or math.isnan(cs) or math.isnan(cs2) or math.isnan(ssbchikou) or math.isnan(ssbchikou2) or math.isnan(
                        ssbchikou3) or math.isnan(kijunchikou) or math.isnan(kijunchikou2) or math.isnan(kijunchikou3) or math.isnan(tenkanchikou) or math.isnan(
                    tenkanchikou2) or math.isnan(tenkanchikou3) or math.isnan(ssachikou) or math.isnan(ssbchikou2) or math.isnan(ssachikou3):
                    print(symbol + " THERE ARE NAN VALUES IN ICHIMOKU DATA")
                    log_to_errors(symbol + " THERE ARE NAN VALUES IN ICHIMOKU DATA" + '\n')
                    error_nan_values = True
                    # quit(0)

                if error_nan_values:
                    continue

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

                if history_resolution == HISTORY_RESOLUTION_MINUTE:
                    datetime_result_min = datetime.now() - timedelta(minutes=1)
                elif history_resolution == HISTORY_RESOLUTION_3MINUTE:
                    #datetime_result_min = datetime.now() - timedelta(minutes=15)
                    datetime_result_min = datetime.now() - timedelta(minutes=3)
                elif history_resolution == HISTORY_RESOLUTION_5MINUTE:
                    #datetime_result_min = datetime.now() - timedelta(minutes=15)
                    datetime_result_min = datetime.now() - timedelta(minutes=5)
                elif history_resolution == HISTORY_RESOLUTION_15MINUTE:
                    #datetime_result_min = datetime.now() - timedelta(hours=1)
                    datetime_result_min = datetime.now() - timedelta(minutes=15)
                elif history_resolution == HISTORY_RESOLUTION_HOUR:
                    datetime_result_min = datetime.now() - timedelta(hours=1)
                elif history_resolution == HISTORY_RESOLUTION_4HOUR:
                    datetime_result_min = datetime.now() - timedelta(hours=4)
                elif history_resolution == HISTORY_RESOLUTION_DAY:
                    datetime_result_min = datetime.now() - timedelta(hours=24)
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

                if history_resolution == HISTORY_RESOLUTION_DAY:
                    result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year  # for daily scan, we must not test the hours
                elif history_resolution == HISTORY_RESOLUTION_MINUTE:
                    result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour == datetime_result_min_hour and data_minute >= datetime_result_min_minute                    
                elif history_resolution == HISTORY_RESOLUTION_3MINUTE:
                    result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour == datetime_result_min_hour and data_minute >= datetime_result_min_minute                    
                elif history_resolution == HISTORY_RESOLUTION_5MINUTE:
                    # print("comparing : " + str(data_hour) + " " + str(data_minute) + " to " + str(datetime_result_min_hour) + " " + str(datetime_result_min_minute))
                    result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour == datetime_result_min_hour and data_minute >= datetime_result_min_minute                    
                elif history_resolution == HISTORY_RESOLUTION_15MINUTE:
                    result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour == datetime_result_min_hour and data_minute >= datetime_result_min_minute                    
                elif history_resolution == HISTORY_RESOLUTION_HOUR:
                    result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour > datetime_result_min_hour #and data_minute >= datetime_result_min_minute                    
                else:
                    result_ok = data_day == datetime_result_min_day and data_month == datetime_result_min_month and data_year == datetime_result_min_year and data_hour >= datetime_result_min_hour

                if scan:
                    if result_ok:
                        # if openp < ssb < close or openp > ssb and close > ssb:
                        # Define your own criterias for filtering assets on the line below
                        if openp < ks and close < ks and close < ts and close < openp and close < ssa and close < ssb and cs < lowchikou and cs < kijunchikou and cs < ssbchikou and cs < ssachikou and cs < tenkanchikou: #and evol_co < -0.1:
                            cs_results = ""
                            if cs < ssbchikou:
                                cs_results += "* CS < SSBCHIKOU - "
                            if cs < ssachikou:
                                cs_results += "* CS < SSACHIKOU - "
                            if cs < kijunchikou:
                                cs_results += "* CS < KSCHIKOU - "
                            if cs < tenkanchikou:
                                cs_results += "* CS < TSCHIKOU - "
                            if cs < closechikou:
                                cs_results += "* CS < CLOSECHIKOU - "
                            if cs < lowchikou:
                                cs_results += "* CS < LOWCHIKOU - "
                            # if cs_results != "":
                            #     log_to_results(cs_results)

                            # print(timestamp, symbol, "O", openp, "H", high, "L", low, "C", close, "SSA", ssa, "SSB", ssb, "KS", ks, "TS", ts, "CS", cs, "EVOL%", evol_co)
                            # print("")
                            str_result = str(timestamp) + " " + symbol + " " + symbol_type + " SSA=" + str(ssa) + " SSB=" + str(
                                ssb) + " KS=" + str(ks) + " TS=" + str(ts) + " O=" + str(openp) + " H=" + str(high) + " L=" + str(
                                low)  # + " C=" + str(close) + " CS=" + str(cs) + " EVOL%=" + str(evol_co)     # We don't concatenate the variable parts (for comparisons in list_results)

                            if not (str_result in list_results):
                                if not new_results_found:
                                    new_results_found = True
                                results_count = results_count + 1
                                list_results.append(str_result)
                                # print(cs_results)
                                str_result = cs_results + "\n" + str(results_count) + " " + str_result + " C=" + str(close) + " CS=" + str(cs) + " EVOL(C/O)%=" + str(
                                    evol_co)  # We add the data with variable parts
                                
                                str_result += "\nhttps://fr.tradingview.com/chart/4hWFksx8/?symbol=BINANCE%3A" + symbol
                                str_result += "\nhttps://fr.tradingview.com/chart/4hWFksx8/?symbol=BINANCE%3A" + symbol + "PERP"

                                print(str_result + "\n")
                                log_to_results(str_result + "\n")

                                dict_evol[symbol] = evol_co

                else:
                    # if result_ok:
                    print(timestamp, symbol, "O", openp, "H", high, "L", low, "C", close, "SSA", ssa, "SSB", ssb, "KS", ks, "TS", ts, "CS", cs)
                    str_result = str(timestamp) + " " + symbol + " O=" + str(openp) + " H=" + str(high) + " L=" + str(low) + " C=" + str(close) + " SSA=" + str(
                        ssa) + " SSB=" + str(
                        ssb) + " KS=" + str(ks) + " TS=" + str(ts) + " CS=" + str(cs) + " EVOL%(C/O)=" + str(evol_co)
                    log_to_results(str_result)

        if new_results_found:
            log_to_results(100 * '*' + "\n")

        new_dict = sorted(dict_evol.items(), key=lambda kv: (kv[1], kv[0]))
        print(str(datetime.now()) + " " + str(new_dict))
        log_to_evol(str(datetime.now()) + " " + str(new_dict))

        # Remove the line below to scan in loop
        #stop_thread = True


x = threading.Thread(target=my_thread, args=(1,))
x.start()
