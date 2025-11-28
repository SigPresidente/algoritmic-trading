#IMPORTS DATA FROM YFINANCE AND CREATES A .CSV FILE FOR PRICE HISTORY

#Libraries
import pandas as pd
from datetime import datetime, timedelta
import os

#Files
from account_data import *

#Config: account data and symbols
symbols = SYMBOLS #Import from account data file
start_date = "2018-01-01"
end_date = datetime.now().strftime("%Y-%m-%d")
output_dir = "." #Inside project directory

#Check correct installation
try:
    import yfinance as yf
    _HAS_YFINANCE = True
except ImportError:
    _HAS_YFINANCE = False
    print("yfinance not installed. Install with: pip install yfinance")


#FETCH FROM YFINANCE
def fetch_and_save_yfinance_data(symbol):
    file_path = f"{output_dir}/{symbol.lower().replace('^', '')}_historical.csv"  #Creates a .csv file

    if os.path.exists(file_path):
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        if df.index.max() >= (datetime.now() - timedelta(days=1)):
            print(f"Data for {symbol} loaded from yfinance cache (up-to-date).")
            return df
        else:
            print(f"Updating data for {symbol}.")
    else:
        df = pd.DataFrame()
        print(f"Fetching new data for {symbol}.")

    #Fetching data from yfinance
    new_data = yf.download(symbol, start=start_date, end=end_date)
    new_data.index = pd.to_datetime(new_data.index)

    #Standardize column (handle single or multi-level)
    if isinstance(new_data.columns, pd.MultiIndex):
        new_data.columns = new_data.columns.get_level_values(0).str.lower()
    else:
        new_data.columns = new_data.columns.str.lower()
    new_data = new_data[["open", "high", "low", "close", "volume"]]  # Select main columns

    #Data filtering and concat (if updating)
    df = pd.concat([df, new_data]).drop_duplicates().sort_index()

    #Save in .CSV format
    df.to_csv(file_path, index_label="date")
    print(f"Data for {symbol} saved to {file_path}.")
    return df

#Execute functions for both sources and for each symbol
def main():
    for sym in symbols:
        data_yfinance= fetch_and_save_yfinance_data(sym)
        print("FROM YFINANCE:", data_yfinance.tail(5)) #Check if function ran correctly

if __name__ == "__main__":
    main()
    