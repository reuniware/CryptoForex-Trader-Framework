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

#array_watch = {"VET/USDT": 0.02749, "BTC/USDT": 23000, "BAT/USDT": 0.4139}
array_watch = {"VET/USDT": 0.02749, "BTC/USDT": 23000, "BAT/USDT": 0.4139}
tickers = exchange.fetch_tickers()
for item in tickers.items():
    symbol = item[0]
    if str(symbol).endswith("/USDT"):
        bid = tickers[symbol]['bid']  # prix de vente (sell)
        ask = tickers[symbol]['ask']  # prix d'achat (buy)
        if ask > 0:
            array_watch[symbol] = ask + ask/100*0.1
            print("adding", symbol, "with target buy price", array_watch[symbol], "current price being", ask)

while True:
    tickers = exchange.fetch_tickers()
    for item in tickers.items():
        symbol = item[0]

        for symbol_to_watch, value_to_watch in array_watch.items():
            if symbol_to_watch == symbol:
                bid = tickers[symbol]['bid'] # prix de vente (sell)
                ask = tickers[symbol]['ask'] # prix d'achat (buy)
                if ask >= value_to_watch:
                    array_watch[symbol_to_watch] = ask + ask/100*0.1
                    print(symbol_to_watch, "is greater or equals to", value_to_watch, "increasing value to watch for", symbol, "to", array_watch[symbol_to_watch])
                    beep.beep(1)

exit(-3)

