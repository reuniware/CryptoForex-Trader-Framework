#python julyscan6.py --percentage 0.0 --interval 5 --output scan_results.txt --filter *usdt --duration 120

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

def calculate_percentage_change(data):
    if len(data) < 2:
        return None, None
    # Get the closing prices of the first and last candle
    initial_price = data[0][4]  # Closing price of the first candle
    latest_price = data[-1][4]  # Closing price of the last candle
    # Calculate percentage change
    percentage_change = ((latest_price - initial_price) / initial_price) * 100
    return percentage_change, latest_price

def convert_to_tradingview_symbol(ccxt_symbol):
    # Convert the ccxt symbol format "BASE/QUOTE" to TradingView format "BINANCE:BASEQUOTE"
    base, quote = ccxt_symbol.split('/')
    return f"BINANCE:{base}{quote}"

def scan_and_display_assets(exchange, symbols, percentage_threshold, timeframe, duration, output_file):
    # Get current time in Paris time zone
    paris_tz = pytz.timezone('Europe/Paris')
    current_time = datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S')
    header = f"Scan results at {current_time} (Paris time):\n"
    print(header.strip())
    
    limit = duration
    for symbol in symbols:
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe, limit)
        if ohlcv:
            percentage_change, latest_price = calculate_percentage_change(ohlcv)
            if percentage_change is not None and percentage_change > percentage_threshold:
                current_time = datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S')
                tradingview_symbol = convert_to_tradingview_symbol(symbol)
                result = f"[{current_time}] {symbol} ({tradingview_symbol}) has increased by {percentage_change:.2f}% in the last {duration} minutes. Current price: {latest_price:.4f}\n"
                print(result.strip())
                
                with open(output_file, 'a') as f:
                    f.write(result)
    
    print("Scan complete.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scan assets for positive percentage change.')
    parser.add_argument('--percentage', type=float, default=0.0, help='Minimum percentage increase to show.')
    parser.add_argument('--interval', type=int, default=600, help='Interval between scans in seconds.')
    parser.add_argument('--output', type=str, default='scan_results.txt', help='Output file for results.')
    parser.add_argument('--filter', type=str, default='*USDT', help='Filter pattern for symbols to scan (e.g., *USDT to scan only USDT pairs).')
    parser.add_argument('--duration', type=int, default=10, help='Number of minutes to consider for the comparison of percentage change.')
    args = parser.parse_args()
    
    percentage_threshold = args.percentage
    interval = args.interval
    output_file = args.output
    filter_pattern = args.filter
    duration = args.duration

    exchange_name = "binance"  # Change to your exchange
    global filter_assets
    timeframe = '1m'           # 1-minute candlesticks for checking last 'duration' minutes

    # Initialize the exchange
    exchange = getattr(ccxt, exchange_name)()

    print("Fetching markets...")
    symbols = fetch_markets(exchange, filter_pattern)
    if not symbols:
        print(f"No symbols found for filter pattern {filter_pattern} in the spot market. Exiting.")
        sys.exit(-1)

    # Print the number of symbols to be scanned
    print(f"Number of symbols to be tracked: {len(symbols)}")

    while True:
        scan_and_display_assets(exchange, symbols, percentage_threshold, timeframe, duration, output_file)
        print(f"Waiting for {interval} seconds before the next scan...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
