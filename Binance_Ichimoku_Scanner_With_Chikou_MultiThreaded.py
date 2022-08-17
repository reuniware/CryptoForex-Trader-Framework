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
import tweepy

from enum import Enum


class ScanType(Enum):
    UP = 0
    DOWN = 1


# Set this variable to ScanType.UP for scanning uptrend assets or to ScanType.DOWN for scanning downtrend assets
scan_type = ScanType.UP

# Set this variable to False to scan in spot mode
scan_futures = False

str_twitter = ""

enable_tweet = False


def tweet(str_to_tweet):
    if enable_tweet is False:
        return

    twitter_auth_keys = {
        "consumer_key": "",
        "consumer_secret": "",
        "access_token": "",
        "access_token_secret": ""
    }

    auth = tweepy.OAuthHandler(
        twitter_auth_keys['consumer_key'],
        twitter_auth_keys['consumer_secret']
    )
    auth.set_access_token(
        twitter_auth_keys['access_token'],
        twitter_auth_keys['access_token_secret']
    )
    api = tweepy.API(auth)

    tweet = str_to_tweet
    status = api.update_status(status=tweet)


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


def log_to_tenkan(str_to_log):
    fr = open("tenkan.txt", "a")
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

if os.path.exists("tenkan.txt"):
    os.remove("tenkan.txt")

for fg in glob.glob("CS_*.txt"):
    os.remove(fg)


print("Scanning type =", scan_type.name)
# log_to_results("Scanning type = " + scan_type.name)

results_count = 0

stop_thread = False

list_results = []
list_results_tenkan = []

array_futures = []

# Set loop_scan to True to scan in loop
loop_scan = True

maxthreads = 75

# Set the timeframe to scan on the following line
interval_for_klinesT = Client.KLINE_INTERVAL_1MINUTE
print("Scanning timeframe =", str(interval_for_klinesT))

days_ago_for_klinest = "80 day ago UTC"  # for daily download by default
if interval_for_klinesT == Client.KLINE_INTERVAL_1MINUTE:
    days_ago_for_klinest = "640 minute ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_3MINUTE:
    days_ago_for_klinest = "1920 minute ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_5MINUTE:
    days_ago_for_klinest = "3200 minute ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_15MINUTE:
    days_ago_for_klinest = "9600 minute ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_30MINUTE:
    days_ago_for_klinest = "19200 minute ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_1HOUR:
    days_ago_for_klinest = "160 hour ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_2HOUR:
    days_ago_for_klinest = "960 hour ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_4HOUR:
    days_ago_for_klinest = "960 hour ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_6HOUR:
    days_ago_for_klinest = "160 day ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_8HOUR:
    days_ago_for_klinest = "160 day ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_12HOUR:
    days_ago_for_klinest = "160 day ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_1DAY:
    days_ago_for_klinest = "160 day ago UTC"
elif interval_for_klinesT == Client.KLINE_INTERVAL_3DAY:
    days_ago_for_klinest = "240 day ago UTC"

dict_evol = {}
dict_detect = {}
new_results_found = False
new_results_tenkan_found = False

nb_trending_assets = 0
nb_total_assets = 0


def execute_code(symbol):
    global results_count, dict_evol, new_results_tenkan_found, dict_detect
    global new_results_found
    global str_twitter
    global nb_trending_assets, nb_total_assets

    symbol_type = "n/a"

    try:
        # klinesT = Client().get_historical_klines(symbol, interval_for_klinesT, "09 May 2022")
        if scan_futures:
            klinesT = Client().get_historical_klines(symbol, interval_for_klinesT, days_ago_for_klinest,
                                                     klines_type=HistoricalKlinesType.FUTURES)
        else:
            klinesT = Client().get_historical_klines(symbol, interval_for_klinesT, days_ago_for_klinest)

        # print(" (ok)")
        nb_total_assets = nb_total_assets + 1

        dframe = pd.DataFrame(klinesT,
                              columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av',
                                       'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])

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
        return
    except requests.exceptions.ConnectionError:
        print("Erreur (ConnectionError) tentative obtention données historiques pour " + symbol)
        log_to_errors("Erreur (ConnectionError) tentative obtention données historiques pour " + symbol)
        return
    except binance.exceptions.BinanceAPIException:
        # in case the symbol does not exist in futures then this exception is thrown
        # print("")
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

        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        # print(dframe['ICH_CS'])

    except KeyError as err:
        print(err)
        return

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
            high2 = dframe['high'].iloc[-2]
            high3 = dframe['high'].iloc[-3]
            high4 = dframe['high'].iloc[-4]
            high5 = dframe['high'].iloc[-5]
            high6 = dframe['high'].iloc[-6]
            high7 = dframe['high'].iloc[-7]
            high8 = dframe['high'].iloc[-8]
            high9 = dframe['high'].iloc[-9]

            close2 = dframe['close'].iloc[-2]
            close3 = dframe['close'].iloc[-3]
            close4 = dframe['close'].iloc[-4]
            close5 = dframe['close'].iloc[-5]
            close6 = dframe['close'].iloc[-6]
            close7 = dframe['close'].iloc[-7]
            close8 = dframe['close'].iloc[-8]
            close9 = dframe['close'].iloc[-9]

            open2 = dframe['open'].iloc[-2]
            open3 = dframe['open'].iloc[-3]
            open4 = dframe['open'].iloc[-4]
            open5 = dframe['open'].iloc[-5]
            open6 = dframe['open'].iloc[-6]
            open7 = dframe['open'].iloc[-7]
            open8 = dframe['open'].iloc[-8]
            open9 = dframe['open'].iloc[-9]

            low2 = dframe['low'].iloc[-2]
            low3 = dframe['low'].iloc[-3]
            low4 = dframe['low'].iloc[-4]
            low5 = dframe['low'].iloc[-5]
            low6 = dframe['low'].iloc[-6]
            low7 = dframe['low'].iloc[-7]
            low8 = dframe['low'].iloc[-8]
            low9 = dframe['low'].iloc[-9]

            ts2 = dframe['ICH_TS'].iloc[-2]
            ts3 = dframe['ICH_TS'].iloc[-3]

            ks2 = dframe['ICH_KS'].iloc[-2]
            ks3 = dframe['ICH_KS'].iloc[-3]

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

        except IndexError as error:
            print(symbol + " EXCEPTION " + str(error))
            log_to_errors(symbol + " EXCEPTION " + str(error) + '\n')
            # quit(0)
            break

        # timestamp = pd.to_datetime(rowdf['time'], unit='ms')
        timestamp = pd.to_datetime(rowdf['timestamp'], unit='ms')

        error_nan_values = False
        # To check the values of Ichimoku data (use TradingView with Ichimoku Cloud to compare them)
        # log_to_results(str(timestamp) + " " + symbol + " closecs=" + str(closechikou) + " closecs2=" + str(closechikou2) + " CS=" + str(cs) + " CS2=" + str(cs2) + " SSBCS=" + str(ssbchikou) + " SSBCS2=" + str(ssbchikou2) + " SSBCS3=" + str(ssbchikou3) + " KSCS=" + str(kijunchikou)+ " KSCS2=" + str(kijunchikou2)+ " KSCS3=" + str(kijunchikou3) + " TSCS=" + str(tenkanchikou)+ " TSCS2=" + str(tenkanchikou2)+ " TSCS3=" + str(tenkanchikou3) + " SSACS=" + str(ssachikou) + " SSACS2=" + str(ssachikou2) + " SSACS3=" + str(ssachikou3) + " SSA=" + str(ssa) + " SSB=" + str(ssb))
        # exit()

        if math.isnan(ssa) or math.isnan(ssb) or math.isnan(closechikou) or math.isnan(closechikou2) or math.isnan(cs) \
                or math.isnan(cs2) or math.isnan(ssbchikou) or math.isnan(ssbchikou2) or math.isnan(ssbchikou3) \
                or math.isnan(kijunchikou) or math.isnan(kijunchikou2) or math.isnan(kijunchikou3) or \
                math.isnan(tenkanchikou) or math.isnan(tenkanchikou2) or math.isnan(tenkanchikou3) or \
                math.isnan(ssachikou) or math.isnan(ssbchikou2) or math.isnan(ssachikou3):
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

                # print("result ok")
                # if openp < ssb < close or openp > ssb and close > ssb:
                # Define your own criterias for filtering assets on the line below

                if scan_type == ScanType.UP:

                    # if current close price is greater than n previous high prices then we consider it is growing
                    growing = False
                    for n in range(2, 5):  # 50 for 1-min
                        high_n = dframe['high'].iloc[-n]
                        if close < high_n:
                            growing = False
                            break
                        growing = True

                    # condition_is_satisfied = open2 < ks2 and close > ks
                    # condition_is_satisfied = low >= ssb and low <= ssb + ssb/100*0.5
                    # condition_is_satisfied = close > openp and openp < ks and close > ks

                    # condition_is_satisfied = ((ssbchikou > ssachikou and ssbchikou2 > ssachikou2 and cs2 < ssbchikou2 and cs > ssbchikou) \
                    #    or (ssachikou > ssbchikou and ssachikou2 < ssbchikou2 and cs2 < ssachikou2 and cs > ssachikou)) \
                    #    and (cs > ssachikou and cs > ssbchikou and cs > tenkanchikou and cs > kijunchikou)

                    condition_is_satisfied = high > low and close > openp and close > ssa and close > ssb and close > ts and close > ks and cs > kijunchikou  # and cs > ssachikou and cs > ssbchikou and cs > highchikou
                    # condition_is_satisfied = growing == True and close > (high - high / 100 * 0.2) and high > low and close > openp and close > ssa and close > ssb and close > ts and close > ks and cs > kijunchikou # and cs > ssachikou and cs > ssbchikou and cs > highchikou
                    # condition_is_satisfied = growing == True and close > (high - high / 100 * 0.2) and high > low and close > openp and close > ssa and close > ssb and close > ts and close > ks  # and cs > ssachikou and cs > ssbchikou and cs > highchikou
                    # condition_is_satisfied = ssbchikou3 > ssachikou3 and ssbchikou2 > ssachikou2 and ssb and cs3 < ssbchikou3 and cs2 > ssbchikou2
                    # H12 : condition_is_satisfied = ts/ts2>1.015 and ts > ts2 and close > openp and close > ssa and close > ssb and close > ts and close > ks and closechikou > ssachikou and closechikou > ssbchikou #and close / openp > 1.0025
                    # condition_is_satisfied = ts > ts2 and ts/ts2 > 1.004 and close > openp and close > ssa and close > ssb #and close / openp > 1.0025
                    # condition_is_satisfied = ts > ts2 and (ts/ts2 > 1.10)
                    # condition_is_satisfied = close > openp and openp > ks and openp > ssb and close > ks and close > ts and close > ssa and close > ssb and cs > highchikou and cs > kijunchikou and cs > ssbchikou and cs > ssachikou and cs > tenkanchikou
                    # condition_is_satisfied = openp > ks and close > ks and close > ts and close > openp and close > ssa and close > ssb and cs > highchikou and cs > kijunchikou and cs > ssbchikou and cs > ssachikou and cs > tenkanchikou
                    # condition_is_satisfied = (ssb>ssa and openp<ssb and close>ssb) or (ssa>ssb and openp<ssa and close>ssa)
                    # condition_is_satisfied = openp<ks and close>ks
                    # condition_is_satisfied = openp>ssa and close>ssa and openp>ssb and close>ssb
                elif scan_type == ScanType.DOWN:
                    condition_is_satisfied = openp < ks and close < ks and close < ts and close < openp and close < ssa and close < ssb and cs < lowchikou and cs < kijunchikou and cs < ssbchikou and cs < ssachikou and cs < tenkanchikou

                if condition_is_satisfied:
                    nb_trending_assets = nb_trending_assets + 1

                    # print("cs cs2 cs3", cs, cs2, cs3)
                    # print(symbol, "ts", ts, "ts2", ts2, "ts/ts2", ts / ts2)
                    print(symbol, "candlestick timestamp = ", str(timestamp))

                    # print("ssbchikou2, ssachikou2, ssbchikou3, ssachikou3, cs3, ssbchikou3, cs2, ssbchikou2", ssbchikou2, ssachikou2, ssbchikou3, ssachikou3, cs3, ssbchikou3, cs2, ssbchikou2)

                    str_lien = "https://tradingview.com/chart/?symbol=BINANCE%3A" + symbol
                    str_result_tenkan = symbol + " " + str_lien + " c=" + str(close) + " o=" + str(
                        openp) + " c/o=" + str(
                        close / openp) + " ts=" + str(ts) + " ts2=" + str(ts2) + " ts/ts2=" + str(
                        ts / ts2)

                    if not (str_result_tenkan in list_results_tenkan):
                        if not (new_results_tenkan_found):
                            new_results_tenkan_found = True
                        list_results_tenkan.append(str_result_tenkan)

                        nbdetect = 0
                        if symbol in dict_detect:
                            nbdetect = dict_detect[symbol]
                            nbdetect = nbdetect + 1
                            dict_detect[symbol] = nbdetect
                        else:
                            dict_detect[symbol] = 1

                        log_to_tenkan(str(datetime.now()) + " : " + str(timestamp) + " (" + str(dict_detect[symbol]) + ")" + " " + str_result_tenkan)

                        symboltweet = ''

                        if symbol.endswith('DOWNUSDT') or symbol.endswith('UPUSDT'):
                            symboltweet = '#' + symbol
                        elif symbol.endswith('USDT'):
                            symboltweet = '$' + symbol.replace('USDT', '')
                        else:
                            symboltweet = '#' + symbol

                        str_for_twitter = str(datetime.now()) + " : " + symboltweet + " is pumping now (" + str(
                            interval_for_klinesT) + "). \nCurrent price=" + str(
                            close) + " $usdt\n#Ichimoku #Bitcoin #DataScience #Crypto #Binance"
                        if len(str_for_twitter) > 280:
                            print("Len of tweet is > 280")
                        else:
                            print("Len of tweet is ok = " + str(len(str_for_twitter)))
                            tweet(str_for_twitter)

                        # log_to_tenkan(str(dframe['close'].iloc[-1]))

                    # print(symbol, "ssachikou3", ssachikou3, "ssachikou2" ,ssachikou2, "cs3", cs3, "cs2", cs2)

                    cs_results = ""

                    if scan_type == ScanType.UP:
                        if cs > ssbchikou:
                            cs_results += "* CS > SSBCHIKOU - "
                        if cs > ssachikou:
                            cs_results += "* CS > SSACHIKOU - "
                        if cs > kijunchikou:
                            cs_results += "* CS > KSCHIKOU - "
                        if cs > tenkanchikou:
                            cs_results += "* CS > TSCHIKOU - "
                        if cs > closechikou:
                            cs_results += "* CS > CLOSECHIKOU - "
                        if cs > highchikou:
                            cs_results += "* CS > HIGHCHIKOU - "
                        # if cs_results != "":
                        #     log_to_results(cs_results)

                        # print(timestamp, symbol, "O", openp, "H", high, "L", low, "C", close, "SSA", ssa, "SSB", ssb, "KS", ks, "TS", ts, "CS", cs, "EVOL%", evol_co)
                    elif scan_type == ScanType.DOWN:
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
                        if cs < highchikou:
                            cs_results += "* CS < LOWCHIKOU - "
                        # if cs_results != "":
                        #     log_to_results(cs_results)

                        # print(timestamp, symbol, "O", openp, "H", high, "L", low, "C", close, "SSA", ssa, "SSB", ssb, "KS", ks, "TS", ts, "CS", cs, "EVOL%", evol_co)

                    # print("")
                    str_result = str(timestamp) + " " + symbol + " " + symbol_type + " SSA=" + str(ssa) + " SSB=" + str(
                        ssb) + " KS=" + str(
                        ks) + " TS=" + str(ts) + " O=" + str(openp) + " H=" + str(high) + " L=" + str(
                        low) + " SSBCS=" + str(
                        ssbchikou)  # + " C=" + str(close) + " CS=" + str(cs) + " EVOL%=" + str(evol_co)     # We don't concatenate the variable parts (for comparisons in list_results)

                    if not (str_result in list_results):
                        if not new_results_found:
                            new_results_found = True
                        results_count = results_count + 1
                        list_results.append(str_result)
                        # print(cs_results)
                        str_result = cs_results + "\n" + str(results_count) + " " + str_result + " C=" + str(
                            close) + " CS=" + str(cs) + " EVOL(C/O)%=" + str(
                            evol_co)  # We add the data with variable parts

                        if scan_futures:
                            str_result += "\nhttps://tradingview.com/chart/?symbol=BINANCE%3A" + symbol + "PERP"
                        else:
                            str_result += "\nhttps://tradingview.com/chart/?symbol=BINANCE%3A" + symbol

                        print(str_result + "\n")
                        log_to_results(str(datetime.now()) + ":" + str_result + "\n")

                        dict_evol[symbol] = str(evol_co) + ";" + str(close) + ";" + str(ts / ts2)

                        str_twitter += "$" + symbol.replace("USDT", "") + " "

        else:

            if symbol in dict_evol:
                del (dict_evol[symbol])

            # if result_ok:
            print(timestamp, symbol, "O", openp, "H", high, "L", low, "C", close, "SSA", ssa, "SSB", ssb, "KS", ks,
                  "TS", ts, "CS", cs, "SSB CS", ssbchikou)
            str_result = str(timestamp) + " " + symbol + " O=" + str(openp) + " H=" + str(high) + " L=" + str(
                low) + " C=" + str(close) + " SSA=" + str(
                ssa) + " SSB=" + str(ssb) + " KS=" + str(ks) + " TS=" + str(ts) + " CS=" + str(cs) + " SSB CS=" + str(
                ssbchikou) + " EVOL%(C/O)=" + str(evol_co)

            log_to_results(str(datetime.now()) + ":" + str_result)


# maxthreads = 10
threadLimiter = threading.BoundedSemaphore(maxthreads)


def scan_one(symbol):
    threadLimiter.acquire()
    try:
        execute_code(symbol)
    finally:
        threadLimiter.release()


threads = []


# nb_trending_assets = 0

def main_thread(name):
    global client, list_results, results_count, stop_thread, interval_for_klinesT
    global new_results_found
    global nb_trending_assets, nb_total_assets

    log_to_evol(str(datetime.now()))

    while not stop_thread:

        # dict_evol = {}

        # new_results_found = False

        info_binance = Client().get_all_tickers()
        # print(info_binance)
        # exit()

        df = pd.DataFrame(info_binance)
        df.set_index('symbol')

        for index, row in df.iterrows():

            symbol = row['symbol']
            symbol_type = "n/a"  # row['type']

            # print(symbol)

            # filtering symbols to scan here
            if not symbol.endswith('USDT'):  # or symbol.endswith("DOWNUSDT") or symbol.endswith("UPUSDT"):
                continue

            if symbol.endswith('UPUSDT') or symbol.endswith(
                    'DOWNUSDT'):  # or symbol.endswith("DOWNUSDT") or symbol.endswith("UPUSDT"):
                continue

            if symbol in ('BUSDUSDT', 'USDCUSDT', 'TUSDUSDT', 'USDPUSDT'):
                continue

                # if symbol != 'BTCUSDT':
                # continue

                # if scan_futures:
                # print(symbol, "trying to scan in futures", end=" ")
                print(symbol, "trying to scan in futures")
            # else:
            # print(symbol, "trying to scan", end=" ")
            # print(symbol, "trying to scan")

            # if symbol.endswith("BEAR/USD") or symbol.endswith("BULL/USD") or symbol.endswith("HEDGE/USD") or symbol.endswith():
            #     continue

            try:
                t = threading.Thread(target=scan_one, args=(symbol,))
                threads.append(t)
                t.start()
            except requests.exceptions.ConnectionError:
                continue

        nb_trending_assets = 0
        nb_total_assets = 0

        for tt in threads:
            tt.join()

        log_to_results(str(datetime.now()) + " nb_trending_assets =" + str(nb_trending_assets))
        log_to_evol(str(datetime.now()) + " nb_trending_assets =" + str(nb_trending_assets))

        log_to_results(str(datetime.now()) + " nb_total_assets =" + str(nb_total_assets))
        log_to_evol(str(datetime.now()) + " nb_total_assets =" + str(nb_total_assets))

        print(str(datetime.now()) + " All threads finished.")
        log_to_results(str(datetime.now()) + " All threads finished.")

        time.sleep(1)

        if loop_scan == True:
            stop_thread = False
        else:
            stop_thread = True
        #####

        if new_results_found:
            log_to_results(100 * '*' + "\n")

        new_dict = sorted(dict_evol.items(), key=lambda kv: (kv[1], kv[0]))
        if new_dict:
            print(str(datetime.now()) + " " + str(new_dict) + "\n")
            log_to_evol(str(datetime.now()) + " " + str(new_dict))
            log_to_results(str(datetime.now()) + " " + str(new_dict) + "\n")

        dict_evol.clear()
        list_results.clear()

        # Remove the line below to scan in loop
        # stop_thread = True

        log_to_results(str_twitter)


x = threading.Thread(target=main_thread, args=(1,))
x.start()
