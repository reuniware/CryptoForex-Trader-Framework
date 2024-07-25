import ccxt
import sys
import os
import argparse
import time
from datetime import datetime
import pytz
import threading

def fetch_markets(exchange):
    try:
        markets = exchange.fetch_markets()
        # Filter to include only assets ending with '/USDT'
        symbols = [market['symbol'] for market in markets if market['spot'] and market['symbol'].endswith('/USDT')]
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

def fetch_current_price(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['ask'] if 'ask' in ticker else None
    except Exception as e:
        print(f"Error fetching current price for {symbol}: {str(e)}")
        return None

def format_candle_time(timestamp):
    return datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

def calculate_percentage_evolution(open_price, current_price):
    if open_price == 0:
        return 0
    return ((current_price - open_price) / open_price) * 100

def is_evening_star(candles):
    if len(candles) != 3:
        return False
    first, second, third = candles
    first_open, first_high, first_low, first_close = first[1], first[2], first[3], first[4]
    second_open, second_high, second_low, second_close = second[1], second[2], second[3], second[4]
    third_open, third_high, third_low, third_close = third[1], third[2], third[3], third[4]
    is_first_bullish = first_close > first_open
    is_second_small_body = abs(second_close - second_open) < (second_high - second_low) * 0.3
    is_second_gap_up = second_open > first_close
    is_third_bearish = third_close < third_open
    is_third_closes_below_mid = third_close < (first_open + first_close) / 2
    return (is_first_bullish and
            is_second_small_body and
            is_second_gap_up and
            is_third_bearish and
            is_third_closes_below_mid)

def is_morning_star(candles):
    if len(candles) != 3:
        return False
    first, second, third = candles
    first_body = first[1] - first[4]
    second_body = abs(second[4] - second[1])
    third_body = third[4] - third[1]
    return (first_body > 0 and
            second_body > 0 and
            third_body > 0 and
            second[4] < first[1] and
            second[1] < first[1] and
            third[1] > third[4] and
            third[4] > (first[1] + first[4]) / 2)

def is_bullish_engulfing(candles):
    if len(candles) != 2:
        return False
    first, second = candles
    first_body = first[4] - first[1]
    second_body = second[4] - second[1]
    return (first_body < 0 and
            second_body > 0 and
            second[1] < first[4] and
            second[4] > first[1])

def is_bearish_engulfing(candles):
    if len(candles) != 2:
        return False
    first, second = candles
    first_body = first[1] - first[4]
    second_body = second[1] - second[4]
    return (first_body > 0 and
            second_body < 0 and
            second[1] > first[4] and
            second[4] < first[1])

def is_doji(candle):
    body = abs(candle[1] - candle[4])
    return body < (candle[2] - candle[3]) * 0.1

def is_hammer(candle):
    body = abs(candle[1] - candle[4])
    lower_shadow = candle[2] - min(candle[1], candle[4])
    upper_shadow = candle[3] - max(candle[1], candle[4])
    return (body < lower_shadow and body < upper_shadow and
            lower_shadow > 2 * body)

def is_hanging_man(candle):
    body = abs(candle[1] - candle[4])
    lower_shadow = candle[2] - min(candle[1], candle[4])
    upper_shadow = candle[3] - max(candle[1], candle[4])
    return (body < lower_shadow and body < upper_shadow and
            lower_shadow > 2 * body and
            upper_shadow < body)

def is_inverted_hammer(candle):
    body = abs(candle[1] - candle[4])
    upper_shadow = candle[3] - max(candle[1], candle[4])
    lower_shadow = candle[2] - min(candle[1], candle[4])
    return (body < upper_shadow and body < lower_shadow and
            upper_shadow > 2 * body)

def is_dark_cloud_cover(candles):
    if len(candles) != 2:
        return False
    first, second = candles
    first_body = first[4] - first[1]
    second_body = second[4] - second[1]
    return (first_body > 0 and
            second_body < 0 and
            second[1] > first[4] and
            second[4] < (first[1] + first[4]) / 2)

def is_three_white_soldiers(candles):
    if len(candles) != 3:
        return False
    first, second, third = candles
    return (first[1] < first[4] and
            second[1] < second[4] and
            third[1] < third[4] and
            second[1] > first[4] and
            third[1] > second[4] and
            third[4] > second[4])

def is_three_black_crows(candles):
    if len(candles) != 3:
        return False
    first, second, third = candles
    return (first[1] > first[4] and
            second[1] > second[4] and
            third[1] > third[4] and
            second[1] < first[4] and
            third[1] < second[4] and
            third[4] < second[4])

def is_rising_three_methods(candles):
    if len(candles) != 5:
        return False
    first, second, third, fourth, fifth = candles
    first_body = first[4] - first[1]
    third_body = third[4] - third[1]
    fifth_body = fifth[4] - fifth[1]
    return (first_body > 0 and
            third_body > 0 and
            fifth_body > 0 and
            second[1] > first[4] and
            third[1] > second[4] and
            fourth[1] < third[4] and
            fifth[1] > fourth[4])

def is_falling_three_methods(candles):
    if len(candles) != 5:
        return False
    first, second, third, fourth, fifth = candles
    first_body = first[1] - first[4]
    third_body = third[1] - third[4]
    fifth_body = fifth[1] - fifth[4]
    return (first_body < 0 and
            third_body < 0 and
            fifth_body < 0 and
            second[1] < first[4] and
            third[1] < second[4] and
            fourth[1] > third[4] and
            fifth[1] < fourth[4])

def is_shooting_star(candle):
    body = abs(candle[1] - candle[4])
    lower_shadow = candle[2] - min(candle[1], candle[4])
    upper_shadow = candle[3] - max(candle[1], candle[4])
    return (body < lower_shadow and body < upper_shadow and
            upper_shadow > 2 * body and
            lower_shadow < body)

def is_piercing_line(candles):
    if len(candles) != 2:
        return False
    first, second = candles
    first_body = first[1] - first[4]
    second_body = second[4] - second[1]
    return (first_body > 0 and
            second_body > 0 and
            second[1] < first[4] and
            second[4] > (first[1] + first[4]) / 2)

def is_harami(candles):
    if len(candles) != 2:
        return False
    first, second = candles
    first_body = abs(first[1] - first[4])
    second_body = abs(second[1] - second[4])
    return (first_body > second_body and
            second[1] >= first[1] and
            second[4] <= first[4])

def is_harami_cross(candles):
    if len(candles) != 3:
        return False
    first, second, third = candles
    first_body = abs(first[1] - first[4])
    second_body = abs(second[1] - second[4])
    third_body = abs(third[1] - third[4])
    return (first_body > second_body and
            second[1] >= first[1] and
            second[4] <= first[4] and
            third[4] > (first[1] + first[4]) / 2)

def is_belt_hold(candles):
    if len(candles) < 3:
        return False
    for i in range(1, len(candles) - 1):
        if abs(candles[i][1] - candles[i][4]) > (candles[i][3] - candles[i][2]) * 0.1:
            return False
    last = candles[-1]
    return (last[4] > max(candle[3] for candle in candles[:-1]) and
            last[1] < min(candle[2] for candle in candles[:-1]))

def is_breakaway(candles):
    if len(candles) < 3:
        return False
    highs = [candle[2] for candle in candles]
    lows = [candle[3] for candle in candles]
    last = candles[-1]
    return (all(highs[i] < highs[i+1] for i in range(len(highs)-1)) and
            last[4] > highs[-1]) or (all(lows[i] > lows[i+1] for i in range(len(lows)-1)) and
            last[4] < lows[-1])

def analyze_symbol(exchange, symbol, timeframe, output_file):
    try:
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe, 4)
        if not ohlcv:
            return

        current_price = fetch_current_price(exchange, symbol)
        if current_price is None:
            return

        if len(ohlcv) < 4:
            return

        completed_candles = ohlcv[-4:-1]
        current_candle = ohlcv[-1]
        current_price = fetch_current_price(exchange, symbol)
        if current_price is None:
            return

        last_candle = completed_candles[-1]

        pattern_detected = False
        pattern_type = ""

        if is_evening_star(completed_candles):
            pattern_detected = True
            pattern_type = "Evening Star"
        elif is_morning_star(completed_candles):
            pattern_detected = True
            pattern_type = "Morning Star"
        elif is_bullish_engulfing(completed_candles):
            pattern_detected = True
            pattern_type = "Bullish Engulfing"
        elif is_bearish_engulfing(completed_candles):
            pattern_detected = True
            pattern_type = "Bearish Engulfing"
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
        elif is_dark_cloud_cover(completed_candles):
            pattern_detected = True
            pattern_type = "Dark Cloud Cover"
        elif is_three_white_soldiers(completed_candles):
            pattern_detected = True
            pattern_type = "Three White Soldiers"
        elif is_three_black_crows(completed_candles):
            pattern_detected = True
            pattern_type = "Three Black Crows"
        elif is_rising_three_methods(completed_candles):
            pattern_detected = True
            pattern_type = "Rising Three Methods"
        elif is_falling_three_methods(completed_candles):
            pattern_detected = True
            pattern_type = "Falling Three Methods"
        elif is_shooting_star(last_candle):
            pattern_detected = True
            pattern_type = "Shooting Star"
        elif is_piercing_line(completed_candles):
            pattern_detected = True
            pattern_type = "Piercing Line"
        elif is_harami(completed_candles):
            pattern_detected = True
            pattern_type = "Harami"
        elif is_harami_cross(completed_candles):
            pattern_detected = True
            pattern_type = "Harami Cross"
        elif is_belt_hold(completed_candles):
            pattern_detected = True
            pattern_type = "Belt Hold"
        elif is_breakaway(completed_candles):
            pattern_detected = True
            pattern_type = "Breakaway"

        if pattern_detected:
            current_time = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
            open_price = current_candle[1]
            evolution = calculate_percentage_evolution(open_price, current_price)
            result = (
                f"[{current_time}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, Pattern detected: {pattern_type}\n"
                f"Detected on candle: {format_candle_time(completed_candles[-1][0])}\n"
                f"Current price: {current_price:.4f}, Current candle evolution: {evolution:.2f}%\n\n"
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
    script_name = os.path.basename(__file__).split('.')[0]
    directory = f"scan_results_{script_name}"

    if not os.path.exists(directory):
        os.makedirs(directory)

    output_file = os.path.join(directory, f"{datetime.now(pytz.UTC).strftime('%Y%m%d_%H%M%S')}_{timeframe}_scan_results.txt")

    exchange = ccxt.binance({
        'rateLimit': 1200,
        'enableRateLimit': True,
    })

    symbols = fetch_markets(exchange)
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