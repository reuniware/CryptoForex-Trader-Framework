import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
import signal
import os
import yfinance as yf
import sys
import time
import keras.models

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)

signal.signal(signal.SIGINT, signal_handler)

# Récupération des données de trading de EUR/USD depuis l'API Yahoo Finance
eur_usd_data = yf.download('EURUSD=X', start='2022-01-01', end='2023-04-20', interval='1h')
eur_usd_data.reset_index(inplace=True)

# Préparation des données pour le modèle LSTM
scaler = MinMaxScaler(feature_range=(0, 1))
data = scaler.fit_transform(np.array(eur_usd_data['Close']).reshape(-1, 1))
training_size = int(len(data) * 0.7)
test_size = len(data) - training_size
train_data, test_data = data[0:training_size, :], data[training_size:len(data), :]

model = Sequential()
model = keras.models.load_model('eur_usd_lstm_model.h5')

# Utilisation du modèle pour prédire le prix de l'EUR/USD en temps réel
# n_last_prices doit être égal à time_step (Si on augmente n_last_prices) ?
n_last_prices = 200 # nombre de derniers prix à utiliser pour la prédiction
previous_price = 0
while True:
    try:
        #with silence_stdout():
        data = yf.download(tickers='EURUSD=X', period='1d', interval='1m', progress=False)

        current_price = data['Close'][-1]

        #current_price = mydata['Close'].iloc[-1]
        last_n_prices = scaler.transform(np.array(eur_usd_data.tail(n_last_prices)['Close']).reshape(-1, 1))
        last_n_prices = np.array(last_n_prices).reshape(1, -1)
        last_n_prices = np.reshape(last_n_prices, (last_n_prices.shape[0], last_n_prices.shape[1], 1))
        predicted_price = model.predict(last_n_prices)
        predicted_price = scaler.inverse_transform(predicted_price)
        print(f'Current Price: {current_price:.5f} | Predicted Price: {predicted_price[0][0]:.5f}')
        eur_usd_data.loc[len(eur_usd_data)] = [pd.Timestamp.now(), None, None, None, current_price, None]

        time.sleep(1)
    except:
        print("exception")
        print(sys.exc_info())
        continue
