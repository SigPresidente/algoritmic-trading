#IMPORTS DATA FROM ALPHA_VANTAGE AND CREATES A .CSV FILE FOR PRICE HISTORY

#Libraries
import pandas as pd
from datetime import datetime, timedelta
import os

#Files
from account_data import * #RESTRICT TO NEEDED
from signals_generation import *

#Config: account data and symbols
api_key = ALPHA_API_KEY
symbols = "^NDX" #Nasdaq-100 (USA) and FTSE MIB (IT) (or DAX30 eventually)
start_date = "2018-01-01"
end_date = datetime.now().strftime("%Y-%m-%d")
output_dir = "." #Inside project directory

#Check correct installation
try:
    from alpha_vantage.timeseries import TimeSeries
    _HAS_ALPHA_VANTAGE = True
except ImportError:
    _HAS_ALPHA_VANTAGE = False
    print("Alpha Vantage not installed. Install with: pip install alpha-vantage")

try:
    import yfinance as yf
    _HAS_YFINANCE = True
except ImportError:
    _HAS_YFINANCE = False
    print("yfinance not installed. Install with: pip install yfinance")


#FETCH FROM ALPHA VANTAGE
def fetch_and_save_alpha_vantage_data(symbol) :
    file_path = f"{output_dir}/{symbol.lower().replace("^", "")}_alpha_vantage_historical.csv" #Creates a .csv file

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

    #Fetching data from Alpha Vantage
    ts = TimeSeries(key=api_key, output_format='pandas')
    new_data, _ = ts.get_daily(symbol=symbol, outputsize='full')
    new_data.index = pd.to_datetime(new_data.index)
    new_data.columns = ["open", "high", "low", "close", "volume"] #Prendo questi 5 dati principali in tabella

    #Data filtering
    new_data = new_data[(new_data.index >= start_date) & (new_data.index <= end_date)]
    df = pd.concat([df, new_data]).drop_duplicates().sort_index()
    
    #Save in .CSV format
    df.to_csv(file_path)
    print(f"Data for {symbol} saved to {file_path}.")
    return df


#FETCH FROM YFINANCE
def fetch_and_save_yfinance_data(symbol):
    file_path = f"{output_dir}/{symbol.lower().replace('^', '')}_yfinance_historical.csv"  # Different name for yfinance source

    if os.path.exists(file_path):
        df = pd.read_csv(file_path, index_col="date", parse_dates=True)
        if df.index.max() >= (datetime.now() - timedelta(days=1)):
            print(f"Data for {symbol} loaded from yfinance cache (up-to-date).")
            return df
        else:
            print(f"Updating data for {symbol} from yfinance.")
    else:
        df = pd.DataFrame()
        print(f"Fetching new data for {symbol} from yfinance.")

    # Fetching data from yfinance
    new_data = yf.download(symbol, start=start_date, end=end_date)
    new_data.index = pd.to_datetime(new_data.index)
    new_data.columns = [col.lower() for col in new_data.columns]  #Standardize column names
    new_data = new_data[["open", "high", "low", "close", "volume"]]  #Select main columns

    # Data filtering and concat (if updating)
    df = pd.concat([df, new_data]).drop_duplicates().sort_index()

    # Save in .CSV format
    df.to_csv(file_path)
    print(f"Data for {symbol} saved to {file_path} (yfinance source).")
    return df

#Execute functions for both sources and for each symbol
for sym in symbols:
    data_yfinance= fetch_and_save_yfinance_data(sym)
    data_alphavantage = fetch_and_save_alpha_vantage_data(sym)
    print("FROM YFINANCE:", data_yfinance.tail(5), "FROM ALPHA VANTAGE:", data_alphavantage.tail(5)) #Debugging
    
    