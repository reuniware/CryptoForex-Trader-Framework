import ccxt
import pandas as pd
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
import time
import argparse
import sys
import os
import signal
from datetime import datetime, timedelta, timezone

# Configuration de l'affichage Pandas (optionnel, pour le débogage)
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

def signal_handler(sig, frame):
    print('Ctrl+C pressé. Arrêt du script...')
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

def initialize_exchange(exchange_name_str):
    try:
        exchange_class = getattr(ccxt, exchange_name_str.lower())
        exchange = exchange_class()
        print(f"Exchange '{exchange_name_str}' initialisé.")
        return exchange
    except ccxt.ExchangeNotFound:
        print(f"Erreur: L'exchange '{exchange_name_str}' n'a pas été trouvé par ccxt.")
        return None
    except Exception as e:
        print(f"Erreur lors de l'initialisation de l'exchange '{exchange_name_str}': {e}")
        return None

def fetch_ohlcv_data(exchange_instance, symbol_str, timeframe_str, limit_int):
    try:
        if not exchange_instance.has['fetchOHLCV']:
            print(f"L'exchange {exchange_instance.id} ne supporte pas fetchOHLCV.")
            return None

        print(f"Téléchargement de {limit_int} bougies pour {symbol_str} en timeframe {timeframe_str}...")
        ohlcv = exchange_instance.fetch_ohlcv(symbol_str, timeframe_str, limit=limit_int)
        if not ohlcv:
            print(f"Aucune donnée OHLCV retournée pour {symbol_str} en {timeframe_str}.")
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        # Convertir le timestamp en datetime UTC puis en local si besoin pour affichage
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.tz_convert(None) # Ou tz_localize(None)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        print(f"Données téléchargées. Dernière bougie: {df['timestamp'].iloc[-1]}, Prix de clôture: {df['close'].iloc[-1]}")
        return df
    except ccxt.NetworkError as e:
        print(f"Erreur réseau ccxt lors du téléchargement des données pour {symbol_str}: {e}")
    except ccxt.ExchangeError as e:
        print(f"Erreur d'exchange ccxt pour {symbol_str}: {e}")
    except Exception as e:
        print(f"Erreur inattendue lors du téléchargement des données pour {symbol_str}: {e}")
    return None

def create_features_target(df_ohlcv, n_lags=5, future_horizon=1):
    df = df_ohlcv.copy()
    df['return'] = df['close'].pct_change()

    X_train_list = []
    y_train_list = []

    for i in range(n_lags, len(df) - future_horizon):
        features = df['return'].iloc[i - n_lags + 1 : i + 1].values
        if np.isnan(features).any() or len(features) < n_lags:
            continue
        X_train_list.append(features)
        target = 1 if df['close'].iloc[i + future_horizon] > df['close'].iloc[i] else 0
        y_train_list.append(target)

    if not X_train_list:
        X_train, y_train = np.array([]).reshape(0, n_lags), np.array([])
    else:
        X_train, y_train = np.array(X_train_list), np.array(y_train_list)

    latest_features_for_prediction = df['return'].iloc[-n_lags:].values
    if np.isnan(latest_features_for_prediction).any() or len(latest_features_for_prediction) < n_lags:
        X_predict_on = None
    else:
        X_predict_on = latest_features_for_prediction.reshape(1, -1)

    return X_train, y_train, X_predict_on

def parse_timeframe_to_seconds(timeframe_str):
    """Convertit une chaîne de timeframe ccxt (ex: '1m', '5m', '1h', '1d') en secondes."""
    multipliers = {'m': 60, 'h': 3600, 'd': 86400}
    try:
        value = int(timeframe_str[:-1])
        unit = timeframe_str[-1].lower()
        if unit not in multipliers:
            raise ValueError(f"Unité de timeframe non supportée: {unit}")
        return value * multipliers[unit]
    except Exception as e:
        raise ValueError(f"Format de timeframe invalide: {timeframe_str}. Erreur: {e}")

def get_next_candle_execution_time(current_dt_utc, timeframe_str, delay_after_close_seconds):
    """Calcule l'heure d'exécution cible, X secondes après la prochaine clôture de bougie théorique."""
    timeframe_seconds = parse_timeframe_to_seconds(timeframe_str)
    current_timestamp_utc = current_dt_utc.timestamp()

    # Calculer le timestamp de début de la bougie actuelle
    current_candle_start_timestamp_utc = (current_timestamp_utc // timeframe_seconds) * timeframe_seconds
    
    # La prochaine clôture de bougie théorique (qui est aussi le début de la suivante)
    next_candle_close_timestamp_utc = current_candle_start_timestamp_utc + timeframe_seconds
    
    target_execution_timestamp_utc = next_candle_close_timestamp_utc + delay_after_close_seconds

    target_execution_dt_utc = datetime.fromtimestamp(target_execution_timestamp_utc, tz=timezone.utc)

    # S'assurer que l'heure d'exécution est dans le futur
    # Cela est utile si le script a pris du temps ou si delay_after_close_seconds est petit
    while target_execution_dt_utc <= datetime.now(timezone.utc):
        # print(f"Heure cible {target_execution_dt_utc.strftime('%Y-%m-%d %H:%M:%S %Z')} déjà passée ou trop proche. Avance à la prochaine bougie.")
        next_candle_close_timestamp_utc += timeframe_seconds # Avancer d'une bougie
        target_execution_timestamp_utc = next_candle_close_timestamp_utc + delay_after_close_seconds
        target_execution_dt_utc = datetime.fromtimestamp(target_execution_timestamp_utc, tz=timezone.utc)
        
    return target_execution_dt_utc


def run_prediction_cycle(exchange, args):
    """Exécute un cycle de téléchargement de données, création de features/target, et prédiction."""
    print(f"\n--- Début du cycle de prédiction à {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    df_ohlcv = fetch_ohlcv_data(exchange, args.symbol, args.timeframe, args.limit_ohlcv)

    if df_ohlcv is None or df_ohlcv.empty:
        print(f"Aucune donnée OHLCV pour {args.symbol}.")
        return False # Indique un échec pour ce cycle

    if len(df_ohlcv) < args.lags + args.horizon + args.min_train_samples:
        print(f"Pas assez de données pour l'entraînement et la prédiction. "
              f"Reçu: {len(df_ohlcv)}, Requis approx: {args.lags + args.horizon + args.min_train_samples}. "
              f"Augmentez --limit_ohlcv ou attendez plus de données.")
        return False

    X_train, y_train, X_to_predict = create_features_target(df_ohlcv, n_lags=args.lags, future_horizon=args.horizon)

    if X_train is None or X_to_predict is None or X_train.shape[0] < args.min_train_samples :
        print(f"Impossible de créer suffisamment de features/targets. "
              f"Échantillons d'entraînement: {X_train.shape[0] if X_train is not None else 0}, "
              f"Requis min: {args.min_train_samples}. Attente...")
        return False

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_to_predict_scaled = scaler.transform(X_to_predict)

    model = KNeighborsClassifier(n_neighbors=args.k)
    model.fit(X_train_scaled, y_train)

    prediction = model.predict(X_to_predict_scaled)
    prediction_proba = model.predict_proba(X_to_predict_scaled)

    action_predite = "HAUSSE" if prediction[0] == 1 else "BAISSE"
    confiance_predite = prediction_proba[0][prediction[0]]

    print(f"\n--- Prédiction KNN pour {args.symbol} ({args.timeframe}) à {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    # Utiliser -1-args.lags pour la bougie qui précède les features de X_to_predict
    # Le prix de la bougie qui précède la première feature de X_to_predict
    if len(df_ohlcv) > args.lags : # S'assurer qu'il y a assez de données pour cet index
         print(f"  Prix de clôture de référence (avant les {args.lags} retours pour la prédiction): {df_ohlcv['close'].iloc[-(args.lags + 1)] :.4f}")
    else:
         print(f"  Pas assez de données pour afficher le prix de clôture de référence.")

    print(f"  Dernière bougie téléchargée: {df_ohlcv['timestamp'].iloc[-1]}, Clôture: {df_ohlcv['close'].iloc[-1]:.4f}")
    # print(f"  Features pour la prédiction (brutes, dernières): {X_to_predict[0][-3:]}") # Pour débogage
    # print(f"  Features pour la prédiction (scalées, dernières): {X_to_predict_scaled[0][-3:]}") # Pour débogage
    print(f"  Prédiction pour les {args.horizon} prochaines périodes: {action_predite} (Confiance: {confiance_predite:.2%})")
    print(f"  (Basé sur k={args.k} voisins, {args.lags} retours passés, horizon de {args.horizon} période(s))")
    print("-" * 70)
    return True # Succès

def main():
    parser = argparse.ArgumentParser(description="Script KNN simple pour le trading.")
    parser.add_argument("-e", "--exchange", type=str, required=True, help="Nom de l'exchange (ex: bybit, binance)")
    parser.add_argument("-s", "--symbol", type=str, required=True, help="Symbole de l'actif (ex: BTC/USDT)")
    parser.add_argument("-tf", "--timeframe", type=str, default="1h", help="Timeframe (ex: 1m, 5m, 1h, 1d)")
    parser.add_argument("-l", "--loop", action='store_true', help="Scanner en boucle après les clôtures de bougies.")
    parser.add_argument("--delay_after_candle", type=int, default=5, help="Délai en secondes après la clôture théorique de la bougie pour lancer le scan.")
    parser.add_argument("-k", type=int, default=5, help="Nombre de voisins pour KNN.")
    parser.add_argument("--lags", type=int, default=10, help="Nombre de retours passés à utiliser comme features.")
    parser.add_argument("--horizon", type=int, default=1, help="Horizon de prédiction en nombre de périodes.")
    parser.add_argument("--limit_ohlcv", type=int, default=200, help="Nombre de bougies OHLCV à télécharger.")
    parser.add_argument("--min_train_samples", type=int, default=50, help="Nombre minimum d'échantillons d'entraînement requis.")

    args = parser.parse_args()

    print("Arguments reçus:")
    for arg, value in vars(args).items():
        print(f"  {arg}: {value}")
    print("-" * 30)

    exchange = initialize_exchange(args.exchange)
    if not exchange:
        sys.exit("Impossible d'initialiser l'exchange. Arrêt.")

    # Première prédiction au démarrage
    print("Lancement de la première prédiction au démarrage...")
    run_prediction_cycle(exchange, args)

    if not args.loop:
        print("Mode non-boucle. Arrêt après la première prédiction.")
        sys.exit(0)

    # Boucle pour les prédictions suivantes
    while True:
        try:
            current_time_utc = datetime.now(timezone.utc)
            next_exec_time_utc = get_next_candle_execution_time(current_time_utc, args.timeframe, args.delay_after_candle)
            
            # Convertir en heure locale pour l'affichage si besoin
            next_exec_time_local = next_exec_time_utc.astimezone(None)
            
            wait_seconds = (next_exec_time_utc - current_time_utc).total_seconds()

            if wait_seconds > 0:
                print(f"\nProchain scan programmé à: {next_exec_time_local.strftime('%Y-%m-%d %H:%M:%S %Z')} (dans {wait_seconds:.0f} secondes)")
                time.sleep(wait_seconds)
            
            run_prediction_cycle(exchange, args)

        except ccxt.RateLimitExceeded as e:
            print(f"Erreur ccxt: RateLimitExceeded. {e}. Attente de 60 secondes...")
            time.sleep(60)
        except ccxt.NetworkError as e:
            print(f"Erreur ccxt: Problème réseau. {e}. Attente de 60 secondes...")
            time.sleep(60)
        except ccxt.ExchangeError as e:
            print(f"Erreur ccxt: Erreur de l'exchange. {e}. Attente de 60 secondes...")
            time.sleep(60)
        except ValueError as e: # Pour les erreurs de parse_timeframe ou autres
            print(f"Erreur de configuration ou de valeur: {e}")
            sys.exit("Arrêt dû à une erreur de configuration.")
        except Exception as e:
            print(f"Une erreur inattendue est survenue: {e}")
            import traceback
            traceback.print_exc()
            print(f"Attente de 60 secondes avant de réessayer...")
            time.sleep(60)

if __name__ == "__main__":
    main()

#python knn_trader_candle_sync.py -e bybit -s BTC/USDT -tf 1m --lags 10 --horizon 1 -k 7 --loop --delay_after_candle 5
