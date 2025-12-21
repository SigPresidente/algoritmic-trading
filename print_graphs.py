#PRINTS GRAPHS FOR STUDY PURPOSES AND SAVES THEM AS PNG FOR THESIS

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
    #Dictionary to store portfolio-level data across all symbols
    portfolio_data = {profile: [] for profile in PROFILES}
    
    for sym in SYMBOLS:
        base = sym.lower().replace('^', '')
        
        #Collect data for all profiles for combined graphs
        all_profiles_data = {}
        
        for profile in PROFILES:
            equity_path = f"{OUTPUT_DIR}/equity_curve_{base}_{profile}.csv"
            trades_path = f"{OUTPUT_DIR}/backtest_trades_{base}_{profile}.csv"

            try:
                df = pd.read_csv(equity_path, index_col=0, parse_dates=True)
                trades_df = pd.read_csv(trades_path)
            except FileNotFoundError:
                print(f"[WARNING] Skipping {sym} {profile} — files not found")
                continue
            except Exception as e:
                print(f"[WARNING] Error loading {sym} {profile}: {e}")
                continue

            #Store for portfolio aggregation
            portfolio_data[profile].append({
                'symbol': sym,
                'df': df.copy(),
                'trades_df': trades_df.copy()
            })

            #Adjust robo comparison to account for split capital
            capital_per_symbol = INITIAL_DEPOSIT / len(SYMBOLS)
            
            if profile in robo_total_returns:
                robo_total_return_from_2018 = robo_total_returns[profile]
                
                #Calculate equivalent daily return rate based on actual time period
                start_date = pd.Timestamp(START_DATE)
                days_since_start = (df.index[-1] - start_date).days
                
                if days_since_start > 0:
                    #Calculate gross daily return
                    daily_return_rate = (1 + robo_total_return_from_2018) ** (1 / days_since_start) - 1
                    
                    #Apply annual commission (1.28% per year)
                    #Convert to daily commission deduction
                    annual_commission_factor = (1 - ROBO_COMMISSION)
                    daily_commission_factor = annual_commission_factor ** (1 / 365)
                    
                    # Net daily return after commission
                    net_daily_return = (1 + daily_return_rate) * daily_commission_factor - 1
                else:
                    net_daily_return = 0
                
                #Build robo equity curve from the start of the backtest data (with split capital)
                days_in_backtest = len(df)
                df['robo_equity'] = capital_per_symbol * (1 + net_daily_return) ** np.arange(days_in_backtest)
                robo_total_return = (df['robo_equity'].iloc[-1] / capital_per_symbol - 1) * 100
                df['robo_returns'] = (df['robo_equity'] / df['robo_equity'].iloc[0] - 1) * 100
            else:
                df['robo_equity'] = np.nan
                robo_total_return = 0
                df['robo_returns'] = 0
            
            #Calculate metrics
            df['algo_returns'] = (df['equity'] / df['equity'].iloc[0] - 1) * 100
            df['benchmark_returns'] = (df['close'] / df['close'].iloc[0] - 1) * 100
            df['peak'] = df['equity'].cummax()
            df['drawdown'] = (df['equity'] - df['peak']) / df['peak'] * 100
            df['daily_ret'] = df['equity'].pct_change().dropna()
            
            #Calculate performance metrics
            max_dd = df['drawdown'].min()
            sharpe = df['daily_ret'].mean() / df['daily_ret'].std() * (252 ** 0.5) if df['daily_ret'].std() != 0 else 0
            total_return = (df['equity'].iloc[-1] / capital_per_symbol - 1) * 100
            
            if profile == 'pac':
                total_closed = len(trades_df)
                win_rate = 0  # N/A for PAC
            else:
                total_closed = len(trades_df[trades_df['pnl'] != 0]) if 'pnl' in trades_df.columns else 0
                win_rate = (len(trades_df[trades_df['pnl'] > 0]) / total_closed * 100) if total_closed > 0 else 0
            
            #Store volatility data
            algo_vol = annualized_vol(df['daily_ret'])
            bench_daily_ret = df['close'].pct_change().dropna()
            bench_vol = annualized_vol(bench_daily_ret)
            
            #Store all data for combined graphs
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
            
            #Save individual metrics CSV
            try:
                pd.Series(all_profiles_data[profile]['metrics']).to_csv(
                    f"{OUTPUT_DIR}/performance_metrics_{base}_{profile}.csv"
                )
                print(f"Metrics saved for {sym} {profile}")
            except Exception as e:
                print(f"[WARNING] Could not save metrics for {sym} {profile}: {e}")

        if not all_profiles_data:
            print(f"[WARNING] No data available for {sym}, skipping graphs")
            continue

        #Define colors for each profile
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

        #1) Equity Curves (per symbol)
        try:
            fig, ax = plt.subplots(figsize=(18, 9))
            
            #Plot algorithm for each profile
            for profile in PROFILES:
                if profile not in all_profiles_data:
                    continue
                data = all_profiles_data[profile]
                df = data['df']
                ax.plot(df.index, df['equity'], label=f'Algorithm - {profile_labels[profile]}', 
                       linewidth=2.8, color=colors[profile], alpha=0.9)
            
            #Plot robo-advisor for profiles with robo comparison
            for profile in ['low', 'medium', 'high']:
                if profile in all_profiles_data:
                    data = all_profiles_data[profile]
                    df = data['df']
                    if not df['robo_equity'].isna().all():
                        ax.plot(df.index, df['robo_equity'], label=f'Moneyfarm - {profile_labels[profile]}', 
                               linewidth=2, color=colors[profile], linestyle='--', alpha=0.6)
            
            #Add benchmark (use first available profile's data)
            first_profile = list(all_profiles_data.keys())[0]
            bench_df = all_profiles_data[first_profile]['df']
            capital_per_symbol = INITIAL_DEPOSIT / len(SYMBOLS)
            ax.plot(bench_df.index, bench_df['close'] / bench_df['close'].iloc[0] * capital_per_symbol, 
                   label=f'Benchmark ({sym})', linewidth=2.5, color='black', linestyle=':', alpha=0.7)
            
            ax.set_title(f'Equity Curve Comparison - {sym} only',
                        fontsize=17, fontweight='bold', pad=20)
            ax.set_xlabel('Date', fontsize=13, fontweight='bold')
            ax.set_ylabel('Portfolio Value ($)', fontsize=13, fontweight='bold')
            ax.legend(fontsize=10, loc='best', ncol=2)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f"{OUTPUT_DIR}/equity_comparison_all_profiles_{base}.png", dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Combined equity curve saved for {sym}")
        except Exception as e:
            print(f"[WARNING] Could not create equity curve for {sym}: {e}")

        #2) Cumulative Returns (per symbol)
        try:
            fig, ax = plt.subplots(figsize=(18, 9))
            
            #Plot algorithm returns
            for profile in PROFILES:
                if profile not in all_profiles_data:
                    continue
                data = all_profiles_data[profile]
                df = data['df']
                ax.plot(df.index, df['algo_returns'], label=f'Algorithm - {profile_labels[profile]}', 
                       linewidth=2.8, color=colors[profile], alpha=0.9)
            
            #Plot robo returns
            for profile in ['low', 'medium', 'high']:
                if profile in all_profiles_data:
                    data = all_profiles_data[profile]
                    df = data['df']
                    if not df['robo_returns'].isna().all() and df['robo_returns'].iloc[-1] != 0:
                        ax.plot(df.index, df['robo_returns'], label=f'Moneyfarm - {profile_labels[profile]}', 
                               linewidth=2, color=colors[profile], linestyle='--', alpha=0.6)
            
            #Add benchmark
            first_profile = list(all_profiles_data.keys())[0]
            bench_df = all_profiles_data[first_profile]['df']
            ax.plot(bench_df.index, bench_df['benchmark_returns'], 
                   label=f'Benchmark ({sym})', linewidth=2.5, color='black', linestyle=':', alpha=0.7)
            
            ax.set_title(f'Cumulative Returns - {sym} (After 26% Italy Tax, Split Capital)', 
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
        except Exception as e:
            print(f"[WARNING] Could not create cumulative returns for {sym}: {e}")

        #3) Drawdown Curves (per symbol)
        try:
            fig, ax = plt.subplots(figsize=(18, 9))
            
            for profile in PROFILES:
                if profile not in all_profiles_data:
                    continue
                data = all_profiles_data[profile]
                df = data['df']
                ax.plot(df.index, df['drawdown'], label=f'{profile_labels[profile]}', 
                       linewidth=2.5, color=colors[profile], alpha=0.9)
                ax.fill_between(df.index, df['drawdown'], 0, color=colors[profile], alpha=0.15)
            
            ax.set_title(f'Drawdown Comparison - {sym} (After Italy Tax)', 
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
        except Exception as e:
            print(f"[WARNING] Could not create drawdown curve for {sym}: {e}")

        #4) Trade P/L Distribution (skip PAC as it doesn't close trades)
        try:
            trading_profiles = [p for p in PROFILES if p != 'pac' and p in all_profiles_data]
            if trading_profiles:
                fig, axes = plt.subplots(1, len(trading_profiles), figsize=(18, 6), sharey=True)
                if len(trading_profiles) == 1:
                    axes = [axes]  # Make it iterable
                    
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
        except Exception as e:
            print(f"[WARNING] Could not create P/L distribution for {sym}: {e}")

        #5) Performance Metrics - Algorithm vs Moneyfarm (per symbol)
        try:
            fig, axes = plt.subplots(2, 2, figsize=(18, 13))
            fig.suptitle(f'Performance Metrics - {sym} only', 
                        fontsize=17, fontweight='bold', y=0.995)
            
            #Use only profiles with robo comparison for this chart
            comparison_profiles = [p for p in ['low', 'medium', 'high'] if p in all_profiles_data]
            x = np.arange(len(comparison_profiles))
            width = 0.35
            
            if comparison_profiles:
                #Metric 1: Total Return (Algo vs Robo)
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
                axes[0, 0].legend(fontsize=10, loc='upper left')
                axes[0, 0].grid(True, alpha=0.3, axis='y')
                axes[0, 0].axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
            
            #Metric 2: Sharpe Ratio (all profiles including PAC)
            available_profiles = list(all_profiles_data.keys())
            sharpes = [all_profiles_data[p]['metrics']['Sharpe Ratio'] for p in available_profiles]
            x_all = np.arange(len(available_profiles))
            bars = axes[0, 1].bar(x_all, sharpes, width*1.5, color=[colors[p] for p in available_profiles], alpha=0.8)
            for bar in bars:
                height = bar.get_height()
                axes[0, 1].text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.2f}', ha='center', va='bottom' if height >= 0 else 'top', 
                               fontsize=10, fontweight='bold')
            axes[0, 1].set_title('Sharpe Ratio (%/%) - All Profiles', fontsize=13, fontweight='bold')
            axes[0, 1].set_xticks(x_all)
            axes[0, 1].set_xticklabels([profile_labels[p] for p in available_profiles], fontsize=10)
            axes[0, 1].grid(True, alpha=0.3, axis='y')
            axes[0, 1].axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
            
            #Metric 3: Max Drawdown (all profiles)
            drawdowns = [all_profiles_data[p]['metrics']['Max Drawdown (%)'] for p in available_profiles]
            bars = axes[1, 0].bar(x_all, drawdowns, width*1.5, color=[colors[p] for p in available_profiles], alpha=0.8)
            for bar in bars:
                height = bar.get_height()
                axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.1f}%', ha='center', va='top', 
                               fontsize=10, fontweight='bold')
            axes[1, 0].set_title('Max Drawdown (%) - All Profiles', fontsize=13, fontweight='bold')
            axes[1, 0].set_xticks(x_all)
            axes[1, 0].set_xticklabels([profile_labels[p] for p in available_profiles], fontsize=10)
            axes[1, 0].grid(True, alpha=0.3, axis='y')
            
            #Metric 4: Total Return Comparison (All Profiles)
            all_returns = [all_profiles_data[p]['metrics']['Total Return (%)'] for p in available_profiles]
            bars = axes[1, 1].bar(x_all, all_returns, width*1.5, color=[colors[p] for p in available_profiles], alpha=0.8)
            for bar in bars:
                height = bar.get_height()
                axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', 
                               fontsize=10, fontweight='bold')
            axes[1, 1].set_title('Total Return (%) - All Profiles', fontsize=13, fontweight='bold')
            axes[1, 1].set_xticks(x_all)
            axes[1, 1].set_xticklabels([profile_labels[p] for p in available_profiles], fontsize=10)
            axes[1, 1].grid(True, alpha=0.3, axis='y')
            axes[1, 1].axhline(y=0, color='gray', linestyle='-', linewidth=0.8)
            
            plt.tight_layout()
            plt.savefig(f"{OUTPUT_DIR}/performance_metrics_all_profiles_{base}.png", dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Combined performance metrics saved for {sym}")
        except Exception as e:
            print(f"[WARNING] Could not create performance metrics for {sym}: {e}")

        #6) Volatility Comparisons (per symbol)
        try:
            fig, ax = plt.subplots(figsize=(16, 8))
            
            available_profiles = list(all_profiles_data.keys())
            algo_vols = [all_profiles_data[p]['algo_vol'] for p in available_profiles]
            bench_vols = [all_profiles_data[p]['bench_vol'] for p in available_profiles]
            robo_vols = [all_profiles_data[p]['robo_vol'] for p in available_profiles]
            
            x_all = np.arange(len(available_profiles))
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
            ax.set_xticklabels([profile_labels[p] for p in available_profiles], fontsize=11)
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
        except Exception as e:
            print(f"[WARNING] Could not create volatility comparison for {sym}: {e}")

        #7) PAC Investment Timeline (per symbol)
        if 'pac' in all_profiles_data:
            try:
                pac_trades = all_profiles_data['pac']['trades_df']
                pac_df = all_profiles_data['pac']['df']
                
                if not pac_trades.empty:
                    #Convert trade dates to datetime if needed
                    if not isinstance(pac_trades['date'].iloc[0], pd.Timestamp):
                        pac_trades['date'] = pd.to_datetime(pac_trades['date'])
                    
                    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10))
                    
                    #Top: Cumulative investment vs Portfolio value
                    capital_per_symbol = INITIAL_DEPOSIT / len(SYMBOLS)
                    cumulative_investment = capital_per_symbol + pac_trades['amount'].cumsum()
                    cumulative_investment.index = pac_trades['date'].values
                    
                    ax1.plot(pac_trades['date'].values, cumulative_investment.values, 
                            label='Cumulative Investment', linewidth=2.5, color='#FF6B6B', alpha=0.8)
                    ax1.plot(pac_df.index, pac_df['equity'], 
                            label='Portfolio Value (After Tax)', linewidth=2.5, color='#06A77D', alpha=0.9)
                    
                    #Create properly aligned series for fill_between
                    cumulative_for_fill = cumulative_investment.reindex(pac_df.index, method='ffill').fillna(capital_per_symbol)
                    ax1.fill_between(pac_df.index, pac_df['equity'], cumulative_for_fill,
                                    alpha=0.2, color='#06A77D', label='Net Gain/Loss')
                    
                    ax1.set_title(f'PAC Strategy - Investment Timeline vs Portfolio Value - {sym}', 
                                 fontsize=15, fontweight='bold')
                    ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
                    ax1.set_ylabel('Value ($)', fontsize=12, fontweight='bold')
                    ax1.legend(fontsize=11)
                    ax1.grid(True, alpha=0.3)
                    
                    #Bottom: Monthly investment markers on price chart
                    ax2.plot(pac_df.index, pac_df['close'], label=f'{sym} Price ($)', 
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
            except Exception as e:
                print(f"[WARNING] Could not create PAC timeline for {sym}: {e}")

    #Aggregated Graphs (total portfolio)
    print("\n" + "="*60)
    print("Generating aggregated graphs...")
    print("="*60)
    
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
    
    #Sum equity curves across all symbols for each profile
    try:
        aggregated_portfolios = {}
        
        for profile in PROFILES:
            if not portfolio_data[profile]:
                continue
                
            #Find common date index across all symbols
            date_indices = [data['df'].index for data in portfolio_data[profile]]
            common_index = date_indices[0]
            for idx in date_indices[1:]:
                common_index = common_index.intersection(idx)
            
            if len(common_index) == 0:
                print(f"[WARNING] No common dates for profile {profile}")
                continue
            
            #Sum equity across all symbols
            total_equity = pd.Series(0, index=common_index)
            for data in portfolio_data[profile]:
                df = data['df']
                total_equity += df.loc[common_index, 'equity']
            
            aggregated_portfolios[profile] = {
                'equity': total_equity,
                'returns': (total_equity / INITIAL_DEPOSIT - 1) * 100
            }
        
        #Generate Moneyfarm comparison
        for profile in ['low', 'medium', 'high']:
            if profile not in aggregated_portfolios:
                continue
                
            robo_total_return_from_2018 = robo_total_returns[profile]
            common_index = aggregated_portfolios[profile]['equity'].index
            start_date = pd.Timestamp(START_DATE)
            days_since_start = (common_index[-1] - start_date).days
            
            if days_since_start > 0:
                daily_return_rate = (1 + robo_total_return_from_2018) ** (1 / days_since_start) - 1
                annual_commission_factor = (1 - ROBO_COMMISSION)
                daily_commission_factor = annual_commission_factor ** (1 / 365)
                net_daily_return = (1 + daily_return_rate) * daily_commission_factor - 1
            else:
                net_daily_return = 0
            
            days_in_backtest = len(common_index)
            robo_equity = INITIAL_DEPOSIT * (1 + net_daily_return) ** np.arange(days_in_backtest)
            aggregated_portfolios[profile]['robo_equity'] = pd.Series(robo_equity, index=common_index)
            aggregated_portfolios[profile]['robo_returns'] = (robo_equity / INITIAL_DEPOSIT - 1) * 100
        
        #1) Portfolio-Level Cumulative Returns (Linear Scale)
        fig, ax = plt.subplots(figsize=(20, 10))
        
        for profile in PROFILES:
            if profile not in aggregated_portfolios:
                continue
            data = aggregated_portfolios[profile]
            ax.plot(data['equity'].index, data['returns'], 
                   label=f'Algorithm - {profile_labels[profile]}', 
                   linewidth=3, color=colors[profile], alpha=0.9)
        
        #Add Moneyfarm comparison
        for profile in ['low', 'medium', 'high']:
            if profile in aggregated_portfolios and 'robo_returns' in aggregated_portfolios[profile]:
                data = aggregated_portfolios[profile]
                ax.plot(data['equity'].index, data['robo_returns'], 
                       label=f'Moneyfarm - {profile_labels[profile]}', 
                       linewidth=2.5, color=colors[profile], linestyle='--', alpha=0.6)
        
        ax.set_title('Total Portfolio Cumulative Returns - All Profiles (Linear Scale)\nAggregated across all symbols', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=14, fontweight='bold')
        ax.set_ylabel('Returns (%)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=12, loc='best', ncol=2)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
        
        #Add annotation for high risk if it's significantly different
        if 'high' in aggregated_portfolios:
            high_return = aggregated_portfolios['high']['returns'].iloc[-1]
            ax.text(0.02, 0.98, f"High Risk Final Return: {high_return:+.1f}%", 
                   transform=ax.transAxes, fontsize=11, fontweight='bold',
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='#F18F01', alpha=0.3))
        
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/portfolio_cumulative_returns_linear.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("Portfolio cumulative returns (linear) saved")
        
        #2) Portfolio-Level Cumulative Returns (Log Scale) - Better for large differences
        fig, ax = plt.subplots(figsize=(20, 10))
        
        for profile in PROFILES:
            if profile not in aggregated_portfolios:
                continue
            data = aggregated_portfolios[profile]
            #Convert to equity ratio for log scale (avoid log of negative numbers)
            equity_ratio = data['equity'] / INITIAL_DEPOSIT
            ax.plot(data['equity'].index, equity_ratio, 
                   label=f'Algorithm - {profile_labels[profile]}', 
                   linewidth=3, color=colors[profile], alpha=0.9)
        
        #Add Moneyfarm comparison
        for profile in ['low', 'medium', 'high']:
            if profile in aggregated_portfolios and 'robo_equity' in aggregated_portfolios[profile]:
                data = aggregated_portfolios[profile]
                robo_ratio = data['robo_equity'] / INITIAL_DEPOSIT
                ax.plot(data['equity'].index, robo_ratio, 
                       label=f'Moneyfarm - {profile_labels[profile]}', 
                       linewidth=2.5, color=colors[profile], linestyle='--', alpha=0.6)
        
        ax.set_yscale('log')
        ax.set_title('Total Portfolio Growth - All Symbols (Logarithmic Scale)', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=14, fontweight='bold')
        ax.set_ylabel('Portfolio Value Multiplier (Log Scale)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=12, loc='best', ncol=2)
        ax.grid(True, alpha=0.3, which='both')
        ax.axhline(y=1, color='gray', linestyle='-', linewidth=1, alpha=0.5, label='Break-even')
        
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/portfolio_cumulative_returns_log.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("Portfolio cumulative returns (log scale) saved")
        
        #3) Portfolio Equity Curves (Absolute values)
        fig, ax = plt.subplots(figsize=(20, 10))
        
        for profile in PROFILES:
            if profile not in aggregated_portfolios:
                continue
            data = aggregated_portfolios[profile]
            ax.plot(data['equity'].index, data['equity'], 
                   label=f'Algorithm - {profile_labels[profile]}', 
                   linewidth=3, color=colors[profile], alpha=0.9)
        
        #Add Moneyfarm comparison
        for profile in ['low', 'medium', 'high']:
            if profile in aggregated_portfolios and 'robo_equity' in aggregated_portfolios[profile]:
                data = aggregated_portfolios[profile]
                ax.plot(data['equity'].index, data['robo_equity'], 
                       label=f'Moneyfarm - {profile_labels[profile]}', 
                       linewidth=2.5, color=colors[profile], linestyle='--', alpha=0.6)
        
        ax.axhline(y=INITIAL_DEPOSIT, color='gray', linestyle=':', linewidth=1.5, alpha=0.7, label='Initial Capital')
        
        ax.set_title('Total Portfolio Equity Curves - All Profiles\nAggregated across all symbols', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=14, fontweight='bold')
        ax.set_ylabel('Portfolio Value ($)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=12, loc='best', ncol=2)
        ax.grid(True, alpha=0.3)
        
        #Add final values as text
        text_y_pos = 0.98
        for profile in PROFILES:
            if profile in aggregated_portfolios:
                final_val = aggregated_portfolios[profile]['equity'].iloc[-1]
                final_ret = aggregated_portfolios[profile]['returns'].iloc[-1]
                ax.text(0.02, text_y_pos, 
                       f"{profile_labels[profile]}: ${final_val:,.0f} ({final_ret:+.1f}%)", 
                       transform=ax.transAxes, fontsize=10, fontweight='bold',
                       verticalalignment='top', color=colors[profile],
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
                text_y_pos -= 0.05
        
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/portfolio_equity_curves.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("Portfolio equity curves saved")
        
        #4) Risk-Adjusted Returns Scatter (Return vs Volatility)
        fig, ax = plt.subplots(figsize=(16, 10))
        
        for profile in PROFILES:
            if profile not in aggregated_portfolios:
                continue
            
            data = aggregated_portfolios[profile]
            returns_series = data['equity'].pct_change().dropna()
            
            total_return = data['returns'].iloc[-1]
            volatility = annualized_vol(returns_series)
            
            ax.scatter(volatility, total_return, s=500, color=colors[profile], 
                      alpha=0.7, edgecolors='black', linewidths=2, 
                      label=profile_labels[profile])
            
            #Add profile labels next to points
            ax.annotate(profile_labels[profile], 
                       xy=(volatility, total_return),
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=11, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor=colors[profile], alpha=0.3))
        
        ax.set_title('Risk-Adjusted Performance - Total Portfolio\nReturn vs Volatility across all profiles', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('Annualized Volatility (%)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Total Return (%)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
        
        #Add diagonal lines for Sharpe ratio reference
        max_vol = max([annualized_vol(aggregated_portfolios[p]['equity'].pct_change().dropna()) 
                      for p in aggregated_portfolios.keys()])
        for sharpe in [0.5, 1.0, 1.5, 2.0]:
            x_line = np.linspace(0, max_vol * 1.2, 100)
            y_line = sharpe * x_line
            ax.plot(x_line, y_line, 'k--', alpha=0.2, linewidth=1)
            ax.text(max_vol * 1.15, sharpe * max_vol * 1.15, 
                   f'Sharpe={sharpe}', fontsize=9, alpha=0.5)
        
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/portfolio_risk_return_scatter.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("Portfolio risk-return scatter saved")
        
        #5) Final Performance Summary Table
        summary_data = []
        for profile in PROFILES:
            if profile not in aggregated_portfolios:
                continue
            
            data = aggregated_portfolios[profile]
            returns_series = data['equity'].pct_change().dropna()
            
            final_equity = data['equity'].iloc[-1]
            total_return = data['returns'].iloc[-1]
            volatility = annualized_vol(returns_series)
            sharpe = returns_series.mean() / returns_series.std() * (252 ** 0.5) if returns_series.std() != 0 else 0
            
            #Calculate drawdown
            peak = data['equity'].cummax()
            drawdown = (data['equity'] - peak) / peak * 100
            max_dd = drawdown.min()
            
            summary_data.append({
                'Profile': profile_labels[profile],
                'Final Value ($)': f"${final_equity:,.2f}",
                'Total Return (%)': f"{total_return:+.2f}%",
                'Volatility (%)': f"{volatility:.2f}%",
                'Sharpe Ratio': f"{sharpe:.2f}",
                'Max Drawdown (%)': f"{max_dd:.2f}%"
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(f"{OUTPUT_DIR}/portfolio_performance_summary.csv", index=False)
        print("Portfolio performance summary saved")
        
        #Create visual table
        fig, ax = plt.subplots(figsize=(16, 6))
        ax.axis('tight')
        ax.axis('off')
        
        table = ax.table(cellText=summary_df.values, colLabels=summary_df.columns,
                        cellLoc='center', loc='center',
                        colWidths=[0.2, 0.15, 0.15, 0.15, 0.15, 0.2])
        
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.5)
        
        #Style header
        for i in range(len(summary_df.columns)):
            table[(0, i)].set_facecolor('#2E86AB')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        #Color rows by profile
        for i, profile in enumerate(PROFILES):
            if profile in [p.lower().replace(' (monthly buy)', '').replace(' risk (p1)', '').replace(' risk (p4)', '').replace(' risk (p7)', '') for p in summary_df['Profile']]:
                for j in range(len(summary_df.columns)):
                    if i < len(summary_df):
                        table[(i+1, j)].set_facecolor(colors[profile])
                        table[(i+1, j)].set_alpha(0.3)
        
        plt.title('Total Portfolio Performance Summary', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/portfolio_performance_table.png", dpi=300, bbox_inches='tight')
        plt.close()
        print("Portfolio performance table saved")
        
    except Exception as e:
        print(f"[ERROR] Failed to create portfolio-level graphs: {e}")

    print("\n" + "="*60)
    print("All portfolio graphs completed")
    print("="*60)

if __name__ == "__main__":
    main()