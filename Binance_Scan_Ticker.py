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

trigger_price = 0.23
symbol = "CHZ/USDT"
print("Current market items")
print("Searching if", symbol, "is available for trading")
symbol_found = False
#print(exchange.markets.items())
for line in exchange.markets.items():
    #print("line", line) # décommenter pour voir les différents assets tradables
    if line[0] == symbol:
        print(symbol, "found (available for trading)")
        symbol_found = True
        break

if symbol_found is False:
    exit(-1)

print("Getting prices for", symbol)
exit_loop = False
while exit_loop is False:
    ticker = exchange.fetch_ticker(symbol)
    # print(ticker)
    #print("ticker", ticker)
    # print(ticker["symbol"], "sell price", ticker["bid"], "buy price", ticker["ask"], "close price", ticker["close"])
    buy = float(ticker["bid"])
    sell = float(ticker["ask"])
    #print(buy)

    if buy > trigger_price:
        beep.beep(1)




