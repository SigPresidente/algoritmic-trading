#Importa dati da Alpha Vantage e crea storage file .csv per ogni simbolo
# (da integrare eventualmente con dati storici da YahooFinance se offline)

from account_data import *
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta
import os

#Config: dati account e creo cache storico dati, verifico se aggiornati
api_key = ALPHA_API_KEY
symbols = ["^NDX", "^FTMIB"] #Utilizziamo Nasdaq-100 (USA) e FTSE MIB (IT)
start_date = "2018-01-01" #Prendo come esempio 2018-oggi
end_date = datetime.now().strftime("%Y-%m-%d")
output_dir = "." #Directory generica, DA VERIFICARE

def fetch_and_save_data(symbol) :
    file_path = f"{output_dir}/{symbol.lower().replace("^", "")}_historical.csv" #Creo un file .csv con dati storici

    if os.path.exists(file_path) :
        df = pd.read_csv(file_path, index_col="date", parse_dates=True)
        if df.index.max() >= (datetime.now() - timedelta(days=1)) :
            print(f"Data for {symbol} loaded from cache (up-to-date).")
            return df
        else :
            print(f"Fetching new data for {symbol}")
    else :
        df = pd.DataFrame()
        print(f"Fetching new data for {symbol}")

    #Fetching dati da Alpha Vantage
    ts = TimeSeries(key=api_key, output_format='pandas')
    new_data, _ = ts.get_daily(symbol=symbol, outputsize='full')
    new_data.index = pd.to_datetime(new_data.index)
    new_data.columns = ["open", "high", "low", "close", "volume"] #Prendo questi 5 dati principali in tabella

    # Filtra dati solo dal 2018 ad oggi
    new_data = new_data[(new_data.index >= start_date) & (new_data.index <= end_date)]
    df = pd.concat([df, new_data]).drop_duplicates().sort_index()
    
    # Salva file formato CSV
    df.to_csv(file_path)
    print(f"Data for {symbol} saved to {file_path}.")
    return df

# Eseguo funzione per entrambi i simboli (NASDAQ e FTSE MIB)
for sym in symbols:
    data = fetch_and_save_data(sym)
    print(data.tail(5))  # Stampa le ultime 5 righe