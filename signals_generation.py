#Genera segnali dai dati importati

import pandas as pd
import yfinance as yf
import ta  # ta-lib da verificare

# Scarica dati
data = yf.download('^NDX', start='2018-01-01', end='2025-10-12')
data['SMA50'] = data['Close'].rolling(window=50).mean()
data['SMA200'] = data['Close'].rolling(window=200).mean()

# Genera segnali
data['Signal'] = 0
data.loc[data['SMA50'] > data['SMA200'], 'Signal'] = 1  # Buy
data.loc[data['SMA50'] < data['SMA200'], 'Signal'] = -1 # Sell

# Stampa ultimi segnali
print(data[['Close', 'SMA50', 'SMA200', 'Signal']].tail(10))