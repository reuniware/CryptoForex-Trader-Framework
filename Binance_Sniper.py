import sys
import threading
from datetime import datetime

import ccxt
import json
from pprint import pprint

from ccxt import binance, Exchange, InsufficientFunds, InvalidOrder

print('CCXT Version:', ccxt.__version__)

exchange = ccxt.binance({
    'apiKey': 'hC3mI1mEJZEqIOZbvnFCi58S0T9esH6z1pTk3puwnfW2N4Sgtyzfpw89lgXidwUK',
    'secret': 'FR1bV8mk0XzfPat2H6MrnoBlwukDMsyOPkCUTSLmxCcwjbTlpw2h4KoSNQ4nyXIK',
    'enableRateLimit': True,  # https://github.com/ccxt/ccxt/wiki/Manual#rate-limit
    'options': {
        'defaultType': 'spot',
        'adjustForTimeDifference': True,
    },
})


exchange.set_sandbox_mode(True)  # comment if you're not using the testnet
markets = exchange.load_markets()
exchange.verbose = False  # debug output


# eg. I want to know the quantity of each crypto (printed if > 0). This is bugged. Use get_all_balance2() instead.
def get_all_balances():
    balance = exchange.fetch_balance()
    # pprint(balance)

    total = 0.0
    for k, v in balance.items():
        print(k, v, type(v))
        if type(v) is dict:
            for kk, vv in v.items():
                if kk == "free":
                    if float(vv) > 0:
                        print("get_all_balances(1):", kk + " ", k, "{:.16f}".format(vv))
                if kk == "total":
                    if float(vv) > 0:
                        if k != "USDT":
                            try:
                                buy, sell = get_ticker(k + "/USDT")
                                #print("sell", sell, "equivalent in USDT", sell * float(vv))
                                print("get_all_balances(2):", kk, k, "{:.16f}".format(vv), "equivalent in USDT", sell * float(vv))
                                total = total + sell * float(vv)
                            except:
                                pass

    print("get_all_balances(3): total equivalent in usdt (relative to sell prices)", total)
    if is_tradable("EUR/USDT"):
        buy_eur, sell_eur = get_ticker("EUR/USDT")
        total_euro = total / sell_eur
        print("get_all_balances(3): total equivalent in eur (relative to sell price)", total_euro)
    usdt_balance = get_usdt_balance()
    total_wallet_usdt = total + usdt_balance
    print("get_all_balances(3): total wallet in usdt (relative to sell price)", total_wallet_usdt)
    if is_tradable("EUR/USDT"):
        total_wallet_euro = (total + usdt_balance) / sell_eur
        print("get_all_balances(3): total wallet in eur (relative to sell price)", total_wallet_euro)

    print("get_all_balances(4): ", end=" ")
    for i in balance.items():
        # print(i)
        # print("i[0]", i[0])
        # print("i[1]", i[1])
        if i[0] == 'free':
            print(i[1])
            # usdt = (i[1]['USDT'])


def get_all_balances2():
    balance = exchange.fetch_balance()
    # pprint(balance)
    for elem in balance['info']['balances']:
        crypto = elem['asset']
        free = elem['free']
        locked = elem['locked']
        if float(free) > 0 or float(locked) > 0:
            print(crypto, free, locked, end=" ")
    print("")
    print(balance['info']['balances'])


def get_usdt_balance():
    balance = exchange.fetch_balance()
    # pprint(balance)

    usdt = 0.0

    for i in balance.items():
        # print(i)
        # print("i[0]", i[0])
        # print("i[1]", i[1])
        if i[0] == 'free':
            #print(i[1])
            usdt = (i[1]['USDT'])

    return usdt


# eg. I want to know how much BTC I have in my wallet
def get_balance_of(crypto_to_get):  # eg. get_balance_of("BTC"), get_balance_of("ETH"), get_balance_of("XRP")...
    balance = exchange.fetch_balance()
    # pprint(balance)

    balance_of_crypto_to_get = 0.0

    for i in balance.items():
        # print(i)
        # print("i[0]", i[0])
        # print("i[1]", i[1])
        if i[0] == 'free':
            #print("i[1]", i[1])
            if crypto_to_get in i[1]:
                #print("OK : crypto to sell has been found in the list of available cryptos from server i[1]")
                balance_of_crypto_to_get = (i[1][crypto_to_get])
                break
            balance_of_crypto_to_get = -1.0

    if balance_of_crypto_to_get == -1.0:
        print("get_balance_of: ERROR : crypto to sell has not been found in the list of available cryptos from server")
        return balance_of_crypto_to_get

    print("get_balance_of:", crypto_to_get, balance_of_crypto_to_get)
    return balance_of_crypto_to_get


# eg. I want to sell 1 BTC
def sell(crypto_to_sell, crypto_to_get, quantity_of_crypto_to_sell):  # eg. sell("BTC", "USDT", 1.5), sell("XRP", "USDT", 25)...
    symbol_to_trade = crypto_to_sell + "/" + crypto_to_get
    type = 'market'  # or 'market'
    side = 'sell'  # or 'buy'
    amount_to_sell = "{:.16f}".format(quantity_of_crypto_to_sell)   # todo : check if 16 digits after point is ok ?
    price = None  # or None
    # extra params and overrides if needed
    params = {
        'test': False,  # test if it's valid, but don't actually place it
    }

    print("sell: Before order sending")
    try:
        order = exchange.create_order(symbol_to_trade, type, side, amount_to_sell, price, params)
        print("sell: SELL Order sent, here are the details:")
        print(order)
        return 0
    except InvalidOrder:
        print("sell: exception", sys.exc_info())
        return -1
    except:
        print("sell: exception", sys.exc_info())
        return -2


# eg. I want to buy 1 BTC and pay in USDT. Returns the executed quantity (effective quantity bought)
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
    executed_quantity = 0.0
    try:
        order = exchange.create_order(symbol, type, side, amount, price, params)

        print("buy: BUY Order sent, here are the details:")
        print(order)

        for item in order.items():
            #print("item", item)
            for subitem in item:
                try:
                    #print("item", item, "subitem", subitem)
                    for subitem2 in subitem:
                        if subitem2 == "executedQty":
                            #print("item", item, "subitem", subitem, "subitem2", subitem2)
                            #print(subitem["executedQty"])
                            executed_quantity = float(subitem["executedQty"])
                            #break
                except:
                    pass

        print("buy: Executed order quantity", executed_quantity)
        return executed_quantity

    except InvalidOrder:
        print("buy: exception", sys.exc_info())
        return -1
    except:
        print("buy: exception", sys.exc_info())
        return -2


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


# eg I want to convert all my ETH to USDT : sell_all_crypto_for("ETH", "USDT")
def sell_all_crypto_for(crypto_to_sell, crypto_to_get):
    while get_balance_of(crypto_to_sell) > 0:
        sell(crypto_to_sell, crypto_to_get, get_balance_of(crypto_to_sell))

#def buy_crypto_until_quantity_reached(crypto_to_buy, quantity_to_reach):
#    while get_balance_of(crypto_to_buy < quantity_to_reach):


# eg. I want to know what is the minimum allowed for buying BTC/USDT (eg. buying is allowed for a minimum of 10 usdt)
def get_allowed_min_notional(crypto_to_buy, crypto_for_payment):
    print("get_allowed_min_notional: Current market items")
    print("get_allowed_min_notional: Searching if ", crypto_to_buy, "/", crypto_for_payment, " is available for trading")
    symbol_found = False
    # print(exchange.markets.items())
    for line in exchange.markets.items():
        #print("get_allowed_minimum_to_buy: line", line)  # décommenter pour voir les différents assets tradables
        if line[0] == crypto_to_buy + "/" + crypto_for_payment:
            print(crypto_to_buy + "/" + crypto_for_payment, "found (available for trading)")
            symbol_found = True
            print("get_allowed_min_notional: line[1]", line[1]["info"]["filters"])
            for subline in line[1]["info"]["filters"]:
                if subline["filterType"] == "MIN_NOTIONAL":
                    print("get_allowed_min_notional: minimum allowed to buy in", crypto_for_payment, "=", subline["minNotional"])
                    return float(subline["minNotional"])
            break
    if symbol_found is False:
        return -1


# eg. I want to know what is the maximum quantity allowed to be sold for a crypto in a single market order
def get_allowed_market_lot_size(crypto_to_buy, crypto_for_payment):
    print("get_allowed_market_lot_size: Current market items")
    print("get_allowed_market_lot_size: Searching if ", crypto_to_buy, "/", crypto_for_payment, " is available for trading")
    symbol_found = False
    # print(exchange.markets.items())
    for line in exchange.markets.items():
        #print("get_allowed_minimum_to_buy: line", line)  # décommenter pour voir les différents assets tradables
        if line[0] == crypto_to_buy + "/" + crypto_for_payment:
            print(crypto_to_buy + "/" + crypto_for_payment, "found (available for trading)")
            symbol_found = True
            print("get_allowed_market_lot_size: line[1]", line[1]["info"]["filters"])
            for subline in line[1]["info"]["filters"]:
                if subline["filterType"] == "MARKET_LOT_SIZE":
                    print("get_allowed_market_lot_size: maximum allowed to sell in", crypto_for_payment, "=", subline["maxQty"])
                    return float(subline["maxQty"])
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


def get_tradable_pairs():
    array_pairs = []
    print("get_tradable_pairs: tradable pairs:")
    for line in exchange.markets.items():
        print(line[0], end=" ")
        array_pairs.append(line[0])
    print("")
    return array_pairs


# eg. I want to know the current prices for XRP/USDT : get_ticker("XRP/USDT")
def get_ticker(symbol_to_get):
    ticker = exchange.fetch_ticker(symbol_to_get)
    # print(ticker)
    # print("get_ticker:", ticker)
    # print(ticker["symbol"])

    # print(ticker["symbol"], "sell price", ticker["bid"], "buy price", ticker["ask"], "close price", ticker["close"])
    sell_price = float(ticker["bid"])
    buy_price = float(ticker["ask"])
    # print("get_ticker: buy price", buy_price, "sell_price", sell_price)
    return buy_price, sell_price


# eg. I want to sell any "/USDT" pair to get USDT (I want to empty every "/USDT" pair)
def sell_all_usdt_pairs():
    array_tradable_pairs = get_tradable_pairs()
    for pair_item in array_tradable_pairs:
        pair = str(pair_item)
        if pair.endswith("/USDT"):
            crypto = pair.replace("/USDT", "")
            balance = get_balance_of(crypto)
            print("sell_all_usdt_pairs:", crypto, get_balance_of(crypto))
            if balance > 0:
                allowed_maximum_to_sell = get_allowed_market_lot_size(crypto, "USDT")
                print("sell_all_usdt_pairs: Allowed maximum to sell=", allowed_maximum_to_sell)
                while get_balance_of(crypto) > allowed_maximum_to_sell:
                    sell(crypto, "USDT", allowed_maximum_to_sell)
                while get_balance_of(crypto) > 0:
                    result = sell(crypto, "USDT", get_balance_of(crypto))
                    if result != 0:
                        break


def buy_all_usdt_pairs(amount_in_usdt_for_each):
    array_tradable_pairs = get_tradable_pairs()
    for pair_item in array_tradable_pairs:
        pair = str(pair_item)
        if pair.endswith("/USDT"):
            crypto = pair.replace("/USDT", "")
            balance = get_balance_of(crypto)
            print("buy_all_usdt_pairs:", crypto, balance)
            buy_for_amount_of(crypto, "USDT", amount_in_usdt_for_each)

            # max_lot_size = get_allowed_market_lot_size(crypto, "USDT")
            # while get_balance_of(crypto) > max_lot_size:
            #     buy_for_amount_of(crypto, "USDT", max_lot_size)
            # balance = get_balance_of(crypto)
            # if balance > 0:
            #     buy_for_amount_of(crypto, "USDT", get_balance_of(crypto))


# eg. I want to cancel all orders for XRP/USDT : cancel_all_orders("XRP/USDT") ; Status of the order must be "NEW"
def cancel_all_orders(symbol_to_cancel):
    orders = exchange.fetch_orders(symbol_to_cancel)
    for elem in orders:
        # print(elem)
        status = elem['info']['status']
        if status == "NEW":
            price_to_sell = elem['info']['price']
            print("cancel_all_orders", elem['info']['orderId'], elem['info']['status'], "price to sell", price_to_sell)  # ['status'])
            cancel = exchange.cancel_all_orders(symbol_to_cancel)


initial_usdt_balance = get_usdt_balance()
print("main: Current balance in USDT", initial_usdt_balance)


#Cancel an order (eg. a limit sell order that has been sent previously)
#canceled = exchange.cancel_order("939421", "XRP/USDT")

# cancel_all_orders("XRP/USDT")
#sell_all_crypto_for("XRP", "USDT")
#sell_all_usdt_pairs()
#get_all_balances2()
#exit(-5)
# while True:
#     orders = exchange.fetch_orders("XRP/USDT")
#     for elem in orders:
#         print(elem)
#         status = elem['info']['status']
#         if status == "NEW":
#             price_to_sell = elem['info']['price']
#             print(elem['info']['orderId'], elem['info']['status'], "price to sell", price_to_sell)#['status'])

#sell_all_usdt_pairs()
#exit(-1)



# SENDING A MARKET ORDER
crypto_to_buy = "XRP"
crypto_for_payment = "USDT"
amount_of_crypto_for_payment = 1000

print("buy_for_amount_of: Getting price for ", crypto_to_buy, "/", crypto_for_payment)
ticker = exchange.fetch_ticker(crypto_to_buy + "/" + crypto_for_payment)
print("buy_for_amount_of: ticker", ticker)
print("buy_for_amount_of: ", ticker["symbol"], "sell price", ticker["bid"], "buy price", ticker["ask"], "close price",
      ticker["close"])
crypto_price = ticker["ask"]
print("buy_for_amount_of: Buy price for ", crypto_to_buy, "/", crypto_for_payment, crypto_price)
quantity_of_crypto_to_buy = amount_of_crypto_for_payment / crypto_price
print("buy_for_amount_of: Quantity of ", crypto_to_buy, "/", crypto_for_payment, "to buy for ",
      amount_of_crypto_for_payment, "usdt", "=", "{:.16f}".format(quantity_of_crypto_to_buy))
symbol = crypto_to_buy + "/USDT"
type = 'market'  # or 'market'
side = 'buy'  # or 'buy'
amount = "{:.16f}".format(quantity_of_crypto_to_buy)  # todo : check if 16 digits after point is ok ?
price = None  # or None
# extra params and overrides if needed
params = {
    'test': False,  # test if it's valid, but don't actually place it
}

max_order_price = 0.0
total_quantity_executed = 0.0
order_id_buy_order = ""
order_id_sell_limit_order = ""
try:
    print("buy_for_amount_of: Before order sending")
    order = exchange.create_order(symbol, type, side, amount, price, params)
    print("buy_for_amount_of: BUY Order sent, here are the details:")
    print(order)
    order_id_buy_order = order['info']['orderId']
    # Here if the order has been fulfilled in more than one trade then we identify the maximum price that has been
    # executed in order to later create an order limit with a price greater that the maximum price identified.
    for elem in order['trades']:
        print("one trade has been ok for price", elem['price'])
        if elem['price'] > max_order_price:
            max_order_price = elem['price']
        total_quantity_executed = total_quantity_executed + elem['amount']
    print("total quantity executed", total_quantity_executed)
    print("max order price executed", max_order_price)

except InsufficientFunds:
    # print("exception", sys.exc_info())
    print("buy_for_amount_of: Fonds insuffisants.")
    exit(-100)
except InvalidOrder:
    print("buy_for_amount_of: exception", sys.exc_info())
    exit(-101)

sellprice = max_order_price + max_order_price/100*0.25
print("will send a sell limit order with price", sellprice)

# SENDING A SELL LIMIT ORDER
symbol = crypto_to_buy + "/USDT"
type = 'limit'  # or 'market'
side = 'sell'  # or 'buy'
amount = total_quantity_executed
price = sellprice
# extra params and overrides if needed
params = {
    'test': False,  # test if it's valid, but don't actually place it
}
try:
    order = exchange.create_order(symbol, type, side, amount, price, params)
    print(order)
    order_id_sell_limit_order = order['info']['orderId']
    for elem in order['trades']:
        print("one trade has been ok for price", elem['price'])
        if elem['price'] > max_order_price:
            max_order_price = elem['price']
        total_quantity_executed = total_quantity_executed + elem['amount']

except InsufficientFunds:
    # print("exception", sys.exc_info())
    print("buy_for_amount_of: Fonds insuffisants.")
    exit(-100)
except InvalidOrder:
    print("buy_for_amount_of: exception", sys.exc_info())
    exit(-101)


stop_scanning_status = False

monitored_symbol_sell_price = 0.0


def main_thread(symbol_to_monitor):
    global monitored_symbol_sell_price
    print("symbol to monitor", "XRP/USDT")
    while stop_scanning_status is False:
        buy, sell = get_ticker("XRP/USDT")
        monitored_symbol_sell_price = sell


x = threading.Thread(target=main_thread, args=(1,))
x.start()


while stop_scanning_status is False:
    #orders = exchange.fetch_orders(symbol)
    order = exchange.fetch_order(order_id_sell_limit_order, "XRP/USDT")
    status = order['info']['status']
    if status == "NEW":
        price_to_sell = order['info']['price']
        #print('\r', end="")
        print("\r", datetime.now(), order['info']['orderId'], order['info']['status'], "price to sell", price_to_sell, "bought at", max_order_price, "current sell price", monitored_symbol_sell_price, " " * 128, end="")
    else:
        price_to_sell = order['info']['price']
        print(datetime.now(), order['info']['orderId'], order['info']['status'], "price to sell", price_to_sell, "bought at", max_order_price, "current sell price", monitored_symbol_sell_price)
        #stop_scanning_status = True
        if status == "FILLED":
            price_to_sell = order['info']['price']
            print(datetime.now(), order['info']['orderId'], order['info']['status'], "price to sell", price_to_sell, "bought at", max_order_price, "current sell price", monitored_symbol_sell_price)
            stop_scanning_status = True

get_all_balances2()


exit(-2)



