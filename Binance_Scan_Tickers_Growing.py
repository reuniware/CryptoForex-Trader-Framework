from datetime import datetime

import ccxt
import time

print('CCXT Version:', ccxt.__version__)

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

percent = 0.5

#array_watch = {"VET/USDT": 0.02749, "BTC/USDT": 23000, "BAT/USDT": 0.4139}
#array_watch = {"VET/USDT": 0.02749, "BTC/USDT": 23000, "BAT/USDT": 0.4139}
array_watch = {}
array_count = {}
array_t0 = {}
array_datetime = {}
time.sleep(0.1)
tickers = exchange.fetch_tickers()
for item in tickers.items():
    symbol = item[0]
    #if str(symbol).endswith("/USDT"):
    bid = tickers[symbol]['bid']  # prix de vente (sell)
    ask = tickers[symbol]['ask']  # prix d'achat (buy)
    if ask > 0:
        array_watch[symbol] = ask + ask/100*percent
        array_t0[symbol] = ask
        array_datetime[symbol] = datetime.now()
        print("adding", symbol, "with target buy price", array_watch[symbol], "current price being", ask)
        array_count[symbol] = 0

while True:
    tickers = exchange.fetch_tickers()
    for item in tickers.items():
        symbol = item[0]

        for symbol_to_watch, value_to_watch in array_watch.items():
            if symbol_to_watch == symbol:
                bid = tickers[symbol]['bid'] # prix de vente (sell)
                ask = tickers[symbol]['ask'] # prix d'achat (buy)
                if ask >= value_to_watch:
                    array_count[symbol] = array_count[symbol] + 1
                    array_watch[symbol_to_watch] = ask + ask/100*percent

                    timedelta = datetime.now() - array_datetime[symbol]
                    # evol_pourcent = ask / array_t0[symbol]
                    evol_pourcent = ((ask - array_t0[symbol]) / array_t0[symbol]) * 100
                    percent_per_second = evol_pourcent / timedelta.total_seconds()
                    str_lien = "https://tradingview.com/chart/?symbol=BINANCE%3A" + symbol.replace('/', '')
                    print(array_count[symbol_to_watch], symbol_to_watch, "is greater or equals to", value_to_watch, "increasing value to watch for", symbol, "to", array_watch[symbol_to_watch], str_lien, "evol/t0", "{:.2f}".format(evol_pourcent) + "%", "diff(t-t0)", timedelta, "%/sec", "{:.2f}".format(percent_per_second, 4))
                    #beep.beep(1)

exit(-3)

