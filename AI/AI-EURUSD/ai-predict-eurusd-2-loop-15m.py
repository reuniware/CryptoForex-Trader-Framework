import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

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
import sys
from keras.losses import mean_squared_error
from binance.client import Client
import matplotlib.pyplot as plt
from datetime import datetime
import ta
from ta.trend import IchimokuIndicator
import glob
import yfinance as yf
from datetime import timedelta


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
    fileList = glob.glob('./modeles_a_trier/*')
    # Iterate over the list of filepaths & remove each file.
    for filePath in fileList:
        try:
            os.remove(filePath)
        except:
            print("Error while deleting file : ", filePath)


cleanup_files()

directory_modeles_a_trier = 'modeles_a_trier'
if not os.path.exists(directory_modeles_a_trier):
    # If it doesn't exist, create it
    os.makedirs(directory_modeles_a_trier)

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR) # only show error messages

force_download = True

avg_predict = 0

data_history_file = "eurusd_data_15m_01062021_02052023.pkl"


while True:

    currentDateAndTime = datetime.now()
    stryear = format(currentDateAndTime.year, '04')
    strmonth = format(currentDateAndTime.month, '02')
    strday = format(currentDateAndTime.day, '02')

    pastDateAndTime = currentDateAndTime - timedelta(days=59)
    stryearpast = format(pastDateAndTime.year, '04')
    strmonthpast = format(pastDateAndTime.month, '02')
    strdaypast = format(pastDateAndTime.day, '02')

    strStartDate = stryearpast + '-' + strmonthpast + '-' + strdaypast
    strEndDate = stryear + '-' + strmonth + '-' + strday

    print("Date range used :", strStartDate, strEndDate)

    # Récupération des données de trading de EUR/USD depuis l'API Yahoo Finance
    #ohlcv = yf.download('EURUSD=X', start='2021-06-01', end='2023-05-02', interval='1h')
    ohlcv = yf.download('EURUSD=X', start=strStartDate, end=strEndDate, interval='15m') # 60 days backward is the maximum range
    ohlcv.reset_index(inplace=True)

    #ticker = yf.Ticker('EURUSD=X')
    # Récupération des données de trading avec le prix BID
    #ohlcv = ticker.history(start='2021-06-01', end='2023-04-21', interval='1h', actions=False, auto_adjust=False, back_adjust=False, proxy=None, rounding=False).sort_index(ascending=False)
    #print(ohlcv)

    #sys.exit(0)

    eur_usd_data = pd.DataFrame(ohlcv, columns=['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'])
    eur_usd_data['Datetime'] = pd.to_datetime(eur_usd_data['Datetime'], unit='ms')

    # Normalisation des données d'entrée
    scaler = MinMaxScaler()
    # data = scaler.fit_transform(eur_usd_data[['open', 'close', 'high', 'low']].values)
    data = scaler.fit_transform(eur_usd_data[['Close']].values)

    # Préparer les données de sortie
    target_col = 'Close'
    target = eur_usd_data[target_col].values.reshape(-1, 1)
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
    #model = Sequential()
    #model.add(LSTM(64, input_shape=(X_train.shape[1], X_train.shape[2]), return_sequences=True))
    #model.add(Dropout(0.2))
    #model.add(LSTM(256, return_sequences=False))
    #model.add(Dropout(0.2))
    #model.add(Dense(1))

    model = Sequential()
    model.add(LSTM(units=150, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(LSTM(units=300))
    model.add(Dense(1))


    # Compilation du modèle
    model.compile(optimizer='adam', loss='mse')

    # Entraînement du modèle
    model.fit(X_train, y_train, epochs=1, batch_size=None, validation_split=0.1, shuffle=False)

    # Evaluation du modèle
    model.evaluate(X_test, y_test)

    #model.load_weights('modele.h5')

    # Prédiction sur les données de test
    y_pred = model.predict(X_test)

    # Vérification du RMSE
    # Prédiction sur l'ensemble de test
    y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1))
    y_pred_inv = scaler.inverse_transform(y_pred)
    # Calcul du RMSE pour chaque prédiction
    rmse_list = []

    lowest_rmse = sys.float_info.max
    highest_rmse = 0

    for i in range(len(y_test)):
        mse = mean_squared_error(y_test_inv[i], y_pred_inv[i])
        rmse = np.sqrt(mse)
        rmse_list.append(rmse)
        if rmse > highest_rmse:
            highest_rmse = rmse
        if rmse < lowest_rmse:
            lowest_rmse = rmse
    # Affichage des RMSE
    #print("RMSE for each prediction:")
    #print(rmse_list)
    # Affichage de la moyenne des RMSE
    print("Mean RMSE = ", np.mean(rmse_list))
    print("Highest RMSE = ", highest_rmse)
    print("Lowest RMSE  = ", lowest_rmse)

    y_test_inv = scaler.inverse_transform(y_test.reshape(-1, 1))
    y_pred_inv = scaler.inverse_transform(y_pred)
    mape = 100 * np.mean(np.abs((y_test_inv - y_pred_inv) / y_test_inv))
    print('Mean Absolute Percentage Error:', mape)

    #if np.mean(rmse_list) > 1000:
    #    continue
    #if mape > 1.005:
    #    continue

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
    plt.plot(y_test, label='Données réelles')
    plt.plot(y_pred, label='Prédictions')
    plt.legend()

    filename = stryear + strmonth + strday + strhour + strmin + '-chart.png'

    plt.title(filename + ' MeanRMSE=' + str(round(np.mean(rmse_list))) + ' MAPE=' + str(mape))

    plt.savefig(directory_modeles_a_trier + '/' + filename)

    plt.show()
    plt.close()
    plt.cla()
    plt.clf()

    filename_weights = stryear + strmonth + strday + strhour + strmin + '-model_weights.h5'

    model.save_weights(directory_modeles_a_trier + '/' + filename_weights)

