#IMPORTS SIGNALS FROM CSV AND SENDS ORDERS TO MT5

#Libraries
import MetaTrader5 as mt5
import pandas as pd

#Files
from account_data import *
from import_data import *

#Config:
symbol = 'US100'  # CHECK SYMBOL FPMarkets
volume = 0.1  #CHECK LOT DIMENSION
deviation = 20  #CHECK SLIPPAGE
account = MT5_ACCOUNT
password = MT5_PASSWORD
server = MT5_SERVER

#Fetch latest signal:
def get_latest_signal(csv_path='ndx_with_macd_rsi_dmi_signals.csv'):
    df = pd.read_csv(csv_path, index_col='date', parse_dates=True)
    latest_signal = df['Signal'].iloc[-1]  #Last row
    return latest_signal

#Send order:
def send_order_to_mt5(signal):
    if not mt5.initialize():
        print("MT5 initialization failed")
        return
    
    #Login
    if not mt5.login(account, password=password, server=server):
        print("MT5 login failed. Check credentials/server.")
        mt5.shutdown()
        return
    
    #Get current info from symbol
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"Invalid symbol: {symbol}")
        mt5.shutdown()
        return
    
    #Prepare order request following signal
    if signal == 1:  # Buy
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask  # Buy at ask price
        comment = "Python Buy Signal"
    elif signal == -1:  # Sell
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid  # Sell at bid price
        comment = "Python Sell Signal"
    else:  # Hold
        print("No signal (Hold). No order sent.")
        mt5.shutdown()
        return
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": deviation,
        "magic": 12345,  #CHECK MAGIC NUMBER
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,  #Good till cancel
        "type_filling": mt5.ORDER_FILLING_IOC,  #Immediate or cancel
    }
    
    #Send order
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.comment}")
    else:
        print(f"Order executed: {result.order} at price {result.price}")
    
    mt5.shutdown()

# Example usage: Get signal and send
latest_signal = get_latest_signal()  # From your generator CSV
send_order_to_mt5(latest_signal)