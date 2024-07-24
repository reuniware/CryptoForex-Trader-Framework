import ccxt
import sys
import os
import argparse
import time
from datetime import datetime
import pytz
import threading
import csv

def fetch_markets(exchange):
    try:
        markets = exchange.fetch_markets()
        symbols = [market['symbol'] for market in markets if market['spot'] and market['symbol'].endswith('/USDT')]
        return symbols
    except (ccxt.ExchangeError, ccxt.NetworkError, ccxt.DDoSProtection) as e:
        print(f"Exchange error: {str(e)}")
        os.kill(os.getpid(), 9)
        sys.exit(-999)

def fetch_ohlcv(exchange, symbol, timeframe, limit=1000):
    try:
        all_candles = []
        since = exchange.parse8601('2020-01-01T00:00:00Z')  # Start date can be adjusted
        while True:
            candles = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            if not candles:
                break
            all_candles.extend(candles)
            since = candles[-1][0] + 1
            if len(candles) < limit:
                break
        return all_candles
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

def save_history_to_file(symbol, timeframe, ohlcv):
    # Create the directory if it doesn't exist
    directory = "downloaded_history"
    if not os.path.exists(directory):
        os.makedirs(directory)

    if not ohlcv:
        print(f"No OHLCV data to save for {symbol}")
        return

    # Determine start and end dates
    start_date = format_candle_time(ohlcv[0][0]).split()[0]
    end_date = format_candle_time(ohlcv[-1][0]).split()[0]

    # Create a filename using the start and end dates, timeframe, and symbol
    filename = (f"{directory}/{symbol.replace('/', '_')}_{start_date}_{end_date}_{timeframe}.csv").replace(" ", "_").replace(":", "-")

    # Write the OHLCV data to a CSV file
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        for candle in ohlcv:
            timestamp, open_price, high_price, low_price, close_price, volume = candle
            writer.writerow([format_candle_time(timestamp), open_price, high_price, low_price, close_price, volume])

    print(f"Saved history to {filename}")

def analyze_symbol(exchange, symbol, timeframe, output_file):
    try:
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe)
        if not ohlcv:
            return

        # Save the history to a file
        save_history_to_file(symbol, timeframe, ohlcv)

        # Find the greatest candle
        max_candle = max(ohlcv, key=lambda x: x[2] - x[3])  # x[2] is high price, x[3] is low price
        open_price = max_candle[1]
        close_price = max_candle[4]  # Close price
        highest_price = max_candle[2]
        lowest_price = max_candle[3]
        timestamp = max_candle[0]
        candle_date_time = format_candle_time(timestamp)

        greatest_candle_info = (
            f"Symbol: {symbol}, Timeframe: {timeframe}, "
            f"Open: {open_price:.4f}, Close: {close_price:.4f}, "
            f"High: {highest_price:.4f}, Low: {lowest_price:.4f}, "
            f"Range: {highest_price - lowest_price:.4f}, "
            f"Greatest Candle DateTime: {candle_date_time}\n"
        )
        
        current_price = fetch_current_price(exchange, symbol)
        if current_price is None:
            return

        current_time = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
        result = (
            f"[{current_time}] {symbol} (BINANCE:{symbol.replace('/', '')}) "
            f"Timeframe: {timeframe}, Current price: {current_price:.4f}\n"
            f"{greatest_candle_info}\n"
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
    parser = argparse.ArgumentParser(description='Show details of the greatest historical candle and save historical data.')
    parser.add_argument('--timeframe', type=str, required=True, help='Timeframe for the candlestick analysis')
    args = parser.parse_args()

    timeframe = args.timeframe
    script_name = os.path.basename(__file__).split('.')[0]
    directory = f"scan_results_{script_name}"

    if not os.path.exists(directory):
        os.makedirs(directory)

    output_file = os.path.join(directory, f"{datetime.now(pytz.UTC).strftime('%Y%m%d_%H%M%S')}_{timeframe}_greatest_candles.txt")

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
