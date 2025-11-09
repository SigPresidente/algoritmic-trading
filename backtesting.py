import pandas as pd
from account_data import SYMBOLS  # Import your symbols list

# Config
initial_cash = 10000.0  # Starting capital
commission = 0.001  # 0.1% per trade
output_dir = "."  # Same as your CSVs

def backtest_symbol(symbol):
    signals_path = f"{output_dir}/{symbol.lower().replace('^', '')}_signals.csv"
    
    # Load signals CSV
    df = pd.read_csv(signals_path, index_col='date', parse_dates=True)
    df = df.sort_index()
    
    # Simulate trades
    position = 0  # 0 = no position, 1 = long
    equity = [initial_cash]
    trades = []  # List for trade details
    current_cash = initial_cash
    
    for i in range(1, len(df)):  # Start from 1 to calculate P/L
        signal = df['Signal'].iloc[i]
        prev_close = df['close'].iloc[i-1]
        close = df['close'].iloc[i]
        
        if signal == 1 and position == 0:  # Buy
            shares = current_cash / close * (1 - commission)
            position = 1
            current_cash = 0
            trades.append({'date': df.index[i], 'action': 'buy', 'price': close, 'pnl': 0})
        
        elif signal == -1 and position == 1:  # Sell
            pnl = shares * (close - prev_close) - (shares * close * commission)
            current_cash = shares * close * (1 - commission)
            position = 0
            trades.append({'date': df.index[i], 'action': 'sell', 'price': close, 'pnl': pnl})
        
        # Append daily equity (assuming hold value)
        if position == 1:
            equity.append(shares * close)
        else:
            equity.append(current_cash)
    
    # Create equity DF for graphs
    equity_df = pd.DataFrame({'date': df.index, 'equity': equity[1:], 'close': df['close']})  # Align lengths
    
    # Save results
    results_path = f"{output_dir}/backtest_results_{symbol.lower().replace('^', '')}.csv"
    pd.DataFrame(trades).to_csv(results_path, index=False)
    print(f"Trades saved to {results_path}")
    
    equity_path = f"{output_dir}/equity_curve_{symbol.lower().replace('^', '')}.csv"
    equity_df.to_csv(equity_path, index=False)
    print(f"Equity curve saved to {equity_path}")
    
    # Summary metrics
    total_pnl = sum(trade['pnl'] for trade in trades)
    num_trades = len(trades)
    win_rate = sum(1 for trade in trades if trade['pnl'] > 0) / num_trades if num_trades > 0 else 0
    print(f"Summary for {symbol}: Total P/L = {total_pnl:.2f}, Trades = {num_trades}, Win Rate = {win_rate:.2%}")

# Run for all symbols
for sym in SYMBOLS:
    backtest_symbol(sym)