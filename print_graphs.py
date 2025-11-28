# PRINTS GRAPHS FOR STUDY PURPOSES AND SAVES THEM AS PNG FOR THESIS

import pandas as pd
import matplotlib.pyplot as plt
from account_data import SYMBOLS

# Config
initial_cash = 5000.0  # Match your backtest initial cash
robo_annual_rate = 0.05  # 5% annual for robo simulation
output_dir = "."  # Where CSVs are; save PNGs here too

# Helper to annualized volatility
def annualized_vol(returns, trading_days=252):
    return returns.std() * (trading_days ** 0.5) * 100

# Loop over each symbol and generate/save all graphs
def main():
    for sym in SYMBOLS:
        equity_path = f"{output_dir}/equity_curve_{sym.lower().replace('^', '')}.csv"
        trades_path = f"{output_dir}/backtest_results_{sym.lower().replace('^', '')}.csv"
        
        # Load data (skip if files missing)
        try:
            df = pd.read_csv(equity_path, parse_dates=['date'], index_col='date')
            trades_df = pd.read_csv(trades_path, parse_dates=['date'])
        except FileNotFoundError:
            print(f"Skipping {sym}: CSVs not found. Run backtesting.py first.")
            continue
        
        # 1. Equity Curve vs. Benchmark and Robo-Simulated Returns
        df['robo_equity'] = initial_cash * (1 + robo_annual_rate / 252).cumprod()[:len(df)]
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['equity'], label='Algo Equity')
        plt.plot(df.index, df['close'] / df['close'].iloc[0] * initial_cash, label='Buy-and-Hold (Close)')
        plt.plot(df.index, df['robo_equity'], label='Robo-Advisor (5% Annual)')
        plt.title(f'Equity Curve Comparison for {sym}')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value ($)')
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{output_dir}/equity_comparison_{sym.lower().replace('^', '')}.png")
        plt.close()  # Close to free memory

        # 2. Cumulative Returns
        df['algo_returns'] = (df['equity'] / df['equity'].iloc[0] - 1) * 100
        df['benchmark_returns'] = (df['close'] / df['close'].iloc[0] - 1) * 100
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['algo_returns'], label='Algo Cumulative Returns (%)')
        plt.plot(df.index, df['benchmark_returns'], label='Benchmark Cumulative Returns (%)')
        plt.title(f'Cumulative Returns for {sym}')
        plt.xlabel('Date')
        plt.ylabel('Returns (%)')
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{output_dir}/cumulative_returns_{sym.lower().replace('^', '')}.png")
        plt.close()

        # 3. Drawdown Curve
        df['peak'] = df['equity'].cummax()
        df['drawdown'] = (df['equity'] - df['peak']) / df['peak'] * 100
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['drawdown'], label='Drawdown (%)', color='red')
        plt.title(f'Drawdown Curve for {sym}')
        plt.xlabel('Date')
        plt.ylabel('Drawdown (%)')
        plt.fill_between(df.index, df['drawdown'], 0, color='red', alpha=0.3)
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{output_dir}/drawdown_{sym.lower().replace('^', '')}.png")
        plt.close()

        # 4. Trade P/L Distribution (Histogram)
        if 'pnl' in trades_df.columns and not trades_df.empty:
            pnl = trades_df[trades_df['action'] == 'sell']['pnl']  # P/L from sells
            plt.figure(figsize=(10, 6))
            pnl.hist(bins=20, color='skyblue', edgecolor='black')
            plt.title(f'Trade P/L Distribution for {sym}')
            plt.xlabel('P/L ($)')
            plt.ylabel('Frequency')
            plt.grid(True)
            plt.savefig(f"{output_dir}/pnl_distribution_{sym.lower().replace('^', '')}.png")
            plt.close()
        else:
            print(f"No trades for {sym}; skipping P/L histogram.")

        # 5. Performance Metrics Table (Save as CSV; optional plot as table image)
        df['daily_ret'] = df['equity'].pct_change().dropna()
        max_dd = df['drawdown'].min()
        sharpe = df['daily_ret'].mean() / df['daily_ret'].std() * (252 ** 0.5) if df['daily_ret'].std() != 0 else 0
        total_return = (df['equity'].iloc[-1] / initial_cash - 1) * 100
        num_trades = len(trades_df) // 2
        win_rate = (trades_df[trades_df['pnl'] > 0]['pnl'].count() / num_trades * 100) if num_trades > 0 else 0

        metrics = {
            'Total Return (%)': total_return,
            'Sharpe Ratio': sharpe,
            'Max Drawdown (%)': max_dd,
            'Win Rate (%)': win_rate,
            'Num Trades': num_trades
        }
        pd.Series(metrics).to_csv(f"{output_dir}/performance_metrics_{sym.lower().replace('^', '')}.csv")
        print(f"Metrics saved for {sym}")

        # 6. Volatility Comparison (Bar Plot)
        algo_vol = annualized_vol(df['daily_ret'])
        bench_daily_ret = df['close'].pct_change().dropna()
        bench_vol = annualized_vol(bench_daily_ret)
        robo_vol = 5.0  # Assume 5% annual vol for robo

        vol_data = {'Algo': algo_vol, 'Benchmark': bench_vol, 'Robo': robo_vol}
        pd.Series(vol_data).plot(kind='bar', color=['blue', 'green', 'orange'])
        plt.title(f'Annualized Volatility Comparison for {sym}')
        plt.ylabel('Volatility (%)')
        plt.grid(True)
        plt.savefig(f"{output_dir}/volatility_comparison_{sym.lower().replace('^', '')}.png")
        plt.close()

    print("All graphs and metrics updated and saved.")

if __name__ == "__main__":
    main()