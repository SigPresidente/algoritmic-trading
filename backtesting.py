# BACKTESTING TOOL FOR EVERY SYMBOL, CHECKS STRATEGY AND GENERATES P/L RESULTS

#Libraries
import pandas as pd

#Files
from account_data import *

#Added taxes for Italy
def apply_italy_tax(equity_series, dates):
    equity_after_tax = equity_series.copy()
    yearly_start_equity = INITIAL_DEPOSIT
    
    #Group by year
    years = dates.year.unique()
    
    for year in years:
        year_mask = dates.year == year
        year_dates = dates[year_mask]
        
        if len(year_dates) == 0:
            continue
            
        #Get last day of the year in our data
        last_day_idx = year_dates[-1]
        last_day_position = dates.get_loc(last_day_idx)
        
        if last_day_position >= len(equity_after_tax):
            continue
            
        year_end_equity = equity_after_tax.iloc[last_day_position]
        
        #Calculate gain for the year
        yearly_gain = year_end_equity - yearly_start_equity
        
        if yearly_gain > 0:
            #Apply 26% tax on gains
            tax_amount = yearly_gain * ITALY_CAPITAL_GAINS_TAX
            
            #Deduct tax from equity for all subsequent days
            equity_after_tax.iloc[last_day_position:] -= tax_amount
            
            #Update starting equity for next year (after tax)
            yearly_start_equity = equity_after_tax.iloc[last_day_position]
        else:
            #No tax on losses, but update starting equity for next year
            yearly_start_equity = year_end_equity
    
    return equity_after_tax

def backtest_symbol(symbol, profile):
    signals_path = f"{OUTPUT_DIR}/{symbol.lower().replace('^','')}_signals_{profile}.csv"
    df = pd.read_csv(signals_path, index_col='date', parse_dates=True).sort_index()

    if profile == 'pac':
        #PAC Strategy: Buy fixed amount monthly, never sell
        cash = INITIAL_DEPOSIT
        total_shares = 0
        equity = []
        trades = []
        
        for date, row in df.iterrows():
            price = row['close']
            signal = row['Signal']
            
            # Buy signal (first day of month)
            if signal == 1 and cash >= PAC_MONTHLY_INVESTMENT:
                # Account for commission when buying
                shares_to_buy = PAC_MONTHLY_INVESTMENT / (price * (1 + COMMISSION))
                commission_cost = shares_to_buy * price * COMMISSION
                total_shares += shares_to_buy
                cash -= PAC_MONTHLY_INVESTMENT
                trades.append({'date': date, 'action': 'buy', 'price': price, 'amount': PAC_MONTHLY_INVESTMENT, 'shares': shares_to_buy, 'commission': commission_cost})
            
            # Daily equity (cash + value of holdings)
            equity.append(cash + total_shares * price)
        
        # Apply Italy tax
        equity_series = pd.Series(equity, index=df.index)
        equity_after_tax = apply_italy_tax(equity_series, df.index)
        equity = equity_after_tax.tolist()
        
    else:
        #Original trading strategies
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
                commission_cost = position * sl_price * COMMISSION
                cash = position * sl_price - commission_cost
                trades.append({'date': date, 'action': 'sell (SL)', 'price': sl_price, 'pnl': pnl, 'commission': commission_cost})
                position = 0
            elif position < 0 and high >= sl_price:
                pnl = abs(position) * (entry_price - sl_price)
                commission_cost = abs(position) * sl_price * COMMISSION
                cash += abs(position) * sl_price - commission_cost
                trades.append({'date': date, 'action': 'buy (SL)', 'price': sl_price, 'pnl': pnl, 'commission': commission_cost})
                position = 0

            #New entries (only when flat)
            if position == 0:
                if signal == 1:                                      
                    shares = cash / (price * (1 + COMMISSION))  # Account for commission on entry
                    position = shares
                    entry_price = price
                    commission_cost = shares * price * COMMISSION
                    sl_price = price * (1 - STOP_LOSS)
                    max_price = price
                    trades.append({'date': date, 'action': 'buy', 'price': price, 'pnl': 0, 'commission': commission_cost})
                    cash = 0
                elif signal == -1 and allow_shorts:
                    shares = cash / (price * (1 + COMMISSION))  # Account for commission on entry
                    position = -shares
                    entry_price = price
                    commission_cost = shares * price * COMMISSION
                    sl_price = price * (1 + STOP_LOSS)
                    min_price = price
                    trades.append({'date': date, 'action': 'sell', 'price': price, 'pnl': 0, 'commission': commission_cost})
                    cash += shares * price - commission_cost

            #Daily equity
            equity.append(cash + position * price)
        
        # Apply Italy tax for trading strategies
        equity_series = pd.Series(equity, index=df.index)
        equity_after_tax = apply_italy_tax(equity_series, df.index)
        equity = equity_after_tax.tolist()

    #Save results
    equity_df = pd.DataFrame({'date': df.index, 'close': df['close'], 'equity': equity}).set_index('date')
    trades_df = pd.DataFrame(trades)

    equity_df.to_csv(f"{OUTPUT_DIR}/equity_curve_{symbol.lower().replace('^','')}_{profile}.csv")
    trades_df.to_csv(f"{OUTPUT_DIR}/backtest_trades_{symbol.lower().replace('^','')}_{profile}.csv", index=False)

    print(f"{symbol} — {profile} backtest completed (with Italy 26% tax)")
    
    #Summary calculations
    if profile == 'pac':
        total_invested = INITIAL_DEPOSIT + (len(trades) * PAC_MONTHLY_INVESTMENT)
        total_closed = len(trades)
        win_rate = 0  # N/A for PAC
    else:
        total_closed = len(trades_df[trades_df['pnl'] != 0]) if 'pnl' in trades_df.columns else 0
        winning_trades = len(trades_df[trades_df['pnl'] > 0]) if 'pnl' in trades_df.columns else 0
        win_rate = winning_trades / total_closed if total_closed > 0 else 0
    
    total_pnl = equity_df['equity'].iloc[-1] - INITIAL_DEPOSIT
    final_equity = equity_df['equity'].iloc[-1]
    
    #Print summary
    print(f"\n=== {symbol} {profile.upper()} (After Italy Tax) ===")
    print(f"Initial capital : ${INITIAL_DEPOSIT:,.2f}")
    if profile == 'pac':
        print(f"Total invested  : ${total_invested:,.2f}")
        print(f"Monthly buys    : {total_closed}")
    print(f"Final equity    : ${final_equity:,.2f}")
    print(f"Total P/L       : ${total_pnl:,.2f} ({total_pnl / INITIAL_DEPOSIT * 100:+.2f}%)")
    if profile != 'pac':
        print(f"Number of trades: {total_closed}")
        print(f"Win rate        : {win_rate:.1%}")
    print()

def main():
    for sym in SYMBOLS:
        for profile in PROFILES:
            backtest_symbol(sym, profile)

if __name__ == "__main__":
    main()