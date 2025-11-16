#BACKTESTING TOOL FOR EVERY SYMBOL, CHECKS STRATEGY AND GENERATES P/L RESULTS

#Libraries
import pandas as pd
from account_data import SYMBOLS

#Config
initial_cash = 5000.0
commission = 0.005  #0.5 % (realistic for robo-advisors)
output_dir = "."

def backtest_symbol(symbol):
    signals_path = f"{output_dir}/{symbol.lower().replace('^', '')}_signals.csv"
    
    #Load signals .csv
    df = pd.read_csv(signals_path, index_col='date', parse_dates=True)
    df = df.sort_index()
    
    #Simulation variables
    position = 0 #0 = no position, 1 = long
    cash = initial_cash
    shares = 0.0
    entry_price = 0.0
    
    equity = []
    trades = []

    for date, row in df.iterrows():
        price = row['close']
        signal = row['Signal']
        
        # --- EXECUTE SIGNALS ---
        if signal == 1 and position == 0:           # BUY
            shares = cash / price * (1 - commission)
            cash = 0.0
            position = 1
            entry_price = price
            trades.append({'date': date, 'action': 'buy', 'price': price, 'shares': shares})
        
        elif signal == -1 and position == 1:         # SELL
            proceeds = shares * price * (1 - commission)
            pnl = proceeds - (shares * entry_price)
            cash = proceeds
            trades.append({'date': date, 'action': 'sell', 'price': price, 'pnl': pnl})
            shares = 0.0
            position = 0
        
        # --- DAILY EQUITY ---
        if position == 1:
            current_value = shares * price
        else:
            current_value = cash
        
        equity.append(current_value)
    
    # Build final DataFrames
    equity_df = pd.DataFrame({
        'date': df.index,
        'close': df['close'],
        'equity': equity
    }).set_index('date')
    
    trades_df = pd.DataFrame(trades)
    
    #Save results
    equity_path = f"{output_dir}/equity_curve_{symbol.lower().replace('^', '')}.csv"
    equity_df.to_csv(equity_path)
    print(f"Equity curve → {equity_path}")
    
    trades_path = f"{output_dir}/backtest_trades_{symbol.lower().replace('^', '')}.csv"
    trades_df.to_csv(trades_path)
    print(f"Trades log    → {trades_path}")
    
    #Summary
    total_pnl = equity_df['equity'].iloc[-1] - initial_cash
    num_trades = len(trades_df)
    winning_trades = len(trades_df[trades_df['pnl'] > 0]) if 'pnl' in trades_df.columns else 0
    win_rate = winning_trades / (num_trades / 2) if num_trades > 0 else 0   # each pair = 1 trade
    
    print(f"\n=== {symbol} ===")
    print(f"Initial capital : ${initial_cash:,.2f}")
    print(f"Final equity    : ${equity_df['equity'].iloc[-1]:,.2f}")
    print(f"Total P/L       : ${total_pnl:,.2f} ({total_pnl/initial_cash*100:+.2f}%)")
    print(f"Number of round-trip trades : {num_trades//2}")
    print(f"Win rate        : {win_rate:.1%}\n")

#Run for all symbols
for sym in SYMBOLS:
    backtest_symbol(sym)