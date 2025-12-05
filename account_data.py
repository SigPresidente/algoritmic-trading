#VARIOUS CONFIGURATION DATA

#Strategy parameters
SHORT_MA = [50, 100, 150]  # Short-term Moving Averages
LONG_MA = [70, 150, 200]  # Long-term Moving Averages
RSI_PERIOD = [7, 10, 14]  # RSI period
RSI_OVERBOUGHT = [50, 60, 70]  # RSI sell thresholds
RSI_OVERSOLD = [50, 40, 20]    # RSI buy thresholds

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

#Yfinance Config
START_DATE = "2018-01-01"

#Robo Advisor Config (cost and returns based on risk profiles)
ROBO_COMMISSION = 0.015 #1.5% commission
ROBO_LOW_RISK =
ROBO_MEDIUM_RISK = 
ROBO_HIGH_RISK =