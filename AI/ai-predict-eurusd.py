# ne fonctionne pas (récupération des données historiques + récupération des données temps réel)

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
import signal
import os

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)

signal.signal(signal.SIGINT, signal_handler)

# Récupération des données de trading de l'EUR/USD depuis l'API Yahoo
eurusd_data = yf.download('EURUSD=X', period='2y', interval='1h')
eurusd_data.reset_index(inplace=True)

# Préparation des données pour le modèle LSTM
scaler = MinMaxScaler(feature_range=(0, 1))
data = scaler.fit_transform(np.array(eurusd_data['Close']).reshape(-1, 1))
training_size = int(len(data) * 0.7)
test_size = len(data) - training_size
train_data, test_data = data[0:training_size, :], data[training_size:len(data), :]

def create_dataset(dataset, time_step=1):
    X, Y = [], []
    for i in range(len(dataset)-time_step-1):
        a = dataset[i:(i+time_step), 0]
        X.append(a)
        Y.append(dataset[i + time_step, 0])
    return np.array(X), np.array(Y)

time_step = 100
X_train, y_train = create_dataset(train_data, time_step)
X_test, y_test = create_dataset(test_data, time_step)

# Reshape des données pour l'entrée dans le modèle LSTM
X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

# Création du modèle LSTM
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
model.add(LSTM(units=50))
model.add(Dense(1))
model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=100, batch_size=None, verbose=1)

# Sauvegarde du modèle
model.save('eurusd_lstm_model.h5')

# Utilisation du modèle pour prédire le prix de l'EUR/USD en temps réel
# n_last_prices doit être égal à time_step
n_last_prices = 100 # nombre de derniers prix à utiliser pour la prédiction
while True:
    try:
        current_price = yf.Ticker('EURUSD=X').info['regularMarketPrice']
        last_n_prices = scaler.transform(np.array(eurusd_data.tail(n_last_prices)['Close']).reshape(-1, 1))
        last_n_prices = np.array(last_n_prices).reshape(1, -1)
        last_n_prices = np.reshape(last_n_prices, (last_n_prices.shape[0], last_n_prices.shape[1], 1))
        predicted_price = model.predict(last_n_prices)
        predicted_price = scaler.inverse_transform(predicted_price)
        print(f'ia3: Current Price: {current_price:.2f} | Predicted Price: {predicted_price[0][0]:.2f}')
        eurusd_data.loc[len(eurusd_data)] = [pd.Timestamp.now(), None, None, None, current_price, None]
    except:
        continue
