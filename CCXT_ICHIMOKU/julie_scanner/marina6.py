#permet de détecter si la bougie précédente est un doji
#et si la bougie en cours est haussière ou baissière

#python marina6.py --timeframe 1d --prev-doji
#[2024-07-23 15:36:21] XZC/USDT (BINANCE:XZCUSDT) Previous candle: Doji, Current price: 4.4460, Current color: green, Price evolution: 2.28%
#[2024-07-23 15:36:21] USDT/BIDR (BINANCE:USDTBIDR) Previous candle: Doji, Current price: 15980.0000, Current color: green, Price evolution: 0.03%

#python marina6.py --timeframe 1d --prev-doji --candle-color green
#[2024-07-23 15:39:49] XZC/USDT (BINANCE:XZCUSDT) Previous candle: Doji, Current price: 4.4460, Current color: green, Price evolution: 2.28%
#[2024-07-23 15:39:49] USDT/BIDR (BINANCE:USDTBIDR) Previous candle: Doji, Current price: 15980.0000, Current color: green, Price evolution: 0.03%

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

def is_doji(candle):
    open_price = candle[1]
    close_price = candle[4]
    high_price = candle[2]
    low_price = candle[3]
    body_size = abs(close_price - open_price)
    candle_range = high_price - low_price
    return body_size / candle_range < 0.1  # Threshold for body size compared to candle range

def convert_to_tradingview_symbol(ccxt_symbol):
    # Convert the ccxt symbol format "BASE/QUOTE" to TradingView format "BINANCE:BASEQUOTE"
    base, quote = ccxt_symbol.split('/')
    return f"BINANCE:{base}{quote}"

def scan_and_display_assets(exchange, symbols, timeframe, output_file, current_candle_color_filter, prev_doji_filter):
    # Get current time in Paris time zone
    paris_tz = pytz.timezone('Europe/Paris')
    current_time = datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S')
    header = f"Scan results at {current_time} (Paris time):\n"
    print(header.strip())
    
    limit = 2  # We need the last two candles to check for a Doji and the current candle
    for symbol in symbols:
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe, limit)
        if len(ohlcv) >= 2:
            prev_candle = ohlcv[-2]  # Previous candle
            current_candle = ohlcv[-1]  # Current candle
            
            # Check if the previous candlestick is a Doji
            is_prev_doji = is_doji(prev_candle)
            
            # Determine the color of the current candle
            current_open = current_candle[1]
            current_close = current_candle[4]
            current_candle_color = "green" if current_close > current_open else "red"
            
            # Determine price evolution of the current candle
            evolution = ((current_close - current_open) / current_open) * 100
            
            # Apply filters
            if (current_candle_color_filter and current_candle_color != current_candle_color_filter) or \
               (prev_doji_filter and not is_prev_doji):
                continue
            
            result = (
                f"[{current_time}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                f"Previous candle: {'Doji' if is_prev_doji else 'Not Doji'}, "
                f"Current price: {current_close:.4f}, Current color: {current_candle_color}, "
                f"Price evolution: {evolution:.2f}%\n"
            )
            print(result.strip())
            with open(output_file, 'a') as f:
                f.write(result)
    
    print("Scan complete.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scan assets for current price, candlestick color, and previous Doji pattern, with various filters.')
    parser.add_argument('--interval', type=int, default=600, help='Interval between scans in seconds.')
    parser.add_argument('--output', type=str, default='scan_results.txt', help='Output file for results.')
    parser.add_argument('--filter', type=str, default='*USDT', help='Filter pattern for symbols to scan (e.g., *USDT to scan only USDT pairs).')
    parser.add_argument('--timeframe', type=str, default='15m', help='Timeframe to scan (e.g., 1m, 5m, 15m, 1h).')
    parser.add_argument('--list-timeframes', action='store_true', help='List available timeframes and exit.')
    parser.add_argument('--candle-color', type=str, choices=['green', 'red'], help='Filter by current candle color (green or red).')
    parser.add_argument('--prev-doji', action='store_true', help='Filter to show only assets where the previous candlestick is a Doji.')
    args = parser.parse_args()

    exchange_name = "binance"  # Change to your exchange
    filter_pattern = args.filter
    timeframe = args.timeframe
    interval = args.interval
    output_file = args.output
    current_candle_color_filter = args.candle_color
    prev_doji_filter = args.prev_doji

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
        scan_and_display_assets(exchange, symbols, timeframe, output_file, current_candle_color_filter, prev_doji_filter)
        print(f"Waiting for {interval} seconds before the next scan...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
