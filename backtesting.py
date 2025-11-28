# BACKTESTING TOOL FOR EVERY SYMBOL, CHECKS STRATEGY AND GENERATES P/L RESULTS

#Libraries
import pandas as pd

#Files
from account_data import SYMBOLS

#Config
initial_cash = 5000.0
commission = 0.005  #0.5 % (realistic for robo-advisors)
sl_percent = 0.02  # 2% SL fixed
tp_percent = 0.04  # 4% TP fixed (1:2 ratio)
output_dir = "."

def backtest_symbol(symbol):
    signals_path = f"{output_dir}/{symbol.lower().replace('^', '')}_signals.csv"
    
    #Load signals .csv
    df = pd.read_csv(signals_path, index_col='date', parse_dates=True)
    df = df.sort_index()
    
    #Simulation variables
    position = 0 #0 = flat, >0 = long shares, <0 = short shares
    cash = initial_cash
    entry_price = 0.0
    sl_price = 0.0
    tp_price = 0.0
    
    equity = []
    trades = []

    for date, row in df.iterrows():
        price = row['close']
        signal = row['Signal']
        high = row['high']  # Use for SL/TP hits (realistic intraday check)
        low = row['low']
        
        # --- CHECK SL/TP FIRST (if in position) ---
        if position > 0:  # Long
            if low <= sl_price:  # Hit SL
                pnl = position * (sl_price - entry_price) - abs(position) * sl_price * commission
                cash = position * sl_price * (1 - commission)
                trades.append({'date': date, 'action': 'sell (SL)', 'price': sl_price, 'pnl': pnl})
                position = 0
            elif high >= tp_price:  # Hit TP
                pnl = position * (tp_price - entry_price) - abs(position) * tp_price * commission
                cash = position * tp_price * (1 - commission)
                trades.append({'date': date, 'action': 'sell (TP)', 'price': tp_price, 'pnl': pnl})
                position = 0
        
        elif position < 0:  # Short
            if high >= sl_price:  # Hit SL (price up)
                pnl = abs(position) * (entry_price - sl_price) - abs(position) * sl_price * commission
                cash = abs(position) * sl_price * (1 - commission)
                trades.append({'date': date, 'action': 'buy (SL)', 'price': sl_price, 'pnl': pnl})
                position = 0
            elif low <= tp_price:  # Hit TP (price down)
                pnl = abs(position) * (entry_price - tp_price) - abs(position) * tp_price * commission
                cash = abs(position) * tp_price * (1 - commission)
                trades.append({'date': date, 'action': 'buy (TP)', 'price': tp_price, 'pnl': pnl})
                position = 0
        
        # --- EXECUTE SIGNALS (only if flat) ---
        if signal == 1 and position == 0:           # BUY (open long)
            shares = cash / price * (1 - commission)
            position = shares
            entry_price = price
            sl_price = price * (1 - sl_percent)
            tp_price = price * (1 + tp_percent)
            trades.append({'date': date, 'action': 'buy', 'price': price, 'pnl': 0})
            cash = 0.0
        
        elif signal == -1 and position == 0:         # SELL (open short)
            shares = cash / price * (1 - commission)
            position = -shares  # Negative for short
            entry_price = price
            sl_price = price * (1 + sl_percent)  # SL above entry
            tp_price = price * (1 - tp_percent)  # TP below entry
            trades.append({'date': date, 'action': 'sell', 'price': price, 'pnl': 0})
            cash = 0.0  # Cash "locked" in short (simplified)
        
        # --- DAILY EQUITY ---
        if position > 0:  # Long value
            current_value = cash + position * price
        elif position < 0:  # Short value (profit if price down)
            current_value = cash + abs(position) * (entry_price - price)
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
def main():
    for sym in SYMBOLS:
        backtest_symbol(sym)

if  __name__ == "__main__":
    main()