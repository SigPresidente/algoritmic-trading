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
symbols = ["^NDX", "^FTMIB", "^GDAXI"] #Nasdaq-100 (USA) and FTSE MIB (IT) (or DAX30 eventually)
start_date = "2018-01-01"
end_date = datetime.now().strftime("%Y-%m-%d")
output_dir = "." #Inside project directory

#Try importing both data sources
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

def fetch_and_save_data(symbol) :
    file_path = f"{output_dir}/{symbol.lower().replace("^", "")}_historical.csv" #Creates a .csv file

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

#Execute function for whichever symbol:
for sym in symbols:
    data = fetch_and_save_data(sym)
    print(data.tail(5))  #Debugging