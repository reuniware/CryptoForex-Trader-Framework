import sys

import ccxt
import json
from pprint import pprint

from ccxt import binance, Exchange, InsufficientFunds, InvalidOrder

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
    # pprint(balance)

    usdt = 0.0

    for i in balance.items():
        # print(i)
        # print("i[0]", i[0])
        # print("i[1]", i[1])
        if i[0] == 'free':
            print(i[1])
            usdt = (i[1]['USDT'])

    return usdt


# eg. I want to know how much BTC I have in my wallet
def get_balance_of(crypto_to_get):  # eg. get_balance_of("BTC"), get_balance_of("ETH"), get_balance_of("XRP")...
    balance = exchange.fetch_balance()
    # pprint(balance)

    balance_of_crypto_to_sell = 0.0

    for i in balance.items():
        # print(i)
        # print("i[0]", i[0])
        # print("i[1]", i[1])
        if i[0] == 'free':
            print("i[1]", i[1])
            if crypto_to_get in i[1]:
                print("OK : crypto to sell has been found in the list of available cryptos from server i[1]")
                balance_of_crypto_to_sell = (i[1][crypto_to_get])
                break
            balance_of_crypto_to_sell = -1.0

    if balance_of_crypto_to_sell == -1.0:
        print("ERROR : crypto to sell has not been found in the list of available cryptos from server")
        return balance_of_crypto_to_sell

    print("balance_of_crypto_to_sell", crypto_to_get, balance_of_crypto_to_sell)
    return balance_of_crypto_to_sell


# eg. I want to sell 1 BTC
def sell(crypto_to_sell, crypto_to_get, quantity_of_crypto_to_sell):  # eg. sell("BTC", "USDT", 1.5), sell("XRP", "USDT", 25)...
    symbol_to_trade = crypto_to_sell + "/" + crypto_to_get
    type = 'market'  # or 'market'
    side = 'sell'  # or 'buy'
    amount = "{:.16f}".format(quantity_of_crypto_to_sell)   # todo : check if 16 digits after point is ok ?
    price = None  # or None
    # extra params and overrides if needed
    params = {
        'test': False,  # test if it's valid, but don't actually place it
    }

    print("sell: Before order sending")
    try:
        order = exchange.create_order(symbol_to_trade, type, side, amount, price, params)
        print("sell: SELL Order sent, here are the details:")
        print(order)
    except InvalidOrder:
        print("sell: exception", sys.exc_info())
    except:
        print("sell: exception", sys.exc_info())


# eg. I want to buy 1 BTC and pay in USDT
def buy(crypto_to_buy, crypto_for_payment, quantity_of_crypto_to_buy):  # eg. buy("BTC", "USDT", 2.5), buy("XRP", "USDT", 100)...
    symbol = crypto_to_buy + "/" + crypto_for_payment
    type = 'market'  # or 'market'
    side = 'buy'  # or 'buy'
    amount = "{:.16f}".format(quantity_of_crypto_to_buy)    # todo : check if 16 digits after point is ok ?
    price = None  # or None
    # extra params and overrides if needed
    params = {
        'test': False,  # test if it's valid, but don't actually place it
    }

    print("buy: Before order sending")
    try:
        order = exchange.create_order(symbol, type, side, amount, price, params)
        print("buy: BUY Order sent, here are the details:")
        print(order)
    except InvalidOrder:
        print("buy: exception", sys.exc_info())
    except:
        print("buy: exception", sys.exc_info())



# eg. I want to buy BTC for a specified amount of USDT
def buy_for_amount_of(crypto_to_buy, crypto_for_payment, amount_of_crypto_for_payment):  # eg. buy("BTC", "USDT", 50) : That will try to buy BTC for 50 usdt
    print("buy_for_amount_of: Getting price for ", crypto_to_buy, "/", crypto_for_payment)
    ticker = exchange.fetch_ticker(crypto_to_buy + "/" + crypto_for_payment)
    print("buy_for_amount_of: ticker", ticker)
    print("buy_for_amount_of: ", ticker["symbol"], "sell price", ticker["bid"], "buy price", ticker["ask"], "close price", ticker["close"])
    crypto_price = ticker["ask"]
    print("buy_for_amount_of: Buy price for ", crypto_to_buy, "/", crypto_for_payment, crypto_price)
    quantity_of_crypto_to_buy = amount_of_crypto_for_payment / crypto_price
    print("buy_for_amount_of: Quantity of ", crypto_to_buy, "/", crypto_for_payment,  "to buy for ", amount_of_crypto_for_payment, "usdt", "=", "{:.16f}".format(quantity_of_crypto_to_buy))

    symbol = crypto_to_buy + "/USDT"
    type = 'market'  # or 'market'
    side = 'buy'  # or 'buy'
    amount = "{:.16f}".format(quantity_of_crypto_to_buy)  # todo : check if 16 digits after point is ok ?
    price = None  # or None
    # extra params and overrides if needed
    params = {
        'test': False,  # test if it's valid, but don't actually place it
    }

    try:
        print("buy_for_amount_of: Before order sending")
        order = exchange.create_order(symbol, type, side, amount, price, params)
        print("buy_for_amount_of: BUY Order sent, here are the details:")
        print(order)
        return ""
    except InsufficientFunds:
        #print("exception", sys.exc_info())
        print("buy_for_amount_of: Fonds insuffisants.")
        return "Insufficient funds"
    except InvalidOrder:
        print("buy_for_amount_of: exception", sys.exc_info())


# eg. I want to know what is the minimum allowed for buying BTC/USDT (eg. buying is allowed for a minimum of 10 usdt)
def get_allowed_minimum_to_buy(crypto_to_buy, crypto_for_payment):
    print("Current market items")
    print("Searching if ", crypto_to_buy, "/", crypto_for_payment, " is available for trading")
    symbol_found = False
    # print(exchange.markets.items())
    for line in exchange.markets.items():
        #print("get_allowed_minimum_to_buy: line", line)  # décommenter pour voir les différents assets tradables
        if line[0] == crypto_to_buy + "/" + crypto_for_payment:
            print(crypto_to_buy + "/" + crypto_for_payment, "found (available for trading)")
            symbol_found = True
            #print("get_allowed_minimum_to_buy: line[1]", line[1]["info"]["filters"])
            for subline in line[1]["info"]["filters"]:
                if subline["filterType"] == "MIN_NOTIONAL":
                    print("minimum allowed to buy in usdt", subline["minNotional"])
                    return float(subline["minNotional"])
            break
    if symbol_found is False:
        return -1


# eg. I want to know if "BTC/USDT" is available for trading : is_tradable("BTC/USDT")
def is_tradable(symbol_to_trade):
    print("is_tradable: Current market items")
    print("is_tradable: Searching if ", symbol_to_trade, " is available for trading")
    symbol_found = False
    # print(exchange.markets.items())
    for line in exchange.markets.items():
        #print("get_allowed_minimum_to_buy: line", line)  # décommenter pour voir les différents assets tradables
        if line[0] == symbol_to_trade:
            symbol_found = True
            break
    return symbol_found


initial_usdt_balance = get_usdt_balance()
print("main: Current balance in USDT", initial_usdt_balance)

print("main: Current market items")
print("main: Searching if BTC/USDT is available for trading")
btcusdt_found = False
# print(exchange.markets.items())
print("main: tradable pairs:")
for line in exchange.markets.items():
    print(line[0], end=" ")

print("")
#sell("BTC", "USDT", get_balance_of("BTC"))

# btc_balance = get_balance_of("BTC")
# if btc_balance > 0:
#     sell("BTC/USDT", btc_balance)
# else:
#     print("KO : balance = 0, nothing to sell.")

# print("usdt balance", get_balance_of("USDT"))
# balance = get_balance_of("USDT")
# buy_for_usdt("BTC", balance)

# buy_for_usdt("BTC", get_balance_of("USDT") )
# sell("BTC", "USDT", get_balance_of("BTC"))

# print("MIN ALLOWED TO BUY IN USDT: ", get_allowed_minimum_to_buy("BTC", "USDT"))
# sell("BTC", "USDT", get_balance_of("BTC"))

#sell("BTC", "USDT", get_balance_of("BTC"))
#buy_for_amount_of("BTC", "USDT", 835)

# print(get_allowed_minimum_to_buy("ETH", "USDT"))
# buy_for_amount_of("ETH", "USDT", 5)

exit(-2)

