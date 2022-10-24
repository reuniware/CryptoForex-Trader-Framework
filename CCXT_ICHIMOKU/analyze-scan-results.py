import os
import ccxt
import signal
import sys

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)

signal.signal(signal.SIGINT, signal_handler)


def log_to_results(str_to_log):
    fr = open("analyze_scan_results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()

def delete_results_log():
    if os.path.exists("analyze_scan_results.txt"):
        os.remove("analyze_scan_results.txt")

delete_results_log()

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

filetoprocess = "202210231230_scan_binance_usdt_gotk.txt"

for filename in os.listdir("ScanResults"):
    if filename == filename:
        print("processing", filename)
        log_to_results("processing " + filename)
        line = 1

        total_evol = 0.0
        group_of_timeframes = ""
        total_evol_group_of_timeframes = 0.0

        try:
            with open(os.path.join("ScanResults", filename), 'r') as f:
                # text = f.read()
                while True:
                    text = f.readline()
                    if not text:
                        break
                    if line > 1:
                        #print(text)

                        exchange_id = text.split(' ')[2]
                        exchange = exchanges[exchange_id]

                        symbol = text.split(' ')[0]
                        price = float(text.split('[')[2].split('= ')[1].split(']')[0])
                        result = exchange.fetch_ohlcv(symbol, '1m', limit=1)
                        currentprice = float(result[0][4])
                        #evol = float("{:.2f}".format((currentprice - price)/price*100))
                        if price > 0:
                            evol = (currentprice - price)/price*100
                        else:
                            evol = 0

                        total_evol = total_evol + evol

                        fill_symbol = " " * (16-len(str(symbol)))
                        fill_price = " " * (16-len(str(price)))
                        fill_currentprice = " " * (16-len(str(currentprice)))
                        fill_evol = " " * (16-len(str(evol)))

                        current_group_of_timeframes = text.split('[')[0].split('spot')[2]
                        if (group_of_timeframes == ""):
                            #print("first group of timeframes detected =", current_group_of_timeframes)
                            group_of_timeframes = current_group_of_timeframes
                            total_evol_group_of_timeframes += evol
                        elif (current_group_of_timeframes != group_of_timeframes):
                            #print("new group of timeframes detected =", current_group_of_timeframes)
                            group_of_timeframes = current_group_of_timeframes
                            total_evol_group_of_timeframes += evol
                            print("Total evol for this group of timeframe =", "{:.2f}".format(total_evol_group_of_timeframes), "%")
                            log_to_results("Total evol for this group of timeframe = " + "{:.2f}".format(total_evol_group_of_timeframes) + " %")
                            total_evol_group_of_timeframes = 0
                            print("")
                            log_to_results("")
                        else:
                            #print("same group of timeframes detected =", current_group_of_timeframes)
                            total_evol_group_of_timeframes += evol
                            #print(total_evol_group_of_timeframes)

                        date_detect = text.split(' ')[3]
                        time_detect = text.split(' ')[4].split('.')[0]

                        print(filename, "\t", symbol, fill_symbol, date_detect + " " + time_detect, "\t[" + str(price) + "]", fill_price, "\t[" + str(currentprice) + "]", fill_currentprice, "\t[" + "{:.2f}".format(evol) + " %]", fill_evol, "\t[" + text.split('[')[0].split('spot')[2] + "]")
                        log_to_results(filename + "\t" + symbol + fill_symbol + date_detect + " " + time_detect + "\t[" + str(price) + "]" + fill_price + "\t[" + str(currentprice) + "]" + fill_currentprice + "\t[" + "{:.2f}".format(evol) + " %]" + fill_evol + "\t[" + text.split('[')[0].split('spot')[2] + "]")
                    line += 1
            # print(text)
        except:
            print(sys.exc_info())
            #exit(-10003)
            pass
        print("Total evol for this file", "{:.2f}".format(total_evol), "%")
        print(100*"*")
        print("")

        log_to_results("Total evol for this file " + "{:.2f}".format(total_evol) + " %")
        log_to_results(100*"*")
        log_to_results("")
