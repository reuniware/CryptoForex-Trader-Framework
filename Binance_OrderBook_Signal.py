import os
from datetime import datetime

import ccxt


def log_to_results(str_to_log):
    fr = open("results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


if os.path.exists("results.txt"):
    os.remove("results.txt")

# retrieve data for the BTC/USDT pair on Binance
binance = ccxt.binance()

sum_highest_qty_bid = 0.0
sum_highest_qty_ask = 0.0
medium_btc_value_bid = 0.0
medium_btc_value_ask = 0.0

bAskSupSell = False
bSellSupAsk = False

while True:
    orderbook = binance.fetch_order_book('BTC/USDT')
    # print(orderbook['symbol'])

    highest_qty = 0.0
    highest_qty_level = 0.0
    for i in range(0, len(orderbook['bids'])):
        # print(orderbook['bids'][i][0], orderbook['bids'][i][1])
        btcvalue = orderbook['bids'][i][0]
        btcqty = orderbook['bids'][i][1]
        if btcqty > highest_qty:
            highest_qty = btcqty
            highest_qty_level = btcvalue

    print("highest qty", highest_qty, "for btc bid level (SELL PRICE)", btcvalue)
    sum_highest_qty_bid = sum_highest_qty_bid + highest_qty

    highest_qty = 0.0
    highest_qty_level = float("inf")
    for i in range(0, len(orderbook['asks'])):
        # print(orderbook['asks'][i][0], orderbook['asks'][i][1])
        btcvalue = orderbook['asks'][i][0]
        btcqty = orderbook['asks'][i][1]
        if btcqty > highest_qty:
            highest_qty = btcqty
            lowest_qty_level = btcvalue

    print("highest qty", highest_qty, "for btc ask level (BUY PRICE)", btcvalue)
    sum_highest_qty_ask = sum_highest_qty_ask + highest_qty

    if sum_highest_qty_bid > sum_highest_qty_ask:
        print("sum_highest_qty_bid (SELL)", sum_highest_qty_bid, "sum_highest_qty_ask (BUY)", sum_highest_qty_ask, "SELL > ASK")
        if bAskSupSell is True:
            print("Trigger point (SELL becoming greater than ASK" + " " + str(btcvalue))
            log_to_results(str(datetime.now()) + " " + "Trigger point (SELL becoming greater than ASK)" + " " + str(btcvalue))
        bSellSupAsk = True
        bAskSupSell = False
    else:
        print("sum_highest_qty_bid (SELL)", sum_highest_qty_bid, "sum_highest_qty_ask (BUY)", sum_highest_qty_ask, "ASK > SELL")
        if bSellSupAsk is True:
            print("Trigger point (ASK becoming greater than SELL" + " " + str(btcvalue))
            log_to_results(str(datetime.now()) + " " + "Trigger point (ASK becoming greater than SELL)" + " " + str(btcvalue))
        bAskSupSell = True
        bSellSupAsk = False

exit(-2)
