#USES HISTORICAL DATA TO CALCULATE A STRATEGY AND GENERATE SIGNALS

#STRATEGY: Calculate SMA50 e SMA200 from .csv data for every symbol. Confront and find crossovers. Generate 1/-1/0 signals.
    #REMOVED MACD (Moving Average Convergence/Divergence)
    #RELAXED RSI (Relative Strength Index)
    #REMOVED DMI (Directional Movement Index)

#Libraries
import pandas as pd
import talib as ta

#Files
from account_data import *

#Config:
symbols = SYMBOLS
short_ma = 50  # Short-term MA
long_ma = 200  # Long-term MA
rsi_period = 14  # RSI period
rsi_overbought = 50  # RSI sell threshold
rsi_oversold = 50    # RSI buy threshold

#Load data:
for sym in symbols:
    csv_path = f'{sym.lower().replace("^", "")}_historical.csv'
    df = pd.read_csv(csv_path, index_col='date', parse_dates=["date"])
    df = df.sort_index()  # Ensure sorted by date

    #Calculate Moving Averages (SMA on Closing Price):
    df['SMA_short'] = df['close'].rolling(window=short_ma).mean()
    df['SMA_long'] = df['close'].rolling(window=long_ma).mean()

    #Calculate RSI (Relative Strength Index):
    df['RSI'] = ta.RSI(df['close'].values, timeperiod=rsi_period)

    # Shift previous values for crossover detection
    df['Prev_SMA_short'] = df['SMA_short'].shift(1)
    df['Prev_SMA_long'] = df['SMA_long'].shift(1)

    # Generate Signals: 1 = Buy (all confirm), -1 = Sell (all confirm), 0 = Hold
    df['Signal'] = 0

    # Buy: MA up cross + RSI oversold
    df.loc[
        ((df['SMA_short'] > df['SMA_long']) & (df['Prev_SMA_short'] <= df['Prev_SMA_long'])) &
        (df['RSI'] < rsi_oversold),
        'Signal'
    ] = 1

    # Sell: MA down cross + RSI overbought
    df.loc[
        ((df['SMA_short'] < df['SMA_long']) & (df['Prev_SMA_short'] >= df['Prev_SMA_long'])) &
        (df['RSI'] > rsi_overbought),
        'Signal'
    ] = -1

    # Drop helper columns and NaN rows
    df = df.drop(columns=['Prev_SMA_short', 'Prev_SMA_long'])
    df = df.dropna()

    # Preview results
    print(df[['close', 'SMA_short', 'SMA_long', 'RSI', 'Signal']].tail(10))

    # Save updated CSV with signals
    output_path = f"{sym.lower().replace('^', '')}_signals.csv"
    df.to_csv(output_path, index_label="date")
    print(f"Signals saved to {output_path}")