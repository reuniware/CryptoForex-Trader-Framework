#!pip install ccxt
#!pip install python-binance

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
import glob

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)


signal.signal(signal.SIGINT, signal_handler)


# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
# pd.set_option('display.expand_frame_repr', True)


def log_to_results(str_to_log):
    fr = open("results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()

    
def cleanup_files():
    fileList = glob.glob('*.png')
    # Iterate over the list of filepaths & remove each file.
    for filePath in fileList:
        try:
            os.remove(filePath)
        except:
            print("Error while deleting file : ", filePath)


directory_modeles_a_trier = 'modeles_a_trier'
if not os.path.exists(directory_modeles_a_trier):
    # If it doesn't exist, create it
    os.makedirs(directory_modeles_a_trier)


force_download = True

avg_predict = 0

data_history_file = "bitcoin_data_4h_01012000_29042023.pkl"
interval = Client.KLINE_INTERVAL_4HOUR

while True:

    if not (os.path.exists(data_history_file)) or force_download == True:
        print("downloading data")
        # Préparer les données d'entrée
        klinesT = Client(tld='us').get_historical_klines("BTCUSDT", interval, "01 January 2000")
        #klinesT = Client().get_historical_klines("BTCUSDT", interval, "01 January 2000")
        bitcoin_data = pd.DataFrame(klinesT,
                                    columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av',
                                                'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
        bitcoin_data['time'] = pd.to_datetime(bitcoin_data['time'], unit='ms')
        bitcoin_data.to_pickle(data_history_file)
    else:
        print("updating data to merge to existing file with data")
        klinesT2 = Client().get_historical_klines("BTCUSDT", interval, "1 day ago UTC")
        bitcoin_data2 = pd.DataFrame(klinesT2,
                                        columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av',
                                                'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
        bitcoin_data2['time'] = pd.to_datetime(bitcoin_data2['time'], unit='ms')
        print("loading existing file with data")
        bitcoin_data = pd.read_pickle(data_history_file)
        print("merging downloaded recent data with existing file with data")
        bitcoin_data = bitcoin_data.merge(bitcoin_data2, how="right")
        print("saving updated data to file")
        bitcoin_data.to_pickle(data_history_file)


    # Normalisation des données d'entrée
    scaler = MinMaxScaler()
    # data = scaler.fit_transform(bitcoin_data[['open', 'close', 'high', 'low']].values)
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

    X_test = None
    y_test = None
    y_pred = None

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

    #model.load_weights('modele.h5')

    # Prédiction sur les données de test
    y_pred = model.predict(X_test)

    # Vérification du RMSE
    # Prédiction sur l'ensemble de test
    y_pred = model.predict(X_test)
    # Calcul du RMSE pour chaque prédiction
    rmse_list = []
    for i in range(len(y_test)):
        mse = mean_squared_error(y_test[i], y_pred[i])
        rmse = np.sqrt(mse)
        rmse_list.append(rmse)
    # Affichage des RMSE
    #print("RMSE for each prediction:")
    #print(rmse_list)
    # Affichage de la moyenne des RMSE
    print("Mean RMSE = " + str(np.mean(rmse_list)))

    # Inverse la normalisation des données de sortie pour obtenir la prédiction réelle
    y_pred = scaler.inverse_transform(y_pred)

    # Affichage de la prédiction
    print("Prédiction pour la prochaine bougie : ", y_pred[-1][0])
    log_to_results("Prédiction pour la prochaine bougie : " + str(y_pred[-1][0]))

    if avg_predict==0:
        avg_predict = avg_predict + y_pred[-1][0]
    else:
        avg_predict = (avg_predict + y_pred[-1][0])/2
    
    log_to_results("average predict = " + str(avg_predict))
    print("average predict = " + str(avg_predict))

    # Inverse la normalisation des données de test pour obtenir les vraies valeurs
    y_test = scaler.inverse_transform(y_test)

    currentDateAndTime = datetime.now()
    stryear = format(currentDateAndTime.year, '04')
    strmonth = format(currentDateAndTime.month, '02')
    strday = format(currentDateAndTime.day, '02')
    strhour = format(currentDateAndTime.hour, '02')
    strmin = format(currentDateAndTime.minute, '02')

    # Tracer les prédictions par rapport aux données réelles
    plt.plot(y_test[-500:], label='Données réelles')
    plt.plot(y_pred[-500:], label='Prédictions')
    plt.legend()

    filename = stryear + strmonth + strday + strhour + strmin + '-chart.png'

    plt.title(filename + ' MeanRMSE=' + str(np.mean(rmse_list)))

    plt.savefig(directory_modeles_a_trier + '/' + filename)

    plt.show()
    plt.close()
    plt.cla()
    plt.clf()
    
    filename_weights = stryear + strmonth + strday + strhour + strmin + '-model_weights.h5'

    model.save_weights(directory_modeles_a_trier + '/' + filename_weights)

