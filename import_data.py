#Importa dati da Alpha Vantage, da integrare con dati storici da YahooFinance

from account_data import *
import pandas as pd
from alpha_vantage.timeseries import TimeSeries

api_key = ALPHA_API_KEY
ts = TimeSeries(key=api_key, output_format='pandas')
data, meta = ts.get_daily(symbol='^NDX', outputsize='full')  # NASDAQ-100
#print(data.head())  # OHLCV data

print(f"API KEY DI ALPHA: {api_key}")