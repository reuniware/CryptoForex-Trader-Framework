import ccxt
import sys
import os
import argparse
import time
from datetime import datetime
import pytz
import re
import threading

# Define detection functions for candlestick patterns

def is_evening_star(candles):
    if len(candles) != 3:
        return False

    first_candle, second_candle, third_candle = candles
    first_open, first_close = first_candle[1], first_candle[4]
    second_open, second_close = second_candle[1], second_candle[4]
    third_open, third_close = third_candle[1], third_candle[4]

    # Check pattern criteria
    return (
        first_close > first_open and
        abs(second_close - second_open) < abs(first_open - first_close) / 2 and
        third_close < third_open and
        abs(third_close - third_open) > abs(first_open - first_close) / 2 and
        third_close < first_open and
        third_close > first_close
    )

def is_morning_star(candles):
    if len(candles) != 3:
        return False

    first_candle, second_candle, third_candle = candles
    first_open, first_close = first_candle[1], first_candle[4]
    second_open, second_close = second_candle[1], second_candle[4]
    third_open, third_close = third_candle[1], third_candle[4]

    # Check pattern criteria
    return (
        first_close < first_open and
        abs(second_close - second_open) < abs(first_open - first_close) / 2 and
        third_close > third_open and
        abs(third_close - third_open) > abs(first_open - first_close) / 2 and
        third_close > first_open and
        third_close < first_close
    )

def is_bullish_engulfing(candles):
    if len(candles) != 2:
        return False

    first_candle, second_candle = candles
    first_open, first_close = first_candle[1], first_candle[4]
    second_open, second_close = second_candle[1], second_candle[4]

    return (
        first_close < first_open and
        second_close > second_open and
        second_close > first_open and
        second_open < first_close
    )

def is_bearish_engulfing(candles):
    if len(candles) != 2:
        return False

    first_candle, second_candle = candles
    first_open, first_close = first_candle[1], first_candle[4]
    second_open, second_close = second_candle[1], second_candle[4]

    return (
        first_close > first_open and
        second_close < second_open and
        second_close < first_open and
        second_open > first_close
    )

def is_doji(candle):
    open_price, close_price = candle[1], candle[4]
    return abs(open_price - close_price) / (candle[2] - candle[3]) < 0.1

def is_hammer(candle):
    open_price, close_price, high_price, low_price = candle[1], candle[4], candle[2], candle[3]
    return (close_price > open_price and
            (high_price - max(open_price, close_price)) < 0.25 * (high_price - low_price) and
            (min(open_price, close_price) - low_price) > 2 * (high_price - close_price))

def is_hanging_man(candle):
    open_price, close_price, high_price, low_price = candle[1], candle[4], candle[2], candle[3]
    return (close_price < open_price and
            (high_price - max(open_price, close_price)) < 0.25 * (high_price - low_price) and
            (min(open_price, close_price) - low_price) > 2 * (high_price - close_price))

def is_inverted_hammer(candle):
    open_price, close_price, high_price, low_price = candle[1], candle[4], candle[2], candle[3]
    return (close_price > open_price and
            (high_price - max(open_price, close_price)) < 0.25 * (high_price - low_price) and
            (min(open_price, close_price) - low_price) < 0.5 * (high_price - low_price))

def is_dark_cloud_cover(candles):
    if len(candles) != 2:
        return False

    first_candle, second_candle = candles
    first_open, first_close = first_candle[1], first_candle[4]
    second_open, second_close = second_candle[1], second_candle[4]

    return (
        first_close > first_open and
        second_close < second_open and
        second_close < (first_open + first_close) / 2 and
        second_open > first_close
    )

def is_three_white_soldiers(candles):
    if len(candles) != 3:
        return False

    c1, c2, c3 = candles
    return (c1[1] < c1[4] and c2[1] < c2[4] and c3[1] < c3[4] and
            c1[1] < c2[1] < c3[1] and c1[4] < c2[4] < c3[4])

def is_three_black_crows(candles):
    if len(candles) != 3:
        return False

    c1, c2, c3 = candles
    return (c1[1] > c1[4] and c2[1] > c2[4] and c3[1] > c3[4] and
            c1[1] > c2[1] > c3[1] and c1[4] > c2[4] > c3[4])

def is_rising_three_methods(candles):
    if len(candles) < 5:
        return False

    c1, c2, c3, c4, c5 = candles
    return (c1[1] < c1[4] and
            c2[1] < c2[4] and c3[1] < c3[4] and
            c4[1] < c4[4] and c5[1] < c5[4] and
            c2[1] > c1[4] and c4[4] > c3[4] and
            c5[4] > c1[4])

def is_falling_three_methods(candles):
    if len(candles) < 5:
        return False

    c1, c2, c3, c4, c5 = candles
    return (c1[1] > c1[4] and
            c2[1] > c2[4] and c3[1] > c3[4] and
            c4[1] > c4[4] and c5[1] > c5[4] and
            c2[4] < c1[1] and c4[1] < c3[4] and
            c5[4] < c1[4])

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

def format_candle_time(timestamp):
    return datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

def calculate_percentage_evolution(open_price, close_price):
    if open_price == 0:
        return 0
    return ((close_price - open_price) / open_price) * 100

def analyze_symbol(exchange, symbol, timeframe, output_file):
    try:
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe, 4)
        if len(ohlcv) < 4:
            return
        
        completed_candles = ohlcv[:-1]  # Exclude the current incomplete candle
        last_candle = ohlcv[-1]  # Current incomplete candle

        pattern_detected = False
        pattern_type = None
        confirmation_message = ""

        if is_evening_star(completed_candles):
            pattern_detected = True
            pattern_type = "Evening Star"
            if last_candle[4] < completed_candles[-1][1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Evening Star pattern."
            else:
                return
        elif is_morning_star(completed_candles):
            pattern_detected = True
            pattern_type = "Morning Star"
            if last_candle[4] > completed_candles[-1][1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Morning Star pattern."
            else:
                return
        elif is_bullish_engulfing(completed_candles):
            pattern_detected = True
            pattern_type = "Bullish Engulfing"
            if last_candle[4] > last_candle[1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Bullish Engulfing pattern."
            else:
                return
        elif is_bearish_engulfing(completed_candles):
            pattern_detected = True
            pattern_type = "Bearish Engulfing"
            if last_candle[4] < last_candle[1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Bearish Engulfing pattern."
            else:
                return
        elif is_doji(last_candle):
            pattern_detected = True
            pattern_type = "Doji"
            if last_candle[4] < last_candle[1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Doji pattern."
            else:
                return
        elif is_hammer(last_candle):
            pattern_detected = True
            pattern_type = "Hammer"
            if last_candle[4] > last_candle[1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Hammer pattern."
            else:
                return
        elif is_hanging_man(last_candle):
            pattern_detected = True
            pattern_type = "Hanging Man"
            if last_candle[4] < last_candle[1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Hanging Man pattern."
            else:
                return
        elif is_inverted_hammer(last_candle):
            pattern_detected = True
            pattern_type = "Inverted Hammer"
            if last_candle[4] > last_candle[1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Inverted Hammer pattern."
            else:
                return
        elif is_dark_cloud_cover(completed_candles):
            pattern_detected = True
            pattern_type = "Dark Cloud Cover"
            if last_candle[4] < completed_candles[-1][1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Dark Cloud Cover pattern."
            else:
                return
        elif is_three_white_soldiers(completed_candles):
            pattern_detected = True
            pattern_type = "Three White Soldiers"
            if last_candle[4] > last_candle[1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Three White Soldiers pattern."
            else:
                return
        elif is_three_black_crows(completed_candles):
            pattern_detected = True
            pattern_type = "Three Black Crows"
            if last_candle[4] < last_candle[1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Three Black Crows pattern."
            else:
                return
        elif is_rising_three_methods(completed_candles):
            pattern_detected = True
            pattern_type = "Rising Three Methods"
            if last_candle[4] > last_candle[1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Rising Three Methods pattern."
            else:
                return
        elif is_falling_three_methods(completed_candles):
            pattern_detected = True
            pattern_type = "Falling Three Methods"
            if last_candle[4] < last_candle[1]:
                confirmation_message = "Pattern confirmation: Current candle confirms the Falling Three Methods pattern."
            else:
                return

        if pattern_detected:
            current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            open_price = last_candle[1]
            close_price = last_candle[4]
            evolution = calculate_percentage_evolution(open_price, close_price)
            result = (
                f"[{current_time}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, Pattern detected: {pattern_type}\n"
                f"Detected on candle: {format_candle_time(completed_candles[-1][0])}\n"
                f"Current price: {close_price:.4f}, Current candle evolution: {evolution:.2f}%\n"
                f"{confirmation_message}\n\n"  # Added an extra newline here
            )
            print(result.strip())
            with open(output_file, 'a') as f:
                f.write(result)
    except Exception as e:
        print(f"Error analyzing symbol {symbol}: {str(e)}")

def worker(exchange, symbols, timeframe, output_file):
    for symbol in symbols:
        analyze_symbol(exchange, symbol, timeframe, output_file)

def main():
    parser = argparse.ArgumentParser(description='Scan for candlestick patterns.')
    parser.add_argument('--timeframe', type=str, required=True, help='Timeframe for the candlestick analysis')
    args = parser.parse_args()

    timeframe = args.timeframe
    output_file = f"scan_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"

    # Fetch and process symbols
    exchange = ccxt.binance({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })

    filter_pattern = '*'
    symbols = fetch_markets(exchange, filter_pattern)
    num_threads = 20
    chunk_size = len(symbols) // num_threads + 1

    threads = []
    for i in range(num_threads):
        start = i * chunk_size
        end = start + chunk_size
        symbols_chunk = symbols[start:end]
        thread = threading.Thread(target=worker, args=(exchange, symbols_chunk, timeframe, output_file))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()
