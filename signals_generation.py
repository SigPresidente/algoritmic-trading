#USES HISTORICAL DATA TO CALCULATE A STRATEGY AND GENERATE SIGNALS

#STRATEGY: Calculate SMA50 e SMA200 from .csv data for every symbol. Confront and find crossovers. Generate 1/-1/0 signals.
    #Added MACD (Moving Average Convergence/Divergence)

#Libraries
import pandas as pd
import ta

#Files
from import_data import *

#Config: 
csv_path = 'ndx_historical.csv'  # Or 'ftmib_historical.csv'
short_window = 50  # Short-term MA
long_window = 200  # Long-term MA
macd_fast = 12  # MACD fast EMA
macd_slow = 26  # MACD slow EMA
macd_signal = 9  # MACD signal EMA

#Load data:
df = pd.read_csv(csv_path, index_col='date', parse_dates=True)
df = df.sort_index()  # Ensure sorted by date
df = df.loc['2018-01-01':]  # Filter from 2018 to current (up to last in CSV)

#Calculate Moving Averages (SMA on Closing Price):
df['SMA_short'] = df['close'].rolling(window=short_window).mean()
df['SMA_long'] = df['close'].rolling(window=long_window).mean()

# Calculate MACD (Moving Average Convergence/Divergence):
macd = ta.trend.MACD(df['close'], window_fast=macd_fast, window_slow=macd_slow, window_sign=macd_signal)
df['MACD'] = macd.macd()
df['MACD_Signal'] = macd.macd_signal()

# Shift previous values for crossover detection
df['Prev_SMA_short'] = df['SMA_short'].shift(1)
df['Prev_SMA_long'] = df['SMA_long'].shift(1)
df['Prev_MACD'] = df['MACD'].shift(1)
df['Prev_MACD_Signal'] = df['MACD_Signal'].shift(1)

# Buy: MA crossover up AND MACD crossover up
df.loc[
    ((df['SMA_short'] > df['SMA_long']) & (df['Prev_SMA_short'] <= df['Prev_SMA_long'])) &
    ((df['MACD'] > df['MACD_Signal']) & (df['Prev_MACD'] <= df['Prev_MACD_Signal'])),
    'Signal'
] = 1

# Sell: MA crossover down AND MACD crossover down
df.loc[
    ((df['SMA_short'] < df['SMA_long']) & (df['Prev_SMA_short'] >= df['Prev_SMA_long'])) &
    ((df['MACD'] < df['MACD_Signal']) & (df['Prev_MACD'] >= df['Prev_MACD_Signal'])),
    'Signal'
] = -1

# Drop helper columns and NaN rows
df = df.drop(columns=['Prev_SMA_short', 'Prev_SMA_long', 'Prev_MACD', 'Prev_MACD_Signal'])
df = df.dropna()

# Preview results
print(df[['close', 'SMA_short', 'SMA_long', 'MACD', 'MACD_Signal', 'Signal']].tail(10))

# Save updated CSV with signals
output_path = 'ndx_with_macd_signals.csv'
df.to_csv(output_path)
print(f"Signals saved to {output_path}")