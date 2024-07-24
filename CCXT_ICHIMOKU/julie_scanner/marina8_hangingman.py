#python marina8_hangingman.py --timeframe 15m
#Fetching markets...
#Number of symbols to be tracked: 526
#Scan results at 2024-07-23 18:23:45 (Paris time):
#[2024-07-23 18:23:45] ETH/USDT (BINANCE:ETHUSDT) Previous candle (Hanging Man) Date: 2024-07-23 16:00:00, Current price: 3466.8000, Current color: green, Price evolution: 0.39%
#[2024-07-23 18:23:45] TUSD/USDT (BINANCE:TUSDUSDT) Previous candle (Hanging Man) Date: 2024-07-23 16:00:00, Current price: 0.9996, Current color: red, Price evolution: -0.01%

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

def is_hanging_man(candle):
    open_price = candle[1]
    close_price = candle[4]
    high_price = candle[2]
    low_price = candle[3]
    body_size = abs(close_price - open_price)
    candle_range = high_price - low_price
    lower_wick_size = min(open_price, close_price) - low_price
    
    if candle_range == 0:
        return False
    
    is_hanging_man = body_size / candle_range < 0.1 and lower_wick_size > 2 * body_size
    return is_hanging_man

def is_tradable(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        # Check if the market has a valid ask price, indicating it is tradable
        return ticker.get('ask') is not None
    except Exception as e:
        print(f"Error checking tradability for {symbol}: {str(e)}")
        return False

def convert_to_tradingview_symbol(ccxt_symbol):
    # Convert the ccxt symbol format "BASE/QUOTE" to TradingView format "BINANCE:BASEQUOTE"
    base, quote = ccxt_symbol.split('/')
    return f"BINANCE:{base}{quote}"

def scan_and_display_assets(exchange, symbols, timeframe, output_file):
    # Get current time in Paris time zone
    paris_tz = pytz.timezone('Europe/Paris')
    current_time = datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S')

    header = f"Scan results at {current_time} (Paris time):\n"
    print(header.strip())
    
    limit = 2  # We need the last two candles to check for patterns
    for symbol in symbols:
        # Check if the asset is tradable
        if not is_tradable(exchange, symbol):
            continue
        
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe, limit)
        if len(ohlcv) >= 2:
            prev_candle = ohlcv[-2]  # Previous candle
            current_candle = ohlcv[-1]  # Current candle
            
            # Check for Hanging Man pattern in the previous candle
            if is_hanging_man(prev_candle):
                # Determine the color of the current candle
                current_open = current_candle[1]
                current_close = current_candle[4]
                current_candle_color = "green" if current_close > current_open else "red"
                
                # Determine price evolution of the current candle
                evolution = ((current_close - current_open) / current_open) * 100
                
                result = (
                    f"[{current_time}] {symbol} ({convert_to_tradingview_symbol(symbol)}) "
                    f"Previous candle (Hanging Man) Date: {datetime.fromtimestamp(prev_candle[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')}, "
                    f"Current price: {current_close:.4f}, Current color: {current_candle_color}, "
                    f"Price evolution: {evolution:.2f}%\n"
                )
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result)
    
    print("Scan complete.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scan assets for the Hanging Man pattern in the previous candlestick.')
    parser.add_argument('--interval', type=int, default=600, help='Interval between scans in seconds.')
    parser.add_argument('--output', type=str, default='scan_results.txt', help='Output file for results.')
    parser.add_argument('--filter', type=str, default='*USDT', help='Filter pattern for symbols to scan (e.g., *USDT to scan only USDT pairs).')
    parser.add_argument('--timeframe', type=str, default='15m', help='Timeframe to scan (e.g., 1m, 5m, 15m, 1h).')
    parser.add_argument('--list-timeframes', action='store_true', help='List available timeframes and exit.')
    args = parser.parse_args()

    exchange_name = "binance"  # Change to your exchange
    filter_pattern = args.filter
    timeframe = args.timeframe
    interval = args.interval
    output_file = args.output

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
        scan_and_display_assets(exchange, symbols, timeframe, output_file)
        print(f"Waiting for {interval} seconds before the next scan...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
