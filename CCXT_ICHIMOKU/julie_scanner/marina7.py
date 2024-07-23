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
        # Fetch markets from the exchange
        markets = exchange.fetch_markets()
        # Apply the filter pattern to the symbols
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

def is_hammer_or_hanging_man(candle):
    open_price = candle[1]
    close_price = candle[4]
    high_price = candle[2]
    low_price = candle[3]
    body_size = abs(close_price - open_price)
    candle_range = high_price - low_price
    lower_wick_size = min(open_price, close_price) - low_price
    upper_wick_size = high_price - max(open_price, close_price)
    
    is_hammer = body_size / candle_range < 0.1 and lower_wick_size > 2 * body_size
    is_hanging_man = body_size / candle_range < 0.1 and upper_wick_size > 2 * body_size
    
    return is_hammer, is_hanging_man

def convert_to_tradingview_symbol(ccxt_symbol):
    # Convert the ccxt symbol format "BASE/QUOTE" to TradingView format "BINANCE:BASEQUOTE"
    base, quote = ccxt_symbol.split('/')
    return f"BINANCE:{base}{quote}"

def scan_and_display_assets(exchange, symbols, timeframe, output_file, current_candle_color_filter, prev_pattern_filter):
    # Get current time in Paris time zone
    paris_tz = pytz.timezone('Europe/Paris')
    current_time = datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S')
    header = f"Scan results at {current_time} (Paris time):\n"
    print(header.strip())
    
    limit = 2  # We need the last two candles to check for patterns
    for symbol in symbols:
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe, limit)
        if len(ohlcv) >= 2:
            prev_candle = ohlcv[-2]  # Previous candle
            current_candle = ohlcv[-1]  # Current candle
            
            # Check for Hammer or Hanging Man pattern in the previous candle
            is_prev_hammer, is_prev_hanging_man = is_hammer_or_hanging_man(prev_candle)
            
            # Determine the color of the current candle
            current_open = current_candle[1]
            current_close = current_candle[4]
            current_candle_color = "green" if current_close > current_open else "red"
            
            # Determine price evolution of the current candle
            evolution = ((current_close - current_open) / current_open) * 100
            
            # Apply filters
            if (current_candle_color_filter and current_candle_color != current_candle_color) or \
               (prev_pattern_filter == 'hammer' and not is_prev_hammer) or \
               (prev_pattern_filter == 'hanging-man' and not is_prev_hanging_man):
                continue
            
            # Determine trend context based on the previous candle
            trend_context = "Uptrend or Downtrend"  # Default message if no pattern filter is applied
            
            if prev_pattern_filter == 'hammer':
                trend_context = "Possible Uptrend" if is_prev_hammer else trend_context
            elif prev_pattern_filter == 'hanging-man':
                trend_context = "Possible Downtrend" if is_prev_hanging_man else trend_context
            
            result = (
                f"[{current_time}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                f"Previous candle: {'Hammer' if is_prev_hammer else 'Hanging Man' if is_prev_hanging_man else 'Not Hammer or Hanging Man'} ({trend_context}), "
                f"Current price: {current_close:.4f}, Current color: {current_candle_color}, "
                f"Price evolution: {evolution:.2f}%\n"
            )
            print(result.strip())
            with open(output_file, 'a') as f:
                f.write(result)
    
    print("Scan complete.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scan assets for current price, candlestick color, and previous pattern, with various filters.')
    parser.add_argument('--interval', type=int, default=600, help='Interval between scans in seconds.')
    parser.add_argument('--output', type=str, default='scan_results.txt', help='Output file for results.')
    parser.add_argument('--filter', type=str, default='*USDT', help='Filter pattern for symbols to scan (e.g., *USDT to scan only USDT pairs).')
    parser.add_argument('--timeframe', type=str, default='15m', help='Timeframe to scan (e.g., 1m, 5m, 15m, 1h).')
    parser.add_argument('--list-timeframes', action='store_true', help='List available timeframes and exit.')
    parser.add_argument('--candle-color', type=str, choices=['green', 'red'], help='Filter by current candle color (green or red).')
    parser.add_argument('--prev-pattern', choices=['hammer', 'hanging-man'], help='Filter to show only assets where the previous candlestick is a Hammer or Hanging Man.')
    args = parser.parse_args()

    exchange_name = "binance"  # Change to your exchange
    filter_pattern = args.filter
    timeframe = args.timeframe
    interval = args.interval
    output_file = args.output
    current_candle_color_filter = args.candle_color
    prev_pattern_filter = args.prev_pattern

    # Initialize the exchange
    exchange = getattr(ccxt, exchange_name)()

    if args.list_timeframes:
        print("Available timeframes:", ', '.join(exchange.timeframes))
        sys.exit(0)

    print("Fetching markets...")
    symbols = fetch_markets(exchange, filter_pattern)
    if not symbols:
        print(f"No symbols found for filter pattern {filter_pattern} in the spot market. Exiting.")
        sys.exit(-1)

    # Print the number of symbols to be scanned
    print(f"Number of symbols to be tracked: {len(symbols)}")

    while True:
        scan_and_display_assets(exchange, symbols, timeframe, output_file, current_candle_color_filter, prev_pattern_filter)
        print(f"Waiting for {interval} seconds before the next scan...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
