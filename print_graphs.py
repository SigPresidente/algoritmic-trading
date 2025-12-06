#PRINTS GRAPHS FOR STUDY PURPOSES AND SAVES THEM AS PNG FOR THESIS

#Libraries
import pandas as pd
import matplotlib.pyplot as plt

#Files
from account_data import *

#Config
robo_rates = {"high": ROBO_HIGH_RISK, "medium": ROBO_MEDIUM_RISK, "low": ROBO_LOW_RISK}

#Helper to annualized volatility
def annualized_vol(returns, trading_days=252):
    return returns.std() * (trading_days ** 0.5) * 100 

#Loop over each symbol and generate/save all graphs
def main():
    for sym in SYMBOLS:
        for profile in PROFILES:
            base = sym.lower().replace('^', '')
            equity_path = f"{OUTPUT_DIR}/equity_curve_{base}_{profile}.csv"
            trades_path = f"{OUTPUT_DIR}/backtest_trades_{base}_{profile}.csv"

            try:
                df = pd.read_csv(equity_path, index_col=0, parse_dates=True)
                trades_df = pd.read_csv(trades_path)
            except FileNotFoundError:
                print(f"Skipping {sym} {profile} — files not found")
                continue

            robo_annual_rate = robo_rates[profile]
        
            # 1) Equity Curve vs. Benchmark and Robo-Simulated Returns
            daily_returns = pd.Series([1 + robo_annual_rate / 252] * len(df))
            df['robo_equity'] = INITIAL_DEPOSIT * daily_returns.cumprod()
            plt.figure(figsize=(12, 6))
            plt.plot(df.index, df['equity'], label='Algo Equity')
            plt.plot(df.index, df['close'] / df['close'].iloc[0] * INITIAL_DEPOSIT, label='Buy-and-Hold (Close)')
            plt.plot(df.index, df['robo_equity'], label=f'Robo-Advisor ({robo_annual_rate*100:.1f}% Annual)')
            plt.title(f'Equity Curve Comparison for {sym} ({profile.capitalize()} Risk)')
            plt.xlabel('Date')
            plt.ylabel('Portfolio Value ($)')
            plt.legend()
            plt.grid(True)
            plt.savefig(f"{OUTPUT_DIR}/equity_comparison_{base}_{profile}.png")
            plt.close()  # Close to free memory

            # 2) Cumulative Returns
            df['algo_returns'] = (df['equity'] / df['equity'].iloc[0] - 1) * 100
            df['benchmark_returns'] = (df['close'] / df['close'].iloc[0] - 1) * 100
            plt.figure(figsize=(12, 6))
            plt.plot(df.index, df['algo_returns'], label='Algo Cumulative Returns (%)')
            plt.plot(df.index, df['benchmark_returns'], label='Benchmark Cumulative Returns (%)')
            plt.title(f'Cumulative Returns for {sym} ({profile.capitalize()} Risk)')
            plt.xlabel('Date')
            plt.ylabel('Returns (%)')
            plt.legend()
            plt.grid(True)
            plt.savefig(f"{OUTPUT_DIR}/cumulative_returns_{base}_{profile}.png")
            plt.close()

            # 3) Drawdown Curve
            df['peak'] = df['equity'].cummax()
            df['drawdown'] = (df['equity'] - df['peak']) / df['peak'] * 100
            plt.figure(figsize=(12, 6))
            plt.plot(df.index, df['drawdown'], label='Drawdown (%)', color='red')
            plt.title(f'Drawdown Curve for {sym} ({profile.capitalize()} Risk)')
            plt.xlabel('Date')
            plt.ylabel('Drawdown (%)')
            plt.fill_between(df.index, df['drawdown'], 0, color='red', alpha=0.3)
            plt.legend()
            plt.grid(True)
            plt.savefig(f"{OUTPUT_DIR}/drawdown_{base}_{profile}.png")
            plt.close()

            # 4) Trade P/L Distribution (Histogram)
            if 'pnl' in trades_df.columns and not trades_df.empty:
                pnl = trades_df[trades_df['pnl'] != 0]['pnl']  # P/L from closes (exclude opens where pnl=0)
                if not pnl.empty:
                    plt.figure(figsize=(10, 6))
                    pnl.hist(bins=20, color='skyblue', edgecolor='black')
                    plt.title(f'Trade P/L Distribution for {sym} ({profile.capitalize()} Risk)')
                    plt.xlabel('P/L ($)')
                    plt.ylabel('Frequency')
                    plt.grid(True)
                    plt.savefig(f"{OUTPUT_DIR}/pnl_distribution_{base}_{profile}.png")
                    plt.close()
                else:
                    print(f"No closed trades for {sym} {profile}; skipping P/L histogram.")
            else:
                print(f"No trades for {sym} {profile}; skipping P/L histogram.")

            # 5) Performance Metrics Table (Save as CSV)
            df['daily_ret'] = df['equity'].pct_change().dropna()
            max_dd = df['drawdown'].min()
            sharpe = df['daily_ret'].mean() / df['daily_ret'].std() * (252 ** 0.5) if df['daily_ret'].std() != 0 else 0
            total_return = (df['equity'].iloc[-1] / INITIAL_DEPOSIT - 1) * 100
            total_closed = len(trades_df[trades_df['pnl'] != 0]) if 'pnl' in trades_df.columns else 0
            win_rate = (len(trades_df[trades_df['pnl'] > 0]) / total_closed * 100) if total_closed > 0 else 0

            metrics = {
                'Total Return (%)': total_return,
                'Sharpe Ratio': sharpe,
                'Max Drawdown (%)': max_dd,
                'Win Rate (%)': win_rate,
                'Num Trades': total_closed
            }
            pd.Series(metrics).to_csv(f"{OUTPUT_DIR}/performance_metrics_{base}_{profile}.csv")
            print(f"Metrics saved for {sym} {profile}")

            # 6) Volatility Comparison (Bar Plot)
            algo_vol = annualized_vol(df['daily_ret'])
            bench_daily_ret = df['close'].pct_change().dropna()
            bench_vol = annualized_vol(bench_daily_ret)
            robo_vol = 5.0  # Assume 5% annual vol for robo

            vol_data = {'Algo': algo_vol, 'Benchmark': bench_vol, 'Robo': robo_vol}
            pd.Series(vol_data).plot(kind='bar', color=['blue', 'green', 'orange'])
            plt.title(f'Annualized Volatility Comparison for {sym} ({profile.capitalize()} Risk)')
            plt.ylabel('Volatility (%)')
            plt.grid(True)
            plt.savefig(f"{OUTPUT_DIR}/volatility_comparison_{base}_{profile}.png")
            plt.close()

    print("All graphs and metrics updated and saved.")

if __name__ == "__main__":
    main()