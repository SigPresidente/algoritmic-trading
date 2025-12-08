# MAIN SCRIPT

#Libraries
import time
import signal
import sys
from datetime import datetime

#Files
from account_data import *
import import_data
import signals_generation
#import metatrader_integration
import backtesting
import print_graphs

#Config for checking intervals (in seconds)
check_interval = 300 #check every 5 mins
backtest_interval = 86400 #1 backtest a day

#Flag for manual cycle shutdown
running = True

def signal_handler(sig, frame):
    global running
    print("\n\n[SHUTDOWN] Received stop signal. Finishing current cycle...")
    running = False

#Main function: runs a full cycle of data acquisition and signal generation->execution
def run_cycle():
    print(f"\n[{datetime.now()}] Starting cycle...")
    
    try:
        #1) Check/update historical data and save CSVs
        for sym in SYMBOLS:
            import_data.fetch_and_save_yfinance_data(sym)
        
        #2) Calculate strategy signals and operate on MT5
        signals_generation.main()
        
        #COMMENTED OUT FOR DEBUGGING
        #for sym in SYMBOLS:
        #    for profile in PROFILES:
        #        latest_signal = metatrader_integration.get_latest_signal(sym, profile)
        #        metatrader_integration.send_order_to_mt5(latest_signal, sym, profile)

        #3) Run backtesting and save data for graphs
        backtesting.main()
        
        #4) Generate and save graphs
        print_graphs.main() 
        
        print(f"[{datetime.now()}] Cycle complete.")
        return True
        
    except Exception as e:
        print(f"[ERROR] Cycle failed: {e}")
        return False

#Manual cycle interruption
def countdown_with_interrupt(seconds):
    end_time = time.time() + seconds
    while time.time() < end_time and running:
        remaining = int(end_time - time.time())
        if remaining > 0 and remaining % 60 == 0:  #Print every minute
            print(f"[INFO] Next cycle in {remaining // 60} minute(s)... (Press Ctrl+C to stop)")
        time.sleep(1)
    return running

#Run on a server (real time)
if __name__ == "__main__":
    #Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("="*60)
    print("TRADING BOT STARTED")
    print("="*60)
    print(f"Check interval: {check_interval} seconds ({check_interval/60:.1f} minutes)")
    print(f"Symbols: {', '.join(SYMBOLS)}")
    print(f"Profiles: {', '.join(PROFILES)}")
    print("\nPress Ctrl+C at any time to stop the bot.")
    print("="*60)
    
    last_backtest_time = time.time() - backtest_interval  #Run backtest on first cycle
    cycle_count = 0
    
    while running:
        cycle_count += 1
        print(f"\n{'='*60}")
        print(f"CYCLE #{cycle_count}")
        print(f"{'='*60}")
        
        success = run_cycle()
        
        if not running:
            break
            
        if success:
            print(f"\n[INFO] Waiting {check_interval} seconds until next cycle...\nPress Ctrl+C to stop.")
            if not countdown_with_interrupt(check_interval):
                break
        else:
            print(f"\n[WARNING] Cycle failed. Waiting 60 seconds before retry...")
            if not countdown_with_interrupt(60):
                break
    
    print("\n" + "="*60)
    print("TRADING BOT STOPPED")
    print("="*60)
    print(f"Total cycles completed: {cycle_count}")
    print(f"Shutdown time: {datetime.now()}")
    print("="*60)
    sys.exit(0)