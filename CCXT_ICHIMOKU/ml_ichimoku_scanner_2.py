import os
import pandas as pd
import numpy as np
import argparse
from datetime import timedelta
from binance.client import Client
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import ta
import pytz

# Parse command-line arguments for timeframe
parser = argparse.ArgumentParser(description="Binance Trend Forecaster with adjustable timeframe")
parser.add_argument("--interval", type=str, default="4h",
                    choices=["1m","3m","5m","15m","30m","1h","4h","1d"],
                    help="Time interval for klines (e.g. '1h', '4h', '1d')")
args = parser.parse_args()

# Map user-friendly intervals to Binance API constants
interval_map = {
    "1m": Client.KLINE_INTERVAL_1MINUTE,
    "3m": Client.KLINE_INTERVAL_3MINUTE,
    "5m": Client.KLINE_INTERVAL_5MINUTE,
    "15m": Client.KLINE_INTERVAL_15MINUTE,
    "30m": Client.KLINE_INTERVAL_30MINUTE,
    "1h": Client.KLINE_INTERVAL_1HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR,
    "1d": Client.KLINE_INTERVAL_1DAY
}
interval = interval_map[args.interval]

# Function to log results to both console and file
def log_results(message, filename="predictions_results.txt"):
    print(message)
    with open(filename, "a") as f:
        f.write(message + "\n")

# Convert UTC timestamp to Europe/Paris timezone
def convert_to_paris_time(utc_time):
    paris_tz = pytz.timezone('Europe/Paris')
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    paris_time = utc_time.astimezone(paris_tz)
    return paris_time.strftime('%Y-%m-%d %H:%M:%S')

# Initialize Binance client
client = Client()

# Settings
result_file = f"predictions_results_{args.interval}.txt"

# Delete the results file if it exists for a fresh start
if os.path.exists(result_file):
    os.remove(result_file)

# Initialize result file header
with open(result_file, "w") as f:
    f.write("Asset,Time,Price,Prediction,UP_Price_Target,DN_Price_Target,UP_TP%,UP_SL%,DN_TP%,DN_SL%,Avg_Time_To_TP(h)\n")

# Get USDT-quoted trading symbols
symbols = [s['symbol'] for s in client.get_exchange_info()['symbols']
           if s['status']=='TRADING' and s['quoteAsset']=='USDT']

# Optimize take-profit / stop-loss function
def optimize_tp_sl(df, signals, side, pgrid, lgrid):
    best = (0, 0, -np.inf)
    prices = df['close'].values
    idxs = np.where(signals == side)[0]
    for tp in pgrid:
        for sl in lgrid:
            rets = []
            for i in idxs:
                entry = prices[i]
                for j in range(i+1, min(i+11, len(prices))):
                    ret = (prices[j] - entry) / entry if side == 1 else (entry - prices[j]) / entry
                    if ret >= tp or ret <= -sl:
                        rets.append(np.sign(ret) * min(abs(ret), max(tp, sl)))
                        break
            if rets:
                avg_ret = np.mean(rets)
                if avg_ret > best[2]:
                    best = (tp, sl, avg_ret)
    return best

def calculate_time_to_threshold(df, threshold=0.01, lookahead_bars=24):
    """
    Calculate how long it takes to cross a price change threshold.
    Returns time in hours.
    """
    n = len(df)
    times = np.full(n, np.nan)
    minutes_per_bar = (df.index[1] - df.index[0]).total_seconds() / 60

    for i in range(n):
        entry = df['close'].iat[i]
        target = entry * (1 + threshold)  # For long positions
        
        for k in range(1, lookahead_bars + 1):
            j = i + k
            if j >= n:
                break
            if df['close'].iat[j] >= target:
                times[i] = k * minutes_per_bar / 60  # Convert to hours
                break

    return times

# Main loop: process each symbol
for symbol in symbols:
    try:
        log_results(f"\n=== {symbol} ({args.interval}) ===", result_file)

        # Load or download historical data
        data_file = f"{symbol}_data_{args.interval}_full.csv"
        if os.path.exists(data_file):
            df = pd.read_csv(data_file, index_col=0, parse_dates=True)
            last_ts = df.index[-1]
            start = (last_ts + timedelta(**{
                'minutes':1 if args.interval=='1m' else 3 if args.interval=='3m' else 5 if args.interval=='5m' else 15 if args.interval=='15m' else 30 if args.interval=='30m' else 60 if args.interval=='1h' else 240 if args.interval=='4h' else 1440
            })).strftime("%d %B %Y %H:%M:%S")
            new = client.get_historical_klines(symbol, interval, start)
            if new:
                new_df = pd.DataFrame(new, columns=[
                    'timestamp','open','high','low','close','volume',
                    'close_time','quote_av','trades','tb_base_av','tb_quote_av','ignore'
                ])
                new_df = new_df[['timestamp','open','high','low','close','volume']].astype(float)
                new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], unit='ms')
                new_df.set_index('timestamp', inplace=True)
                df = pd.concat([df, new_df]).drop_duplicates()
                df.to_csv(data_file)
        else:
            klines = client.get_historical_klines(symbol, interval, "01 December 2021")
            df = pd.DataFrame(klines, columns=[
                'timestamp','open','high','low','close','volume',
                'close_time','quote_av','trades','tb_base_av','tb_quote_av','ignore'
            ])
            df = df[['timestamp','open','high','low','close','volume']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df.to_csv(data_file)

        # Compute technical indicators
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        df['macd'] = ta.trend.MACD(df['close']).macd()
        for s in [10, 20, 50, 100]:
            df[f'ema_{s}'] = df['close'].ewm(span=s).mean()
        for w in [10, 20, 50, 100]:
            df[f'sma_{w}'] = df['close'].rolling(window=w).mean()
        bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        df['bbw'] = (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
        df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14).adx()
        st = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'], window=14)
        df['st_k'] = st.stoch()
        df['st_d'] = st.stoch_signal()
        df['wr'] = ta.momentum.WilliamsRIndicator(df['high'], df['low'], df['close'], lbp=14).williams_r()
        df['cci'] = ta.trend.CCIIndicator(df['high'], df['low'], df['close'], window=20).cci()
        df['mom'] = df['close'] - df['close'].shift(10)
        ichi = ta.trend.IchimokuIndicator(df['high'], df['low'], window1=9, window2=26, window3=52)
        df['span_a'] = ichi.ichimoku_a()
        df['span_b'] = ichi.ichimoku_b()
        df.dropna(inplace=True)

        # Label signals based on Ichimoku cloud
        df['signal'] = np.select([
            (df['close'] > df['span_a']) & (df['close'] > df['span_b']),
            (df['close'] < df['span_a']) & (df['close'] < df['span_b'])
        ], [1, 0], default=-1)

        # Train/test split
        features = [c for c in df.columns if c not in ['open','high','low','close','volume','signal']]
        X, y = df[features], df['signal']
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, shuffle=False)
        model = RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42)
        model.fit(Xtr, ytr)
        ypr = model.predict(Xte)

        # Log classification report
        report = classification_report(yte, ypr, zero_division=0)
        log_results(f"Classification report for {symbol}:\n{report}", result_file)

        # Predict latest trend
        latest_df = X.iloc[-1:]
        trend_label = model.predict(latest_df)[0]

        # Convert timestamp to Paris time and fetch price
        pred_time_utc = df.index[-1]
        pred_time = convert_to_paris_time(pred_time_utc)
        current_price = df['close'].iloc[-1]
        trend_str = {1:'Uptrend', 0:'Downtrend', -1:'Neutral'}[trend_label]
        
        # Optimize TP/SL
        hist_sign = model.predict(X)
        pgrid = np.arange(0.01, 0.1, 0.01)
        lgrid = np.arange(0.01, 0.1, 0.01)
        up_tp, up_sl, _ = optimize_tp_sl(df, hist_sign, 1, pgrid, lgrid)
        dn_tp, dn_sl, _ = optimize_tp_sl(df, hist_sign, 0, pgrid, lgrid)

        # Calculate predicted price targets
        predicted_up_price = current_price * (1 + up_tp)
        predicted_dn_price = current_price * (1 - dn_tp)

        # Estimate time to reach TP (long positions only)
        time_to_tp = calculate_time_to_threshold(df, threshold=up_tp, lookahead_bars=24)
        avg_time_to_tp = np.nanmean(time_to_tp)  # Average in hours

        # Log results
        log_results(f"Time: {pred_time}, Price: {current_price:.4f}, Prediction: {trend_str}", result_file)
        log_results(f"UP Price Target: {predicted_up_price:.4f} (+{up_tp*100:.1f}%)", result_file)
        log_results(f"DN Price Target: {predicted_dn_price:.4f} (-{dn_tp*100:.1f}%)", result_file)
        log_results(f"Optimal UP TP/SL: +{up_tp*100:.1f}% / -{up_sl*100:.1f}%", result_file)
        log_results(f"Optimal DN TP/SL: +{dn_tp*100:.1f}% / -{dn_sl*100:.1f}%", result_file)
        log_results(f"Avg. Time to TP: {avg_time_to_tp:.1f} hours", result_file)

        # Write CSV line
        with open(result_file, "a") as f:
            f.write(f"{symbol},{pred_time},{current_price:.4f},{trend_str},"
                    f"{predicted_up_price:.4f},{predicted_dn_price:.4f},"
                    f"{up_tp*100:.1f},{up_sl*100:.1f},{dn_tp*100:.1f},{dn_sl*100:.1f},"
                    f"{avg_time_to_tp:.1f}\n")

    except Exception as e:
        log_results(f"Error processing {symbol}: {str(e)}", result_file)

# End of processing
log_results("\nAll assets processed.", result_file)
