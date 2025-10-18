#Importa dati da Alpha Vantage (limitati/pagamento), da integrare con dati storici da yahoofinance

import pandas as pd
from alpha_vantage.timeseries import TimeSeries

api_key = 'YOUR_API_KEY'  # Sostituisci con tua key
ts = TimeSeries(key=api_key, output_format='pandas')
data, meta = ts.get_daily(symbol='^NDX', outputsize='full')  # NASDAQ-100
print(data.head())  # OHLCV data