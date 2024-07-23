#python marina8_scan_all_patterns_past.py --timeframe 1d
#Fetching markets...
#Number of symbols to be tracked: 526
#Scan results at 2024-07-23 21:37:17 (Paris time):
#Scanning BTC/USDT...
#Downloaded 1000 candles for BTC/USDT
#[2021-10-30 02:00:00] BTC/USDT (BINANCE:BTCUSDT) Timeframe: 1d, Number of candles: 1000, Pattern detected: Hammer, Detected candle: 2021-10-30 02:00:00
#[2021-10-30 02:00:00] BTC/USDT (BINANCE:BTCUSDT) Timeframe: 1d, Number of candles: 1000, Pattern detected: Hanging Man, Detected candle: 2021-10-30 02:00:00
#[2021-10-31 02:00:00] BTC/USDT (BINANCE:BTCUSDT) Timeframe: 1d, Number of candles: 1000, Pattern detected: Hammer, Detected candle: 2021-10-31 02:00:00

import ccxt
import sys
import os
import argparse
import time
from datetime import datetime
import pytz
import re

def fetch_markets(exchange, filter_assets):
    try:
        markets = exchange.fetch_markets()
        pattern = re.compile(filter_assets.replace('*', '.*'), re.IGNORECASE)
        symbols = [market['symbol'] for market in markets if pattern.match(market['symbol']) and market['spot']]
        return symbols
    except (ccxt.ExchangeError, ccxt.NetworkError, ccxt.DDoSProtection) as e:
        print(f"Exchange error: {str(e)}")
        os.kill(os.getpid(), 9)
        sys.exit(-999)

def fetch_ohlcv(exchange, symbol, timeframe, since=None):
    try:
        ohlcv = []
        while True:
            new_ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            if len(new_ohlcv) == 0:
                break
            since = new_ohlcv[-1][0] + 1
            ohlcv.extend(new_ohlcv)
            time.sleep(exchange.rateLimit / 1000)
        return ohlcv
    except Exception as e:
        print(f"Error fetching OHLCV data for {symbol}: {str(e)}")
        return []

def is_evening_star(candles):
    if len(candles) != 3:
        return False

    first_candle, second_candle, third_candle = candles

    first_open = first_candle[1]
    first_close = first_candle[4]
    second_open = second_candle[1]
    second_close = second_candle[4]
    third_open = third_candle[1]
    third_close = third_candle[4]

    if first_close <= first_open:
        return False

    if abs(second_close - second_open) >= abs(first_open - first_close) / 2:
        return False

    if third_close >= third_open or abs(third_close - third_open) <= abs(first_open - first_close) / 2:
        return False

    if third_close >= first_open or third_close <= first_close:
        return False

    return True

def is_morning_star(candles):
    if len(candles) != 3:
        return False

    first_candle, second_candle, third_candle = candles

    first_open = first_candle[1]
    first_close = first_candle[4]
    second_open = second_candle[1]
    second_close = second_candle[4]
    third_open = third_candle[1]
    third_close = third_candle[4]

    if first_close >= first_open:
        return False

    if abs(second_close - second_open) >= abs(first_open - first_close) / 2:
        return False

    if third_close <= third_open or abs(third_close - third_open) <= abs(first_open - first_close) / 2:
        return False

    if third_close <= first_open or third_close >= first_close:
        return False

    return True

def is_doji(candle):
    open_price = candle[1]
    close_price = candle[4]
    return abs(open_price - close_price) <= (candle[2] - candle[3]) * 0.1

def is_hammer(candle):
    open_price = candle[1]
    high_price = candle[2]
    low_price = candle[3]
    close_price = candle[4]
    body_length = abs(close_price - open_price)
    lower_shadow = open_price - low_price if open_price > close_price else close_price - low_price
    upper_shadow = high_price - open_price if open_price > close_price else high_price - close_price

    return body_length <= (high_price - low_price) * 0.3 and lower_shadow >= 2 * body_length and upper_shadow <= body_length

def is_hanging_man(candle):
    open_price = candle[1]
    high_price = candle[2]
    low_price = candle[3]
    close_price = candle[4]
    body_length = abs(close_price - open_price)
    lower_shadow = open_price - low_price if open_price > close_price else close_price - low_price
    upper_shadow = high_price - open_price if open_price > close_price else high_price - close_price

    return body_length <= (high_price - low_price) * 0.3 and lower_shadow >= 2 * body_length and upper_shadow <= body_length and close_price < open_price

def is_tradable(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker.get('ask') is not None
    except Exception as e:
        print(f"Error checking tradability for {symbol}: {str(e)}")
        return False

def convert_to_tradingview_symbol(ccxt_symbol):
    base, quote = ccxt_symbol.split('/')
    return f"BINANCE:{base}{quote}"

def scan_and_display_assets(exchange, symbols, timeframe, output_file):
    paris_tz = pytz.timezone('Europe/Paris')
    current_time = datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S')

    header = f"Scan results at {current_time} (Paris time):\n"
    print(header.strip())

    for symbol in symbols:
        print(f"Scanning {symbol}...")
        
        if not is_tradable(exchange, symbol):
            continue
        
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe)
        num_candles = len(ohlcv)
        print(f"Downloaded {num_candles} candles for {symbol}")
        
        if num_candles >= 3:
            for i in range(num_candles - 3):
                candles = ohlcv[i:i+3]  # Three consecutive candles

                if is_evening_star(candles):
                    evening_star_time = datetime.fromtimestamp(candles[-1][0] / 1000, paris_tz).strftime('%Y-%m-%d %H:%M:%S')
                    result = (
                        f"[{evening_star_time}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                        f"Timeframe: {timeframe}, Number of candles: {num_candles}, Pattern detected: Evening Star, "
                        f"Detected candle(s): {datetime.fromtimestamp(candles[0][0] / 1000, paris_tz).strftime('%Y-%m-%d %H:%M:%S')}, "
                        f"{datetime.fromtimestamp(candles[1][0] / 1000, paris_tz).strftime('%Y-%m-%d %H:%M:%S')}, "
                        f"{evening_star_time}\n"
                    )
                    print(result.strip())
                    with open(output_file, 'a') as f:
                        f.write(result)

                if is_morning_star(candles):
                    morning_star_time = datetime.fromtimestamp(candles[-1][0] / 1000, paris_tz).strftime('%Y-%m-%d %H:%M:%S')
                    result = (
                        f"[{morning_star_time}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                        f"Timeframe: {timeframe}, Number of candles: {num_candles}, Pattern detected: Morning Star, "
                        f"Detected candle(s): {datetime.fromtimestamp(candles[0][0] / 1000, paris_tz).strftime('%Y-%m-%d %H:%M:%S')}, "
                        f"{datetime.fromtimestamp(candles[1][0] / 1000, paris_tz).strftime('%Y-%m-%d %H:%M:%S')}, "
                        f"{morning_star_time}\n"
                    )
                    print(result.strip())
                    with open(output_file, 'a') as f:
                        f.write(result)
        
        for i in range(num_candles):
            candle = ohlcv[i]
            candle_time = datetime.fromtimestamp(candle[0] / 1000, paris_tz).strftime('%Y-%m-%d %H:%M:%S')

            if is_doji(candle):
                result = (
                    f"[{candle_time}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                    f"Timeframe: {timeframe}, Number of candles: {num_candles}, Pattern detected: Doji, "
                    f"Detected candle: {candle_time}\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result)

            if is_hammer(candle):
                result = (
                    f"[{candle_time}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                    f"Timeframe: {timeframe}, Number of candles: {num_candles}, Pattern detected: Hammer, "
                    f"Detected candle: {candle_time}\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result)

            if is_hanging_man(candle):
                result = (
                    f"[{candle_time}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                    f"Timeframe: {timeframe}, Number of candles: {num_candles}, Pattern detected: Hanging Man, "
                    f"Detected candle: {candle_time}\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result)

    print("Scan complete.")

def main():
    parser = argparse.ArgumentParser(description='Scan assets for various candlestick patterns in the previous candlesticks.')
    parser.add_argument('--output', type=str, default='scan_results.txt', help='Output file for results.')
    parser.add_argument('--filter', type=str, default='*USDT', help='Filter pattern for symbols to scan (e.g., *USDT to scan only USDT pairs).')
    parser.add_argument('--timeframe', type=str, default='15m', help='Timeframe to scan (e.g., 1m, 5m, 15m, 1h, 1d).')
    args = parser.parse_args()

    exchange_name = "binance"  # Change to your exchange
    filter_pattern = args.filter
    timeframe = args.timeframe
    output_file = args.output

    exchange = getattr(ccxt, exchange_name)()

    print("Fetching markets...")
    symbols = fetch_markets(exchange, filter_pattern)
    if not symbols:
        print(f"No symbols found for filter pattern {filter_pattern} in the spot market. Exiting.")
        sys.exit(-1)

    print(f"Number of symbols to be tracked: {len(symbols)}")

    scan_and_display_assets(exchange, symbols, timeframe, output_file)

if __name__ == "__main__":
    main()
