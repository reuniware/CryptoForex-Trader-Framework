import ccxt
import sys
import os
import argparse
import time
from datetime import datetime
import pytz
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def fetch_ohlcv(exchange, symbol, timeframe, limit):
    try:
        return exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    except Exception as e:
        print(f"Error fetching OHLCV data for {symbol}: {str(e)}")
        return []

def calculate_percentage_evolution(open_price, close_price):
    return ((close_price - open_price) / open_price) * 100

def format_candle_time(candle):
    return datetime.fromtimestamp(candle[0] / 1000, tz=pytz.utc).strftime('%Y-%m-%d %H:%M:%S')

def is_tradable(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker.get('ask') is not None
    except Exception as e:
        print(f"Error checking tradability for {symbol}: {str(e)}")
        return False

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

def is_bullish_engulfing(candles):
    if len(candles) != 2:
        return False

    first_candle, second_candle = candles

    first_open = first_candle[1]
    first_close = first_candle[4]
    second_open = second_candle[1]
    second_close = second_candle[4]

    return (second_open < first_close and second_close > first_open) and (second_open < second_close)

def is_bearish_engulfing(candles):
    if len(candles) != 2:
        return False

    first_candle, second_candle = candles

    first_open = first_candle[1]
    first_close = first_candle[4]
    second_open = second_candle[1]
    second_close = second_candle[4]

    return (second_open > first_close and second_close < first_open) and (second_open > second_close)

def is_dark_cloud_cover(candles):
    if len(candles) != 2:
        return False

    first_candle, second_candle = candles

    first_open = first_candle[1]
    first_close = first_candle[4]
    second_open = second_candle[1]
    second_close = second_candle[4]

    return (second_close < second_open and second_close > first_open and second_open > first_close)

def is_three_white_soldiers(candles):
    if len(candles) != 3:
        return False

    first_candle, second_candle, third_candle = candles

    return (first_candle[4] > first_candle[1] and
            second_candle[4] > second_candle[1] and
            third_candle[4] > third_candle[1] and
            third_candle[1] > second_candle[4] and
            second_candle[1] > first_candle[4])

def is_three_black_crows(candles):
    if len(candles) != 3:
        return False

    first_candle, second_candle, third_candle = candles

    return (first_candle[4] < first_candle[1] and
            second_candle[4] < second_candle[1] and
            third_candle[4] < third_candle[1] and
            third_candle[1] < second_candle[4] and
            second_candle[1] < first_candle[4])

def is_rising_three_methods(candles):
    if len(candles) != 5:
        return False

    first_candle, *middle_candles, last_candle = candles

    if not (first_candle[4] > first_candle[1] and last_candle[4] > last_candle[1]):
        return False

    if any(c[4] <= c[1] for c in middle_candles):
        return False

    return last_candle[4] > first_candle[4]

def is_falling_three_methods(candles):
    if len(candles) != 5:
        return False

    first_candle, *middle_candles, last_candle = candles

    if not (first_candle[4] < first_candle[1] and last_candle[4] < last_candle[1]):
        return False

    if any(c[4] >= c[1] for c in middle_candles):
        return False

    return last_candle[4] < first_candle[4]

def is_doji(candle):
    open_price = candle[1]
    close_price = candle[4]
    return abs(open_price - close_price) <= (candle[2] - candle[3]) * 0.1

def is_hammer(candle):
    open_price = candle[1]
    close_price = candle[4]
    low = candle[3]
    high = candle[2]

    body_length = abs(open_price - close_price)
    lower_shadow = open_price - low if open_price < close_price else close_price - low
    upper_shadow = high - open_price if open_price > close_price else high - close_price

    return (body_length <= lower_shadow * 0.3) and (upper_shadow <= body_length * 0.3)

def is_hanging_man(candle):
    open_price = candle[1]
    close_price = candle[4]
    low = candle[3]
    high = candle[2]

    body_length = abs(open_price - close_price)
    lower_shadow = open_price - low if open_price < close_price else close_price - low
    upper_shadow = high - open_price if open_price > close_price else high - close_price

    return (body_length <= lower_shadow * 0.3) and (upper_shadow >= body_length * 0.6)

def is_inverted_hammer(candle):
    open_price = candle[1]
    close_price = candle[4]
    low = candle[3]
    high = candle[2]

    body_length = abs(open_price - close_price)
    lower_shadow = open_price - low if open_price < close_price else close_price - low
    upper_shadow = high - open_price if open_price > close_price else high - close_price

    return (body_length <= upper_shadow * 0.3) and (lower_shadow <= body_length * 0.3)

def analyze_symbol(exchange, symbol, timeframe, output_file):
    try:
        if not is_tradable(exchange, symbol):
            return

        ohlcv = fetch_ohlcv(exchange, symbol, timeframe, 4)  # Fetch last 4 candles
        if len(ohlcv) < 4:
            print(f"Not enough data for {symbol}.")
            return

        last_candle = ohlcv[-1]
        candles = ohlcv[-4:]  # Get the last 4 candles for pattern detection

        pattern_detected = False
        pattern_type = None

        if is_evening_star(candles):
            pattern_detected = True
            pattern_type = "Evening Star"
        elif is_morning_star(candles):
            pattern_detected = True
            pattern_type = "Morning Star"
        elif is_bullish_engulfing(candles[-2:]):
            pattern_detected = True
            pattern_type = "Bullish Engulfing"
        elif is_bearish_engulfing(candles[-2:]):
            pattern_detected = True
            pattern_type = "Bearish Engulfing"
        elif is_dark_cloud_cover(candles[-2:]):
            pattern_detected = True
            pattern_type = "Dark Cloud Cover"
        elif is_three_white_soldiers(candles):
            pattern_detected = True
            pattern_type = "Three White Soldiers"
        elif is_three_black_crows(candles):
            pattern_detected = True
            pattern_type = "Three Black Crows"
        elif is_rising_three_methods(candles):
            pattern_detected = True
            pattern_type = "Rising Three Methods"
        elif is_falling_three_methods(candles):
            pattern_detected = True
            pattern_type = "Falling Three Methods"
        elif is_doji(last_candle):
            pattern_detected = True
            pattern_type = "Doji"
        elif is_hammer(last_candle):
            pattern_detected = True
            pattern_type = "Hammer"
        elif is_hanging_man(last_candle):
            pattern_detected = True
            pattern_type = "Hanging Man"
        elif is_inverted_hammer(last_candle):
            pattern_detected = True
            pattern_type = "Inverted Hammer"

        if pattern_detected:
            current_price = exchange.fetch_ticker(symbol)['last']
            open_price = last_candle[1]
            close_price = last_candle[4]
            evolution = calculate_percentage_evolution(open_price, close_price)

            confirmation_message = ""
            if pattern_type in ["Three Black Crows", "Falling Three Methods"]:
                if close_price < open_price:
                    confirmation_message = "Pattern confirmation: Current candle confirms the pattern."
                else:
                    confirmation_message = "Pattern confirmation: Current candle does not confirm the pattern."
            elif pattern_type in ["Three White Soldiers", "Rising Three Methods"]:
                if close_price > open_price:
                    confirmation_message = "Pattern confirmation: Current candle confirms the pattern."
                else:
                    confirmation_message = "Pattern confirmation: Current candle does not confirm the pattern."
            elif pattern_type in ["Doji", "Hammer", "Hanging Man", "Inverted Hammer"]:
                if (pattern_type == "Doji" and is_doji(last_candle)) or \
                   (pattern_type == "Hammer" and is_hammer(last_candle)) or \
                   (pattern_type == "Hanging Man" and is_hanging_man(last_candle)) or \
                   (pattern_type == "Inverted Hammer" and is_inverted_hammer(last_candle)):
                    confirmation_message = f"Pattern confirmation: Current candle confirms the {pattern_type} pattern."
                else:
                    confirmation_message = f"Pattern confirmation: Current candle does not confirm the {pattern_type} pattern."

            result = (
                f"[{datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                f"Pattern detected: {pattern_type}\n"
                f"Detected on candle:\n"
                f"  1. {format_candle_time(ohlcv[-1])}\n"
                f"Current price: {current_price:.4f}, Current candle evolution: {evolution:.2f}%\n"
                f"{confirmation_message}\n"
            )
            print(result.strip())
            with open(output_file, 'a') as f:
                f.write(result + "\n")

    except Exception as e:
        print(f"Error analyzing symbol {symbol}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Scan assets for various candlestick patterns.')
    parser.add_argument('--interval', type=int, default=600, help='Interval between scans in seconds.')
    parser.add_argument('--output', type=str, default='scan_results.txt', help='Output file for results.')
    parser.add_argument('--filter', type=str, default='*USDT', help='Filter pattern for symbols to scan (e.g., *USDT to scan only USDT pairs).')
    parser.add_argument('--timeframe', type=str, default='15m', help='Timeframe to scan (e.g., 1m, 5m, 15m, 1h).')
    parser.add_argument('--list-timeframes', action='store_true', help='List available timeframes and exit.')
    parser.add_argument('--threads', type=int, default=20, help='Number of threads to use for scanning.')
    args = parser.parse_args()

    exchange_name = "binance"  # Change to your exchange
    filter_pattern = args.filter
    timeframe = args.timeframe
    interval = args.interval
    output_file = args.output
    num_threads = args.threads

    exchange = getattr(ccxt, exchange_name)()

    if args.list_timeframes:
        print("Available timeframes:", ', '.join(exchange.timeframes))
        sys.exit(0)

    print("Fetching markets...")
    symbols = fetch_markets(exchange, filter_pattern)
    if not symbols:
        print(f"No symbols found for filter pattern {filter_pattern} in the spot market. Exiting.")
        sys.exit(-1)

    print(f"Number of symbols to be tracked: {len(symbols)}")

    while True:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(analyze_symbol, exchange, symbol, timeframe, output_file): symbol for symbol in symbols}
            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"Error processing symbol {symbol}: {str(e)}")
        
        print(f"Waiting for {interval} seconds before the next scan...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
