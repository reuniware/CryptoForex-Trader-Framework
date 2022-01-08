# Number of threads running simultaneously is controlled with the variable maxthreads :)

import glob
import os
import sqlite3
import threading
import time
from datetime import datetime

import ftx
import pandas as pd
import requests

import_to_database = True  # only works with maxthreads = 1 (will be if import_to_database = True) or for one (of very few) symbol (filter symbols in the main_thread
delete_db_at_startup = False
max_block_of_5000_download = -1  # set to -1 for unlimited blocks (all data history)
log_data_history_to_files = False  # This option is for logging data history to one file per symbol (eg. scan_ETH_USD.txt)
# log_scan_results_to_files = True  # This option if for logging the scan results to one file per symbol (at the bottom of eg. scan_ETH_USD.txt)
maxthreads = 50

if import_to_database:
    maxthreads = 1
    print("maxthread forced to " + str(maxthreads) + " because of import_to_database is active")


def log_to_results(str_to_log):
    fr = open("results.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_errors(str_to_log):
    fr = open("errors.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_trades(str_to_log):
    fr = open("trades.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_evol(str_to_log):
    fr = open("evol.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_debug(str_to_log):
    fr = open("debug.txt", "a")
    fr.write(str_to_log + "\n")
    fr.close()


def log_to_file(str_file, str_to_log):
    fr = open(str_file, "a")
    fr.write(str_to_log + "\n")
    fr.close()


ftx_client = ftx.FtxClient(
    api_key='',
    api_secret='',
    subaccount_name=''
)

# result = client.get_balances()
# print(result)

if os.path.exists("results.txt"):
    os.remove("results.txt")

if os.path.exists("errors.txt"):
    os.remove("errors.txt")

if os.path.exists("trades.txt"):
    os.remove("trades.txt")

if os.path.exists("evol.txt"):
    os.remove("evol.txt")

for fg in glob.glob("CS_*.txt"):
    os.remove(fg)

for fg in glob.glob("scan_*.txt"):
    os.remove(fg)

for fg in glob.glob("debug.txt"):
    os.remove(fg)

if import_to_database:
    if delete_db_at_startup:
        for fg in glob.glob("data_history.db"):
            os.remove(fg)

stop_thread = False

if import_to_database:
    con = sqlite3.connect('data_history.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS history (date text, symbol text, timeframe text, open real, high real, low real, close real)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS history_pk ON history (date, symbol, timeframe)")
    con.commit()
    con.close()


def execute_code(symbol):
    global log_data_history_to_files
    # print("scan one : " + symbol)

    resolution = 60 * 60 * 1  # set the resolution of one japanese candlestick here
    timeframe = "H1"  # used for inserting into SQLITE database
    # max_block_of_5000_download = 1  # set to -1 for unlimited blocks (all data history)

    unixtime_endtime = time.time()
    converted_endtime = datetime.utcfromtimestamp(unixtime_endtime)
    # print("current unix time = " + str(unixtime_endtime))
    # print("converted_endtime = " + str(converted_endtime))
    tosubtract = resolution * 5000  # 60 * 60 * 1 * 5000
    # print("to substract in seconds = " + str(tosubtract))
    newunixtime_starttime = unixtime_endtime - tosubtract
    converted_starttime = datetime.utcfromtimestamp(newunixtime_starttime)
    # print("new unix time = " + str(newunixtime_starttime))
    # print("new converted_starttime = " + str(converted_starttime))

    data = []

    end_of_data_reached = False

    symbol_filename = "scan_" + str.replace(symbol, "-", "_").replace("/", "_") + ".txt"

    current_block_of_5000_download = 0
    max_block_of_5000_download_reached = False

    while not end_of_data_reached and not max_block_of_5000_download_reached:

        downloaded_data = ftx_client.get_historical_data(
            market_name=symbol,
            resolution=resolution,
            limit=1000000,
            start_time=newunixtime_starttime,
            end_time=unixtime_endtime)

        converted_endtime = datetime.utcfromtimestamp(unixtime_endtime)
        converted_starttime = datetime.utcfromtimestamp(newunixtime_starttime)

        print(symbol + " : downloaded_data size = " + str(len(downloaded_data)) + " from " + str(converted_starttime) + " to " + str(converted_endtime))
        data.extend(downloaded_data)

        unixtime_endtime = newunixtime_starttime
        newunixtime_starttime = newunixtime_starttime - tosubtract

        if len(downloaded_data) == 0:
            print(symbol + " : end of data from server reached")
            end_of_data_reached = True

        if max_block_of_5000_download != -1:
            current_block_of_5000_download += 1
            if current_block_of_5000_download >= max_block_of_5000_download:
                print(symbol + " : max number of block of 5000 reached")
                max_block_of_5000_download_reached = True

    if import_to_database:
        con2 = sqlite3.connect('data_history.db', timeout=5)
        cur2 = con2.cursor()

    # if log_data_history_to_files:
    for oneline in data:

        if log_data_history_to_files:
            log_to_file(symbol_filename, str(oneline))

        if import_to_database:
            try:
                cur2.execute("SELECT * FROM history WHERE date = ? and symbol = ? and timeframe = ?", [oneline['startTime'], symbol, timeframe])
                data = cur2.fetchone()
                if data is None:
                    # print("There is no record with", oneline['startTime'], symbol, timeframe)
                    cur2.execute("INSERT INTO history VALUES (?,?,?,?,?,?,?)",
                                 [oneline['startTime'], symbol, timeframe, oneline['open'], oneline['high'], oneline['low'], oneline['close']])
                else:
                    # print("There is already a record with", oneline['startTime'], symbol, "H1")
                    pass
            except sqlite3.IntegrityError:
                pass
            except sqlite3.OperationalError:  # database is locked (the number of parallel threads should be decreased)
                log_to_errors(
                    "(threading problem with sqlite) insert error for " + oneline['startTime'] + " " + symbol + " " + timeframe + " " + str(oneline['open']) + " " + str(
                        oneline['high']) + " " +
                    str(oneline['low']) + " " + str(oneline['close']))
                pass

    if import_to_database:
        con2.commit()
        con2.close()


# maxthreads = 5
threadLimiter = threading.BoundedSemaphore(maxthreads)


def scan_one(symbol):
    threadLimiter.acquire()
    try:
        execute_code(symbol)
    finally:
        threadLimiter.release()


threads = []


def main_thread(name):
    global ftx_client, list_results, results_count, num_req, stop_thread

    print(str(datetime.now()) + " All threads starting.")
    log_to_results(str(datetime.now()) + " All threads starting.")

    markets = requests.get('https://ftx.com/api/markets').json()
    df = pd.DataFrame(markets['result'])
    df.set_index('name')

    for index, row in df.iterrows():
        symbol = row['name']
        # symbol_type = row['type']

        # filter for specific symbols here
        # if not symbol == "ETH/USD":
        #     continue

        # if not symbol.endswith("/USD"):
        #     continue

        try:
            t = threading.Thread(target=scan_one, args=(symbol,))
            threads.append(t)
            t.start()
        except requests.exceptions.ConnectionError:
            continue

    for tt in threads:
        tt.join()

    print(str(datetime.now()) + " All threads finished.")
    log_to_results(str(datetime.now()) + " All threads finished.")

    time.sleep(1)

    stop_thread = True


x = threading.Thread(target=main_thread, args=(1,))
x.start()
