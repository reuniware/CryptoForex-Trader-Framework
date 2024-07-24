#python bluewenne4.py --timeframe 1d
#[2024-07-24 19:45:33] REN/USDT (BINANCE:RENUSDT) Timeframe: 1d, Current price: 0.0489
#Symbol: REN/USDT, Timeframe: 1d, Open: 1.0935, Close: 0.9597, High: 1.1060, Low: 0.0151, Range: 1.0909, Greatest Candle DateTime: 2021-04-18 00:00:00
#[2024-07-24 19:45:34] CVP/USDT (BINANCE:CVPUSDT) Timeframe: 1d, Current price: 0.2349
#Symbol: CVP/USDT, Timeframe: 1d, Open: 1.6670, Close: 1.8090, High: 3.1370, Low: 1.5820, Range: 1.5550, Greatest Candle DateTime: 2021-10-30 00:00:00
#[2024-07-24 19:45:34] MINA/USDT (BINANCE:MINAUSDT) Timeframe: 1d, Current price: 0.5212
#Symbol: MINA/USDT, Timeframe: 1d, Open: 4.0080, Close: 5.7670, High: 5.8600, Low: 3.9330, Range: 1.9270, Greatest Candle DateTime: 2021-09-09 00:00:00
#[2024-07-24 19:45:35] DODO/USDT (BINANCE:DODOUSDT) Timeframe: 1d, Current price: 0.1170
#Symbol: DODO/USDT, Timeframe: 1d, Open: 2.7880, Close: 6.2250, High: 10.0000, Low: 2.7880, Range: 7.2120, Greatest Candle DateTime: 2021-02-19 00:00:00
#[2024-07-24 19:45:35] RVN/USDT (BINANCE:RVNUSDT) Timeframe: 1d, Current price: 0.0190
#Symbol: RVN/USDT, Timeframe: 1d, Open: 0.1453, Close: 0.2256, High: 0.2929, Low: 0.1389, Range: 0.1540, Greatest Candle DateTime: 2021-02-20 00:00:00

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

def analyze_symbol(exchange, symbol, timeframe, output_file):
    try:
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe)
        if not ohlcv:
            return

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
    parser = argparse.ArgumentParser(description='Show details of the greatest historical candle.')
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
