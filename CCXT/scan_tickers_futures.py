import ccxt
import beepy as beep
import time
import atexit


def exitfunc():
    beep.beep(1)


atexit.register(exitfunc)

print('CCXT Version:', ccxt.__version__)

exchange = ccxt.bybit({
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

array_watch = {"BTC/USDT": 16682}
# array_watch = {"ETH/USDT": 1778.61, "BTC/USDT": 21796.18, "LINK/USDT": 8.1015, "ATOM/USDT": 17.198}
array_watch_down = {}

# eg. I want to know when VET/USDT gets above 0.02749 and I want to know when BTC/USDT gets above 23000
while True:
    time.sleep(1)

    exchange.options['defaultType'] = 'swap'  # very important set spot as default type
    tickers = exchange.fetch_tickers()

    #markets = exchange.fetch_markets()
    # for oneline in markets:
    #     print(oneline['type'])

    for item in tickers.items():
        symbol = item[0]
        # print(symbol)
        if symbol == "BTC/USDT":
            print(symbol, tickers[symbol]['bid'], tickers[symbol]['ask'])

        for symbol_to_watch, value_to_watch in array_watch.items():
            if symbol_to_watch == symbol:
                bid = tickers[symbol]['bid']  # prix de vente (sell)
                ask = tickers[symbol]['ask']  # prix d'achat (buy)
                if ask <= value_to_watch:
                    print(symbol_to_watch, "is greater or equals to", value_to_watch)
                    beep.beep(1)

        for symbol_to_watch, value_to_watch in array_watch_down.items():
            if symbol_to_watch == symbol:
                bid = tickers[symbol]['bid']  # prix de vente (sell)
                ask = tickers[symbol]['ask']  # prix d'achat (buy)
                if bid <= value_to_watch:
                    print(symbol_to_watch, "is lower or equals to", value_to_watch)
                    beep.beep(1)
