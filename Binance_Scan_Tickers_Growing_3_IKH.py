# DDoSProtection: binanceus 429 Too Many Requests {"code":-1003,"msg":"Too much request weight used; current limit is 1200 request weight per 1 MINUTE. Please use WebSocket Streams for live updates to avoid polling the API."}

#!pip install ccxt
#!pip install ta

from datetime import datetime

import ccxt
import time
import os
import pandas as pd
import ta

print('CCXT Version:', ccxt.__version__)

def log_to_results(str_to_log):
    fr = open("scan_growing_results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()

if os.path.exists("scan_growing_results.txt"):
    os.remove("scan_growing_results.txt")

def log_to_evol(str_to_log):
    fr = open("scan_growing_results_evol.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()

if os.path.exists("scan_growing_results_evol.txt"):
    os.remove("scan_growing_results_evol.txt")

exchange = ccxt.binanceus({
    'apiKey': '',
    'secret': '',
    'enableRateLimit': True,  # https://github.com/ccxt/ccxt/wiki/Manual#rate-limit
    'options': {
        'defaultType': 'spot',
        'adjustForTimeDifference': True,
    },
})

def get_data_for_timeframe(symbol, tf):
    if tf not in exchange.timeframes:
        print(symbol, tf, "is not in exchange's timeframes.")
        return False
    result = exchange.fetch_ohlcv(symbol, tf, limit=52 + 26 + 52 + 26)
    return result

price_close = 0

def check_timeframe_up(symbol, tf):
    global price_close
    result = get_data_for_timeframe(symbol, tf)
    if not result:
        return
    # print(tf, symbol, result)
    dframe = pd.DataFrame(result)
    dframe['timestamp'] = pd.to_numeric(dframe[0])
    dframe['open'] = pd.to_numeric(dframe[1])
    dframe['high'] = pd.to_numeric(dframe[2])
    dframe['low'] = pd.to_numeric(dframe[3])
    dframe['close'] = pd.to_numeric(dframe[4])
    dframe['ICH_SSB'] = ta.trend.ichimoku_b(dframe['high'], dframe['low'], window2=26, window3=52).shift(26)
    dframe['ICH_SSA'] = ta.trend.ichimoku_a(dframe['high'], dframe['low'], window1=9, window2=26).shift(26)
    dframe['ICH_KS'] = ta.trend.ichimoku_base_line(dframe['high'], dframe['low'])
    dframe['ICH_TS'] = ta.trend.ichimoku_conversion_line(dframe['high'], dframe['low'])
    dframe['ICH_CS'] = dframe['close'].shift(-26)
    ssb = dframe['ICH_SSB'].iloc[-1]
    ssa = dframe['ICH_SSA'].iloc[-1]
    kijun = dframe['ICH_KS'].iloc[-1]
    tenkan = dframe['ICH_TS'].iloc[-1]
    chikou = dframe['ICH_CS'].iloc[-27]
    price_open = dframe['open'].iloc[-1]
    price_high = dframe['high'].iloc[-1]
    price_low = dframe['low'].iloc[-1]
    price_close = dframe['close'].iloc[-1]
    price_open_chikou = dframe['open'].iloc[-27]
    price_high_chikou = dframe['high'].iloc[-27]
    price_low_chikou = dframe['low'].iloc[-27]
    price_close_chikou = dframe['close'].iloc[-27]
    tenkan_chikou = dframe['ICH_TS'].iloc[-27]
    kijun_chikou = dframe['ICH_KS'].iloc[-27]
    ssa_chikou = dframe['ICH_SSA'].iloc[-27]
    ssb_chikou = dframe['ICH_SSB'].iloc[-27]

    ssb1 = dframe['ICH_SSB'].iloc[-2]
    ssa1 = dframe['ICH_SSA'].iloc[-2]
    kijun1 = dframe['ICH_KS'].iloc[-2]
    tenkan1 = dframe['ICH_TS'].iloc[-2]
    chikou1 = dframe['ICH_CS'].iloc[-28]
    price_open1 = dframe['open'].iloc[-2]
    price_high1 = dframe['high'].iloc[-2]
    price_low1 = dframe['low'].iloc[-2]
    price_close1 = dframe['close'].iloc[-2]
    price_open_chikou1 = dframe['open'].iloc[-28]
    price_high_chikou1 = dframe['high'].iloc[-28]
    price_low_chikou1 = dframe['low'].iloc[-28]
    price_close_chikou1 = dframe['close'].iloc[-28]
    tenkan_chikou1 = dframe['ICH_TS'].iloc[-28]
    kijun_chikou1 = dframe['ICH_KS'].iloc[-28]
    ssa_chikou1 = dframe['ICH_SSA'].iloc[-28]
    ssb_chikou1 = dframe['ICH_SSB'].iloc[-28]

    #if price_close1 > price_open1:
    if price_close1 > ssa1 and price_close1 > ssb1 and price_close1 > tenkan1 and price_close1 > kijun1:
        if chikou1 > ssa_chikou1 and chikou1 > ssb_chikou1 and chikou1 > tenkan_chikou1 and chikou1 > kijun_chikou1:
            if chikou1 > price_high_chikou1:
                if price_close > ssa and price_close > ssb and price_close > tenkan and price_close > kijun:
                    if chikou > ssa_chikou and chikou > ssb_chikou and chikou > tenkan_chikou and chikou > kijun_chikou:
                        percent = (price_close1 - price_open1) / price_open1 * 100
                        print("(UPTREND)" + ";" + str(datetime.now()).split('.')[0] + ";" + symbol + ";" + tf + ";" + str(price_close1) + ";" + str(price_open1) + ";" + "{:.4f}".format(percent), "%")
                        log_to_results("(UPTREND)" + ";" + str(datetime.now()).split('.')[0] + ";" + symbol + ";" + tf + ";" + str(price_close1).replace(".", ",") + ";" + str(price_open1).replace(".", ",") + ";" + "{:.4f}".format(percent).replace(".", ",") + "%")
                        return True

exchange.set_sandbox_mode(False)  # comment if you're not using the testnet
markets = exchange.load_markets()
exchange.verbose = False  # debug output

percent = 2.5 # 4 seems the best

#array_watch = {"VET/USDT": 0.02749, "BTC/USDT": 23000, "BAT/USDT": 0.4139}
#array_watch = {"VET/USDT": 0.02749, "BTC/USDT": 23000, "BAT/USDT": 0.4139}
array_watch = {}
array_count = {}
array_t0 = {}
array_datetime = {}
array_evol = {}
array_evol_ask = {}

#time.sleep(0.1)
tickers = exchange.fetch_tickers()
for item in tickers.items():
    symbol = item[0]
    if not str(symbol).endswith("/USDT") or str(symbol).endswith("DOWN/USDT") or str(symbol).endswith("UP/USDT"):
        continue
    bid = tickers[symbol]['bid']  # prix de vente (sell)
    ask = tickers[symbol]['ask']  # prix d'achat (buy)
    #print(symbol, bid, ask)
    if ask is not None and ask > 0:
        array_watch[symbol] = ask# + ask/100*percent
        array_t0[symbol] = ask
        array_datetime[symbol] = datetime.now()
        print("adding", symbol, "with target buy price", array_watch[symbol], "current price being", ask)
        array_count[symbol] = 0

while True:
    time.sleep(0.0125)
    array_evol.clear()
    tickers = exchange.fetch_tickers()
    for item in tickers.items():
        symbol = item[0]

        for symbol_to_watch, value_to_watch in array_watch.items():
            if symbol_to_watch == symbol:
                bid = tickers[symbol]['bid'] # prix de vente (sell)
                ask = tickers[symbol]['ask'] # prix d'achat (buy)
                if ask > value_to_watch:
                    array_count[symbol] = array_count[symbol] + 1
                    array_watch[symbol_to_watch] = ask# + ask/100*percent

                    timedelta = datetime.now() - array_datetime[symbol]
                    # evol_pourcent = ask / array_t0[symbol]
                    evol_pourcent = ((ask - array_t0[symbol]) / array_t0[symbol]) * 100
                    array_evol[symbol] = evol_pourcent
                    percent_per_second = evol_pourcent / timedelta.total_seconds()
                    #str_lien = "https://tradingview.com/chart/?symbol=BINANCE%3A" + symbol.replace('/', '')
                    print(array_count[symbol_to_watch], symbol_to_watch, ">=", value_to_watch, "increasing value to watch for", symbol, "to", array_watch[symbol_to_watch], "evol/t0", "{:.2f}".format(evol_pourcent) + "%", "diff(t-t0)", timedelta, "%/sec", "{:.4f}".format(percent_per_second))
                    log_to_results(str(array_count[symbol_to_watch]) + " " + symbol_to_watch + " "+ ">=" + " " + str(value_to_watch) + " " + "increasing value to watch for" + " " + symbol + " " + "to" + " " + str(array_watch[symbol_to_watch]) + " " + "evol/t0" + " " + "{:.2f}".format(evol_pourcent) + "%" + " " + "diff(t-t0)" + " " + str(timedelta) + "%/sec" + " " + "{:.4f}".format(percent_per_second))
                    #beep.beep(1)
                    array_evol_ask[symbol] = ask

    if len(array_evol)>0:
        array_evol_sorted = sorted(array_evol.items(), key=lambda x: x[1], reverse=True)
        #str_lien = "https://tradingview.com/chart/?symbol=BINANCE%3A" + (array_evol_sorted[0][0]).replace('/', '')
        print(str(array_evol_sorted[0]) + " ")
        #"{:.2f}".format(evol_pourcent)
        evol_ask = array_evol_ask[str(array_evol_sorted[0][0])]
        stimestamp = str(datetime.now()).rsplit('.', 1)[0]
        print(stimestamp + " " + str(array_evol_sorted[0][0]) + " " + str(evol_ask) + " " + "{:.2f}".format(array_evol_sorted[0][1]) + "% ")

        result = check_timeframe_up(str(array_evol_sorted[0][0]), '1h')
        if result == True:
          log_to_evol(stimestamp + " " + str(array_evol_sorted[0][0]) + " " + str(evol_ask) + " " + "{:.2f}".format(array_evol_sorted[0][1]) + "% ")

        # result = check_timeframe_up(str(array_evol_sorted[0][0]), '1h')
        # if result == True:
        #   log_to_evol("result=" + str(result))


exit(-3)

