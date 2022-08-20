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


# eg. I want to know the current prices for XRP/USDT : get_ticker("XRP/USDT")
def get_ticker(symbol_to_get):
    ticker = binance.fetch_ticker(symbol_to_get)
    # print(ticker)
    # print("get_ticker:", ticker)
    # print(ticker["symbol"])

    # print(ticker["symbol"], "sell price", ticker["bid"], "buy price", ticker["ask"], "close price", ticker["close"])
    sell_price = float(ticker["bid"])
    buy_price = float(ticker["ask"])
    # print("get_ticker: buy price", buy_price, "sell_price", sell_price)
    return buy_price, sell_price


array_bids = {}
array_asks = {}
previous_bids_max_qty = 0.0
previous_bids_btc_value = 0.0
previous_asks_max_qty = 0.0
previous_asks_btc_value = 0.0

while True:
    orderbook = binance.fetch_order_book('BTC/USDT')
    # print(orderbook['symbol'])

    for i in range(0, len(orderbook['bids'])):
        #print(orderbook['bids'][i][0], orderbook['bids'][i][1])
        btcvalue = orderbook['bids'][i][0]
        btcqty = orderbook['bids'][i][1]
        if btcvalue in array_bids:
            qty = array_bids[btcvalue]
            qty = qty + btcqty
            array_bids[btcvalue] = float(qty)
        else:
            array_bids[btcvalue] = float(btcqty)
        #print(array_bids)
        greatest_qty = 0.0
        associated_btc_val = 0.0
        for a, b in array_bids.items():
            #print(a, b)
            if b > greatest_qty:
                greatest_qty = b
                associated_btc_val = a
        if greatest_qty != previous_bids_max_qty and associated_btc_val != previous_asks_btc_value:
            print("greatest BID (SELL) qty", greatest_qty, "for btc value", associated_btc_val, get_ticker("BTC/USDT"))
            log_to_results("greatest BID (SELL) qty" + " " + str(greatest_qty) + " " + "for btc value" + " " + str(associated_btc_val) + " " + str(get_ticker("BTC/USDT")))
        previous_bids_max_qty = greatest_qty
        previous_bids_btc_value = associated_btc_val

    for i in range(0, len(orderbook['asks'])):
        #print(orderbook['asks'][i][0], orderbook['asks'][i][1])
        btcvalue = orderbook['asks'][i][0]
        btcqty = orderbook['asks'][i][1]
        if btcvalue in array_asks:
            qty = array_asks[btcvalue]
            qty = qty + btcqty
            array_asks[btcvalue] = float(qty)
        else:
            array_asks[btcvalue] = float(btcqty)
        #print(array_asks)
        greatest_qty = 0.0
        associated_btc_val = 0.0
        for a, b in array_asks.items():
            #print(a, b)
            if b > greatest_qty:
                greatest_qty = b
                associated_btc_val = a
        if greatest_qty != previous_asks_max_qty and associated_btc_val != previous_asks_btc_value:
            print("greatest ASK (BUY) qty", greatest_qty, "for btc value", associated_btc_val, get_ticker("BTC/USDT"))
            log_to_results("greatest ASK (BUY) qty" + " " + str(greatest_qty) + " " + "for btc value" + " " + str(associated_btc_val) + " " + str(get_ticker("BTC/USDT")))
        previous_asks_max_qty = greatest_qty
        previous_asks_btc_value = associated_btc_val



exit(-2)
