# python knn_trader.py -e binance -s BTC/USDT -tf 15m --lags 10 --horizon 1 -k 7 --loop --interval 300

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

# Configuration de l'affichage Pandas (optionnel, pour le débogage)
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False) # Empêche le retour à la ligne des DataFrames larges

def signal_handler(sig, frame):
    print('Ctrl+C pressé. Arrêt du script...')
    os._exit(0) # _exit pour forcer la sortie, utile si des threads ccxt sont bloqués

signal.signal(signal.SIGINT, signal_handler)

def initialize_exchange(exchange_name_str):
    """Initialise et retourne une instance de l'exchange ccxt."""
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
    """Récupère les données OHLCV pour un symbole et une timeframe donnés."""
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
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        # S'assurer que les colonnes numériques le sont bien
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
    """
    Crée les features (X) et la target (y) pour le modèle KNN.
    Features: 'n_lags' retours passés en pourcentage.
    Target: Si le prix de clôture dans 'future_horizon' périodes sera plus élevé (1) ou non (0).
    Retourne X_train, y_train, et X_to_predict (les features les plus récentes pour la prédiction).
    """
    df = df_ohlcv.copy()
    df['return'] = df['close'].pct_change() # Calcul des retours en pourcentage

    X_train_list = []
    y_train_list = []

    # Itérer sur les indices de 'df' (qui a déjà les 'return')
    # On a besoin de 'n_lags' retours pour une feature.
    # La target est 'future_horizon' périodes APRÈS la bougie 'i' dont on considère le prix de clôture.
    # La bougie 'i' est celle à la fin de la séquence de 'n_lags' retours.
    # Exemple: lags=3. returns à t-2, t-1, t. Clôture à t. Target compare clôture[t+H] vs clôture[t]
    # On peut former une feature à partir de l'indice 'n_lags' de df_ohlcv (qui correspond à l'indice n_lags des returns si le premier return est NaN)
    # Boucle sur les indices de df_ohlcv (ou df, qui a la même longueur après pct_change)
    for i in range(n_lags, len(df) - future_horizon):
        # Les features sont les n_lags retours se terminant à la bougie 'i'.
        # df['return'].iloc[i] est le retour entre la bougie i-1 et i.
        # Donc, pour la bougie i, on prend les retours df['return'].iloc[i-n_lags+1 : i+1]
        features = df['return'].iloc[i - n_lags + 1 : i + 1].values

        # S'il y a des NaN dans les features (par exemple au début à cause de pct_change), on saute
        if np.isnan(features).any() or len(features) < n_lags:
            continue

        X_train_list.append(features)
        # La target est basée sur le prix de clôture de la bougie 'i'
        target = 1 if df['close'].iloc[i + future_horizon] > df['close'].iloc[i] else 0
        y_train_list.append(target)

    if not X_train_list:
        X_train, y_train = np.array([]).reshape(0, n_lags), np.array([])
    else:
        X_train, y_train = np.array(X_train_list), np.array(y_train_list)

    # Features pour la prédiction (les n_lags derniers retours disponibles dans le dataset)
    # Ces retours mènent jusqu'à la dernière bougie disponible df.iloc[-1]
    latest_features_for_prediction = df['return'].iloc[-n_lags:].values
    if np.isnan(latest_features_for_prediction).any() or len(latest_features_for_prediction) < n_lags:
        X_predict_on = None # Pas assez de données ou NaN pour la prédiction
    else:
        X_predict_on = latest_features_for_prediction.reshape(1, -1)

    return X_train, y_train, X_predict_on


def main():
    parser = argparse.ArgumentParser(description="Script KNN simple pour le trading.")
    parser.add_argument("-e", "--exchange", type=str, required=True, help="Nom de l'exchange (ex: bybit, binance)")
    parser.add_argument("-s", "--symbol", type=str, required=True, help="Symbole de l'actif (ex: BTC/USDT)")
    parser.add_argument("-tf", "--timeframe", type=str, default="1h", help="Timeframe (ex: 1m, 5m, 1h, 1d)")
    parser.add_argument("-l", "--loop", action='store_true', help="Scanner en boucle.")
    parser.add_argument("--interval", type=int, default=60, help="Intervalle en secondes entre les scans en boucle.")
    parser.add_argument("-k", type=int, default=5, help="Nombre de voisins pour KNN.")
    parser.add_argument("--lags", type=int, default=10, help="Nombre de retours passés à utiliser comme features.")
    parser.add_argument("--horizon", type=int, default=1, help="Horizon de prédiction en nombre de périodes.")
    parser.add_argument("--limit_ohlcv", type=int, default=200, help="Nombre de bougies OHLCV à télécharger.")
    parser.add_argument("--min_train_samples", type=int, default=50, help="Nombre minimum d'échantillons d'entraînement requis.")


    args = parser.parse_args()

    # Affichage des arguments (similaire à votre script)
    print("Arguments reçus:")
    for arg, value in vars(args).items():
        print(f"  {arg}: {value}")
    print("-" * 30)


    exchange = initialize_exchange(args.exchange)
    if not exchange:
        sys.exit("Impossible d'initialiser l'exchange. Arrêt.")

    while True:
        try:
            # 1. Télécharger les données OHLCV
            df_ohlcv = fetch_ohlcv_data(exchange, args.symbol, args.timeframe, args.limit_ohlcv)

            if df_ohlcv is None or df_ohlcv.empty:
                print(f"Aucune donnée OHLCV pour {args.symbol}. Attente avant de réessayer si en boucle...")
                if not args.loop: break
                time.sleep(args.interval)
                continue

            if len(df_ohlcv) < args.lags + args.horizon + args.min_train_samples:
                 print(f"Pas assez de données pour l'entraînement et la prédiction. "
                       f"Reçu: {len(df_ohlcv)}, Requis approx: {args.lags + args.horizon + args.min_train_samples}. "
                       f"Augmentez --limit_ohlcv ou attendez plus de données.")
                 if not args.loop: break
                 time.sleep(args.interval)
                 continue

            # 2. Créer les features et la target
            X_train, y_train, X_to_predict = create_features_target(df_ohlcv, n_lags=args.lags, future_horizon=args.horizon)

            if X_train is None or X_to_predict is None or len(X_train) < args.min_train_samples:
                print(f"Impossible de créer suffisamment de features/targets. "
                      f"Échantillons d'entraînement: {len(X_train) if X_train is not None else 0}, "
                      f"Requis min: {args.min_train_samples}. Attente...")
                if not args.loop: break
                time.sleep(args.interval)
                continue

            # 3. Scaler les features
            # IMPORTANT: Le scaler est ajusté (fit) UNIQUEMENT sur X_train
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_to_predict_scaled = scaler.transform(X_to_predict) # Appliquer la même transformation

            # 4. Entraîner le modèle KNN
            model = KNeighborsClassifier(n_neighbors=args.k)
            model.fit(X_train_scaled, y_train)

            # 5. Faire une prédiction pour le prochain mouvement
            prediction = model.predict(X_to_predict_scaled)
            prediction_proba = model.predict_proba(X_to_predict_scaled)

            action_predite = "HAUSSE" if prediction[0] == 1 else "BAISSE"
            confiance_predite = prediction_proba[0][prediction[0]] # Confiance dans la classe prédite

            print(f"\n--- Prédiction KNN pour {args.symbol} ({args.timeframe}) à {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
            print(f"  Dernier prix de clôture analysé: {df_ohlcv['close'].iloc[-1-args.lags] :.4f} (fin des features de prédiction)")
            # Note: Les features de X_to_predict sont basées sur les retours *jusqu'à* la dernière bougie de df_ohlcv.
            # La prédiction concerne le mouvement APRÈS la dernière bougie de df_ohlcv, sur un horizon de 'args.horizon'.
            print(f"  Features pour la prédiction (scalées, première et dernière): {X_to_predict_scaled[0][:2]} ... {X_to_predict_scaled[0][-2:]}")
            print(f"  Prédiction pour les {args.horizon} prochaines périodes: {action_predite} (Confiance: {confiance_predite:.2%})")
            print(f"  (Basé sur k={args.k} voisins, {args.lags} retours passés, horizon de {args.horizon} période(s))")
            print("-" * 70)

            if not args.loop:
                break
            print(f"\nProchain scan dans {args.interval} secondes...")
            time.sleep(args.interval)

        except ccxt.RateLimitExceeded as e:
            print(f"Erreur ccxt: RateLimitExceeded. {e}. Attente de 60 secondes...")
            time.sleep(60)
        except ccxt.NetworkError as e:
            print(f"Erreur ccxt: Problème réseau. {e}. Attente de {args.interval} secondes...")
            time.sleep(args.interval)
        except ccxt.ExchangeError as e: # Erreurs plus générales de l'exchange
            print(f"Erreur ccxt: Erreur de l'exchange. {e}. Attente de {args.interval} secondes...")
            time.sleep(args.interval)
        except Exception as e:
            print(f"Une erreur inattendue est survenue: {e}")
            import traceback
            traceback.print_exc()
            if not args.loop:
                break
            print(f"Attente de {args.interval} secondes avant de réessayer...")
            time.sleep(args.interval)

if __name__ == "__main__":
    main()

  
# Ce que fait ce code :
#   Se connecter à l'exchange (binance par exemple).
#   Scanner l'actif BTC/USDT.
#   Utiliser la timeframe 15m.
#   Utiliser les 10 derniers retours comme features (--lags 10).
#   Prédire si le prix montera ou baissera dans la prochaine période de 15m (--horizon 1).
#   Utiliser 7 voisins pour KNN (-k 7).
#   Tourner en boucle (--loop) avec un intervalle de 300 secondes (5 minutes) entre chaque prédiction.
#   Avertissements importants :
#   Ceci n'est PAS un conseil financier. L'utilisation de ce script pour du trading réel est à vos propres risques.
#   Simpliste : Ce modèle KNN est très basique. Les marchés financiers sont complexes et influencés par de nombreux facteurs non pris en compte ici.
#   Pas de backtesting : Un backtesting rigoureux sur des données historiques est crucial avant d'envisager toute utilisation réelle. Ce script ne fait que des prédictions "en avant" sans évaluer sa performance passée.
#   Surapprentissage (Overfitting) : Avec peu de données ou des paramètres mal choisis, le modèle peut facilement surapprendre les données d'entraînement et mal performer sur de nouvelles données.
#   Latence et Slippage : En trading réel, la latence d'exécution des ordres et le slippage peuvent affecter considérablement les performances.
#   Ce code devrait vous donner une bonne base pour comprendre comment l'algorithme KNN peut être appliqué au trading en utilisant les données de marché en temps (quasi) réel.
