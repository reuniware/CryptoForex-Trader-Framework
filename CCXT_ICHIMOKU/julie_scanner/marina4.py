#python marina4.py --timeframe 1h --scan-type green
#Fetching markets...
#Number of symbols to be tracked: 526
#Scan results at 2024-07-23 14:55:15 (Paris time):
#[2024-07-23 14:55:17] BNB/USDT (BINANCE:BNBUSDT) is currently green in the 1h timeframe. Price evolution: 0.6000 (0.10%)
#[2024-07-23 14:55:20] XLM/USDT (BINANCE:XLMUSDT) is currently green in the 1h timeframe. Price evolution: 0.0003 (0.29%)
#[2024-07-23 14:55:20] TRX/USDT (BINANCE:TRXUSDT) is currently green in the 1h timeframe. Price evolution: 0.0002 (0.15%)
#[2024-07-23 14:55:21] ICX/USDT (BINANCE:ICXUSDT) is currently green in the 1h timeframe. Price evolution: 0.0001 (0.06%)

#python marina4.py --timeframe 1h --scan-type red
#[2024-07-23 14:56:54] BTC/USDT (BINANCE:BTCUSDT) is currently red in the 1h timeframe. Price evolution: -206.0000 (-0.31%)
#[2024-07-23 14:56:54] ETH/USDT (BINANCE:ETHUSDT) is currently red in the 1h timeframe. Price evolution: -7.5900 (-0.22%)
#[2024-07-23 14:56:54] NEO/USDT (BINANCE:NEOUSDT) is currently red in the 1h timeframe. Price evolution: -0.0400 (-0.35%)
#[2024-07-23 14:56:55] QTUM/USDT (BINANCE:QTUMUSDT) is currently red in the 1h timeframe. Price evolution: -0.0070 (-0.26%)

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

def calculate_price_evolution(candle):
    # Calculate the price evolution of the current candlestick
    open_price = candle[1]  # Open price of the current candlestick
    close_price = candle[4] # Close price of the current candlestick
    evolution = close_price - open_price
    return evolution, ((evolution / open_price) * 100)

def scan_and_display_assets(exchange, symbols, timeframe, output_file, scan_type):
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
            
            if (scan_type == "red" and is_current_candle_red) or (scan_type == "green" and is_current_candle_green):
                # Calculate price evolution
                evolution, evolution_percent = calculate_price_evolution(current_candle)
                
                current_time = datetime.now(paris_tz).strftime('%Y-%m-%d %H:%M:%S')
                tradingview_symbol = convert_to_tradingview_symbol(symbol)
                
                color = "red" if is_current_candle_red else "green"
                result = (
                    f"[{current_time}] {symbol} ({tradingview_symbol}) is currently {color} in the {timeframe} timeframe. "
                    f"Price evolution: {evolution:.4f} ({evolution_percent:.2f}%)\n"
                )
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
    parser.add_argument('--timeframe', type=str, default='15m', help='Timeframe to scan (e.g., 1m, 5m, 15m, 1h).')
    parser.add_argument('--list-timeframes', action='store_true', help='List available timeframes and exit.')
    parser.add_argument('--scan-type', type=str, choices=['red', 'green'], required=True, help='Scan for red or green candlesticks.')
    args = parser.parse_args()

    exchange_name = "binance"  # Change to your exchange
    filter_pattern = args.filter
    timeframe = args.timeframe
    interval = args.interval
    output_file = args.output
    scan_type = args.scan_type

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
        scan_and_display_assets(exchange, symbols, timeframe, output_file, scan_type)
        print(f"Waiting for {interval} seconds before the next scan...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
