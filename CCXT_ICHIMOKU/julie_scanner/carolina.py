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

def fetch_ohlcv(exchange, symbol, timeframe, limit):
    try:
        return exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
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

def format_candle_time(candle):
    utc_time = datetime.fromtimestamp(candle[0] / 1000, pytz.utc)
    return utc_time.strftime('%Y-%m-%d %H:%M:%S')

def get_pattern_explanation(pattern_name):
    explanations = {
        'Evening Star': (
            "The Evening Star is a bearish reversal pattern that occurs at the end of an uptrend. "
            "It consists of three candles: a large bullish candle, a small-bodied candle (the star), "
            "and a large bearish candle. The pattern suggests a potential reversal to a downtrend."
        ),
        'Morning Star': (
            "The Morning Star is a bullish reversal pattern that occurs at the end of a downtrend. "
            "It consists of three candles: a large bearish candle, a small-bodied candle (the star), "
            "and a large bullish candle. The pattern suggests a potential reversal to an uptrend."
        ),
        'Doji': (
            "A Doji is a single candle pattern that indicates indecision in the market. The open and close "
            "prices are very close or the same, creating a small body. It can signal a potential reversal "
            "or continuation depending on its context."
        ),
        'Hammer': (
            "A Hammer is a single candle pattern that appears at the end of a downtrend and indicates a potential "
            "reversal to an uptrend. It has a small body at the top of the trading range with a long lower shadow. "
            "The color of the body is less important, but the long lower shadow indicates buying pressure."
        ),
        'Hanging Man': (
            "A Hanging Man is a single candle pattern that appears at the end of an uptrend and indicates a potential "
            "reversal to a downtrend. It has a small body at the top of the trading range with a long lower shadow. "
            "The color of the body is less important, but the long lower shadow indicates selling pressure."
        ),
    }
    return explanations.get(pattern_name, "No explanation available.")

def scan_and_display_assets(exchange, symbols, timeframe, output_file):
    current_time = datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')

    header = f"Scan results at {current_time} (UTC):\n"
    print(header.strip())

    for symbol in symbols:
        print(f"Scanning {symbol}...")

        if not is_tradable(exchange, symbol):
            continue

        # Fetch 5 candles to ensure we can exclude the current incomplete candle
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe, limit=5)

        if len(ohlcv) < 3:
            print(f"Not enough data to scan {symbol}. Skipping.")
            continue

        # Exclude the current incomplete candle
        candles = ohlcv[-4:-1]
        if len(candles) == 3:
            # Check patterns that require 3 candles
            if is_evening_star(candles):
                candle_times = [format_candle_time(candle) for candle in candles]
                result = (
                    f"[{candle_times[-1]}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(candles) + 1}, "
                    f"Pattern detected: Evening Star\n"
                    f"Pattern Explanation: {get_pattern_explanation('Evening Star')}\n"
                    f"Detected on candles:\n"
                    f"  1. {candle_times[0]}\n"
                    f"  2. {candle_times[1]}\n"
                    f"  3. {candle_times[2]}\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

            if is_morning_star(candles):
                candle_times = [format_candle_time(candle) for candle in candles]
                result = (
                    f"[{candle_times[-1]}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(candles) + 1}, "
                    f"Pattern detected: Morning Star\n"
                    f"Pattern Explanation: {get_pattern_explanation('Morning Star')}\n"
                    f"Detected on candles:\n"
                    f"  1. {candle_times[0]}\n"
                    f"  2. {candle_times[1]}\n"
                    f"  3. {candle_times[2]}\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

        # Check single candle patterns (Doji, Hammer, Hanging Man)
        if len(ohlcv) >= 1:
            candle = ohlcv[-2]
            candle_time = format_candle_time(candle)

            if is_doji(candle):
                result = (
                    f"[{candle_time}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Doji\n"
                    f"Pattern Explanation: {get_pattern_explanation('Doji')}\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

            if is_hammer(candle):
                result = (
                    f"[{candle_time}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Hammer\n"
                    f"Pattern Explanation: {get_pattern_explanation('Hammer')}\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

            if is_hanging_man(candle):
                result = (
                    f"[{candle_time}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Hanging Man\n"
                    f"Pattern Explanation: {get_pattern_explanation('Hanging Man')}\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

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
