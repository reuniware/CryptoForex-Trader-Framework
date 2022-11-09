import os
import ccxt
import signal
import sys
from datetime import datetime


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)


signal.signal(signal.SIGINT, signal_handler)

excludeSpecialSymbolsFromGateIo = True
excludeSpecialSymbolsFromBinance = True

currentDateAndTime = datetime.now()
stryear = format(currentDateAndTime.year, '04')
strmonth = format(currentDateAndTime.month, '02')
strday = format(currentDateAndTime.day, '02')
strhour = format(currentDateAndTime.hour, '02')
strmin = format(currentDateAndTime.minute, '02')

# Set this variable to True for logging only positive evolutions, to False for logging all.
only_positive_evol = False
ope_for_filename = ""
if only_positive_evol is True:
    ope_for_filename = "_ope"

file_filter = "20221109"
file_filter2 = ""
#file_filter = ""

logfilename = "./ScanResultsAnalyzer/" + stryear + strmonth + strday + strhour + strmin + "_analyzer_results_[" + file_filter.replace(
    '.txt', '') + "]"  + "[" + file_filter2.replace('.txt', '') + "]" + ope_for_filename + ".txt"


def log_to_results(str_to_log):
    fr = open(logfilename, "a")
    fr.write(str_to_log + "\n")
    fr.close()


def delete_results_log():
    if os.path.exists(logfilename):
        os.remove(logfilename)


delete_results_log()

print("Current date and time = " + str(currentDateAndTime))
log_to_results("Current date and time = " + str(currentDateAndTime))

print("Only positive evol :", only_positive_evol)
log_to_results("Only positive evol : " + str(only_positive_evol))

print("excludeSpecialSymbolsFromGateIo : " + str(excludeSpecialSymbolsFromGateIo))
print("excludeSpecialSymbolsFromBinance : " + str(excludeSpecialSymbolsFromBinance))

exchanges = {}
for id in ccxt.exchanges:
    exchange = getattr(ccxt, id)
    exchanges[id] = exchange()
    # print(exchanges[id])
    try:
        ex = exchanges[id]
        # markets = ex.fetch_markets()
        # print(markets)
    except:
        continue

# filetoprocess = "202210241557_scan_binance_usdt_gotk.txt"

# you must launch Ichimoku2022_Multithreaded as the following example :
# python Ichimoku_Multithreaded.py -e binance -f *usdt -gotk
# the result file will be created in the ./ScanResults folder
# the result file will look like "202210241557_scan_binance_usdt_gotk.txt"
# there can be more than one result file but I advise you to begin with one
# then launch this python script : python analyze-scan-results.py
# it will analyze the file(s) ending with "_binance_usdt_gotk.txt"
# it will output its results in the file named "analyze_scan_results.txt"
# what will be analyzed is the evolution of the assets that have got over their kijun sen line
#   relatively to the current value of these assets
#   the results will never be the same because the analysis is done relatively to the current value
#   (for the same result file analyzed twice or more, eg. "202210241557_scan_binance_usdt_gotk.txt")

array_evol_tf_group_global = []
global_dict_evol_file = {}
global_dict_evol_tf_group = {}
global_dict_assets_per_tf_group = {}

special_gateio_results = []

if file_filter.strip() != "":
    print("File filter condition = " + file_filter)
    log_to_results("File filter condition = " + file_filter)
else:
    print("File filter condition = ALL FILES")
    log_to_results("File filter condition = ALL FILES")

if file_filter2.strip() != "":
    print("File filter 2 condition = " + file_filter2)
    log_to_results("File filter 2 condition = " + file_filter2)
else:
    print("File filter 2 condition = ALL FILES")
    log_to_results("File filter 2 condition = ALL FILES")

print("")
log_to_results("")

for filename in os.listdir("ScanResults"):

    nb_assets_in_file = 0

    condition = False
    if file_filter.strip() != "":
        condition = file_filter in filename
        if file_filter2.strip() != "":
            condition = condition and (file_filter2 in filename)
    else:
        condition = filename in filename

    # if "_scan_binance_usdt_iotc.txt" in filename: #filename == filename:
    # if filename in filename: #filename == filename:
    if condition is True:
        print("PROCESSING", filename)
        log_to_results("PROCESSING " + filename)
        line = 1

        group_of_timeframes = ""

        dict_evol_tf_group = {}
        dict_assets_per_tf_group = {}

        tickers_downloaded = False

        try:
            with open(os.path.join("ScanResults", filename), 'r') as f:
                # text = f.read()
                while True:
                    text = f.readline()
                    if not text:
                        break
                    if line > 1:
                        # print(text)

                        exchange_id = text.split(' ')[2]
                        exchange = exchanges[exchange_id]

                        split_term = 'spot'
                        if exchange_id == 'bybit':
                            split_term = 'swap'

                        if not tickers_downloaded:
                            tickers = exchange.fetch_tickers()
                            tickers_downloaded = True

                        symbol = text.split(' ')[0]
                        # Bypass special leverage symbols from gateio ; Change variable excludeSpecialSymbolsFromGateIo to True if you need to include these
                        if excludeSpecialSymbolsFromGateIo is True and (symbol.endswith("3S_USDT") or symbol.endswith("3L_USDT") or symbol.endswith("5S_USDT") or symbol.endswith("5L_USDT")) or symbol.endswith("BEAR_USDT") or symbol.endswith("BULL_USDT"):
                            #print("Bypassed : " + symbol)
                            #log_to_results("Bypassed : " + symbol)
                            continue
                        # Bypass special symbols from binance ; Change variable excludeSpecialSymbolsFromBinance to True if you need to include these
                        if excludeSpecialSymbolsFromBinance is True and (symbol.endswith("DOWNUSDT") or symbol.endswith("UPUSDT")):
                            #print("Bypassed : " + symbol)
                            #log_to_results("Bypassed : " + symbol)                     
                            continue
                        # print(symbol)
                        price = float(text.split('[')[2].split('= ')[1].split(']')[0])
                        # result = exchange.fetch_ohlcv(symbol, '1m', limit=1)

                        currentprice = 0
                        symbol_found = False
                        for symbol2, ticker in tickers.items():
                            #print(symbol2)
                            if exchange_id == 'binance':
                                symbol2 = symbol2.replace('/', '')
                            elif exchange_id == 'gateio':
                                symbol = symbol.replace('_', '/')
                            elif exchange_id == 'bybit':
                                symbol2 = symbol2.replace('/', '').replace(':USDT', '')
                            if symbol2 == symbol:
                                #print(symbol2, ticker['datetime'], 'close: ' + str(ticker['close']))
                                currentprice = float(ticker['close'])
                                symbol_found = True
                                break

                        if symbol_found == False:
                            print("symbol has not been found in tickers :", symbol, symbol2)
                            continue

                        #currentprice = float(result[0][4])
                        #tickers = exchange.fetch_tickers()

                        # evol = float("{:.2f}".format((currentprice - price)/price*100))
                        if price > 0:
                            evol = (currentprice - price) / price * 100
                        else:
                            evol = 0

                        bypass = False
                        if only_positive_evol is True:
                            if evol < 0:
                                bypass = True

                        if bypass is False:

                            # To have less characters on outputs (this can be removed/commented if necessary)
                            if exchange_id == "gateio":
                                if symbol.endswith('_USDT'): # might be useless now with new way of getting tickers
                                    symbol = symbol.replace('_USDT', '')
                                if symbol.endswith('/USDT'):
                                    symbol = symbol.replace('/USDT', '')
                            elif exchange_id == "binance":
                                if symbol.endswith('USDT'):
                                    symbol = symbol.replace('USDT', '')

                            fill_symbol = " " * (16 - len(str(symbol)))
                            fill_price = " " * (16 - len(str(price)))
                            fill_currentprice = " " * (16 - len(str(currentprice)))
                            fill_evol = " " * (16 - len(str(evol)))

                            parsed_group_of_timeframes = text.split('[')[0].split(split_term)[2].strip()

                            # print(parsed_group_of_timeframes)
                            if parsed_group_of_timeframes not in dict_assets_per_tf_group:
                                dict_assets_per_tf_group[parsed_group_of_timeframes] = symbol
                            else:
                                currentval = dict_assets_per_tf_group[parsed_group_of_timeframes]
                                dict_assets_per_tf_group[parsed_group_of_timeframes] = currentval + ";" + symbol
                            # print(dict_assets_per_tf_group)

                            if parsed_group_of_timeframes not in global_dict_assets_per_tf_group:
                                global_dict_assets_per_tf_group[parsed_group_of_timeframes] = symbol
                            else:
                                currentval = global_dict_assets_per_tf_group[parsed_group_of_timeframes]
                                global_dict_assets_per_tf_group[parsed_group_of_timeframes] = currentval + ";" + symbol

                            if group_of_timeframes == "":
                                # print("first group of timeframes detected =", current_group_of_timeframes)
                                group_of_timeframes = parsed_group_of_timeframes

                                if group_of_timeframes in dict_evol_tf_group:
                                    current_val = dict_evol_tf_group[group_of_timeframes]
                                    dict_evol_tf_group[group_of_timeframes] = (float(current_val) + evol)
                                else:
                                    dict_evol_tf_group[group_of_timeframes] = evol

                                if group_of_timeframes in global_dict_evol_tf_group:
                                    current_val = global_dict_evol_tf_group[group_of_timeframes]
                                    global_dict_evol_tf_group[group_of_timeframes] = (float(current_val) + evol)
                                else:
                                    global_dict_evol_tf_group[group_of_timeframes] = evol

                            elif parsed_group_of_timeframes != group_of_timeframes:
                                # print("new group of timeframes detected =", current_group_of_timeframes)
                                group_of_timeframes = parsed_group_of_timeframes

                                if group_of_timeframes in dict_evol_tf_group:
                                    current_val = dict_evol_tf_group[group_of_timeframes]
                                    dict_evol_tf_group[group_of_timeframes] = (float(current_val) + evol)
                                else:
                                    dict_evol_tf_group[group_of_timeframes] = evol

                                if group_of_timeframes in global_dict_evol_tf_group:
                                    current_val = global_dict_evol_tf_group[group_of_timeframes]
                                    global_dict_evol_tf_group[group_of_timeframes] = (float(current_val) + evol)
                                else:
                                    global_dict_evol_tf_group[group_of_timeframes] = evol

                                # To have a space between each group of timeframes, uncomment the 2 lines here after
                                # print("")
                                # log_to_results("")
                            else:
                                # print("same group of timeframes detected =", current_group_of_timeframes)
                                if group_of_timeframes in dict_evol_tf_group:
                                    current_val = dict_evol_tf_group[group_of_timeframes]
                                    dict_evol_tf_group[group_of_timeframes] = (float(current_val) + evol)
                                else:
                                    dict_evol_tf_group[group_of_timeframes] = evol

                                if group_of_timeframes in global_dict_evol_tf_group:
                                    current_val = global_dict_evol_tf_group[group_of_timeframes]
                                    global_dict_evol_tf_group[group_of_timeframes] = (float(current_val) + evol)
                                else:
                                    global_dict_evol_tf_group[group_of_timeframes] = evol

                                pass

                            date_detect = text.split(' ')[3]
                            time_detect = text.split(' ')[4].split('.')[0]

                            # print(filename, "\t", symbol, fill_symbol, date_detect + " " + time_detect, "\t[" + str(price) + "]", fill_price, "\t[" + str(currentprice) + "]", fill_currentprice, "\t[" + "{:.2f}".format(evol) + " %]", fill_evol,
                            #    "\t[" + text.split('[')[0].split(split_term)[2] + "]")
                            # log_to_results(filename + "\t" + symbol + fill_symbol + date_detect + " " + time_detect + "\t[" + str(price) + "]" + fill_price + "\t[" + str(currentprice) + "]" + fill_currentprice + "\t[" + "{:.2f}".format(
                            #    evol) + " %]" + fill_evol + "\t[" + text.split('[')[0].split(split_term)[2] + "]")

                            print(symbol, fill_symbol, date_detect + " " + time_detect, "\t[" + str(price) + "]",
                                  fill_price, "\t[" + str(currentprice) + "]", fill_currentprice,
                                  "\t[" + "{:.2f}".format(evol) + " %]", fill_evol,
                                  "\t[" + text.split('[')[0].split(split_term)[2] + "]")
                            log_to_results(symbol + fill_symbol + date_detect + " " + time_detect + "\t[" + str(
                                price) + "]" + fill_price + "\t[" + str(
                                currentprice) + "]" + fill_currentprice + "\t[" + "{:.2f}".format(
                                evol) + " %]" + fill_evol + "\t[" + text.split('[')[0].split(split_term)[2] + "]")

                            nb_assets_in_file += 1

                            #SPECIAL EXPERIMENTAL GATEIO SUPER PUMP FORECAST RESULTS
                            if ("1m 4h 8h 1d" or "1m 5m 1h 4h 8h 1d" or "30m 1h 4h 8h 1d") in text.split('[')[0].split(split_term)[2]:
                                special_gateio_results.append(symbol + fill_symbol + date_detect + " " + time_detect + "\t[" + str(
                                price) + "]" + fill_price + "\t[" + str(
                                currentprice) + "]" + fill_currentprice + "\t[" + "{:.2f}".format(
                                evol) + " %]" + fill_evol + "\t[" + text.split('[')[0].split(split_term)[2] + "]")


                    line += 1
            # print(text)
        except:
            # print(sys.exc_info())
            # exit(-10003)
            pass

        print("")
        log_to_results("")

        # By default we don't print the ascending order (Set the variable here after to True if you want to print it)
        show_ascending_order = False
        total_evol = 0.0
        if len(dict_evol_tf_group) > 0:
            if show_ascending_order:
                print("")
                log_to_results("")
                print("Average evol per group of timeframes :")
                log_to_results("Average evol per group of timeframes :")
            for (key, value) in dict_evol_tf_group.items():
                if show_ascending_order:
                    fill_key = "." * (48 - len(key))
                    print("[" + key + "]", fill_key, "{:.2f}".format(value), "%")
                    log_to_results("[" + key + "]" + fill_key + "{:.2f}".format(value) + " %")
                total_evol += value

            if show_ascending_order:
                print("")
                log_to_results("")

            print("Average evol per group of timeframes (ordered) :")
            log_to_results("Average evol per group of timeframes (ordered) :")
            first_record_done = False
            for k in sorted(dict_evol_tf_group, key=lambda k: dict_evol_tf_group[k], reverse=True):
                fill_key = "." * (48 - len(k))
                # print("[" + k + "]", fill_key, "{:.2f}".format(dict_evol_tf_group[k]), "%")
                # log_to_results("[" + k + "]" + fill_key + "{:.2f}".format(dict_evol_tf_group[k]) + "%")
                print("[" + k + "]", fill_key, "{:.2f}".format(dict_evol_tf_group[k]/len(dict_assets_per_tf_group)), "%", 4 * " ", dict_assets_per_tf_group[k])
                log_to_results("[" + k + "]" + fill_key + "{:.2f}".format(dict_evol_tf_group[k]/len(dict_evol_tf_group)) + "%" + 4 * " " + dict_assets_per_tf_group[k])

                if first_record_done is False:
                    array_evol_tf_group_global.append("[" + k + "]" + fill_key + "{:.2f}".format(dict_evol_tf_group[k]/len(dict_assets_per_tf_group)) + "%" + 4 * " " + dict_assets_per_tf_group[k])
                    first_record_done = True

            print("")
            log_to_results("")

            print("number of assets in file = ", str(nb_assets_in_file))
            log_to_results("number of assets in file = " + str(nb_assets_in_file))
            print("Average total evol for this file", "{:.2f}".format(total_evol/nb_assets_in_file), "%")
            global_dict_evol_file[filename] = total_evol
            print(100 * "*")
            print("")

            log_to_results(
                "Average total evol for this file " + "{:.2f}".format(total_evol/nb_assets_in_file) + " %")
            log_to_results(100 * "*")
            log_to_results("")

        print("")
        log_to_results("")

# The first best group of timeframes from each file.
print("GLOBAL Best groups of timeframes for each processed file")
log_to_results("Best groups of timeframes for each processed file")
for line in array_evol_tf_group_global:
    print(line)
    log_to_results(line)

print("")
log_to_results("")

# All groups of timeframes from all files (ordered).
print("GLOBAL Average evol per group of timeframes (ordered) :")
log_to_results("GLOBAL Average evol per group of timeframes (ordered) :")
for k in sorted(global_dict_evol_tf_group, key=lambda k: global_dict_evol_tf_group[k], reverse=True):
    fill_key = "." * (48 - len(k))
    print("[" + k + "]", fill_key, "{:.2f}".format(global_dict_evol_tf_group[k]), "%", 4 * " ",
          global_dict_assets_per_tf_group[k])
    log_to_results("[" + k + "]" + fill_key + "{:.2f}".format(global_dict_evol_tf_group[k]) + "%" + 4 * " " +
                   global_dict_assets_per_tf_group[k])

print("")
log_to_results("")

# All evol per filename (ordered)
print("GLOBAL evol per file (ordered) :")
log_to_results("GLOBAL evol per file (ordered) :")
for k in sorted(global_dict_evol_file, key=lambda k: global_dict_evol_file[k], reverse=True):
    fill_key = "." * (64 - len(k))
    print(k, fill_key, global_dict_evol_file[k])
    log_to_results(k + fill_key + str(global_dict_evol_file[k]))

print("")
log_to_results("")

# All evol per filename (unordered)
highest_avg_per_hour = 0
highest_avg_per_min = 0
print("GLOBAL evol per file (unordered) :")
log_to_results("GLOBAL evol per file (unordered) :")
for k in global_dict_evol_file:

    filedatetime = k.split('_')[0]
    #print(filedatetime)
    date_time_obj = datetime.strptime(filedatetime, '%Y%m%d%H%M')
    # print('Date:', date_time_obj.date())
    # print('Time:', date_time_obj.time())
    # print('Date-time:', date_time_obj)
    diff = datetime.now() - date_time_obj
    diff_sec = diff.total_seconds()
    diff_min = diff_sec/60
    diff_hour = diff_min/60
    #print("diff_hour", diff_hour)

    evol = global_dict_evol_file[k]
    #print(evol)
    avg_evol_per_hour = evol/diff_hour
    avg_evol_per_min = evol/diff_min
    avg_evol_per_sec = evol/diff_sec

    str_highest_avg_per_hour = ""
    if avg_evol_per_hour > highest_avg_per_hour:
        highest_avg_per_hour = avg_evol_per_hour
        str_highest_avg_per_hour = " (*HAPH)"

    str_highest_avg_per_min = ""
    if avg_evol_per_min > highest_avg_per_min:
        highest_avg_per_min = avg_evol_per_min
        str_highest_avg_per_min = " (*HAPM)"

    fill_key = "." * (64 - len(k))
    print(k + fill_key + "{:.8f}".format(global_dict_evol_file[k]) + " (avg/hour): " + "{:.8f}".format(avg_evol_per_hour) + " (avg/min): " + "{:.8f}".format(avg_evol_per_min) + str_highest_avg_per_hour + str_highest_avg_per_min)
    log_to_results(k + fill_key + "{:.8f}".format(global_dict_evol_file[k]) + " (avg/hour): " + "{:.8f}".format(avg_evol_per_hour) + " (avg/min): " + "{:.8f}".format(avg_evol_per_min) + str_highest_avg_per_hour + str_highest_avg_per_min)

print("")
log_to_results("")

print("SPECIAL GATEIO RESULTS")
log_to_results("SPECIAL GATEIO RESULTS")
for line in special_gateio_results:
    print(line)
    log_to_results(line)
