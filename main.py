# MAIN SCRIPT

#Libraries
import time
from datetime import datetime

#Files
import import_data
import signals_generation
import metatrader_integration
import backtesting
import print_graphs

#Config for checking intervals (in seconds)
check_interval = 300 #check every 5 mins
backtest_interval = 86400 #1 backtest a day

#Main function: runs a full cycle of data acquisition and signal generation->execution
def run_cycle():
    print(f"\n[{datetime.now()}] Starting cycle...")
    
    #1) Check/update historical data and save CSVs
    for sym in import_data.symbols:
        import_data.fetch_and_save_yfinance_data(sym)
    
    #2) Calculate strategy signals and operate on MT5
    signals_generation.main()
    
    for sym in signals_generation.symbols:
        csv_path = f"{sym.lower().replace('^', '')}_signals.csv"
        latest_signal = metatrader_integration.get_latest_signal(csv_path)
        metatrader_integration.send_order_to_mt5(latest_signal)
    
    #3) Run backtesting and save data for graphs
    backtesting.main()
    
    #4) Generate and save graphs
    print_graphs.main() 
    
    print(f"[{datetime.now()}] Cycle complete.")

#Run on a server (real time)
if __name__ == "__main__":
    last_backtest_time = time.time() - backtest_interval  #Run backtest on first cycle
    
    while True:
        run_cycle()
        
        #Sleep for check interval
        time.sleep(check_interval)