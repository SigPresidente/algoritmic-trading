#PRINTS GRAPHS FOR STUDY PURPOSES AND SAVES THEM AS PNG FOR THESIS
#NOW INCLUDES: PAC PROFILE AND ITALY TAX VISUALIZATION

#Libraries
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#Files
from account_data import *

#Config
#Total returns from Moneyfarm website from 2018-01-01
robo_total_returns = {
    "low": ROBO_LOW_RISK,       # Portfolio 1: 2.3% total from 2018
    "medium": ROBO_MEDIUM_RISK, # Portfolio 4: 46.3% total from 2018  
    "high": ROBO_HIGH_RISK      # Portfolio 7: 118.9% total from 2018
}

#Moneyfarm volatility estimates from website
robo_volatilities = {
    "low": 4.5,      # Portfolio 1: Very low risk, mostly fixed income
    "medium": 8.5,   # Portfolio 4: Balanced risk, mixed allocation
    "high": 14.0     # Portfolio 7: High risk, predominantly equity
}

#Helper to annualized volatility
def annualized_vol(returns, trading_days=252):
    return returns.std() * (trading_days ** 0.5) * 100 

#Loop over each symbol and generate/save all graphs
def main():
    for sym in SYMBOLS:
        base = sym.lower().replace('^', '')
        
        # Collect data for all profiles for combined graphs
        all_profiles_data = {}
        
        for profile in PROFILES:
            equity_path = f"{OUTPUT_DIR}/equity_curve_{base}_{profile}.csv"
            trades_path = f"{OUTPUT_DIR}/backtest_trades_{base}_{profile}.csv"

            try:
                df = pd.read_csv(equity_path, index_col=0, parse_dates=True)
                trades_df = pd.read_csv(trades_path)
            except FileNotFoundError:
                print(f"Skipping {sym} {profile} — files not found")
                continue

            if profile in robo_total_returns:
                robo_total_return_from_2018 = robo_total_returns[profile]
                
                # Calculate equivalent daily return rate based on actual time period
                start_date = pd.Timestamp(START_DATE)
                days_since_start = (df.index[-1] - start_date).days
                
                if days_since_start > 0:
                    # Calculate gross daily return
                    daily_return_rate = (1 + robo_total_return_from_2018) ** (1 / days_since_start) - 1
                    
                    # Apply annual commission (1.28% per year)
                    # Convert to daily commission deduction
                    annual_commission_factor = (1 - ROBO_COMMISSION)
                    daily_commission_factor = annual_commission_factor ** (1 / 365)
                    
                    # Net daily return after commission
                    net_daily_return = (1 + daily_return_rate) * daily_commission_factor - 1
                else:
                    net_daily_return = 0
                
                # Build robo equity curve from the start of the backtest data
                days_in_backtest = len(df)
                df['robo_equity'] = INITIAL_DEPOSIT * (1 + net_daily_return) ** np.arange(days_in_backtest)
                robo_total_return = (df['robo_equity'].iloc[-1] / INITIAL_DEPOSIT - 1) * 100
                df['robo_returns'] = (df['robo_equity'] / df['robo_equity'].iloc[0] - 1) * 100
            else:
                df['robo_equity'] = np.nan
                robo_total_return = 0
                df['robo_returns'] = 0
            
            # Calculate metrics
            df['algo_returns'] = (df['equity'] / df['equity'].iloc[0] - 1) * 100
            df['benchmark_returns'] = (df['close'] / df['close'].iloc[0] - 1) * 100
            df['peak'] = df['equity'].cummax()
            df['drawdown'] = (df['equity'] - df['peak']) / df['peak'] * 100
            df['daily_ret'] = df['equity'].pct_change().dropna()
            
            # Calculate performance metrics
            max_dd = df['drawdown'].min()
            sharpe = df['daily_ret'].mean() / df['daily_ret'].std() * (252 ** 0.5) if df['daily_ret'].std() != 0 else 0
            total_return = (df['equity'].iloc[-1] / INITIAL_DEPOSIT - 1) * 100
            
            if profile == 'pac':
                total_closed = len(trades_df)
                win_rate = 0  # N/A for PAC
            else:
                total_closed = len(trades_df[trades_df['pnl'] != 0]) if 'pnl' in trades_df.columns else 0
                win_rate = (len(trades_df[trades_df['pnl'] > 0]) / total_closed * 100) if total_closed > 0 else 0
            
            # Store volatility data
            algo_vol = annualized_vol(df['daily_ret'])
            bench_daily_ret = df['close'].pct_change().dropna()
            bench_vol = annualized_vol(bench_daily_ret)
            
            # Store all data for combined graphs
            all_profiles_data[profile] = {
                'df': df,
                'trades_df': trades_df,
                'algo_vol': algo_vol,
                'bench_vol': bench_vol,
                'robo_vol': robo_volatilities.get(profile, 0),
                'robo_total_return': robo_total_return,
                'metrics': {
                    'Total Return (%)': total_return,
                    'Sharpe Ratio': sharpe,
                    'Max Drawdown (%)': max_dd,
                    'Win Rate (%)': win_rate,
                    'Num Trades': total_closed
                }
            }
            
            # Save individual metrics CSV
            pd.Series(all_profiles_data[profile]['metrics']).to_csv(
                f"{OUTPUT_DIR}/performance_metrics_{base}_{profile}.csv"
            )
            print(f"Metrics saved for {sym} {profile}")

        if not all_profiles_data:
            print(f"No data available for {sym}")
            continue

        # Define colors for each profile
        colors = {
            'low': '#2E86AB',
            'medium': '#A23B72', 
            'high': '#F18F01',
            'pac': '#06A77D'
        }
        
        profile_labels = {
            'low': 'Low Risk (P1)',
            'medium': 'Medium Risk (P4)',
            'high': 'High Risk (P7)',
            'pac': 'PAC (Monthly Buy)'
        }

        # 1) Equity Curves
        fig, ax = plt.subplots(figsize=(18, 9))
        
        # Plot algorithm for each profile
        for profile in PROFILES:
            data = all_profiles_data[profile]
            df = data['df']
            ax.plot(df.index, df['equity'], label=f'Algorithm - {profile_labels[profile]}', 
                   linewidth=2.8, color=colors[profile], alpha=0.9)
        
        # Plot robo-advisor for profiles with robo comparison
        for profile in ['low', 'medium', 'high']:
            if profile in all_profiles_data:
                data = all_profiles_data[profile]
                df = data['df']
                if not df['robo_equity'].isna().all():
                    ax.plot(df.index, df['robo_equity'], label=f'Moneyfarm - {profile_labels[profile]}', 
                           linewidth=2, color=colors[profile], linestyle='--', alpha=0.6)
        
        # Add benchmark
        bench_df = all_profiles_data[PROFILES[0]]['df']
        ax.plot(bench_df.index, bench_df['close'] / bench_df['close'].iloc[0] * INITIAL_DEPOSIT, 
               label=f'Benchmark ({sym})', linewidth=2.5, color='black', linestyle=':', alpha=0.7)
        
        ax.set_title(f'Equity Curve Comparison (After 26% Italy Tax) - {sym}', 
                    fontsize=17, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=13, fontweight='bold')
        ax.set_ylabel('Portfolio Value ($)', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10, loc='best', ncol=2)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/equity_comparison_all_profiles_{base}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Combined equity curve saved for {sym}")

        # 2) Cumulative Returns
        fig, ax = plt.subplots(figsize=(18, 9))
        
        # Plot algorithm returns
        for profile in PROFILES:
            data = all_profiles_data[profile]
            df = data['df']
            ax.plot(df.index, df['algo_returns'], label=f'Algorithm - {profile_labels[profile]}', 
                   linewidth=2.8, color=colors[profile], alpha=0.9)
        
        # Plot robo returns
        for profile in ['low', 'medium', 'high']:
            if profile in all_profiles_data:
                data = all_profiles_data[profile]
                df = data['df']
                if not df['robo_returns'].isna().all() and df['robo_returns'].iloc[-1] != 0:
                    ax.plot(df.index, df['robo_returns'], label=f'Moneyfarm - {profile_labels[profile]}', 
                           linewidth=2, color=colors[profile], linestyle='--', alpha=0.6)
        
        # Add benchmark
        ax.plot(bench_df.index, bench_df['benchmark_returns'], 
               label=f'Benchmark ({sym})', linewidth=2.5, color='black', linestyle=':', alpha=0.7)
        
        ax.set_title(f'Cumulative Returns Comparison (After 26% Italy Tax) - {sym}', 
                    fontsize=17, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=13, fontweight='bold')
        ax.set_ylabel('Returns (%)', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10, loc='best', ncol=2)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/cumulative_returns_all_profiles_{base}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Combined cumulative returns saved for {sym}")

        # 3) Drawdown Curves
        fig, ax = plt.subplots(figsize=(18, 9))
        
        for profile in PROFILES:
            data = all_profiles_data[profile]
            df = data['df']
            ax.plot(df.index, df['drawdown'], label=f'{profile_labels[profile]}', 
                   linewidth=2.5, color=colors[profile], alpha=0.9)
            ax.fill_between(df.index, df['drawdown'], 0, color=colors[profile], alpha=0.15)
        
        ax.set_title(f'Drawdown Comparison - All Risk Profiles (After Italy Tax) - {sym}', 
                    fontsize=17, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=13, fontweight='bold')
        ax.set_ylabel('Drawdown (%)', fontsize=13, fontweight='bold')
        ax.legend(fontsize=11, loc='best')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/drawdown_all_profiles_{base}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Combined drawdown curve saved for {sym}")

        # 4) Trade P/L Distribution (skip PAC as it doesn't close trades)
        trading_profiles = [p for p in PROFILES if p != 'pac']
        fig, axes = plt.subplots(1, len(trading_profiles), figsize=(18, 6), sharey=True)
        fig.suptitle(f'Trade P/L Distribution - Trading Profiles - {sym}', 
                    fontsize=16, fontweight='bold', y=1.02)
        
        for idx, profile in enumerate(trading_profiles):
            data = all_profiles_data[profile]
            trades_df = data['trades_df']
            
            if 'pnl' in trades_df.columns and not trades_df.empty:
                pnl = trades_df[trades_df['pnl'] != 0]['pnl']
                if not pnl.empty:
                    axes[idx].hist(pnl, bins=20, color=colors[profile], edgecolor='black', alpha=0.7)
                    axes[idx].axvline(pnl.mean(), color='red', linestyle='--', linewidth=2, 
                                     label=f'Mean: ${pnl.mean():.2f}')
                    axes[idx].set_title(profile_labels[profile], fontsize=13, fontweight='bold')
                    axes[idx].set_xlabel('P/L ($)', fontsize=11)
                    if idx == 0:
                        axes[idx].set_ylabel('Frequency', fontsize=11)
                    axes[idx].legend(fontsize=9)
                    axes[idx].grid(True, alpha=0.3)
                else:
                    axes[idx].text(0.5, 0.5, 'No closed trades', 
                                  transform=axes[idx].transAxes, ha='center', va='center', fontsize=12)
                    axes[idx].set_title(profile_labels[profile], fontsize=13, fontweight='bold')
            else:
                axes[idx].text(0.5, 0.5, 'No trade data', 
                              transform=axes[idx].transAxes, ha='center', va='center', fontsize=12)
                axes[idx].set_title(profile_labels[profile], fontsize=13, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/pnl_distribution_all_profiles_{base}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Combined P/L distribution saved for {sym}")

        # 5) Performance Metrics - Algorithm vs Moneyfarm
        fig, axes = plt.subplots(2, 2, figsize=(18, 13))
        fig.suptitle(f'Performance Metrics (After 26% Italy Tax) - Algorithm vs Moneyfarm - {sym}', 
                    fontsize=17, fontweight='bold', y=0.995)
        
        # Use only profiles with robo comparison for this chart
        comparison_profiles = ['low', 'medium', 'high']
        x = np.arange(len(comparison_profiles))
        width = 0.35
        
        # Metric 1: Total Return (Algo vs Robo)
        algo_returns = [all_profiles_data[p]['metrics']['Total Return (%)'] for p in comparison_profiles]
        robo_returns = [all_profiles_data[p]['robo_total_return'] for p in comparison_profiles]
        
        bars1 = axes[0, 0].bar(x - width/2, algo_returns, width, label='Algorithm', 
                              color=[colors[p] for p in comparison_profiles], alpha=0.8)
        bars2 = axes[0, 0].bar(x + width/2, robo_returns, width, label='Moneyfarm', 
                              color=[colors[p] for p in comparison_profiles], alpha=0.5, hatch='//')
        
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                axes[0, 0].text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', 
                               fontsize=9, fontweight='bold')
        
        axes[0, 0].set_title('Total Return (%) - Algorithm vs Moneyfarm', fontsize=13, fontweight='bold')
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels([profile_labels[p] for p in comparison_profiles], fontsize=10)
        axes[0, 0].legend(fontsize=10)
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        axes[0, 0].axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
        
        # Metric 2: Sharpe Ratio (all profiles including PAC)
        sharpes = [all_profiles_data[p]['metrics']['Sharpe Ratio'] for p in PROFILES]
        x_all = np.arange(len(PROFILES))
        bars = axes[0, 1].bar(x_all, sharpes, width*1.5, color=[colors[p] for p in PROFILES], alpha=0.8)
        for bar in bars:
            height = bar.get_height()
            axes[0, 1].text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.2f}', ha='center', va='bottom' if height >= 0 else 'top', 
                           fontsize=10, fontweight='bold')
        axes[0, 1].set_title('Sharpe Ratio (All Profiles)', fontsize=13, fontweight='bold')
        axes[0, 1].set_xticks(x_all)
        axes[0, 1].set_xticklabels([profile_labels[p] for p in PROFILES], fontsize=10)
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        axes[0, 1].axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
        
        # Metric 3: Max Drawdown (all profiles)
        drawdowns = [all_profiles_data[p]['metrics']['Max Drawdown (%)'] for p in PROFILES]
        bars = axes[1, 0].bar(x_all, drawdowns, width*1.5, color=[colors[p] for p in PROFILES], alpha=0.8)
        for bar in bars:
            height = bar.get_height()
            axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}%', ha='center', va='top', 
                           fontsize=10, fontweight='bold')
        axes[1, 0].set_title('Max Drawdown (%) - All Profiles', fontsize=13, fontweight='bold')
        axes[1, 0].set_xticks(x_all)
        axes[1, 0].set_xticklabels([profile_labels[p] for p in PROFILES], fontsize=10)
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # Metric 4: Total Return Comparison (All Profiles)
        all_returns = [all_profiles_data[p]['metrics']['Total Return (%)'] for p in PROFILES]
        bars = axes[1, 1].bar(x_all, all_returns, width*1.5, color=[colors[p] for p in PROFILES], alpha=0.8)
        for bar in bars:
            height = bar.get_height()
            axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', 
                           fontsize=10, fontweight='bold')
        axes[1, 1].set_title('Total Return (%) - All Profiles', fontsize=13, fontweight='bold')
        axes[1, 1].set_xticks(x_all)
        axes[1, 1].set_xticklabels([profile_labels[p] for p in PROFILES], fontsize=10)
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        axes[1, 1].axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
        
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/performance_metrics_all_profiles_{base}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Combined performance metrics saved for {sym}")

        # 6) Volatility Comparisons (including PAC)
        fig, ax = plt.subplots(figsize=(16, 8))
        
        algo_vols = [all_profiles_data[p]['algo_vol'] for p in PROFILES]
        bench_vols = [all_profiles_data[p]['bench_vol'] for p in PROFILES]
        robo_vols = [all_profiles_data[p]['robo_vol'] for p in PROFILES]
        
        x_all = np.arange(len(PROFILES))
        width = 0.25
        
        bars1 = ax.bar(x_all - width, algo_vols, width, label='Algorithm', color='#2E86AB', alpha=0.8)
        bars2 = ax.bar(x_all, bench_vols, width, label=f'Benchmark ({sym})', color='#A23B72', alpha=0.8)
        bars3 = ax.bar(x_all + width, robo_vols, width, label='Moneyfarm', color='#F18F01', alpha=0.8)
        
        def add_value_labels(bars):
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        add_value_labels(bars1)
        add_value_labels(bars2)
        add_value_labels(bars3)
        
        ax.set_xlabel('Risk Profile', fontsize=13, fontweight='bold')
        ax.set_ylabel('Annualized Volatility (%)', fontsize=13, fontweight='bold')
        ax.set_title(f'Volatility Comparison - All Profiles - {sym}', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(x_all)
        ax.set_xticklabels([profile_labels[p] for p in PROFILES], fontsize=11)
        ax.legend(fontsize=11, loc='upper left')
        ax.grid(True, alpha=0.3, axis='y')
        
        ax.text(0.98, 0.02, 'Note: Moneyfarm volatilities are estimates. PAC robo value is 0 (not applicable).',
               transform=ax.transAxes, fontsize=8, style='italic',
               verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/volatility_comparison_all_profiles_{base}.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Combined volatility comparison saved for {sym}")

        # 7) NEW: PAC Investment Timeline
        if 'pac' in all_profiles_data:
            pac_trades = all_profiles_data['pac']['trades_df']
            pac_df = all_profiles_data['pac']['df']
            
            # Convert trade dates to datetime if needed
            if not isinstance(pac_trades['date'].iloc[0], pd.Timestamp):
                pac_trades['date'] = pd.to_datetime(pac_trades['date'])
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10))
            
            # Top: Cumulative investment vs Portfolio value
            cumulative_investment = INITIAL_DEPOSIT + pac_trades['amount'].cumsum()
            cumulative_investment.index = pac_trades['date'].values
            
            ax1.plot(pac_trades['date'].values, cumulative_investment.values, 
                    label='Cumulative Investment', linewidth=2.5, color='#FF6B6B', alpha=0.8)
            ax1.plot(pac_df.index, pac_df['equity'], 
                    label='Portfolio Value (After Tax)', linewidth=2.5, color='#06A77D', alpha=0.9)
            
            # Create properly aligned series for fill_between
            cumulative_for_fill = cumulative_investment.reindex(pac_df.index, method='ffill').fillna(INITIAL_DEPOSIT)
            ax1.fill_between(pac_df.index, pac_df['equity'], cumulative_for_fill,
                            alpha=0.2, color='#06A77D', label='Net Gain/Loss')
            
            ax1.set_title(f'PAC Strategy - Investment Timeline vs Portfolio Value - {sym}', 
                         fontsize=15, fontweight='bold')
            ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Value ($)', fontsize=12, fontweight='bold')
            ax1.legend(fontsize=11)
            ax1.grid(True, alpha=0.3)
            
            # Bottom: Monthly investment markers on price chart
            ax2.plot(pac_df.index, pac_df['close'], label=f'{sym} Price', 
                    linewidth=2, color='black', alpha=0.7)
            ax2.scatter(pac_trades['date'].values, pac_trades['price'].values, 
                       color='#06A77D', s=80, alpha=0.7, zorder=5, label='Monthly Purchases')
            
            ax2.set_title(f'Monthly Purchase Points on {sym} Price Chart', fontsize=15, fontweight='bold')
            ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
            ax2.set_ylabel(f'{sym} Price', fontsize=12, fontweight='bold')
            ax2.legend(fontsize=11)
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(f"{OUTPUT_DIR}/pac_investment_timeline_{base}.png", dpi=300, bbox_inches='tight')
            plt.close()
            print(f"PAC investment timeline saved for {sym}")

    print("\n" + "="*70)
    print("All graphs updated with PAC profile and Italy tax (26%) included.")
    print("="*70)

if __name__ == "__main__":
    main()