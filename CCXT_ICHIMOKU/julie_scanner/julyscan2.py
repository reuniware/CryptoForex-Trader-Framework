import ccxt
import sys
import os
import argparse

def fetch_markets(exchange, filter_assets):
    try:
        # Fetch markets from the exchange
        markets = exchange.fetch_markets()
        # Filter symbols based on the specified filter_assets criteria
        symbols = [market['symbol'] for market in markets if filter_assets in market['symbol']]
        return symbols
    except (ccxt.ExchangeError, ccxt.NetworkError, ccxt.DDoSProtection) as e:
        print(f"Exchange error: {str(e)}")
        os.kill(os.getpid(), 9)
        sys.exit(-999)

def fetch_ohlcv(exchange, symbol, timeframe, limit=10):
    try:
        return exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    except Exception as e:
        print(f"Error fetching OHLCV data for {symbol}: {str(e)}")
        return []

def calculate_percentage_change(data):
    if len(data) < 2:
        return None
    # Get the closing prices of the first and last candle
    initial_price = data[0][4]  # Closing price of the first candle
    latest_price = data[-1][4]  # Closing price of the last candle
    # Calculate percentage change
    percentage_change = ((latest_price - initial_price) / initial_price) * 100
    return percentage_change

def scan_and_display_assets(exchange, symbols, percentage_threshold, timeframe):
    for symbol in symbols:
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe)
        if ohlcv:
            percentage_change = calculate_percentage_change(ohlcv)
            if percentage_change is not None and percentage_change > percentage_threshold:
                print(f"{symbol} has increased by {percentage_change:.2f}% in the last 10 minutes.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scan assets for positive percentage change.')
    parser.add_argument('--percentage', type=float, default=0.0, help='Minimum percentage increase to show.')
    args = parser.parse_args()
    
    percentage_threshold = args.percentage

    exchange_name = "binance"  # Change to your exchange
    global filter_assets
    filter_assets = "USDT"     # Adjust the filter to match your needs
    timeframe = '1m'           # 1-minute candlesticks for checking last 10 minutes

    # Initialize the exchange
    exchange = getattr(ccxt, exchange_name)()

    symbols = fetch_markets(exchange, filter_assets)
    if not symbols:
        print(f"No symbols found for filter {filter_assets}. Exiting.")
        sys.exit(-1)

    print(f"Tracking symbols: {symbols}")

    scan_and_display_assets(exchange, symbols, percentage_threshold, timeframe)

if __name__ == "__main__":
    main()
