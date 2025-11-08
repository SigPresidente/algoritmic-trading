import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('equity_curve.csv', index_col=0, parse_dates=True)
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['Equity'], label='Strategy Equity')
plt.plot(df.index, df['close'], label='NASDAQ-100 Close')
plt.title('Backtest Equity Curve vs. Benchmark (2018-2025)')
plt.xlabel('Date')
plt.ylabel('Value')
plt.legend()
plt.grid(True)
plt.show()