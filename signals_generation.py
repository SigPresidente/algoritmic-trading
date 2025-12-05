#USES HISTORICAL DATA TO CALCULATE A STRATEGY AND GENERATE SIGNALS

#STRATEGY: 1. Calculates short moving-average and long moving-average from .csv data for every symbol.
#          2. Confronts and finds crossovers. 
#          3. Generates buy/sell signals.
#          4. Considers RSI (Relative Strength Index) to avoid overbought/oversold conditions

#Libraries
import pandas as pd
import talib as ta

#Files
from account_data import *

#Config:
symbols = SYMBOLS
short_ma = SHORT_MA
long_ma = LONG_MA
rsi_period = RSI_PERIOD
rsi_overbought = RSI_OVERBOUGHT
rsi_oversold = RSI_OVERSOLD
output_dir = OUTPUT_DIR

#Load data:
def main() :
    for sym in symbols:
        csv_path = f"{output_dir}/{sym.lower().replace("^", "")}_historical.csv" 
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
            (df['RSI'] <= rsi_oversold),
            'Signal'
        ] = 1

        # Sell: MA down cross + RSI overbought (but disable for long-only)
        df.loc[
            ((df['SMA_short'] < df['SMA_long']) & (df['Prev_SMA_short'] >= df['Prev_SMA_long'])) &
            (df['RSI'] >= rsi_overbought),
            'Signal'
        ] = -1

#!DISABLE FOR SHORTS        
        # Long-only: Convert sells to holds
        df.loc[df['Signal'] == -1, 'Signal'] = 0

        # Drop helper columns and NaN rows
        df = df.drop(columns=['Prev_SMA_short', 'Prev_SMA_long'])
        df = df.dropna()

        # Preview results
        print(df[['close', 'SMA_short', 'SMA_long', 'RSI', 'Signal']].tail(10))

        # Save updated CSV with signals
        signals_path = f"{output_dir}/{sym.lower().replace('^', '')}_signals.csv"
        df.to_csv(signals_path, index_label="date")
        print(f"Signals saved to {signals_path}")

if __name__ == "__main__":
    main() 