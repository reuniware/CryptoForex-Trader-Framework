#gitpod /workspace/Binance-and-FTX-API-Work/CCXT_ICHIMOKU/julie_scanner (main) $ python marina.py --interval 600 --output scan_results.txt --filter *usdt
#[2024-07-23 14:36:23] BTC/USDT (BINANCE:BTCUSDT) has a current candlestick that is red in the 15m timeframe.
#[2024-07-23 14:36:23] ETH/USDT (BINANCE:ETHUSDT) has a current candlestick that is green in the 15m timeframe.
#[2024-07-23 14:36:23] BNB/USDT (BINANCE:BNBUSDT) has a current candlestick that is green in the 15m timeframe.

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
    
    limit = 1  # We only need the current candlestick
    for symbol in symbols:
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe, limit)
        if ohlcv and len(ohlcv) == 1:
            # Check if the current candlestick is red or green
            current_candle = ohlcv[-1]
            is_current_candle_red = current_candle[1] > current_candle[4]
            is_current_candle_green = current_candle[1] < current_candle[4]
            
            if is_current_candle_red or is_current_candle_green:
                current_time = datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S')
                tradingview_symbol = convert_to_tradingview_symbol(symbol)
                
                color = "red" if is_current_candle_red else "green"
                result = f"[{current_time}] {symbol} ({tradingview_symbol}) has a current candlestick that is {color} in the 15m timeframe.\n"
                print(result.strip())
                with open(output_file, 'a') as f:
                    f.write(result)
    
    print("Scan complete.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scan assets for specific candlestick patterns.')
    parser.add_argument('--interval', type=int, default=600, help='Interval between scans in seconds.')
    parser.add_argument('--output', type=str, default='scan_results.txt', help='Output file for results.')
    parser.add_argument('--filter', type=str, default='*USDT', help='Filter pattern for symbols to scan (e.g., *USDT to scan only USDT pairs).')
    args = parser.parse_args()
    
    interval = args.interval
    output_file = args.output
    filter_pattern = args.filter

    exchange_name = "binance"  # Change to your exchange
    global filter_assets
    timeframe = '15m'          # 15-minute candlesticks

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
        scan_and_display_assets(exchange, symbols, timeframe, output_file)
        print(f"Waiting for {interval} seconds before the next scan...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
