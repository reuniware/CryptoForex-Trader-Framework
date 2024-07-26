import ccxt
import sys
import os
import argparse
import time
from datetime import datetime, timezone
import pytz
import threading
import csv
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import joblib

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
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def save_history_to_file(symbol, timeframe, ohlcv):
    directory = "downloaded_history"
    if not os.path.exists(directory):
        os.makedirs(directory)

    if not ohlcv:
        print(f"No OHLCV data to save for {symbol}")
        return

    start_date = format_candle_time(ohlcv[0][0]).split()[0]
    end_date = format_candle_time(ohlcv[-1][0]).split()[0]
    filename = (f"{directory}/{symbol.replace('/', '_')}_{timeframe}_{start_date}_{end_date}.csv").replace(" ", "_").replace(":", "-")

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        for candle in ohlcv:
            timestamp, open_price, high_price, low_price, close_price, volume = candle
            writer.writerow([format_candle_time(timestamp), open_price, high_price, low_price, close_price, volume])

    print(f"Saved history to {filename}")

def load_data_from_files(directory, symbol_filter=None):
    all_data = []
    filenames = []
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            if symbol_filter and not filename.startswith(symbol_filter):
                continue  # Skip files that do not start with the symbol filter
            filepath = os.path.join(directory, filename)
            df = pd.read_csv(filepath)
            df['symbol'] = filename.split('_')[0]  # Adjust this if your filenames have different formats
            timeframe = filename.split('_')[1]  # Extract timeframe from filename
            df['Timeframe'] = timeframe
            all_data.append(df)
            filenames.append(filepath)
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame(), filenames

def preprocess_data(df):
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df.set_index('Timestamp', inplace=True)
    df.sort_index(inplace=True)
    df['Target'] = df['Close'].shift(-1)
    df.dropna(inplace=True)
    
    X = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    y = df['Target']
    
    return X, y

def train_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse**0.5
    print(f"Model trained. RMSE: {rmse:.4f}")
    
    return model, scaler

def predict_next_candle(model, scaler, data):
    data_scaled = scaler.transform(data[['Open', 'High', 'Low', 'Close', 'Volume']])
    prediction = model.predict(data_scaled)
    return prediction

def analyze_symbol(exchange, symbol, timeframe, output_file):
    try:
        ohlcv = fetch_ohlcv(exchange, symbol, timeframe)
        if not ohlcv:
            return

        save_history_to_file(symbol, timeframe, ohlcv)

        max_candle = max(ohlcv, key=lambda x: x[2] - x[3])
        open_price = max_candle[1]
        close_price = max_candle[4]
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

def write_predictions_to_file(output_file, predictions):
    with open(output_file, 'a') as f:
        for symbol, last_timestamp, timeframe, prediction in predictions:
            # Convert integer timestamp to datetime if needed
            if isinstance(last_timestamp, int):
                last_timestamp = datetime.fromtimestamp(last_timestamp / 1000, tz=timezone.utc)
            
            last_timestamp_str = last_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"Prediction for {symbol} ({timeframe}):\n")
            f.write(f"- Last Timestamp: {last_timestamp_str}\n")
            f.write(f"- Predicted Value: {prediction[-1]:.4f}\n")  # Show the last prediction value
            f.write("\n")

def worker(exchange, symbols, timeframe, output_file):
    for symbol in symbols:
        if symbol in fetch_markets(exchange):
            analyze_symbol(exchange, symbol, timeframe, output_file)
        else:
            print(f"Skipping invalid symbol {symbol}")

def main():
    parser = argparse.ArgumentParser(description='Show details of the greatest historical candle, save historical data, and train a model.')
    parser.add_argument('--timeframe', type=str, required=True, help='Timeframe for the candlestick analysis')
    parser.add_argument('--train', action='store_true', help='Train model using existing historical data')
    parser.add_argument('--use-existing', action='store_true', help='Use existing historical data files')
    args = parser.parse_args()

    timeframe = args.timeframe
    train_model_flag = args.train
    use_existing_flag = args.use_existing
    script_name = os.path.basename(__file__).split('.')[0]
    result_directory = f"scan_results_{script_name}"

    if not os.path.exists(result_directory):
        os.makedirs(result_directory)

    output_file = os.path.join(result_directory, f"{datetime.now(pytz.UTC).strftime('%Y%m%d_%H%M%S')}_{timeframe}_greatest_candles.txt")

    if train_model_flag:
        historical_data_dir = "downloaded_history"
        symbol_filter = 'BTC_USDT'  # Filter files that start with BTC_USDT
        df, filenames = load_data_from_files(historical_data_dir, symbol_filter)
        if df.empty:
            print("No historical data found for training.")
            return

        print("Training model using the following BTC-related files:")
        for filename in filenames:
            print(f"- {filename}")

        X, y = preprocess_data(df)
        if X.empty or y.empty:
            print("No valid data available for training.")
            return

        model, scaler = train_model(X, y)

        joblib.dump(model, 'model.pkl')
        joblib.dump(scaler, 'scaler.pkl')
        
    elif use_existing_flag:
        model = joblib.load('model.pkl')
        scaler = joblib.load('scaler.pkl')
        
        historical_data_dir = "downloaded_history"
        symbol_filter = 'BTC_USDT'  # Filter files that start with BTC_USDT
        df, filenames = load_data_from_files(historical_data_dir, symbol_filter)
        if df.empty:
            print("No historical data found for prediction.")
            return

        print("Using the following BTC-related files for prediction:")
        for filename in filenames:
            print(f"- {filename}")

        predictions = []
        for symbol in df['symbol'].unique():
            symbol_data = df[df['symbol'] == symbol]
            timeframe = symbol_data['Timeframe'].iloc[0]  # Get timeframe for prediction
            last_timestamp = symbol_data.index[-1]  # Get the last timestamp
            next_candle_prediction = predict_next_candle(model, scaler, symbol_data)
            predictions.append((symbol, last_timestamp, timeframe, next_candle_prediction))

        write_predictions_to_file(output_file, predictions)

    else:
        exchange = ccxt.binance()
        symbols = fetch_markets(exchange)
        worker(exchange, symbols, timeframe, output_file)

if __name__ == "__main__":
    main()
