import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
import signal
import os
import yfinance as yf

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)

signal.signal(signal.SIGINT, signal_handler)

# Récupération des données de trading de EUR/USD depuis l'API Yahoo Finance
eur_usd_data = yf.download('EURUSD=X', start='2023-01-01', end='2023-04-20', interval='1h')
eur_usd_data.reset_index(inplace=True)

# Préparation des données pour le modèle LSTM
scaler = MinMaxScaler(feature_range=(0, 1))
data = scaler.fit_transform(np.array(eur_usd_data['Close']).reshape(-1, 1))
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
model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=1, batch_size=None, verbose=1)

# Sauvegarde du modèle
model.save('eur_usd_lstm_model.h5')

# Utilisation du modèle pour prédire le prix de l'EUR/USD en temps réel
# n_last_prices doit être égal à time_step
n_last_prices = 100 # nombre de derniers prix à utiliser pour la prédiction
while True:
    try:
        current_price = eur_usd_data['Close'].iloc[-1]
        last_n_prices = scaler.transform(np.array(eur_usd_data.tail(n_last_prices)['Close']).reshape(-1, 1))
        last_n_prices = np.array(last_n_prices).reshape(1, -1)
        last_n_prices = np.reshape(last_n_prices, (last_n_prices.shape[0], last_n_prices.shape[1], 1))
        predicted_price = model.predict(last_n_prices)
        predicted_price = scaler.inverse_transform(predicted_price)
        print(f'Current Price: {current_price:.2f} | Predicted Price: {predicted_price[0][0]:.2f}')
        eur_usd_data.loc[len(eur_usd_data)] = [pd.Timestamp.now(), None, None, None, current_price, None]
    except:
        continue
