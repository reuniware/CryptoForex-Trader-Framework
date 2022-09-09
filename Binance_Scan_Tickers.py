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

array_watch = {"ETH/USDT": 1746, "BTC/USDT": 21437, "ATOM/USDT": 16.820}
array_watch_down = {"ETH/USDT": 1696, "BTC/USDT": 21129}

# eg. I want to know when VET/USDT gets above 0.02749 and I want to know when BTC/USDT gets above 23000
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

        for symbol_to_watch, value_to_watch in array_watch_down.items():
            if symbol_to_watch == symbol:
                bid = tickers[symbol]['bid'] # prix de vente (sell)
                ask = tickers[symbol]['ask'] # prix d'achat (buy)
                if bid <= value_to_watch:
                    print(symbol_to_watch, "is lower or equals to", value_to_watch)
                    beep.beep(1)

exit(-3)
