from datetime import datetime

import ccxt
import time
import os

print('CCXT Version:', ccxt.__version__)

def log_to_results(str_to_log):
    fr = open("scan_growing_results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()

if os.path.exists("scan_growing_results.txt"):
    os.remove("scan_growing_results.txt")

def log_to_evol(str_to_log):
    fr = open("scan_growing_results_evol.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()

if os.path.exists("scan_growing_results_evol.txt"):
    os.remove("scan_growing_results_evol.txt")

exchange = ccxt.binance({
    'apiKey': '',
    'secret': '',
    'enableRateLimit': True,  # https://github.com/ccxt/ccxt/wiki/Manual#rate-limit
    'options': {
        'defaultType': 'spot',
        'adjustForTimeDifference': True,
    },
})

exchange.set_sandbox_mode(False)  # comment if you're not using the testnet
markets = exchange.load_markets()
exchange.verbose = False  # debug output

percent = 2.5 # 4 seems the best

#array_watch = {"VET/USDT": 0.02749, "BTC/USDT": 23000, "BAT/USDT": 0.4139}
#array_watch = {"VET/USDT": 0.02749, "BTC/USDT": 23000, "BAT/USDT": 0.4139}
array_watch = {}
array_count = {}
array_t0 = {}
array_datetime = {}
array_evol = {}
array_evol_ask = {}

#time.sleep(0.1)
tickers = exchange.fetch_tickers()
for item in tickers.items():
    symbol = item[0]
    if not str(symbol).endswith("/USDT") or str(symbol).endswith("DOWN/USDT") or str(symbol).endswith("UP/USDT"):
        continue
    bid = tickers[symbol]['bid']  # prix de vente (sell)
    ask = tickers[symbol]['ask']  # prix d'achat (buy)
    if ask > 0:
        array_watch[symbol] = ask# + ask/100*percent
        array_t0[symbol] = ask
        array_datetime[symbol] = datetime.now()
        print("adding", symbol, "with target buy price", array_watch[symbol], "current price being", ask)
        array_count[symbol] = 0

while True:
    time.sleep(0.0125)
    array_evol.clear()
    tickers = exchange.fetch_tickers()
    for item in tickers.items():
        symbol = item[0]

        for symbol_to_watch, value_to_watch in array_watch.items():
            if symbol_to_watch == symbol:
                bid = tickers[symbol]['bid'] # prix de vente (sell)
                ask = tickers[symbol]['ask'] # prix d'achat (buy)
                if ask > value_to_watch:
                    array_count[symbol] = array_count[symbol] + 1
                    array_watch[symbol_to_watch] = ask# + ask/100*percent

                    timedelta = datetime.now() - array_datetime[symbol]
                    # evol_pourcent = ask / array_t0[symbol]
                    evol_pourcent = ((ask - array_t0[symbol]) / array_t0[symbol]) * 100
                    array_evol[symbol] = evol_pourcent
                    percent_per_second = evol_pourcent / timedelta.total_seconds()
                    str_lien = "https://tradingview.com/chart/?symbol=BINANCE%3A" + symbol.replace('/', '')
                    print(array_count[symbol_to_watch], symbol_to_watch, ">=", value_to_watch, "increasing value to watch for", symbol, "to", array_watch[symbol_to_watch], str_lien, "evol/t0", "{:.2f}".format(evol_pourcent) + "%", "diff(t-t0)", timedelta, "%/sec", "{:.4f}".format(percent_per_second))
                    log_to_results(str(array_count[symbol_to_watch]) + " " + symbol_to_watch + " "+ ">=" + " " + str(value_to_watch) + " " + "increasing value to watch for" + " " + symbol + " " + "to" + " " + str(array_watch[symbol_to_watch]) + " " + str_lien + " " + "evol/t0" + " " + "{:.2f}".format(evol_pourcent) + "%" + " " + "diff(t-t0)" + " " + str(timedelta) + "%/sec" + " " + "{:.4f}".format(percent_per_second))
                    #beep.beep(1)
                    array_evol_ask[symbol] = ask

    if len(array_evol)>0:
        array_evol_sorted = sorted(array_evol.items(), key=lambda x: x[1], reverse=True)
        str_lien = "https://tradingview.com/chart/?symbol=BINANCE%3A" + (array_evol_sorted[0][0]).replace('/', '')
        print(str(array_evol_sorted[0]) + " " + str_lien)
        #"{:.2f}".format(evol_pourcent)
        evol_ask = array_evol_ask[str(array_evol_sorted[0][0])]
        print(str(datetime.now()) + " " + str(array_evol_sorted[0][0]) + " " + str(evol_ask) + " " + "{:.2f}".format(array_evol_sorted[0][1]) + "% " + str_lien)
        log_to_evol(str(datetime.now()) + " " + str(array_evol_sorted[0][0]) + " " + str(evol_ask) + " " + "{:.2f}".format(array_evol_sorted[0][1]) + "% " + str_lien)

exit(-3)

