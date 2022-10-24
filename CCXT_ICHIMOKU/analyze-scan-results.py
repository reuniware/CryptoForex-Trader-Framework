import os
import ccxt
import signal

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)

signal.signal(signal.SIGINT, signal_handler)


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

exchange = exchanges['binance']

filetoprocess = "202210231230_scan_binance_usdt_gotk.txt"

for filename in os.listdir("ScanResults"):
    if filename == filename:
        print("processing", filename)
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
                        symbol = text.split(' ')[0]
                        price = float(text.split('[')[2].split('= ')[1].split(']')[0])
                        result = exchange.fetch_ohlcv(symbol, '1m', limit=1)
                        currentprice = float(result[0][4])
                        #evol = float("{:.2f}".format((currentprice - price)/price*100))
                        evol = (currentprice - price)/price*100

                        total_evol = total_evol + evol

                        fill_symbol = " " * (8-len(str(symbol)))
                        fill_price = " " * (8-len(str(price)))
                        fill_currentprice = " " * (8-len(str(currentprice)))
                        fill_evol = " " * (8-len(str(evol)))

                        current_group_of_timeframes = text.split('[')[0].split('spot')[2]
                        if (group_of_timeframes == ""):
                            #print("first group of timeframes detected =", current_group_of_timeframes)
                            group_of_timeframes = current_group_of_timeframes
                            total_evol_group_of_timeframes += evol
                        elif (current_group_of_timeframes != group_of_timeframes):
                            #print("new group of timeframes detected =", current_group_of_timeframes)
                            group_of_timeframes = current_group_of_timeframes
                            total_evol_group_of_timeframes += evol
                            print("Average evol for this group of timeframe =", "{:.2f}".format(total_evol_group_of_timeframes), "%")
                            total_evol_group_of_timeframes = 0
                            print("")
                        else:
                            #print("same group of timeframes detected =", current_group_of_timeframes)
                            total_evol_group_of_timeframes += evol
                            #print(total_evol_group_of_timeframes)

                        print(filename, "\t", symbol, fill_symbol, "\t[" + str(price) + "]", fill_price, "\t[" + str(currentprice) + "]", fill_currentprice, "\t[" + "{:.2f}".format(evol) + " %]", fill_evol, "\t[" + text.split('[')[0].split('spot')[2] + "]")

                    line += 1
            # print(text)
        except:
            pass
        print("Average evol for this file", "{:.2f}".format(total_evol), "%")
        print(100*"*")
        print("")
