import ccxt
import beepy as beep

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

array_watch = {"VET/USDT": 0.02749, "BTC/USDT": 23000}

while True:
    tickers = exchange.fetch_tickers()
    for item in tickers.items():
        symbol = item[0]

        for symbol_to_watch, value_to_watch in array_watch.items():
            if symbol_to_watch == symbol:
                bid = tickers[symbol]['bid'] # prix de vente (sell)
                ask = tickers[symbol]['ask'] # prix d'achat (buy)
                if ask >= value_to_watch:
                    print(symbol_to_watch, "is greater or equals to", value_to_watch)
                    beep.beep(1)

exit(-3)

