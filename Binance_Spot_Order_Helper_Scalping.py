import ccxt
import json
from pprint import pprint

from ccxt import binance, Exchange

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

exchange.set_sandbox_mode(True)  # comment if you're not using the testnet
markets = exchange.load_markets()
exchange.verbose = False  # debug output


def get_usdt_balance():
    balance = exchange.fetch_balance()
    #pprint(balance)

    usdt = 0.0

    for i in balance.items():
        # print(i)
        # print("i[0]", i[0])
        # print("i[1]", i[1])
        if i[0] == 'free':
            print(i[1])
            usdt = (i[1]['USDT'])

    return usdt


initial_usdt_balance = get_usdt_balance()
print("Current balance in USDT", initial_usdt_balance)

print("Current market items")
print("Searching if BTC/USDT is available for trading")
btcusdt_found = False
#print(exchange.markets.items())
for line in exchange.markets.items():
    #print("line", line) # décommenter pour voir les différents assets tradables
    if line[0] == "BTC/USDT":
        print("BTC/USDT found (available for trading)")
        btcusdt_found = True
        break

if btcusdt_found is False:
    exit(-1)

#exit(-2)

btcusdt_price = 0.0
quantity_to_buy = 0
usdt_to_invest = 5000
print("Getting price for BTC/USDT")
ticker = exchange.fetch_ticker("BTC/USDT")
print(ticker)
print("ticker", ticker)
print(ticker["symbol"], "sell price", ticker["bid"], "buy price", ticker["ask"], "close price", ticker["close"])
btcusdt_price = ticker["ask"]
print("Buy price for BTC/USDT", btcusdt_price)
quantity_to_buy = usdt_to_invest / btcusdt_price
print("Quantity of BTC/USDT to buy for ", usdt_to_invest, "usdt", "=", quantity_to_buy)
print("End getting price for BTC/USDT")

# exit(-3)
# markets = binance.load_markets()
# print(markets)

symbol = 'BTC/USDT'
type = 'market'  # or 'market'
side = 'buy'  # or 'buy'
amount = quantity_to_buy
price = None  # or None
# extra params and overrides if needed
params = {
    'test': False,  # test if it's valid, but don't actually place it
}

print("Order sending")
order = exchange.create_order(symbol, type, side, amount, price, params)
print("Order sent")
print("Order details")
print(order)

#exit(-4)

print("Details of the executed order received from server:")
origQty = order["info"]["origQty"]
executedQty = order["info"]["executedQty"]
print("origQty", origQty, "executedQty", executedQty)
status = order["info"]["status"]
print("status received from the server", status)

fees_paid = 0.0
fees_currency = ""
trades = order["trades"]
for line in trades:
    print("line", line["fees"])
    for subline in line["fees"]:
        fees_paid = subline["cost"]
        fees_currency = subline["currency"]
        print("fees paid", fees_paid, "fees currency", fees_currency)
        break

fills = order["info"]["fills"]
effective_quantity_bought = 0.0
for line in fills:
    effective_price_bought = line["price"]
    effective_quantity_bought = effective_quantity_bought + float(line["qty"])
    print("effective price bought", line["price"])
    print("effective quantity bought", line["qty"])
    print("effective commission", line["commission"])
    print("effective commission asset", line["commissionAsset"])
    print("effective trader id", line["tradeId"])

if origQty == executedQty:
    print("Quantity asked has been ok for the server")
elif origQty > executedQty:
    print("Quantity asked is greater than the one the server is telling us")
elif origQty < executedQty:
    print("Quantity asked is lower than the one the server is telling us")

quantity_to_sell = effective_quantity_bought
exitLoop = False
while exitLoop is False:
    print("Getting price for BTC/USDT")
    ticker = exchange.fetch_ticker("BTC/USDT")
    # print(ticker)
    print("ticker", ticker)
    # print(ticker["symbol"], "sell price", ticker["bid"], "buy price", ticker["ask"], "close price", ticker["close"])
    btcusdt_price = float(ticker["bid"])

    nouvelle_balance_virtuelle = quantity_to_sell * btcusdt_price
    print("nouvelle balance virtuelle", "{:.6f}".format(nouvelle_balance_virtuelle))

    #if btcusdt_price > float(effective_price_bought):
    if nouvelle_balance_virtuelle - usdt_to_invest >= 1.5:
        symbol = 'BTC/USDT'
        type = 'market'  # or 'market'
        side = 'sell'  # or 'buy'
        amount = quantity_to_sell
        price = None  # or None
        # extra params and overrides if needed
        params = {
            'test': False,  # test if it's valid, but don't actually place it
        }

        print("Order sending")
        order = exchange.create_order(symbol, type, side, amount, price, params)
        print("Order sent")
        print("Order details")
        print(order)

        print("bénéfice = ", get_usdt_balance() - initial_usdt_balance)

        exitLoop = True
