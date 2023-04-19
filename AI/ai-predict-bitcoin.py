import time
import numpy as np
import pandas as pd
import ccxt
from keras.models import Sequential
from keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

# Initialiser l'échange Binance
exchange = ccxt.binance()
symbol = 'BTC/USDT'

# Récupérer les données historiques du cours du Bitcoin
limit = 500
ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1d', limit=limit)
df = pd.DataFrame(ohlcv, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
df['date'] = pd.to_datetime(df['date'], unit='ms')
df = df.set_index('date')
df = df.astype(float)
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(df['close'].values.reshape(-1, 1))

# Fonction pour créer les données d'entrée et de sortie du modèle LSTM
def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-look_back-1):
        a = dataset[i:(i+look_back), 0]
        dataX.append(a)
        dataY.append(dataset[i + look_back, 0])
    return np.array(dataX), np.array(dataY)

look_back = 20
trainX, trainY = create_dataset(scaled_data, look_back)

# Créer le modèle LSTM
model = Sequential()
model.add(LSTM(50, input_shape=(look_back, 1)))
model.add(Dense(1))
model.compile(loss='mean_squared_error', optimizer='adam')

# Entraîner le modèle sur les données historiques
model.fit(trainX, trainY, epochs=50, batch_size=1, verbose=2)

# Prédire le prix du Bitcoin en temps réel
while True:
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=look_back)
    df = pd.DataFrame(ohlcv, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'], unit='ms')
    df = df.set_index('date')
    df = df.astype(float)
    last_price = df.iloc[-1]['close']
    scaled_last_price = scaler.transform(np.array([[last_price]]))
    input_data = scaled_data[-look_back:]
    input_data = np.append(input_data, scaled_last_price)
    input_data = input_data.reshape(-1, 1)
    input_data = scaler.inverse_transform(input_data)
    input_data = create_dataset(input_data, look_back)
    predicted_price = model.predict(input_data.reshape(1, look_back, 1))
    predicted_price = scaler.inverse_transform(predicted_price)
    print('Prix actuel: {:.2f}'.format(last_price))
    print('Prix prédit: {:.2f}'.format(predicted_price[0][0]))
    time.sleep(60)  # Attendre 1 minute avant de faire une nouvelle prédiction
