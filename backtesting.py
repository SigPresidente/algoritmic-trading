# BACKTESTING TOOL FOR EVERY SYMBOL, CHECKS STRATEGY AND GENERATES P/L RESULTS

#Libraries
import pandas as pd

#Files
from account_data import *

def backtest_symbol(symbol, profile):
    signals_path = f"{OUTPUT_DIR}/{symbol.lower().replace('^','')}_signals_{profile}.csv"
    df = pd.read_csv(signals_path, index_col='date', parse_dates=True).sort_index()

    cash = INITIAL_DEPOSIT
    position = 0
    entry_price = sl_price = max_price = min_price = 0.0
    allow_shorts = profile != 'low' #Low risk only goes long

    equity = []
    trades = []

    for date, row in df.iterrows():
        price, high, low, signal = row['close'], row['high'], row['low'], row['Signal']

        #Trailing stop update
        if position > 0:                                    
            max_price = max(max_price, high)
            sl_price = max(sl_price, max_price * (1 - TRAIL_PERCENT))
        elif position < 0:                                 
            min_price = min(min_price, low)
            sl_price = min(sl_price, min_price * (1 + TRAIL_PERCENT))

        #Stop-loss check
        if position > 0 and low <= sl_price:
            pnl = position * (sl_price - entry_price)
            cash = position * sl_price
            trades.append({'date': date, 'action': 'sell (SL)', 'price': sl_price, 'pnl': pnl})
            position = 0
        elif position < 0 and high >= sl_price:
            pnl = abs(position) * (entry_price - sl_price)
            cash += abs(position) * sl_price
            trades.append({'date': date, 'action': 'buy (SL)', 'price': sl_price, 'pnl': pnl})
            position = 0

        #New entries (only when flat)
        if position == 0:
            if signal == 1:                                      
                shares = cash / price
                position = shares
                entry_price = price
                sl_price = price * (1 - STOP_LOSS)
                max_price = price
                trades.append({'date': date, 'action': 'buy', 'price': price, 'pnl': 0})
                cash = 0
            elif signal == -1 and allow_shorts:                  
                shares = cash / price
                position = -shares
                entry_price = price
                sl_price = price * (1 + STOP_LOSS)
                min_price = price
                trades.append({'date': date, 'action': 'sell', 'price': price, 'pnl': 0})
                cash += shares * price

        #Daily equity
        equity.append(cash + position * price)

    #Save results
    equity_df = pd.DataFrame({'date': df.index, 'close': df['close'], 'equity': equity}).set_index('date')
    trades_df = pd.DataFrame(trades)

    equity_df.to_csv(f"{OUTPUT_DIR}/equity_curve_{symbol.lower().replace('^','')}_{profile}.csv")
    trades_df.to_csv(f"{OUTPUT_DIR}/backtest_trades_{symbol.lower().replace('^','')}_{profile}.csv")

    print(f"{symbol} – {profile} backtest completed")
    
    #Summary calculations
    total_closed = len(trades_df[trades_df['pnl'] != 0]) if 'pnl' in trades_df.columns else 0
    winning_trades = len(trades_df[trades_df['pnl'] > 0]) if 'pnl' in trades_df.columns else 0
    win_rate = winning_trades / total_closed if total_closed > 0 else 0
    total_pnl = equity_df['equity'].iloc[-1] - INITIAL_DEPOSIT
    final_equity = equity_df['equity'].iloc[-1]
    
    #Print summary
    print(f"\n=== {symbol} {profile} ===")
    print(f"Initial capital : ${INITIAL_DEPOSIT:,.2f}")
    print(f"Final equity    : ${final_equity:,.2f}")
    print(f"Total P/L       : ${total_pnl:,.2f} ({total_pnl / INITIAL_DEPOSIT * 100:+.2f}%)")
    print(f"Number of round-trip trades : {total_closed}")
    print(f"Win rate        : {win_rate:.1%}\n")

def main():
    for sym in SYMBOLS:
        for profile in PROFILES:
            backtest_symbol(sym, profile)

if __name__ == "__main__":
    main()