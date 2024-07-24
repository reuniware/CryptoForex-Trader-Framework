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

def format_candle_time(candle):
    timestamp = candle[0]
    utc_time = datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
    return utc_time

def calculate_percentage_evolution(open_price, close_price):
    return ((close_price - open_price) / open_price) * 100

def is_tradable(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker.get('ask') is not None
    except Exception as e:
        print(f"Error checking tradability for {symbol}: {str(e)}")
        return False

# Pattern detection functions
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

    if second_close <= second_open:
        return False

    if first_close >= second_open or first_open <= second_close:
        return False

    return True

def is_bearish_engulfing(candles):
    if len(candles) != 2:
        return False

    first_candle, second_candle = candles

    first_open = first_candle[1]
    first_close = first_candle[4]
    second_open = second_candle[1]
    second_close = second_candle[4]

    if second_close >= second_open:
        return False

    if first_close <= second_open or first_open >= second_close:
        return False

    return True

def is_dark_cloud_cover(candles):
    if len(candles) != 2:
        return False

    first_candle, second_candle = candles

    first_open = first_candle[1]
    first_close = first_candle[4]
    second_open = second_candle[1]
    second_close = second_candle[4]

    if first_close <= first_open:
        return False

    if second_close >= second_open:
        return False

    if second_close >= first_open or second_close < (first_open + first_close) / 2:
        return False

    return True

def is_three_white_soldiers(candles):
    if len(candles) != 3:
        return False

    for i in range(3):
        if candles[i][4] <= candles[i][1]:
            return False

    if not (candles[0][4] < candles[1][1] and candles[1][4] < candles[2][1]):
        return False

    return True

def is_three_black_crows(candles):
    if len(candles) != 3:
        return False

    for i in range(3):
        if candles[i][4] >= candles[i][1]:
            return False

    if not (candles[0][4] > candles[1][1] and candles[1][4] > candles[2][1]):
        return False

    return True

def is_rising_three_methods(candles):
    if len(candles) != 5:
        return False

    first_candle, second_candle, third_candle, fourth_candle, fifth_candle = candles

    if first_candle[4] <= first_candle[1]:
        return False

    if second_candle[4] <= second_candle[1] or third_candle[4] <= third_candle[1] or fourth_candle[4] <= fourth_candle[1] or fifth_candle[4] <= fifth_candle[1]:
        return False

    if not (fifth_candle[4] > first_candle[4]):
        return False

    return True

def is_falling_three_methods(candles):
    if len(candles) != 5:
        return False

    first_candle, second_candle, third_candle, fourth_candle, fifth_candle = candles

    if first_candle[4] >= first_candle[1]:
        return False

    if second_candle[4] >= second_candle[1] or third_candle[4] >= third_candle[1] or fourth_candle[4] >= fourth_candle[1] or fifth_candle[4] >= fifth_candle[1]:
        return False

    if not (fifth_candle[4] < first_candle[4]):
        return False

    return True

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
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe, 5)
        if len(ohlcv) < 3:
            return

        last_candle = ohlcv[-1]
        previous_candles = ohlcv[-4:-1]

        current_price = exchange.fetch_ticker(symbol)['last']
        evolution = calculate_percentage_evolution(last_candle[1], last_candle[4])

        if is_tradable(exchange, symbol):
            if is_evening_star(previous_candles):
                candle_time = format_candle_time(last_candle)
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Evening Star\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(previous_candles[-1])}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] < last_candle[1]:
                    print("Pattern confirmation: Current candle confirms the Evening Star pattern.\n")
                else:
                    print("Pattern confirmation: Current candle does not confirm the Evening Star pattern.\n")

            elif is_morning_star(previous_candles):
                candle_time = format_candle_time(last_candle)
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Morning Star\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(previous_candles[-1])}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] > last_candle[1]:
                    print("Pattern confirmation: Current candle confirms the Morning Star pattern.\n")
                else:
                    print("Pattern confirmation: Current candle does not confirm the Morning Star pattern.\n")

            elif is_bullish_engulfing(previous_candles):
                candle_time = format_candle_time(last_candle)
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Bullish Engulfing\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(previous_candles[-1])}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] > last_candle[1]:
                    print("Pattern confirmation: Current price confirms the Bullish Engulfing pattern.\n")
                else:
                    print("Pattern confirmation: Current price does not confirm the Bullish Engulfing pattern.\n")

            elif is_bearish_engulfing(previous_candles):
                candle_time = format_candle_time(last_candle)
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Bearish Engulfing\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(previous_candles[-1])}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] < last_candle[1]:
                    print("Pattern confirmation: Current price confirms the Bearish Engulfing pattern.\n")
                else:
                    print("Pattern confirmation: Current price does not confirm the Bearish Engulfing pattern.\n")

            elif is_dark_cloud_cover(previous_candles):
                candle_time = format_candle_time(last_candle)
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Dark Cloud Cover\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(previous_candles[-1])}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] < last_candle[1]:
                    print("Pattern confirmation: Current candle confirms the Dark Cloud Cover pattern.\n")
                else:
                    print("Pattern confirmation: Current candle does not confirm the Dark Cloud Cover pattern.\n")

            elif is_three_white_soldiers(previous_candles):
                candle_time = format_candle_time(last_candle)
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Three White Soldiers\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(previous_candles[-1])}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] > last_candle[1]:
                    print("Pattern confirmation: Current candle confirms the Three White Soldiers pattern.\n")
                else:
                    print("Pattern confirmation: Current candle does not confirm the Three White Soldiers pattern.\n")

            elif is_three_black_crows(previous_candles):
                candle_time = format_candle_time(last_candle)
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Three Black Crows\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(previous_candles[-1])}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] < last_candle[1]:
                    print("Pattern confirmation: Current candle confirms the Three Black Crows pattern.\n")
                else:
                    print("Pattern confirmation: Current candle does not confirm the Three Black Crows pattern.\n")

            elif is_rising_three_methods(ohlcv):
                candle_time = format_candle_time(last_candle)
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Rising Three Methods\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(ohlcv[0])}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] > last_candle[1]:
                    print("Pattern confirmation: Current candle confirms the Rising Three Methods pattern.\n")
                else:
                    print("Pattern confirmation: Current candle does not confirm the Rising Three Methods pattern.\n")

            elif is_falling_three_methods(ohlcv):
                candle_time = format_candle_time(last_candle)
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Falling Three Methods\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(ohlcv[0])}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] < last_candle[1]:
                    print("Pattern confirmation: Current candle confirms the Falling Three Methods pattern.\n")
                else:
                    print("Pattern confirmation: Current candle does not confirm the Falling Three Methods pattern.\n")

            elif is_doji(last_candle):
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Doji\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(last_candle)}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] == last_candle[1]:
                    print("Pattern confirmation: Current candle confirms the Doji pattern.\n")
                else:
                    print("Pattern confirmation: Current candle does not confirm the Doji pattern.\n")

            elif is_hammer(last_candle):
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Hammer\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(last_candle)}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] > last_candle[1]:
                    print("Pattern confirmation: Current candle confirms the Hammer pattern.\n")
                else:
                    print("Pattern confirmation: Current candle does not confirm the Hammer pattern.\n")

            elif is_hanging_man(last_candle):
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Hanging Man\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(last_candle)}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] < last_candle[1]:
                    print("Pattern confirmation: Current candle confirms the Hanging Man pattern.\n")
                else:
                    print("Pattern confirmation: Current candle does not confirm the Hanging Man pattern.\n")

            elif is_inverted_hammer(last_candle):
                result = (
                    f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                    f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, "
                    f"Pattern detected: Inverted Hammer\n"
                    f"Detected on candle:\n"
                    f"  1. {format_candle_time(last_candle)}\n"
                    f"Current candle evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result + "\n")

                if last_candle[4] > last_candle[1]:
                    print("Pattern confirmation: Current candle confirms the Inverted Hammer pattern.\n")
                else:
                    print("Pattern confirmation: Current candle does not confirm the Inverted Hammer pattern.\n")

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
