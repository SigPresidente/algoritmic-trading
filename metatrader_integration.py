#IMPORTS SIGNALS FROM .CSV AND SENDS ORDERS TO MT5

#Libraries
import MetaTrader5 as mt5
import pandas as pd

#Files
from account_data import *

#Config
mt5_symbol_map = {"^NDX": "US100"}

#Fetch latest signal
def get_latest_signal(sym, profile):
    csv_path = f"{OUTPUT_DIR}/{sym.lower().replace('^', '')}_signals_{profile}.csv"
    df = pd.read_csv(csv_path, index_col='date', parse_dates=True)
    return df['Signal'].iloc[-1]  #Last row

#Send order
def send_order_to_mt5(signal, sym, profile):
    if not mt5.initialize():
        print("MT5 initialization failed")
        return
    
    #Log into account
    if not mt5.login(MT5_ACCOUNT, password=MT5_PASSWORD, server=MT5_SERVER):
        print("MT5 login failed. Check credentials/server.")
        mt5.shutdown()
        return
    
    mt5_symbol = mt5_symbol_map.get(sym, None)
    if mt5_symbol is None:
        print(f"No MT5 symbol mapping for {sym}")
        mt5.shutdown()
        return
    
    #Get current info from MT5 symbol
    tick = mt5.symbol_info_tick(mt5_symbol)
    if tick is None:
        print(f"Invalid symbol: {mt5_symbol}")
        mt5.shutdown()
        return
    
    # Get profile-specific risk parameters (skip PAC as it's not for MT5)
    if profile == 'pac':
        print("PAC profile doesn't use MT5 trading. Skipping.")
        mt5.shutdown()
        return
    
    #Make calculations for SL/TP/Trail
    profile_idx = PROFILES.index(profile)
    sl_percent = STOP_LOSS[profile_idx]
    tp_percent = TAKE_PROFIT[profile_idx]
    trail_percent = TRAIL_PERCENT[profile_idx]
   
    sl = 0.0
    tp = 0.0
    if signal == 1:  # Buy
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask  # Buy at ask price
        sl = price * (1 - sl_percent)  # SL below entry
        tp = price * (1 + tp_percent)  # TP above entry
        comment = f"Python Buy {profile.upper()}"
    elif signal == -1:  # Sell
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid  # Sell at bid price
        sl = price * (1 + sl_percent)  # SL above entry
        tp = price * (1 - tp_percent)  # TP below entry
        comment = f"Python Sell {profile.upper()}"
    else:  # Hold
        print("No signal (Hold). No order sent.")
        mt5.shutdown()
        return
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": mt5_symbol,
        "volume": LOT_SIZE,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": SLIPPAGE,
        "magic": MAGIC_NUMBER,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,  # Good till cancel
        "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or cancel
    }
    
    # Send order
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.comment}")
    else:
        print(f"Order executed: {result.order} at price {result.price}")
        print(f"  Profile: {profile.upper()}")
        print(f"  SL: {sl:.2f} ({sl_percent*100:.1f}%)")
        print(f"  TP: {tp:.2f} ({tp_percent*100:.1f}%)")
        print(f"  Trailing: {trail_percent*100:.1f}%")
    
    mt5.shutdown()