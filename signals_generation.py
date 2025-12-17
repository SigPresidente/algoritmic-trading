#USES HISTORICAL DATA TO CALCULATE A STRATEGY AND GENERATE SIGNALS, BASED ON PROFILE RISK

#STRATEGY: 1. Calculates short moving-average and long moving-average from .csv data for every symbol.
#          2. Confronts and finds crossovers. 
#          3. Generates buy/sell signals.
#          4. Considers RSI (Relative Strength Index) to avoid overbought/oversold conditions
#          5. PAC profile: Monthly buy-and-hold strategy

#Libraries
import pandas as pd
import talib as ta

#Files
from account_data import *

#Load data
def main():
    for sym in SYMBOLS:
        base_path = f"{OUTPUT_DIR}/{sym.lower().replace('^', '')}_historical.csv"
        df_base = pd.read_csv(base_path, index_col='date', parse_dates=True).sort_index()

        for idx, profile in enumerate(PROFILES):
            df = df_base.copy()

            if profile == 'pac':
                # PAC strategy: Buy signal on first trading day of each month
                df['Signal'] = 0
                df['year_month'] = df.index.to_period('M')
                
                # Mark first trading day of each month with buy signal
                first_days = df.groupby('year_month').head(1).index
                df.loc[first_days, 'Signal'] = 1
                
                df = df.drop(columns=['year_month'])
                
                # Save and continue to next profile (skip moving average calculations)
                out_path = f"{OUTPUT_DIR}/{sym.lower().replace('^', '')}_signals_{profile}.csv"
                df.to_csv(out_path)
                print(f"{sym} — {profile} signals → {out_path}")
                continue
                
            else:
                # Load parameters for this risk profile
                short_ma = SHORT_MA[idx]
                long_ma  = LONG_MA[idx]
                rsi_period = RSI_PERIOD[idx]
                overbought = RSI_OVERBOUGHT[idx]
                oversold   = RSI_OVERSOLD[idx]

                # Indicators
                df['SMA_short'] = df['close'].rolling(short_ma).mean()
                df['SMA_long']  = df['close'].rolling(long_ma).mean()
                df['RSI'] = ta.RSI(df['close'], timeperiod=rsi_period)

                # Crossover detection
                df['Prev_short'] = df['SMA_short'].shift(1)
                df['Prev_long']  = df['SMA_long'].shift(1)

                df['Signal'] = 0

                #Buy signal
                df.loc[(df['SMA_short'] > df['SMA_long']) &
                       (df['Prev_short'] <= df['Prev_long']) &
                       (df['RSI'] <= oversold), 'Signal'] = 1

                #Sell signal
                df.loc[(df['SMA_short'] < df['SMA_long']) &
                       (df['Prev_short'] >= df['Prev_long']) &
                       (df['RSI'] >= overbought), 'Signal'] = -1

                #Low-risk profile (only long positions)
                if profile == 'low':
                    df.loc[df['Signal'] == -1, 'Signal'] = 0

                # Clean
                df = df.drop(columns=['Prev_short', 'Prev_long'])

            # Save (for non-PAC profiles, since PAC already saved above)
            df = df.dropna()
            out_path = f"{OUTPUT_DIR}/{sym.lower().replace('^', '')}_signals_{profile}.csv"
            df.to_csv(out_path)
            print(f"{sym} — {profile} signals → {out_path}")

if __name__ == "__main__":
    main()