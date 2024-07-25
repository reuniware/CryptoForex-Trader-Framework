import ccxt
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout
import signal
import os
import sys
from keras.losses import mean_squared_error
from binance.client import Client
import matplotlib.pyplot as plt
from datetime import datetime
import ta
from ta.trend import IchimokuIndicator


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)


signal.signal(signal.SIGINT, signal_handler)


#pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)
#pd.set_option('display.expand_frame_repr', True)


def log_to_results(str_to_log):
    fr = open("results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


force_download = True


data_history_file = "bitcoin_data_h4_01012000_27042023.pkl"

if not (os.path.exists(data_history_file)) or force_download == True:
    print("downloading data")
    # Préparer les données d'entrée
    klinesT = Client().get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_4HOUR, "01 January 2000")
    bitcoin_data = pd.DataFrame(klinesT,
                                columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av',
                                         'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
    bitcoin_data['time'] = pd.to_datetime(bitcoin_data['time'], unit='ms')
    bitcoin_data.to_pickle(data_history_file)
else:
    print("using existing file for data")
    bitcoin_data = pd.read_pickle(data_history_file)


# calculer le RSI pour une période de 14 jours
#rsi_period = 14
#bitcoin_data['rsi'] = ta.momentum.RSIIndicator(close=bitcoin_data['close'].astype(float), window=rsi_period).rsi()
#bitcoin_data['rsi'] = bitcoin_data['rsi'].fillna(0)

kijun_sen_period = 26
ichimoku = IchimokuIndicator(high=bitcoin_data['high'], low=bitcoin_data['low'], window1=9, window2=kijun_sen_period)
bitcoin_data['kijun_sen'] = ichimoku.ichimoku_conversion_line()
bitcoin_data['kijun_sen'] = bitcoin_data['kijun_sen'].fillna(0)
bitcoin_data['tenkan_sen'] = ichimoku.ichimoku_base_line()
bitcoin_data['tenkan_sen'] = bitcoin_data['tenkan_sen'].fillna(0)
bitcoin_data['chikou_span'] = bitcoin_data['close'].shift(-26)
bitcoin_data['chikou_span'] = bitcoin_data['chikou_span'].fillna(0)
bitcoin_data['chikou_above_kijun'] = (bitcoin_data['chikou_span'].shift(26).astype(float) > bitcoin_data['kijun_sen'].shift(26).astype(float)).astype(int)
bitcoin_data['chikou_below_kijun'] = (bitcoin_data['chikou_span'].shift(26).astype(float) < bitcoin_data['kijun_sen'].shift(26).astype(float)).astype(int)
bitcoin_data['chikou_above_tenkan'] = (bitcoin_data['chikou_span'].shift(26).astype(float) > bitcoin_data['tenkan_sen'].shift(26).astype(float)).astype(int)
bitcoin_data['chikou_below_tenkan'] = (bitcoin_data['chikou_span'].shift(26).astype(float) < bitcoin_data['tenkan_sen'].shift(26).astype(float)).astype(int)


# Normalisation des données d'entrée
scaler = MinMaxScaler()
#data = scaler.fit_transform(bitcoin_data[['open', 'close', 'high', 'low']].values)
data = scaler.fit_transform(bitcoin_data[['close']].values)

# Préparer les données de sortie
target_col = 'close'
target = bitcoin_data[target_col].values.reshape(-1, 1)
target = scaler.fit_transform(target)

# Fractionnement des données en ensembles de formation et de test
train_size = int(len(data) * 0.7)
train_data, test_data = data[:train_size], data[train_size:]
train_target, test_target = target[:train_size], target[train_size:]


# Fonction pour créer un ensemble de données à partir des séquences d'entrée et de sortie
def create_dataset(X, y, time_steps=1):
    Xs, ys = [], []
    for i in range(len(X) - time_steps):
        Xs.append(X[i:(i + time_steps)])
        ys.append(y[i + time_steps])
    return np.array(Xs), np.array(ys)


# Définition de la séquence temporelle des pas de temps
TIME_STEPS = 60

# Création des ensembles de données pour l'entraînement et le test
X_train, y_train = create_dataset(train_data, train_target, time_steps=TIME_STEPS)
X_test, y_test = create_dataset(test_data, test_target, time_steps=TIME_STEPS)

# Définition de l'architecture du modèle
model = Sequential()
model.add(LSTM(256, input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=True))
model.add(Dropout(0.2))
model.add(LSTM(64, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(1))

# Compilation du modèle
model.compile(optimizer='adam', loss='mape')

# Entraînement du modèle
model.fit(X_train, y_train, epochs=1, batch_size=None, validation_split=0.1, shuffle=False)

# Evaluation du modèle
model.evaluate(X_test, y_test)

# Prédiction sur les données de test
y_pred = model.predict(X_test)

# Inverse la normalisation des données de sortie pour obtenir la prédiction réelle
y_pred = scaler.inverse_transform(y_pred)

# Affichage de la prédiction
print("Prédiction pour la prochaine bougie : ", y_pred[-1][0])
log_to_results("Prédiction pour la prochaine bougie : " + str(y_pred[-1][0]))

# Inverse la normalisation des données de test pour obtenir les vraies valeurs
y_test = scaler.inverse_transform(y_test)

currentDateAndTime = datetime.now()
stryear = format(currentDateAndTime.year, '04')
strmonth = format(currentDateAndTime.month, '02')
strday = format(currentDateAndTime.day, '02')
strhour = format(currentDateAndTime.hour, '02')
strmin = format(currentDateAndTime.minute, '02')

# Tracer les prédictions par rapport aux données réelles
plt.plot(y_test, label='Données réelles')
plt.plot(y_pred, label='Prédictions')
plt.legend()

filename = stryear + strmonth + strday + strhour + strmin + 'chart.png'
plt.savefig(filename)

plt.show()
