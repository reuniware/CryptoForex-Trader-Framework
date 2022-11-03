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

currentDateAndTime = datetime.now()
stryear = format(currentDateAndTime.year, '04')
strmonth = format(currentDateAndTime.month, '02')
strday = format(currentDateAndTime.day, '02')
strhour = format(currentDateAndTime.hour, '02')
strmin = format(currentDateAndTime.minute, '02')

logfilename = stryear + strmonth + strday + strhour + strmin + "_results.txt"


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

exchange_id = "gateio"
exchange = exchanges[exchange_id]

dict_close0 = {}
dict_close = {}
dict_evol0 = {}

while True:
    tickers = exchange.fetch_tickers()
    for symbol, ticker in tickers.items():
        if not symbol.endswith("/USDT") or symbol.endswith("3L/USDT") or symbol.endswith("3S/USDT") or symbol.endswith("5L/USDT") or symbol.endswith("5S/USDT"):
            continue
        
        current_close = float(ticker['close'])

        if symbol not in dict_close0:
            dict_close0[symbol] = current_close
            dict_close[symbol] = current_close
            dict_evol0[symbol] = 0
        else:
            previous_close = dict_close[symbol]
            if previous_close>0:
                evol = (current_close - previous_close)/previous_close*100
                #if evol>0:
                #    print(symbol, evol)
                if dict_close0[symbol]>0:
                    evol0 = (current_close - dict_close0[symbol])/dict_close0[symbol]*100
                    if evol0 > dict_evol0[symbol]:
                        print(symbol, evol0, "%(t0)")
                        log_to_results(str(datetime.now()) + " " + symbol + " " + str(evol0) + " %(t0)")
                        dict_evol0[symbol] = evol0


            dict_close[symbol] = current_close

            
