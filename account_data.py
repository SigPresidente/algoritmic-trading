#VARIOUS CONFIGURATION DATA

#Strategy parameters
SHORT_MA = 100  # Short-term Moving Average
LONG_MA = 150  # Long-term Moving Average
RSI_PERIOD = 14  # RSI period
RSI_OVERBOUGHT = 50  # RSI sell threshold
RSI_OVERSOLD = 50    # RSI buy threshold

#Account parameters
SYMBOLS = ["^NDX"]
INITIAL_DEPOSIT = 5000
COMMISSION = 0.000 #no commissions on "manual" trading
STOP_LOSS = 0.02 #2% SL fixed
TAKE_PROFIT = 0.04 #4% TP when used
TRAIL_PERCENT = 0.02 #2% trailing stop loss

#Metatrader5 Config
MT5_ACCOUNT = "77777777"
MT5_PASSWORD = "password"
MT5_SERVER = "FirstPrudentialMarkets-Demo"
MAGIC_NUMBER = "09031994"
LOT_SIZE = 1.0
SLIPPAGE = 20

#Output directory
OUTPUT_DIR = "./output"