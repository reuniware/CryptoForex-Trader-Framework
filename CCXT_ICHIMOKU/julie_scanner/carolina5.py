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
    
    # Extracting open, high, low, close prices for each candle
    first_open, first_high, first_low, first_close = first[1], first[2], first[3], first[4]
    second_open, second_high, second_low, second_close = second[1], second[2], second[3], second[4]
    third_open, third_high, third_low, third_close = third[1], third[2], third[3], third[4]
    
    # Define criteria for an Evening Star
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

    # Check first candle is bearish
    # Check second candle is small and gaps down from the first
    # Check third candle is bullish and closes above the midpoint of the first candle
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

def analyze_symbol(exchange, symbol, timeframe, output_file):
    try:
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe, 4)  # Fetching 4 candles for 3-candle pattern detection
        if not ohlcv:
            return

        # Check if symbol is tradable
        current_price = fetch_current_price(exchange, symbol)
        if current_price is None:
            return

        # Analyze candles
        completed_candles = ohlcv[:-1]
        current_candle = ohlcv[-1]
        last_candle = completed_candles[-1]
        
        pattern_detected = False
        confirmation_message = ""

        if is_evening_star(completed_candles):
            pattern_detected = True
            pattern_type = "Evening Star"
            if current_price < last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Evening Star pattern."
            else:
                return
        elif is_morning_star(completed_candles):
            pattern_detected = True
            pattern_type = "Morning Star"
            if current_price > last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Morning Star pattern."
            else:
                return
        elif is_bullish_engulfing(completed_candles):
            pattern_detected = True
            pattern_type = "Bullish Engulfing"
            if current_price > last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Bullish Engulfing pattern."
            else:
                return
        elif is_bearish_engulfing(completed_candles):
            pattern_detected = True
            pattern_type = "Bearish Engulfing"
            if current_price < last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Bearish Engulfing pattern."
            else:
                return
        elif is_doji(last_candle):
            pattern_detected = True
            pattern_type = "Doji"
            if abs(current_price - last_candle[1]) < 0.01:  # Adjust confirmation condition if needed
                confirmation_message = "Pattern confirmation: Current price confirms the Doji pattern."
            else:
                return
        elif is_hammer(last_candle):
            pattern_detected = True
            pattern_type = "Hammer"
            if current_price > last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Hammer pattern."
            else:
                return
        elif is_hanging_man(last_candle):
            pattern_detected = True
            pattern_type = "Hanging Man"
            if current_price < last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Hanging Man pattern."
            else:
                return
        elif is_inverted_hammer(last_candle):
            pattern_detected = True
            pattern_type = "Inverted Hammer"
            if current_price > last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Inverted Hammer pattern."
            else:
                return
        elif is_dark_cloud_cover(completed_candles):
            pattern_detected = True
            pattern_type = "Dark Cloud Cover"
            if current_price < last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Dark Cloud Cover pattern."
            else:
                return
        elif is_three_white_soldiers(completed_candles):
            pattern_detected = True
            pattern_type = "Three White Soldiers"
            if current_price > last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Three White Soldiers pattern."
            else:
                return
        elif is_three_black_crows(completed_candles):
            pattern_detected = True
            pattern_type = "Three Black Crows"
            if current_price < last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Three Black Crows pattern."
            else:
                return
        elif is_rising_three_methods(completed_candles):
            pattern_detected = True
            pattern_type = "Rising Three Methods"
            if current_price > last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Rising Three Methods pattern."
            else:
                return
        elif is_falling_three_methods(completed_candles):
            pattern_detected = True
            pattern_type = "Falling Three Methods"
            if current_price < last_candle[1]:
                confirmation_message = "Pattern confirmation: Current price confirms the Falling Three Methods pattern."
            else:
                return

        if pattern_detected:
            current_time = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
            open_price = current_candle[1]
            evolution = calculate_percentage_evolution(open_price, current_price)
            result = (
                f"[{current_time}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
                f"Timeframe: {timeframe}, Number of candles: {len(ohlcv)}, Pattern detected: {pattern_type}\n"
                f"Detected on candle: {format_candle_time(completed_candles[-1][0])}\n"
                f"Current price: {current_price:.4f}, Current candle evolution: {evolution:.2f}%\n"
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
    output_file = f"{datetime.now(pytz.UTC).strftime('%Y%m%d_%H%M%S')}_scan_results.txt"

    # Fetch and process symbols
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
