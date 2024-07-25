#!pip install python-binance
#!pip install discord.py
#!pip install ta
#!pip install yfinance
#!zip -r 'modeles_a_trier_btcusdt_10062023_1.5489_timestep60.zip' 'modeles_a_trier'
#!cp './modeles_a_trier_btcusdt_10062023_1.5489_timestep60.zip' './drive/MyDrive/'
#!rm -rf modeles*
#!cp ./drive/MyDrive/modeles_a_trier_btcusdt_10062023_1.5489_timestep60.zip ./
#!unzip modeles_a_trier_btcusdt_10062023_1.5489_timestep60.zip

import os, shutil
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

#import ccxt
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
#from binance.client import Client
import matplotlib.pyplot as plt
from datetime import datetime
import ta
from ta.trend import IchimokuIndicator
import glob
import yfinance as yf
from datetime import timedelta
import keras.losses
from discord import SyncWebhook
from keras.layers import SimpleRNN
from keras.layers import Input
from keras.models import Model
import requests
from binance.client import Client

from fastai.tabular.all import *
from sklearn.cluster import KMeans


discord = True
create_model = False   # If False the will load a model from a whole model directory.
delete_all_models_at_startup = False  # if create_model is True then we can delete all models directories at startup
                                      # if create_model is False this has no effect
whole_model_folder_to_load = './modeles_a_trier/20230610100232-whole_model'
show_chart_if_using_existing_model = False

# Définition de la séquence temporelle des pas de temps
TIME_STEPS = 60
nbepochs = 200

webhook = SyncWebhook.from_url("https://discord.com/api/webhooks/1113100473659043851/TLc1PABe6wQIipjaumvVOrNVmG7ZWgfNQyp7z67OcMphgWpn5HepYKE9dt_zVOIK4Gvr")
#webhook.send("test")


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    os.kill(os.getpid(), 9)
    sys.exit(-888)

signal.signal(signal.SIGINT, signal_handler)


if create_model is False and discord is True:
  try:
      webhook.send(str(datetime.now()).split('.')[0] + " > " + "**Starting BTC/USDT AI with Deep Learning Model [" + os.path.basename(whole_model_folder_to_load) + "]**")
  except:
      print("Upload impossible (1)")


# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
# pd.set_option('display.expand_frame_repr', True)


def log_to_results(str_to_log):
    fr = open("results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def cleanup_files():
    #fileList = glob.glob('./modeles_a_trier/*')
    ## Iterate over the list of filepaths & remove each file.
    #for filePath in fileList:
    #    try:
    #        os.remove(filePath)
    #    except:
    #        print("Error while deleting file : ", filePath)

    folder = './modeles_a_trier'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

if create_model and delete_all_models_at_startup:
  cleanup_files()

directory_modeles_a_trier = 'modeles_a_trier'
if not os.path.exists(directory_modeles_a_trier):
    # If it doesn't exist, create it
    os.makedirs(directory_modeles_a_trier)

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR) # only show error messages

force_download = False

avg_predict = 0

#data_history_file = "eurusd_data_15m_01062021_14052023.pkl"

currentDateAndTime = datetime.now()
currentDateAndTime = currentDateAndTime + timedelta(days=1)
stryear = format(currentDateAndTime.year, '04')
strmonth = format(currentDateAndTime.month, '02')
strday = format(currentDateAndTime.day, '02')

#pastDateAndTime = currentDateAndTime - timedelta(days=59) # 59 if timeframe = 15m
pastDateAndTime = currentDateAndTime - timedelta(days=729) # 729 if timeframe = 1h
stryearpast = format(pastDateAndTime.year, '04')
strmonthpast = format(pastDateAndTime.month, '02')
strdaypast = format(pastDateAndTime.day, '02')

strStartDate = stryearpast + '-' + strmonthpast + '-' + strdaypast
strEndDate = stryear + '-' + strmonth + '-' + strday

print("Date range used :", strStartDate, strEndDate)

data_history_file = "eurusd_data_15m_" + strStartDate + "_" + strEndDate + ".pkl"

previous_prediction = 0
average_diff = 0
initial_close_price = 0

asset = "BTCUSDT"

#while True:

interval = Client.KLINE_INTERVAL_1MINUTE

print("downloading data")
# Préparer les données d'entrée
klinesT = Client(tld='us').get_historical_klines(asset, interval, "01 January 2023")
crypto_data = pd.DataFrame(klinesT, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av',
                                                'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
crypto_data['time'] = pd.to_datetime(crypto_data['time'], unit='ms')


# Préparer les données pour Fastai
# Gardons uniquement les colonnes nécessaires
crypto_data = crypto_data[['open', 'high', 'low', 'volume', 'close']]

# Convertir les colonnes en données numériques si nécessaire
crypto_data = crypto_data.apply(pd.to_numeric)

# Appliquer K-means avec 3 clusters
num_clusters = 3
kmeans = KMeans(n_clusters=num_clusters, random_state=42)
kmeans.fit(crypto_data)

# Obtenir les centres des clusters et les étiquettes de chaque point de données
centroids = kmeans.cluster_centers_
labels = kmeans.labels_

# Ajouter les étiquettes au DataFrame original
crypto_data['cluster'] = labels

# Afficher les centres des clusters
print("Centres des clusters :")
print(centroids)

# Afficher les points de données et leurs clusters sur un graphique 2D
plt.scatter(crypto_data['open'], crypto_data['close'], c=labels, cmap='rainbow')
plt.scatter(centroids[:, 0], centroids[:, 4], marker='X', s=200, c='black')
plt.xlabel('Open')
plt.ylabel('Close')
plt.title('K-means Clustering')
plt.show()
