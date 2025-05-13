import os
import pandas as pd
import numpy as np
import argparse
from datetime import timedelta
from binance.client import Client
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import ta
import pytz
import traceback

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Binance Ichimoku Trend Forecaster with adjustable timeframe and prediction horizon")
parser.add_argument("--interval", type=str, default="4h",
                    choices=["1m","3m","5m","15m","30m","1h","4h","1d"],
                    help="Time interval for klines (e.g. '1h', '4h', '1d')")
parser.add_argument("--predict_horizon", type=int, default=5,
                    help="How many bars into the future to predict the Ichimoku signal (default: 5)")
parser.add_argument("--history_start", type=str, default="01 January 2021",
                    help="Start date for fetching historical data (e.g., '01 January 2021')")
args = parser.parse_args()

interval_map = {
    "1m": Client.KLINE_INTERVAL_1MINUTE, "3m": Client.KLINE_INTERVAL_3MINUTE,
    "5m": Client.KLINE_INTERVAL_5MINUTE, "15m": Client.KLINE_INTERVAL_15MINUTE,
    "30m": Client.KLINE_INTERVAL_30MINUTE, "1h": Client.KLINE_INTERVAL_1HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR, "1d": Client.KLINE_INTERVAL_1DAY
}
BINANCE_INTERVAL = interval_map[args.interval]
PREDICTION_HORIZON = args.predict_horizon
HISTORY_START_DATE = args.history_start

def log_results(message, filename="ichimoku_rf_predictions_results.txt"):
    print(message)
    with open(filename, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def convert_to_paris_time(utc_time_input):
    paris_tz = pytz.timezone('Europe/Paris')
    if isinstance(utc_time_input, pd.Timestamp):
        utc_time_aware = utc_time_input.tz_localize('UTC') if utc_time_input.tzinfo is None else utc_time_input.tz_convert('UTC')
    else: 
        utc_time_aware = pytz.utc.localize(utc_time_input) if utc_time_input.tzinfo is None else utc_time_input.astimezone(pytz.utc)
    return utc_time_aware.astimezone(paris_tz).strftime('%Y-%m-%d %H:%M:%S')

client = Client()
RESULT_FILENAME_BASE = f"ichimoku_rf_predictions_{args.interval}_h{PREDICTION_HORIZON}.txt"
if os.path.exists(RESULT_FILENAME_BASE): os.remove(RESULT_FILENAME_BASE)
with open(RESULT_FILENAME_BASE, "w", encoding="utf-8") as f:
    f.write(f"Asset,Time,Current_Price,Current_Ichimoku_Signal,Predicted_Future_Signal_In_{PREDICTION_HORIZON}Bars,UP_Price_Target,DN_Price_Target,UP_TP%,UP_SL%,DN_TP%,DN_SL%,Avg_Time_To_TP(h)\n")

try:
    exchange_info = client.get_exchange_info()
    symbols = [s['symbol'] for s in exchange_info['symbols']
               if s['status'] == 'TRADING' and s['quoteAsset'] == 'USDT' and not any(suffix in s['symbol'] for suffix in ['UPUSDT', 'DOWNUSDT', 'BEARUSDT', 'BULLUSDT', 'HALF', 'EDGE', 'LEVERAGED'])]
    # symbols = ['BTCUSDT', 'ETHUSDT'] 
except Exception as e:
    log_results(f"Error fetching exchange info: {e}", RESULT_FILENAME_BASE)
    symbols = ['BTCUSDT', 'ETHUSDT'] 

def get_timedelta_for_interval(interval_str):
    if interval_str.endswith('m'): return timedelta(minutes=int(interval_str[:-1]))
    if interval_str.endswith('h'): return timedelta(hours=int(interval_str[:-1]))
    if interval_str.endswith('d'): return timedelta(days=int(interval_str[:-1]))
    return timedelta(minutes=1)

def optimize_tp_sl(df_optimize, signals_optimize, side, pgrid, lgrid, lookahead=10):
    best_tp, best_sl, max_avg_ret = 0.01, 0.01, -np.inf
    if df_optimize.empty or not isinstance(signals_optimize, (np.ndarray, pd.Series)) or not len(signals_optimize): return best_tp, best_sl, 0
    prices_optimize = df_optimize['close'].values
    if isinstance(signals_optimize, pd.Series): signals_optimize = signals_optimize.values
    signal_indices = np.where(signals_optimize == side)[0]
    if not signal_indices.size: return best_tp, best_sl, 0
    for tp_pct in pgrid:
        for sl_pct in lgrid:
            if sl_pct <= 0: continue
            current_trades_returns = []
            for i in signal_indices:
                if i + lookahead >= len(prices_optimize): continue
                entry_price = prices_optimize[i]
                outcome_achieved = False
                for k in range(1, lookahead + 1):
                    current_price = prices_optimize[i + k]
                    ret_val = (current_price - entry_price) / entry_price if side == 1 else (entry_price - current_price) / entry_price
                    if ret_val >= tp_pct: current_trades_returns.append(tp_pct); outcome_achieved = True; break
                    elif ret_val <= -sl_pct: current_trades_returns.append(-sl_pct); outcome_achieved = True; break
                if not outcome_achieved:
                    final_price = prices_optimize[i + lookahead]
                    final_ret = (final_price - entry_price) / entry_price if side == 1 else (entry_price - final_price) / entry_price
                    current_trades_returns.append(final_ret)
            if current_trades_returns:
                avg_ret = np.mean(current_trades_returns)
                if avg_ret > max_avg_ret: max_avg_ret, best_tp, best_sl = avg_ret, tp_pct, sl_pct
    return best_tp, best_sl, max_avg_ret if max_avg_ret > -np.inf else 0

def calculate_time_to_threshold(df_calc, threshold_pct=0.01, lookahead_bars_calc=24):
    n_calc = len(df_calc)
    times_to_tp = np.full(n_calc, np.nan)
    if n_calc < 2: return times_to_tp
    df_calc_no_duplicates = df_calc[~df_calc.index.duplicated(keep='first')] if df_calc.index.has_duplicates else df_calc
    if len(df_calc_no_duplicates) < 2: return times_to_tp
    if not df_calc_no_duplicates.index.is_monotonic_increasing: df_calc_no_duplicates = df_calc_no_duplicates.sort_index()
    if len(df_calc_no_duplicates) < 2: return times_to_tp
    minutes_per_bar = (df_calc_no_duplicates.index[1] - df_calc_no_duplicates.index[0]).total_seconds() / 60
    for i in range(n_calc - lookahead_bars_calc):
        entry_price_calc = df_calc['close'].iat[i]
        target_price_up = entry_price_calc * (1 + threshold_pct)
        for k_calc in range(1, lookahead_bars_calc + 1):
            if df_calc['high'].iat[i + k_calc] >= target_price_up:
                times_to_tp[i] = k_calc * minutes_per_bar / 60; break
    return times_to_tp

# Main loop
for symbol in symbols:
    try:
        log_results(f"\n=== {symbol} ({args.interval}, Horizon: {PREDICTION_HORIZON}) ===", RESULT_FILENAME_BASE)
        data_file = f"{symbol}_data_{args.interval}_full.csv"; df = pd.DataFrame()
        if os.path.exists(data_file):
            try: df = pd.read_csv(data_file, index_col=0, parse_dates=True)
            except Exception: df = pd.DataFrame()
        if not df.empty:
            last_ts = df.index[-1]; start_delta = get_timedelta_for_interval(args.interval)
            start_str = (last_ts + start_delta).strftime("%d %b %Y %H:%M:%S")
            new_klines = client.get_historical_klines(symbol, BINANCE_INTERVAL, start_str)
            if new_klines:
                new_df_data = [[float(k) for k in d[:6]] for d in new_klines]
                new_df = pd.DataFrame(new_df_data, columns=['timestamp','open','high','low','close','volume'])
                new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], unit='ms')
                new_df.set_index('timestamp', inplace=True)
                df = pd.concat([df, new_df]); df = df[~df.index.duplicated(keep='last')]; df.sort_index(inplace=True)
                df.to_csv(data_file)
        if df.empty:
            klines = client.get_historical_klines(symbol, BINANCE_INTERVAL, HISTORY_START_DATE)
            if not klines: log_results(f"No data for {symbol} from {HISTORY_START_DATE}. Skip.", RESULT_FILENAME_BASE); continue
            df_data = [[float(k) for k in d[:6]] for d in klines]
            df = pd.DataFrame(df_data, columns=['timestamp','open','high','low','close','volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True); df = df[~df.index.duplicated(keep='first')]; df.sort_index(inplace=True)
            df.to_csv(data_file)

        if len(df) < 200: log_results(f"Need 200 bars for {symbol}, got {len(df)}. Skip.", RESULT_FILENAME_BASE); continue

        # 1. Compute Ichimoku Components
        ichi_params = {'high': df['high'], 'low': df['low'], 'window1': 9, 'window2': 26, 'window3': 52}
        df['tenkan_sen'] = ta.trend.ichimoku_conversion_line(df['high'], df['low'], window1=9, window2=26) # Plus précis pour ta.trend
        df['kijun_sen'] = ta.trend.ichimoku_base_line(df['high'], df['low'], window1=9, window2=26)     # Plus précis pour ta.trend
        df['span_a'] = ta.trend.ichimoku_a(df['high'], df['low'], window1=9, window2=26)                 # Utilise les méthodes directes
        df['span_b'] = ta.trend.ichimoku_b(df['high'], df['low'], window2=26, window3=52)                # Utilise les méthodes directes

        # --- CALCUL MANUEL DU CHIKOU SPAN (inspiré du scanner Inelida) ---
        df['chikou_span'] = df['close'].shift(-26)
        # --- FIN DU CALCUL MANUEL ---

        df['ichimoku_current_signal'] = np.select(
            [(df['close'] > df['span_a']) & (df['close'] > df['span_b']) & (df['tenkan_sen'] > df['kijun_sen']),
             (df['close'] < df['span_a']) & (df['close'] < df['span_b']) & (df['tenkan_sen'] < df['kijun_sen'])],
            [1, 0], default=-1)
        df['target_future_signal'] = df['ichimoku_current_signal'].shift(-PREDICTION_HORIZON)
        
        price_lagged26 = df['close'].shift(26)
        span_a_lagged26 = df['span_a'].shift(26) 
        span_b_lagged26 = df['span_b'].shift(26)

        df['feat_price_above_cloud'] = ((df['close'] > df['span_a']) & (df['close'] > df['span_b'])).astype(int)
        df['feat_price_below_cloud'] = ((df['close'] < df['span_a']) & (df['close'] < df['span_b'])).astype(int)
        df['feat_tk_cross_bull'] = (df['tenkan_sen'] > df['kijun_sen']).astype(int)
        df['feat_tk_cross_bear'] = (df['tenkan_sen'] < df['kijun_sen']).astype(int)
        df['feat_price_above_ks'] = (df['close'] > df['kijun_sen']).astype(int)
        df['feat_price_above_ts'] = (df['close'] > df['tenkan_sen']).astype(int)
        df['feat_chikou_above_price_lagged'] = (df['chikou_span'] > price_lagged26).astype(int)
        df['feat_chikou_above_cloud_lagged'] = ((df['chikou_span'] > span_a_lagged26) & (df['chikou_span'] > span_b_lagged26)).astype(int)
        
        # Drop NaNs APRES que toutes les features dépendant de shifts soient calculées
        # La colonne 'chikou_span' (shift -26) et 'target_future_signal' (shift -HORIZON) introduiront des NaNs à la fin.
        # Les Spans A/B (projetés) et Tenkan/Kijun introduiront des NaNs au début.
        # Les features 'lagged' (shift +26) introduiront des NaNs au début.
        # Il faut donc un dropna global à la fin.
        df.dropna(inplace=True) # Drop toutes les lignes avec au moins un NaN après tous les calculs

        if len(df) < 100: log_results(f"Need 100 bars post-Ichimoku/feats/dropna for {symbol}. Got {len(df)}. Skip.", RESULT_FILENAME_BASE); continue

        base_features = ['tenkan_sen', 'kijun_sen', 'span_a', 'span_b', 'chikou_span', 'ichimoku_current_signal']
        relative_features = []
        df['price_vs_span_a'] = (df['close'] - df['span_a']) / df['span_a'].replace(0, 1e-9) # Avoid DivByZero
        df['price_vs_span_b'] = (df['close'] - df['span_b']) / df['span_b'].replace(0, 1e-9)
        df['tenkan_vs_kijun'] = (df['tenkan_sen'] - df['kijun_sen']) / df['kijun_sen'].replace(0, 1e-9)
        relative_features.extend(['price_vs_span_a', 'price_vs_span_b', 'tenkan_vs_kijun'])
        new_bool_features = ['feat_price_above_cloud', 'feat_price_below_cloud', 'feat_tk_cross_bull', 'feat_tk_cross_bear',
                             'feat_price_above_ks', 'feat_price_above_ts', 'feat_chikou_above_price_lagged', 'feat_chikou_above_cloud_lagged']
        features = base_features + relative_features + new_bool_features
        df.replace([np.inf, -np.inf], np.nan, inplace=True) # Au cas où 1e-9 ne suffirait pas
        df.dropna(subset=features + ['target_future_signal'], inplace=True) # Un dernier drop pour les features spécifiques

        if len(df) < 50: log_results(f"Need 50 bars post-all-features/dropna for {symbol}. Got {len(df)}. Skip.", RESULT_FILENAME_BASE); continue

        X = df[features]; y = df['target_future_signal'].astype(int)
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, shuffle=False)

        if len(Xtr) < 20 or len(Xte) < 10: log_results(f"Need more split data for {symbol}. Skip.", RESULT_FILENAME_BASE); continue

        model = RandomForestClassifier(n_estimators=150, max_depth=12, min_samples_split=15, 
                                     min_samples_leaf=8, class_weight='balanced_subsample', 
                                     random_state=42, n_jobs=-1)
        model.fit(Xtr, ytr)
        ypr_train, ypr_test = model.predict(Xtr), model.predict(Xte)
        train_accuracy, test_accuracy = accuracy_score(ytr, ypr_train), accuracy_score(yte, ypr_test)

        log_results(f"Train Accuracy for {symbol}: {train_accuracy:.4f}", RESULT_FILENAME_BASE)
        log_results(f"Test Accuracy for {symbol}: {test_accuracy:.4f}", RESULT_FILENAME_BASE)
        if train_accuracy > test_accuracy + 0.15: log_results(f"WARNING: Overfitting for {symbol}?", RESULT_FILENAME_BASE)
        
        # Classification Report Logic
        try:
            unique_labels_in_data = np.unique(np.concatenate((yte, ypr_test)))
            target_names_for_report = [str(label) for label in unique_labels_in_data]
            report_test = classification_report(yte, ypr_test, labels=unique_labels_in_data, target_names=target_names_for_report, zero_division=0)
            log_results(f"Test Classification Report for {symbol}:\n{report_test}", RESULT_FILENAME_BASE)
        except ValueError as ve:
            log_results(f"Could not generate classification report for {symbol} (อาจมีป้ายกำกับที่ไม่สอดคล้องกัน): {ve}. y_true unique: {np.unique(yte)}, y_pred unique: {np.unique(ypr_test)}", RESULT_FILENAME_BASE)
            # Fallback to basic report if detailed one fails
            report_test_fallback = classification_report(yte, ypr_test, zero_division=0)
            log_results(f"Fallback Test Classification Report for {symbol}:\n{report_test_fallback}", RESULT_FILENAME_BASE)
        except Exception as e_rep: # Catch any other report error
            log_results(f"Generic error generating classification report for {symbol}: {e_rep}", RESULT_FILENAME_BASE)


        importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
        log_results(f"Feature Importances for {symbol}:\n{importances.to_string()}", RESULT_FILENAME_BASE)

        latest_features_df = X.iloc[-1:]; current_price = df['close'].iloc[-1]
        predicted_future_trend_label = model.predict(latest_features_df)[0]
        current_ichimoku_label = df['ichimoku_current_signal'].iloc[-1]
        pred_time_paris = convert_to_paris_time(df.index[-1])

        trend_map = {1:'Future Bullish', 0:'Future Bearish', -1:'Future Neutral'}
        current_trend_map = {1:'Current Bullish', 0:'Current Bearish', -1:'Current Neutral'}
        predicted_future_trend_str = trend_map.get(predicted_future_trend_label, f"Unknown ({predicted_future_trend_label})")
        current_ichimoku_str = current_trend_map.get(current_ichimoku_label, f"Unknown ({current_ichimoku_label})")
        
        up_tp_pct_opt, up_sl_pct_opt, dn_tp_pct_opt, dn_sl_pct_opt = 0.02, 0.01, 0.02, 0.01; avg_time_to_tp_val = np.nan
        if len(Xtr) >= 50:
            pgrid, lgrid = np.arange(0.01, 0.06, 0.01), np.arange(0.005, 0.04, 0.005)
            train_df_for_opt = df.loc[Xtr.index].copy()
            if not train_df_for_opt.empty:
                temp_up_tp, temp_up_sl, _ = optimize_tp_sl(train_df_for_opt, ytr, 1, pgrid, lgrid, PREDICTION_HORIZON + 5)
                if temp_up_tp > 0 and temp_up_sl > 0 : up_tp_pct_opt, up_sl_pct_opt = temp_up_tp, temp_up_sl
                temp_dn_tp, temp_dn_sl, _ = optimize_tp_sl(train_df_for_opt, ytr, 0, pgrid, lgrid, PREDICTION_HORIZON + 5)
                if temp_dn_tp > 0 and temp_dn_sl > 0 : dn_tp_pct_opt, dn_sl_pct_opt = temp_dn_tp, temp_dn_sl
                if predicted_future_trend_label == 1 and up_tp_pct_opt > 0:
                    df_for_time_calc = df.loc[:Xtr.index[-1]] if not Xtr.empty else df
                    times_to_tp_hist = calculate_time_to_threshold(df_for_time_calc, up_tp_pct_opt, PREDICTION_HORIZON * 3)
                    avg_time_to_tp_val = np.nanmean(times_to_tp_hist)

        predicted_up_price, predicted_dn_price = current_price * (1 + up_tp_pct_opt), current_price * (1 - dn_tp_pct_opt)
        log_results(f"Time: {pred_time_paris}, Price: {current_price:.6f}", RESULT_FILENAME_BASE)
        log_results(f"Current Ichimoku State: {current_ichimoku_str}", RESULT_FILENAME_BASE)
        log_results(f"Predicted Signal in {PREDICTION_HORIZON} bars: {predicted_future_trend_str}", RESULT_FILENAME_BASE)
        
        csv_up_target, csv_dn_target = '', ''; csv_up_tp, csv_up_sl = f"{up_tp_pct_opt*100:.1f}", f"{up_sl_pct_opt*100:.1f}"
        csv_dn_tp, csv_dn_sl = f"{dn_tp_pct_opt*100:.1f}", f"{dn_sl_pct_opt*100:.1f}"
        if predicted_future_trend_label == 1:
            log_results(f"UP Price Target: {predicted_up_price:.6f} (+{up_tp_pct_opt*100:.1f}%)", RESULT_FILENAME_BASE)
            log_results(f"Optimal UP TP/SL: +{up_tp_pct_opt*100:.1f}% / -{up_sl_pct_opt*100:.1f}%", RESULT_FILENAME_BASE)
            csv_up_target = f"{predicted_up_price:.6f}"
        elif predicted_future_trend_label == 0:
            log_results(f"DN Price Target: {predicted_dn_price:.6f} (-{(dn_tp_pct_opt)*100:.1f}%)", RESULT_FILENAME_BASE)
            log_results(f"Optimal DN TP/SL: +{dn_tp_pct_opt*100:.1f}% / -{dn_sl_pct_opt*100:.1f}%", RESULT_FILENAME_BASE)
            csv_dn_target = f"{predicted_dn_price:.6f}"
        avg_time_to_tp_str = f"{avg_time_to_tp_val:.1f}" if not np.isnan(avg_time_to_tp_val) else ''
        log_results(f"Avg. Time to TP: {avg_time_to_tp_str} hours", RESULT_FILENAME_BASE)
        with open(RESULT_FILENAME_BASE, "a", encoding="utf-8") as f:
            f.write(f"{symbol},{pred_time_paris},{current_price:.6f},{current_ichimoku_str},{predicted_future_trend_str},"
                    f"{csv_up_target},{csv_dn_target},{csv_up_tp},{csv_up_sl},{csv_dn_tp},{csv_dn_sl},{avg_time_to_tp_str}\n")
    except Exception as e:
        log_results(f"CRITICAL Error processing {symbol}: {str(e)}", RESULT_FILENAME_BASE)
        log_results(traceback.format_exc(), RESULT_FILENAME_BASE)
log_results("\nAll Ichimoku assets processed.", RESULT_FILENAME_BASE)
