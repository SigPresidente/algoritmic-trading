#Comanda operazioni su MT5 dai segnali generati

import MetaTrader5 as mt5

# Inizializza MT5 (avvia MT5 terminale)
if not mt5.initialize():
    print("Inizializzazione fallita")
    mt5.shutdown()

# Login account demo
account = xxxx  
password = 'xxxx'
server = 'xxxx'  # Broker
mt5.login(account, password, server)

# Invia ordine basato su segnale (da script)
symbol = 'NDX'  # nome simbolo su mt5
signal = 1  # Segnale arriva da script (1=buy, -1=sell)

if signal == 1:
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": 0.1,  # Lotto da decidere
        "type": mt5.ORDER_TYPE_BUY,
        "price": mt5.symbol_info_tick(symbol).ask,
        "deviation": 20,
        "magic": 234000,
        "comment": "Python Buy",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    print(result)

# Chiudi connessione
mt5.shutdown()