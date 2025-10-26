#USES HISTORICAL DATA TO CALCULATE A STRATEGY AND GENERATE SIGNALS

#STRATEGY: Calculate SMA50 e SMA200 from .csv data for every symbol. Confront and find crossovers. Generate 1/-1/0 signals.
    #Added MACD (Moving Average Convergence/Divergence)
    #Added RSI (Relative Strength Index)
    #Added DMI (Directional Movement Index)

#Libraries
import pandas as pd
import talib as ta

#Files
from account_data import * #RESTRICT TO NEEDED
from import_data import *

#Config: 
csv_path = 'ndx_historical.csv'  # Or 'ftmib_historical.csv'
short_ma = 50  # Short-term MA
long_ma = 200  # Long-term MA
macd_fast = 12  # MACD fast EMA
macd_slow = 26  # MACD slow EMA
macd_signal = 9  # MACD signal EMA
rsi_period = 14  # RSI period
rsi_overbought = 70  # RSI sell threshold
rsi_oversold = 30    # RSI buy threshold
dmi_period = 14      # DMI period (standard)

#Load data:
df = pd.read_csv(csv_path, index_col='date', parse_dates=True)
df = df.sort_index()  # Ensure sorted by date
df = df.loc['2018-01-01':]  # Filter from 2018 to current (up to last in CSV)

#Calculate Moving Averages (SMA on Closing Price):
df['SMA_short'] = df['close'].rolling(window=short_ma).mean()
df['SMA_long'] = df['close'].rolling(window=long_ma).mean()

# Calculate MACD (Moving Average Convergence/Divergence):
macd = ta.trend.MACD(df['close'], window_fast=macd_fast, window_slow=macd_slow, window_sign=macd_signal)
df['MACD'] = macd.macd()
df['MACD_Signal'] = macd.macd_signal()

#Calculate RSI (Relative Strength Index):
rsi = ta.momentum.RSI(df['close'], window=rsi_period)
df['RSI'] = rsi

# Calculate DMI (+DI, -DI) using ta
dmi = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=dmi_period)
df['Plus_DI'] = dmi.adx_pos()
df['Minus_DI'] = dmi.adx_neg()

# Shift previous values for crossover detection
df['Prev_SMA_short'] = df['SMA_short'].shift(1)
df['Prev_SMA_long'] = df['SMA_long'].shift(1)
df['Prev_MACD'] = df['MACD'].shift(1)
df['Prev_MACD_Signal'] = df['MACD_Signal'].shift(1)
df['Prev_Plus_DI'] = df['Plus_DI'].shift(1)
df['Prev_Minus_DI'] = df['Minus_DI'].shift(1)

# Generate Signals: 1 = Buy (all confirm), -1 = Sell (all confirm), 0 = Hold
df['Signal'] = 0

# Buy: MA up cross + MACD up cross + RSI oversold + +DI up cross
df.loc[
    ((df['SMA_short'] > df['SMA_long']) & (df['Prev_SMA_short'] <= df['Prev_SMA_long'])) &
    ((df['MACD'] > df['MACD_Signal']) & (df['Prev_MACD'] <= df['Prev_MACD_Signal'])) &
    (df['RSI'] < rsi_oversold) &
    ((df['Plus_DI'] > df['Minus_DI']) & (df['Prev_Plus_DI'] <= df['Prev_Minus_DI'])),
    'Signal'
] = 1

# Sell: MA down cross + MACD down cross + RSI overbought + +DI down cross
df.loc[
    ((df['SMA_short'] < df['SMA_long']) & (df['Prev_SMA_short'] >= df['Prev_SMA_long'])) &
    ((df['MACD'] < df['MACD_Signal']) & (df['Prev_MACD'] >= df['Prev_MACD_Signal'])) &
    (df['RSI'] > rsi_overbought) &
    ((df['Plus_DI'] < df['Minus_DI']) & (df['Prev_Plus_DI'] >= df['Prev_Minus_DI'])),
    'Signal'
] = -1

# Drop helper columns and NaN rows
df = df.drop(columns=['Prev_SMA_short', 'Prev_SMA_long', 'Prev_MACD', 'Prev_MACD_Signal', 'Prev_Plus_DI', 'Prev_Minus_DI'])
df = df.dropna()

# Preview results
print(df[['close', 'SMA_short', 'SMA_long', 'MACD', 'MACD_Signal', 'RSI', 'Plus_DI', 'Minus_DI', 'Signal']].tail(10))

# Save updated CSV with signals
output_path = 'ndx_with_macd_rsi_dmi_signals.csv'
df.to_csv(output_path)
print(f"Signals saved to {output_path}")