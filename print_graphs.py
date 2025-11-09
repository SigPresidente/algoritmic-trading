import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('equity_curve_ndx.csv')
df['date'] = pd.to_datetime(df['date'])
plt.plot(df['date'], df['equity'], label='Equity')
plt.plot(df['date'], df['close'], label='Close Price')
plt.title('Equity Curve vs. Close Price')
plt.xlabel('Date')
plt.ylabel('Value')
plt.legend()
plt.grid(True)
plt.show()