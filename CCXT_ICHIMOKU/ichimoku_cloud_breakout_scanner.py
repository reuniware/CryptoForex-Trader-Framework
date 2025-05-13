# Ichimoku Scanner for Traders 2.0 (Inelida Scanner for Traders)
# Example of use : python ichimoku_cloud_breakout_scanner.py -e binance -f *USDT -tf 1d -up

import sys
import os
import ccxt
import pandas as pd
from datetime import datetime
import time
import threading
import ta
import argparse
import signal
#import beepy as beep
#import tweepy # Tweet functionality commented out for simplicity

# from datetime import date # Not used

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.expand_frame_repr', True)

enable_tweet = False # Disabled for this example


# def tweet(str_to_tweet):
#     if enable_tweet is False:
#         return
#     # ... (tweet function code) ...


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)


signal.signal(signal.SIGINT, signal_handler)


def log_to_errors(str_to_log):
    fr = open("errors.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_results(str_to_log):
    fr = open("results_cloud_breakouts.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()

# Removed unused log functions for brevity

def delete_results_log():
    if os.path.exists("results_cloud_breakouts.txt"):
        os.remove("results_cloud_breakouts.txt")


def delete_errors_log():
    if os.path.exists("errors.txt"):
        os.remove("errors.txt")

delete_errors_log()

exchanges = {}
for id_exchange in ccxt.exchanges:
    try:
        exchange_class = getattr(ccxt, id_exchange)
        exchanges[id_exchange] = exchange_class()
    except Exception:
        # print(f"Could not load exchange {id_exchange}")
        continue

# ... (get_number_of_active_assets_for_exchange function can be kept if needed, but not central to this change) ...

parser = argparse.ArgumentParser(description="Ichimoku Cloud Breakout Scanner")
parser.add_argument("-e", "--exchange", help="Set exchange (e.g., bybit, binance)", required=True)
parser.add_argument('-g', '--get-exchanges', action='store_true', help="Get list of available exchanges")
parser.add_argument('-a', '--get-assets', action='store_true', help="Get list of available assets for the specified exchange")
parser.add_argument('-f', '--filter-assets', help="Assets filter (e.g., *USDT, BTC*)")
parser.add_argument('-r', '--retry', action='store_true', help="Retry until exchange is available (again)")
parser.add_argument('-l', '--loop', action='store_true',
                    help="Scan in loop (useful for continually scan one asset or a few ones)")
parser.add_argument('-tf', '--timeframes',
                    help="The timeframe(s) to scan for Ichimoku cloud breakouts (separated by ',' if more than one, e.g., 1h,4h)", required=True)
parser.add_argument('-up', '--up', action='store_true', help="Scan for upward cloud breakouts (this is the primary mode for this script now)")
# parser.add_argument('-down', '--down', action='store_true', help="Scan for downward cloud breakouts (not implemented in this version)") # Kept for consistency, but not used

args = parser.parse_args()

print("Ichimoku Cloud Breakout Scanner")
print(f"Scan started at: {datetime.now()}")
print(f"Arguments: {args}")


if sys.gettrace() is not None: # Debugging defaults
    print("Debugger detected, using default arguments for testing.")
    args.exchange = "binance" # Changed to binance as bybit might need more setup for some users
    args.filter_assets = "*USDT"
    args.loop = False # Set to False for single run during debug
    args.timeframes = "1h" # Test with a single, common timeframe
    args.up = True
    # args.down = False # Not relevant for this version

if args.get_exchanges:
    print("Available exchanges:", ' '.join(ccxt.exchanges))
    sys.exit(0)

# Exchange initialization
exchange = None
if args.exchange:
    arg_exchange_l = args.exchange.lower().strip()
    if arg_exchange_l in exchanges:
        exchange = exchanges[arg_exchange_l]
        print(f"Using exchange: {exchange.id}")
    else:
        print(f"Error: Exchange '{args.exchange}' is not supported or could not be loaded.")
        print("Available exchanges:", ' '.join(ex for ex in exchanges.keys() if exchanges[ex])) # Show loaded exchanges
        sys.exit(-1)
else:
    if not args.get_exchanges: # if not just asking for list
        print("Error: No exchange specified. Use -e <exchange_name>.")
        sys.exit(-2)

if args.get_assets:
    if not exchange:
        print("Please specify an exchange with -e to list its assets.")
        sys.exit(-509)
    try:
        markets = exchange.fetch_markets()
        active_assets = [m['symbol'] for m in markets if m.get('active', True)] # Use symbol, not id
        print(f"Active assets on {exchange.id} ({len(active_assets)}):")
        print(' '.join(active_assets))
    except Exception as e:
        print(f"Could not fetch markets for {exchange.id}: {e}")
    sys.exit(0)


filter_assets = ""
if args.filter_assets:
    filter_assets = args.filter_assets.strip().upper()
    if ("*" in filter_assets and not filter_assets.startswith("*") and not filter_assets.endswith("*")) \
            or (filter_assets.count("*") > 1):
        print("Error: Only one '*' wildcard allowed, either at the start or at the end of the filter string.")
        sys.exit(-10004)

retry = args.retry
loop_scan = args.loop

array_tf = set()
if args.timeframes:
    x = args.timeframes.split(',')
    for tf_item in x:
        tf_item_stripped = tf_item.strip()
        if tf_item_stripped: # Ensure not empty string
             array_tf.add(tf_item_stripped)
    if not array_tf:
        print("Error: No valid timeframes provided.")
        sys.exit(-3)
else:
     print("Error: No timeframes specified. Use -tf <timeframe> (e.g., 1h,4h).")
     sys.exit(-3)

scan_up = args.up
# scan_down = args.down # Not used in this version

debug_delays = False
delay_thread = 0.05 # Adjusted for potentially faster/slower exchanges
delay_request = 0

# --- New/Modified Functions ---

def get_ohlcv_data(symbol, timeframe, limit=100): # Increased default limit slightly
    """Fetches OHLCV data for a symbol and timeframe."""
    if timeframe not in exchange.timeframes:
        # print(f"Warning: Timeframe {timeframe} not officially supported by {exchange.id} for {symbol}. Trying anyway.")
        # Some exchanges might still return data for unlisted timeframes
        pass # Allow attempting to fetch
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < 2: # Need at least 2 candles for previous/current
            # print(f"Not enough OHLCV data for {symbol} on {timeframe} (received {len(ohlcv) if ohlcv else 0}). Required >= 2.")
            return None
        return ohlcv
    except ccxt.NetworkError as e:
        print(f"NetworkError fetching {symbol} {timeframe}: {e}. Skipping.")
        log_to_errors(f"{datetime.now()} NetworkError: {symbol} {timeframe} {e}")
        return None
    except ccxt.ExchangeError as e:
        print(f"ExchangeError fetching {symbol} {timeframe}: {e}. Skipping.")
        log_to_errors(f"{datetime.now()} ExchangeError: {symbol} {timeframe} {e}")
        return None
    except Exception as e:
        print(f"Generic error fetching {symbol} {timeframe}: {e}. Skipping.")
        log_to_errors(f"{datetime.now()} GenericError: {symbol} {timeframe} {e}")
        return None

def check_cloud_breakout_up(symbol, timeframe):
    """
    Checks if the price just crossed above the Ichimoku cloud.
    Requires at least 78 candles (52 for SSB + 26 for projection).
    Using ta library, it needs enough data points for its window calculations.
    The default `limit` in `get_ohlcv_data` should be sufficient if it's around 100.
    The ta library itself will handle NaNs for initial periods.
    """
    ohlcv = get_ohlcv_data(symbol, timeframe, limit=52 + 26 + 2) # Ensure enough data for calc + prev/curr
    if not ohlcv:
        return False

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    if len(df) < 52 + 26 + 2: # Check again after DataFrame creation
        # print(f"DataFrame for {symbol} on {timeframe} has {len(df)} rows, less than required {52+26+2}.")
        return False

    # Calculate Ichimoku components
    # shift(26) is to project SSA/SSB into the future for standard plotting,
    # so df['ICH_SSA'].iloc[-1] is the cloud value for the current candle's time.
    try:
        df['ICH_SSA'] = ta.trend.ichimoku_a(df['high'], df['low'], window1=9, window2=26).shift(26)
        df['ICH_SSB'] = ta.trend.ichimoku_b(df['high'], df['low'], window2=26, window3=52).shift(26)
    except Exception as e:
        # print(f"Error calculating Ichimoku for {symbol} {timeframe}: {e}")
        return False

    # Drop NA rows that result from indicator calculations and shifts
    df.dropna(subset=['ICH_SSA', 'ICH_SSB', 'close'], inplace=True)
    if len(df) < 2: # Need at least current and previous candle after NaN drop
        # print(f"Not enough data points after Ichimoku calculation for {symbol} on {timeframe}.")
        return False

    # Current candle's data (latest complete candle)
    current_close = df['close'].iloc[-1]
    current_ssa = df['ICH_SSA'].iloc[-1]
    current_ssb = df['ICH_SSB'].iloc[-1]

    # Previous candle's data
    previous_close = df['close'].iloc[-2]
    previous_ssa = df['ICH_SSA'].iloc[-2] # Cloud values at the previous candle's time
    previous_ssb = df['ICH_SSB'].iloc[-2]

    # Condition 1: Current close is above the cloud
    current_above_cloud = current_close > current_ssa and current_close > current_ssb

    # Condition 2: Previous close was NOT strictly above the cloud (i.e., was inside or below)
    # This means previous_close <= max(previous_ssa, previous_ssb)
    previous_not_strictly_above_cloud = previous_close <= max(previous_ssa, previous_ssb)
    
    # print(f"Debug {symbol} {timeframe}: curr_close={current_close:.2f}, curr_ssa={current_ssa:.2f}, curr_ssb={current_ssb:.2f} -> above_cloud={current_above_cloud}")
    # print(f"Debug {symbol} {timeframe}: prev_close={previous_close:.2f}, prev_ssa={previous_ssa:.2f}, prev_ssb={previous_ssb:.2f} -> prev_not_above={previous_not_strictly_above_cloud}")


    if current_above_cloud and previous_not_strictly_above_cloud:
        return True
    return False

# --- Main Execution Logic ---
active_threads = []
threadLimiter = threading.BoundedSemaphore(10) # Default max threads, can be adjusted

def execute_scan_for_symbol(symbol, type_of_asset, exchange_id_str):
    global threadLimiter
    threadLimiter.acquire()
    try:
        # print(f"Scanning {symbol} ({type_of_asset}) on {exchange_id_str} across timeframes: {array_tf}")
        if scan_up: # Only proceed if -up flag is set
            for tf_to_check in array_tf:
                try:
                    if check_cloud_breakout_up(symbol, tf_to_check):
                        # Construct TradingView link
                        tv_symbol_suffix = ".P" if exchange_id_str.upper() == "BYBIT" and "PERP" in symbol.upper() else "" # Bybit perpetuals often .P
                        tv_symbol = symbol.replace("/", "") # BTC/USDT -> BTCUSDT for TradingView
                        
                        # Special handling for some exchanges if needed for TV links
                        if exchange_id_str.upper() == "KUCOIN":
                             tv_exchange_prefix = "KUCOIN" # Kucoin sometimes needs full prefix
                        elif exchange_id_str.upper() == "BINANCE" and ("USDⓈ-M" in type_of_asset or "COIN-M" in type_of_asset or ".P" in symbol.upper() or type_of_asset == "future"): # Binance futures
                             tv_exchange_prefix = "BINANCEPERP" # Or BINANCE
                             tv_symbol = symbol # Keep as is for futures like BTCUSDT.P
                        else:
                             tv_exchange_prefix = exchange_id_str.upper()

                        str_link = f"https://www.tradingview.com/chart/?symbol={tv_exchange_prefix}:{tv_symbol}{tv_symbol_suffix}"
                        
                        # Log result
                        current_time_str = str(datetime.now()).split('.')[0]
                        log_message = f"CLOUD BREAKOUT UP: {symbol} on {tf_to_check} at {current_time_str} - {str_link}"
                        print(log_message)
                        log_to_results(log_message)
                        # Optional: tweet(log_message)
                        break # Found a breakout on one TF, no need to check others for this symbol per iteration
                except Exception as e:
                    print(f"Error during scan for {symbol} on {tf_to_check}: {e}")
                    log_to_errors(f"{datetime.now()} ScanError: {symbol} {tf_to_check} {e}")
                
                if delay_request > 0: time.sleep(delay_request)

    except Exception as e:
        print(f"Outer error in execute_scan_for_symbol for {symbol}: {e}")
        log_to_errors(f"{datetime.now()} OuterScanError: {symbol} {e}")
    finally:
        threadLimiter.release()


def main_scan_loop():
    global threadLimiter

    # Adjust maxthreads based on exchange if needed (example from original)
    if exchange.id.lower() == "binance": maxthreads = 20 # Binance is generally robust
    elif exchange.id.lower() == "bybit": maxthreads = 15
    elif exchange.id.lower() == "ftx": maxthreads = 1 # FTX is gone, but kept as example
    else: maxthreads = 10
    threadLimiter = threading.BoundedSemaphore(maxthreads)
    print(f"Set maxthreads to {maxthreads} for {exchange.id}")

    delete_results_log()
    log_to_results(f"Cloud Breakout Scan Results at: {datetime.now()} for {exchange.id} on TFs: {', '.join(array_tf)}")

    markets_fetched_successfully = False
    while not markets_fetched_successfully:
        try:
            markets = exchange.fetch_markets()
            markets_fetched_successfully = True
            print(f"Fetched {len(markets)} markets from {exchange.id}")
        except (ccxt.ExchangeError, ccxt.NetworkError, ccxt.DDoSProtection) as e:
            print(f"Exchange error fetching markets: {e}. Retrying in 5s if -r is set.")
            if not retry:
                print("Will not retry. Exiting.")
                sys.exit(-777)
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error fetching markets: {e}")
            sys.exit(-778)

    while True: # Main loop for -l option
        threads = []
        processed_symbols_count = 0
        for market_data in markets:
            symbol = market_data['symbol'] # Use 'symbol' (e.g., BTC/USDT) consistently
            active = market_data.get('active', True) # Default to True if 'active' key is missing
            asset_type = market_data.get('type', 'unknown') # spot, future, option, etc.

            # Apply asset filter
            condition_ok = active
            if filter_assets:
                if filter_assets.startswith("*") and filter_assets.endswith("*"): # e.g. *BTC*
                     if len(filter_assets) > 2 : # more than just **
                        condition_ok = condition_ok and filter_assets.strip("*") in symbol.upper()
                     # else no specific filtering beyond active if it's just "**"
                elif filter_assets.startswith("*"): # e.g. *USDT
                    condition_ok = condition_ok and symbol.upper().endswith(filter_assets.replace("*", ""))
                elif filter_assets.endswith("*"): # e.g. BTC*
                    condition_ok = condition_ok and symbol.upper().startswith(filter_assets.replace("*", ""))
                else: # exact match
                    condition_ok = condition_ok and symbol.upper() == filter_assets
            
            if condition_ok:
                # print(f"Queueing scan for {symbol}")
                t = threading.Thread(target=execute_scan_for_symbol, args=(symbol, asset_type, exchange.id))
                threads.append(t)
                t.start()
                processed_symbols_count += 1
                if delay_thread > 0: time.sleep(delay_thread)
        
        print(f"Launched {processed_symbols_count} scan threads. Waiting for completion...")
        start_time = time.time()
        for tt in threads:
            tt.join()
        end_time = time.time()
        print(f"--- Scan cycle completed in {end_time - start_time:.2f} seconds ---")

        if not loop_scan:
            break
        else:
            print(f"Looping: waiting 60 seconds before next scan cycle...") # Add a delay for loop mode
            time.sleep(60)

    print(f"Scan finished at: {datetime.now()}")

if __name__ == "__main__":
    if not args.get_exchanges and not args.get_assets: # Only run main scan if not doing utility tasks
        main_scan_loop()
